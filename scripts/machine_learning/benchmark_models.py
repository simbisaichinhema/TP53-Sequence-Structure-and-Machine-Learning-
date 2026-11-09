"""Multi-model benchmark for TP53 missense pathogenicity classification.

Fair protocol (identical for every algorithm):
  - Same 21-column feature matrix (data/processed/structural_features/
    tp53_features.csv)
  - Same stratified 80/20 train/test split, seed 42
  - Same 5-fold stratified CV on the training partition only
  - Preprocessing (scaling) fit inside the pipeline on training folds only
  - Held-out test used once per model for final metrics — never for
    hyperparameter or model selection

Baselines (logistic_regression, random_forest) use the same estimator
settings as scripts/machine_learning/train.py. The existing train.py /
predict.py / model.joblib pipeline is left untouched; this script writes
its own artefacts under results/machine_learning/benchmark/.

Usage:
  python3 scripts/machine_learning/benchmark_models.py
  python3 scripts/machine_learning/benchmark_models.py --skip-figures
  python3 scripts/machine_learning/benchmark_models.py --models random_forest svm

Outputs:
  results/machine_learning/benchmark/benchmark_results.csv
  results/machine_learning/benchmark/benchmark_results.json
  results/machine_learning/benchmark/cv_folds.json
  results/machine_learning/benchmark/experiment_config.json
  results/machine_learning/benchmark/models/<name>.joblib
  results/machine_learning/benchmark/benchmark_report.md
  figures/machine_learning/benchmark/*.png
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.utils.class_weight import compute_sample_weight

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from metrics_utils import (RATE_METRICS, aggregate_cv_metrics,  # noqa: E402
                           binary_metrics, round_metrics)
from model_registry import (ModelSpec, all_specs,  # noqa: E402
                            display_names, missing_optional_packages)

FEAT_CSV = REPO / "data/processed/structural_features/tp53_features.csv"
RES_DIR = REPO / "results/machine_learning/benchmark"
MODEL_DIR = RES_DIR / "models"
FIG_DIR = REPO / "figures/machine_learning/benchmark"

# Identical to train.py — do not drift
FEATURES = ["pos_norm", "in_core", "dom_TAD1", "dom_TAD2", "dom_PRR",
            "dom_DBD", "dom_hinge", "dom_TET", "dom_CTD", "dist_to_zn",
            "grantham", "d_hydro", "d_volume", "d_charge", "d_polarity",
            "ref_hydro", "ref_volume", "ref_charge", "plddt_at_pos",
            "plddt_window5", "dna_contact"]

SEED = 42
TEST_SIZE = 0.2
N_SPLITS = 5
STAGE = "baseline"

TARGET_DESC = "ClinVar pathogenicity (1=P/LP, 0=B/LB)"

# Publication-style defaults (no exaggerated axes; bars start at 0)
RC = {
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "legend.fontsize": 9,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.axisbelow": True,
}


def load_data():
    df = pd.read_csv(FEAT_CSV)
    missing = [f for f in FEATURES if f not in df.columns]
    if missing:
        raise SystemExit(f"Missing feature columns in {FEAT_CSV}: {missing}")
    if "label" not in df.columns:
        raise SystemExit("label column missing from feature CSV")
    X = df[FEATURES].to_numpy(dtype=float)
    y = df["label"].astype(int).to_numpy()
    return df, X, y


def fit_predict(est, spec: ModelSpec, X_tr, y_tr, X_ev):
    fit_params = {}
    if spec.balance_mode == "sample_weight":
        w = compute_sample_weight("balanced", y_tr)
        step = est.steps[-1][0] if hasattr(est, "steps") else None
        if step is not None:
            fit_params[f"{step}__sample_weight"] = w
        else:
            fit_params["sample_weight"] = w
    est.fit(X_tr, y_tr, **fit_params)
    proba = est.predict_proba(X_ev)[:, 1]
    pred = (proba >= 0.5).astype(int)
    return pred, proba


def evaluate_model(spec: ModelSpec, X_tr, y_tr, X_te, y_te, seed: int):
    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=seed)
    fold_metrics = []
    for tr_i, va_i in cv.split(X_tr, y_tr):
        est = spec.builder(seed)
        pred, proba = fit_predict(est, spec, X_tr[tr_i], y_tr[tr_i],
                                  X_tr[va_i])
        fold_metrics.append(binary_metrics(y_tr[va_i], pred, proba))
    cv_agg = aggregate_cv_metrics(fold_metrics)

    # Final model on full training partition, evaluated once on held-out test
    est = spec.builder(seed)
    pred_te, proba_te = fit_predict(est, spec, X_tr, y_tr, X_te)
    test_metrics = binary_metrics(y_te, pred_te, proba_te)

    return {
        "name": spec.name,
        "display_name": spec.display_name,
        "family": spec.family,
        "needs_scaling": spec.needs_scaling,
        "balance_mode": spec.balance_mode,
        "notes": spec.notes,
        "cv": cv_agg,
        "test": test_metrics,
        "test_pred": pred_te,
        "test_proba": proba_te,
        "fitted": est,
    }


def flatten_for_csv(result: dict) -> dict:
    row = {
        "model": result["name"],
        "display_name": result["display_name"],
        "family": result["family"],
        "balance_mode": result["balance_mode"],
        "needs_scaling": result["needs_scaling"],
        "stage": STAGE,
    }
    for k in RATE_METRICS:
        row[f"cv_{k}_mean"] = result["cv"][f"{k}_mean"]
        row[f"cv_{k}_std"] = result["cv"][f"{k}_std"]
    for k in ("tn", "fp", "fn", "tp"):
        row[f"cv_{k}_sum"] = result["cv"][k]
    for k in RATE_METRICS:
        row[f"test_{k}"] = result["test"][k]
    for k in ("tn", "fp", "fn", "tp"):
        row[f"test_{k}"] = result["test"][k]
    return row


def json_ready(result: dict) -> dict:
    return {
        "name": result["name"],
        "display_name": result["display_name"],
        "family": result["family"],
        "needs_scaling": result["needs_scaling"],
        "balance_mode": result["balance_mode"],
        "notes": result["notes"],
        "cv": {k: (round(v, 4) if isinstance(v, float) else v)
               for k, v in result["cv"].items() if k != "folds"},
        "cv_folds": [{k: (round(v, 4) if isinstance(v, float) else v)
                      for k, v in f.items()} for f in result["cv"]["folds"]],
        "test": {k: (round(v, 4) if isinstance(v, float) else v)
                 for k, v in result["test"].items()},
    }


def save_model_bundle(spec: ModelSpec, result: dict, path: Path):
    joblib.dump({
        "pipeline": result["fitted"],
        "features": FEATURES,
        "model_name": result["name"],
        "display_name": result["display_name"],
        "target": TARGET_DESC,
        "seed": SEED,
        "stage": STAGE,
        "test_metrics": {k: (round(v, 4) if isinstance(v, float) else v)
                         for k, v in result["test"].items()},
        "cv_roc_auc_mean": round(result["cv"]["roc_auc_mean"], 4),
        "cv_f1_mean": round(result["cv"]["f1_mean"], 4),
    }, path)


# --- figures ---

def _apply_style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(RC)
    return plt


def _sorted_models(results, key):
    return sorted(results, key=lambda r: r["cv"][f"{key}_mean"], reverse=True)


def fig_bar_comparison(results, metric, title, ylabel, fname, ylim=None):
    plt = _apply_style()
    names = [r["display_name"] for r in results]
    means = [r["cv"][f"{metric}_mean"] for r in results]
    stds = [r["cv"][f"{metric}_std"] for r in results]
    order = np.argsort(means)[::-1]
    names = [names[i] for i in order]
    means = [means[i] for i in order]
    stds = [stds[i] for i in order]

    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(names))
    ax.bar(x, means, yerr=stds, capsize=4, color="#1b2a4a",
           edgecolor="black", linewidth=0.6, alpha=0.9)
    ax.set_xticks(x, names, rotation=35, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title + " (5-fold CV on train, mean ± SD)")
    ax.set_ylim(ylim if ylim is not None else (0, 1.0))
    fig.tight_layout()
    fig.savefig(FIG_DIR / fname)
    plt.close(fig)


def fig_roc_curves(results, y_te, n_test=None):
    plt = _apply_style()
    from sklearn.metrics import roc_curve
    n_lbl = f"n={n_test if n_test is not None else len(y_te)}"
    fig, ax = plt.subplots(figsize=(7, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, max(len(results), 1)))
    for r, c in zip(results, colors):
        fpr, tpr, _ = roc_curve(y_te, r["test_proba"])
        ax.plot(fpr, tpr, color=c, lw=1.8,
                label=f"{r['display_name']} (AUC={r['test']['roc_auc']:.3f})")
    ax.plot([0, 1], [0, 1], "--", color="grey", lw=1, label="Chance")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title(f"ROC curves — held-out test set ({n_lbl})")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(loc="lower right", frameon=True, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "roc_curves.png")
    plt.close(fig)


def fig_pr_curves(results, y_te, n_test=None):
    plt = _apply_style()
    from sklearn.metrics import precision_recall_curve
    n_lbl = f"n={n_test if n_test is not None else len(y_te)}"
    fig, ax = plt.subplots(figsize=(7, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, max(len(results), 1)))
    base = float(np.mean(y_te))
    for r, c in zip(results, colors):
        prec, rec, _ = precision_recall_curve(y_te, r["test_proba"])
        ax.plot(rec, prec, color=c, lw=1.8,
                label=f"{r['display_name']} (AP={r['test']['pr_auc']:.3f})")
    ax.axhline(base, ls="--", color="grey", lw=1,
               label=f"Prevalence ({base:.2f})")
    ax.set_xlabel("Recall (sensitivity)")
    ax.set_ylabel("Precision")
    ax.set_title(f"Precision–recall curves — held-out test set ({n_lbl})")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(loc="upper right", frameon=True, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "precision_recall_curves.png")
    plt.close(fig)


def fig_confusion_matrices(results, y_te, n_test=None):
    plt = _apply_style()
    from sklearn.metrics import confusion_matrix
    n_lbl = f"n={n_test if n_test is not None else len(y_te)}"
    n = len(results)
    ncols = 5
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.2 * ncols, 3.2 * nrows))
    axes = np.atleast_1d(axes).ravel()
    for ax in axes:
        ax.axis("off")
    for ax, r in zip(axes, results):
        cm = confusion_matrix(y_te, r["test_pred"], labels=[0, 1])
        ax.axis("on")
        im = ax.imshow(cm, cmap="Blues")
        ax.set_xticks([0, 1], ["Benign", "Pathogenic"])
        ax.set_yticks([0, 1], ["Benign", "Pathogenic"])
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title(f"{r['display_name']}", fontsize=10)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, int(cm[i, j]), ha="center", va="center",
                        color="black" if cm[i, j] < cm.max() / 2 else "white")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle(f"Confusion matrices — held-out test set ({n_lbl})",
                 y=1.01)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "confusion_matrices.png")
    plt.close(fig)


def fig_cv_variability(results):
    plt = _apply_style()
    results = _sorted_models(results, "roc_auc")
    names = [r["display_name"] for r in results]
    aucs = [r["cv"]["roc_auc_mean"] for r in results]
    auc_sd = [r["cv"]["roc_auc_std"] for r in results]
    f1s = [r["cv"]["f1_mean"] for r in results]
    f1_sd = [r["cv"]["f1_std"] for r in results]

    x = np.arange(len(names))
    width = 0.38
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width / 2, aucs, width, yerr=auc_sd, capsize=3,
           label="ROC-AUC", color="#1b2a4a", edgecolor="black", linewidth=0.5)
    ax.bar(x + width / 2, f1s, width, yerr=f1_sd, capsize=3,
           label="F1", color="#0e7c7b", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x, names, rotation=35, ha="right")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.0)
    ax.set_title("Cross-validation performance and variability "
                 "(5-fold, train partition)")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "cv_performance_variability.png")
    plt.close(fig)


def write_report(results, cfg, path: Path):
    dnames = display_names()
    lines = [
        "# TP53 multi-model benchmark report",
        "",
        f"Generated: {cfg['generated_at_utc']}  ",
        f"Stage: **{cfg['stage']}** (baseline hyperparameters, no tuning)  ",
        f"Random seed: **{cfg['seed']}**",
        "",
        "## Protocol",
        "",
        f"- Dataset: `{cfg['feature_csv']}` — n={cfg['n_samples']}, "
        f"features={cfg['n_features']} (same matrix for every model)",
        f"- Labels: {cfg['target']}",
        f"- Split: stratified {int((1 - cfg['test_size']) * 100)}/"
        f"{int(cfg['test_size'] * 100)} train/test, seed {cfg['seed']} "
        f"(train={cfg['n_train']}, test={cfg['n_test']})",
        f"- CV: {cfg['n_splits']}-fold stratified on the **training partition "
        "only**",
        "- Preprocessing: `StandardScaler` inside the pipeline for linear "
        "models and SVM; tree ensembles unscaled",
        "- Class imbalance: balanced class weights or balanced sample "
        "weights fitted per training fold",
        "- Held-out test: used once per model for final metrics; **not** "
        "used for model or hyperparameter selection",
        "",
        "## Optional packages",
        "",
    ]
    missing = cfg.get("missing_optional_packages") or []
    if missing:
        lines.append("Skipped models (package not installed):")
        for m in missing:
            lines.append(f"- `{m['package']}` — install with `{m['pip']}`")
    else:
        lines.append("All optional packages available "
                     "(xgboost, lightgbm, catboost).")

    lines += [
        "",
        "## Consolidated test-set results (held-out, n="
        f"{cfg['n_test']})",
        "",
        "| Model | Accuracy | Bal. acc | Precision | Recall | Specificity "
        "| F1 | ROC-AUC | PR-AUC | MCC | TN | FP | FN | TP |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(results, key=lambda x: x["test"]["roc_auc"], reverse=True):
        t = r["test"]
        lines.append(
            f"| {r['display_name']} | {t['accuracy']:.3f} | "
            f"{t['balanced_accuracy']:.3f} | {t['precision']:.3f} | "
            f"{t['recall']:.3f} | {t['specificity']:.3f} | {t['f1']:.3f} | "
            f"{t['roc_auc']:.3f} | {t['pr_auc']:.3f} | {t['mcc']:.3f} | "
            f"{t['tn']} | {t['fp']} | {t['fn']} | {t['tp']} |")

    lines += [
        "",
        "## Cross-validation (train partition, mean ± SD)",
        "",
        "| Model | Acc | Bal. acc | F1 | ROC-AUC | PR-AUC | MCC |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in sorted(results, key=lambda x: x["cv"]["roc_auc_mean"],
                    reverse=True):
        c = r["cv"]
        lines.append(
            f"| {r['display_name']} | "
            f"{c['accuracy_mean']:.3f}±{c['accuracy_std']:.3f} | "
            f"{c['balanced_accuracy_mean']:.3f}±"
            f"{c['balanced_accuracy_std']:.3f} | "
            f"{c['f1_mean']:.3f}±{c['f1_std']:.3f} | "
            f"{c['roc_auc_mean']:.3f}±{c['roc_auc_std']:.3f} | "
            f"{c['pr_auc_mean']:.3f}±{c['pr_auc_std']:.3f} | "
            f"{c['mcc_mean']:.3f}±{c['mcc_std']:.3f} |")

    best = max(results, key=lambda r: r["cv"]["roc_auc_mean"])
    best_test = max(results, key=lambda r: r["test"]["roc_auc"])
    lines += [
        "",
        "## Selection notes",
        "",
        f"- Highest mean CV ROC-AUC (selection criterion, train only): "
        f"**{best['display_name']}** "
        f"({best['cv']['roc_auc_mean']:.3f}±{best['cv']['roc_auc_std']:.3f})",
        f"- Highest held-out test ROC-AUC (reported, not used for "
        f"selection): {best_test['display_name']} "
        f"({best_test['test']['roc_auc']:.3f})",
        "",
        "Model selection and any hyperparameter search use CV on the "
        "training partition only. Test metrics are descriptive of the "
        "fixed split.",
        "",
        "## Scientific limitations",
        "",
        "- These are **research prototype scores on a random stratified "
        f"split of {cfg['n_samples']} ClinVar missense variants**, not "
        "clinical performance estimates.",
        "- Variants from the same residue (and from the same hotspot) "
        "can appear in both train and test. Position carries strong "
        "signal; random splitting therefore risks optimistic estimates.",
        "- Position-aware (group-by-residue) and leave-one-hotspot-out "
        "evaluation are prepared as a separate experiment "
        "(`scripts/machine_learning/position_aware_validation.py`).",
        "- No difficult variants were removed and no labels were "
        "modified to improve scores.",
        f"- n={cfg['n_samples']} is small; results need external "
        "validation before any downstream use.",
        "",
        "## Artefacts",
        "",
        "- `results/machine_learning/benchmark/benchmark_results.csv`",
        "- `results/machine_learning/benchmark/benchmark_results.json`",
        "- `results/machine_learning/benchmark/cv_folds.json`",
        "- `results/machine_learning/benchmark/experiment_config.json`",
        "- `results/machine_learning/benchmark/models/*.joblib`",
        "- `figures/machine_learning/benchmark/*.png`",
        "- Prediction: `python3 scripts/machine_learning/predict.py "
        "--model results/machine_learning/benchmark/models/<name>.joblib "
        "R 175 H`",
        "",
    ]
    path.write_text("\n".join(lines))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--models", nargs="*", default=None,
                    help="Subset of model names to run")
    ap.add_argument("--skip-figures", action="store_true")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args(argv)

    import matplotlib
    matplotlib.use("Agg")
    # sklearn>=1.9 deprecation noise around SVC(probability=True)
    warnings.filterwarnings(
        "ignore",
        message=r".*`probability` parameter was deprecated.*",
        category=FutureWarning)

    RES_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    specs = all_specs(include_extra=bool(args.models))
    if args.models:
        wanted = set(args.models)
        known = {s.name for s in specs}
        unknown = wanted - known
        if unknown:
            raise SystemExit(f"Unknown models: {sorted(unknown)}; "
                             f"available: {sorted(known)}")
        specs = [s for s in specs if s.name in wanted]

    df, X, y = load_data()
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=args.seed)

    print(f"dataset n={len(y)} features={len(FEATURES)} "
          f"P={int(y.sum())} B={len(y) - int(y.sum())}")
    print(f"train={len(y_tr)} (P={int(y_tr.sum())}) test={len(y_te)} "
          f"(P={int(y_te.sum())}) seed={args.seed}")
    print(f"models: {', '.join(s.name for s in specs)}")

    results = []
    t0 = time.time()
    for spec in specs:
        t1 = time.time()
        res = evaluate_model(spec, X_tr, y_tr, X_te, y_te, args.seed)
        dt = time.time() - t1
        results.append(res)
        print(f"  {spec.name}: CV AUC={res['cv']['roc_auc_mean']:.4f}"
              f"±{res['cv']['roc_auc_std']:.4f} "
              f"F1={res['cv']['f1_mean']:.4f}±{res['cv']['f1_std']:.4f} | "
              f"test AUC={res['test']['roc_auc']:.4f} "
              f"F1={res['test']['f1']:.4f} "
              f"acc={res['test']['accuracy']:.4f} ({dt:.1f}s)")
        save_model_bundle(spec, res, MODEL_DIR / f"{spec.name}.joblib")

    elapsed = time.time() - t0
    print(f"done in {elapsed:.1f}s")

    # --- consolidated outputs ---
    csv_rows = [flatten_for_csv(r) for r in results]
    csv_df = pd.DataFrame(csv_rows)
    csv_path = RES_DIR / "benchmark_results.csv"
    csv_df.to_csv(csv_path, index=False)

    cfg = {
        "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "test_size": TEST_SIZE,
        "n_splits": N_SPLITS,
        "feature_csv": str(FEAT_CSV.relative_to(REPO)),
        "features": FEATURES,
        "n_features": len(FEATURES),
        "n_samples": int(len(y)),
        "n_train": int(len(y_tr)),
        "n_test": int(len(y_te)),
        "n_pathogenic": int(y.sum()),
        "n_benign": int(len(y) - y.sum()),
        "target": TARGET_DESC,
        "models_run": [r["name"] for r in results],
        "missing_optional_packages": missing_optional_packages(),
        "selection_metric": "cv_roc_auc_mean (train CV only)",
        "test_set_used_for_selection": False,
        "script": "scripts/machine_learning/benchmark_models.py",
        "elapsed_seconds": round(elapsed, 2),
        "class_balance_mode": {
            r["name"]: r["balance_mode"] for r in results
        },
        "scaling": {
            r["name"]: ("StandardScaler in Pipeline" if r["needs_scaling"]
                        else "none (tree/ensemble)") for r in results
        },
    }
    (RES_DIR / "experiment_config.json").write_text(
        json.dumps(cfg, indent=2))

    payload = {
        "config": cfg,
        "results": [json_ready(r) for r in results],
    }
    (RES_DIR / "benchmark_results.json").write_text(
        json.dumps(payload, indent=2))

    folds = {r["name"]: r["cv"]["folds"] for r in results}
    (RES_DIR / "cv_folds.json").write_text(json.dumps(
        {k: round_metrics(v) for k, v in folds.items()}, indent=2))

    write_report(results, cfg, RES_DIR / "benchmark_report.md")

    # --- figures ---
    if not args.skip_figures:
        ordered = sorted(results, key=lambda r: r["cv"]["roc_auc_mean"],
                         reverse=True)
        fig_bar_comparison(
            ordered, "accuracy",
            "Model accuracy comparison", "Accuracy (CV mean)",
            "accuracy_comparison.png")
        fig_bar_comparison(
            ordered, "f1",
            "Model F1 comparison", "F1 (CV mean)",
            "f1_comparison.png")
        fig_bar_comparison(
            ordered, "roc_auc",
            "Model ROC-AUC comparison", "ROC-AUC (CV mean)",
            "roc_auc_comparison.png")
        fig_bar_comparison(
            ordered, "pr_auc",
            "Model PR-AUC comparison", "PR-AUC / average precision (CV mean)",
            "pr_auc_comparison.png")
        fig_roc_curves(sorted(results, key=lambda r: r["test"]["roc_auc"],
                              reverse=True), y_te, n_test=len(y_te))
        fig_pr_curves(sorted(results, key=lambda r: r["test"]["pr_auc"],
                             reverse=True), y_te, n_test=len(y_te))
        fig_confusion_matrices(
            sorted(results, key=lambda r: r["test"]["f1"], reverse=True),
            y_te, n_test=len(y_te))
        fig_cv_variability(results)
        print(f"figures -> {FIG_DIR}")

    # Console summary table
    print("\nHeld-out test metrics:")
    hdr = (f"{'model':24s} {'acc':>6s} {'bal':>6s} {'f1':>6s} "
           f"{'auc':>6s} {'ap':>6s} {'mcc':>6s}")
    print(hdr)
    for r in sorted(results, key=lambda x: x["test"]["roc_auc"],
                    reverse=True):
        t = r["test"]
        print(f"{r['name']:24s} {t['accuracy']:6.3f} "
              f"{t['balanced_accuracy']:6.3f} {t['f1']:6.3f} "
              f"{t['roc_auc']:6.3f} {t['pr_auc']:6.3f} {t['mcc']:6.3f}")

    print(f"\nwrote {csv_path.relative_to(REPO)} + JSON + report + "
          f"{len(results)} model artefacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
