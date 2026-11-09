"""Controlled hyperparameter optimisation for promising benchmark models.

Runs only on the training partition (stratified CV); the held-out test set
is never used for search. Baseline results from benchmark_models.py are
left untouched — tuned results are written to separate files.

Search spaces are intentionally small (n≈310 training rows).

Usage:
  python3 scripts/machine_learning/tune_models.py
  python3 scripts/machine_learning/tune_models.py --top-k 3
  python3 scripts/machine_learning/tune_models.py --models random_forest svm

Outputs:
  results/machine_learning/benchmark/tuned_benchmark.csv
  results/machine_learning/benchmark/tuned_benchmark.json
  results/machine_learning/benchmark/tuning_searches.json
  results/machine_learning/benchmark/models/<name>_tuned.joblib
  results/machine_learning/benchmark/tuning_report.md
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import (ParameterGrid, StratifiedKFold,
                                     train_test_split)
from sklearn.utils.class_weight import compute_sample_weight

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from benchmark_models import (FEATURES, MODEL_DIR, RES_DIR,  # noqa: E402
                              SEED, TARGET_DESC, TEST_SIZE, evaluate_model,
                              flatten_for_csv, json_ready, load_data)
from metrics_utils import binary_metrics, round_metrics  # noqa: E402
from model_registry import all_specs  # noqa: E402

# Small, controlled grids — deliberately narrow
SEARCH_SPACES: dict[str, list[dict]] = {
    "logistic_regression": [
        {"clf__C": [0.1, 1.0, 10.0]},
    ],
    "random_forest": [
        {"clf__n_estimators": [400, 600],
         "clf__max_depth": [None, 12],
         "clf__min_samples_leaf": [1, 3]},
    ],
    "svm": [
        {"clf__C": [0.5, 1.0, 2.0],
         "clf__gamma": ["scale", 0.01]},
    ],
    "extra_trees": [
        {"clf__n_estimators": [400, 600],
         "clf__max_depth": [None, 12],
         "clf__min_samples_leaf": [1, 3]},
    ],
    "gradient_boosting": [
        {"clf__n_estimators": [200, 300],
         "clf__learning_rate": [0.05, 0.1],
         "clf__max_depth": [2, 3]},
    ],
    "hist_gradient_boosting": [
        {"clf__max_iter": [200, 300],
         "clf__learning_rate": [0.05, 0.1],
         "clf__max_leaf_nodes": [15, 31]},
    ],
    "xgboost": [
        {"clf__n_estimators": [300, 400],
         "clf__learning_rate": [0.05, 0.1],
         "clf__max_depth": [3, 4]},
    ],
    "lightgbm": [
        {"clf__n_estimators": [300, 400],
         "clf__learning_rate": [0.05, 0.1],
         "clf__num_leaves": [15, 31]},
    ],
    "catboost": [
        {"clf__iterations": [300, 400],
         "clf__learning_rate": [0.05, 0.1],
         "clf__depth": [4, 6]},
    ],
    "adaboost": [
        {"clf__n_estimators": [200, 400],
         "clf__learning_rate": [0.05, 0.1]},
    ],
}


def expand_grid(space: list[dict]) -> list[dict]:
    combos: list[dict] = []
    for part in space:
        combos.extend(list(ParameterGrid(part)))
    return combos


def search_best(spec, X_tr, y_tr, seed: int, n_splits: int = 5):
    """Grid search by mean CV ROC-AUC on the training partition only."""
    combos = expand_grid(SEARCH_SPACES.get(spec.name, []))
    if not combos:
        return None, None

    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    fold_splits = list(cv.split(X_tr, y_tr))
    scores = []
    for params in combos:
        fold_aucs = []
        for tr_i, va_i in fold_splits:
            est = spec.builder(seed)
            est.set_params(**params)
            # Re-apply balance mode after set_params (pipeline steps intact)
            fit_params = {}
            if spec.balance_mode == "sample_weight":
                w = compute_sample_weight("balanced", y_tr[tr_i])
                step = est.steps[-1][0]
                fit_params[f"{step}__sample_weight"] = w
            est.fit(X_tr[tr_i], y_tr[tr_i], **fit_params)
            proba = est.predict_proba(X_tr[va_i])[:, 1]
            m = binary_metrics(y_tr[va_i],
                               (proba >= 0.5).astype(int), proba)
            fold_aucs.append(m["roc_auc"])
        scores.append(float(np.mean(fold_aucs)))

    best_i = int(np.nanargmax(scores))
    return combos[best_i], {
        "best_cv_roc_auc": round(scores[best_i], 4),
        "all_scores": [round(s, 4) for s in scores],
        "all_params": [json.dumps(c, default=str) for c in combos],
        "n_candidates": len(combos),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--top-k", type=int, default=3,
                    help="Tune the K models with best baseline CV ROC-AUC")
    ap.add_argument("--models", nargs="*", default=None,
                    help="Explicit model names (overrides --top-k)")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args(argv)

    baseline_path = RES_DIR / "benchmark_results.json"
    if not baseline_path.exists():
        raise SystemExit("Run benchmark_models.py first "
                         "(baseline_benchmark_results.json missing).")

    baseline = json.loads(baseline_path.read_text())
    base_by_name = {r["name"]: r for r in baseline["results"]}

    specs = {s.name: s for s in all_specs(include_extra=True)}
    if args.models:
        names = args.models
    else:
        ranked = sorted(base_by_name,
                        key=lambda n: base_by_name[n]["cv"]["roc_auc_mean"],
                        reverse=True)
        names = ranked[: args.top_k]

    unknown = [n for n in names if n not in specs]
    if unknown:
        raise SystemExit(f"Unknown/unavailable models: {unknown}")

    df, X, y = load_data()
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=args.seed)

    print(f"tuning {names} on train n={len(y_tr)} "
          f"(test n={len(y_te)} untouched during search)")

    search_log = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "selection_metric": "mean CV ROC-AUC (5-fold, train only)",
        "test_used_for_search": False,
        "models": {},
    }
    tuned_rows = []
    tuned_json = []
    t0 = time.time()

    for name in names:
        spec = specs[name]
        t1 = time.time()
        best_params, info = search_best(spec, X_tr, y_tr, args.seed)
        if best_params is None:
            print(f"  {name}: no search space, skipped")
            continue
        print(f"  {name}: best CV AUC={info['best_cv_roc_auc']} "
              f"params={best_params} ({time.time() - t1:.1f}s)")
        search_log["models"][name] = {"best_params": best_params, **info}

        # Evaluate tuned estimator with the same fair protocol as baseline
        from dataclasses import replace

        base_builder = spec.builder

        def _make_builder(params, _b=base_builder):
            def _build(seed):
                est = _b(seed)
                est.set_params(**params)
                return est
            return _build

        tuned_spec = replace(
            spec,
            builder=_make_builder(best_params),
            notes=(spec.notes + "; tuned: "
                   + json.dumps(best_params, default=str)).strip("; "),
        )

        res = evaluate_model(tuned_spec, X_tr, y_tr, X_te, y_te, args.seed)
        res["name"] = f"{name}_tuned"
        res["display_name"] = f"{spec.display_name} (tuned)"
        res["family"] = spec.family
        tuned_rows.append(flatten_for_csv(res))
        # flatten uses STAGE from benchmark; overwrite stage field
        tuned_rows[-1]["stage"] = "tuned"
        tuned_rows[-1]["model"] = name
        tuned_rows[-1]["tuned"] = True
        tuned_rows[-1]["best_params"] = json.dumps(best_params, default=str)

        payload = json_ready(res)
        payload["name"] = name
        payload["display_name"] = f"{spec.display_name} (tuned)"
        payload["stage"] = "tuned"
        payload["best_params"] = {k: (v if not isinstance(v, float)
                                      else round(v, 4))
                                  for k, v in best_params.items()}
        tuned_json.append(payload)

        joblib.dump({
            "pipeline": res["fitted"],
            "features": FEATURES,
            "model_name": f"{name}_tuned",
            "display_name": f"{spec.display_name} (tuned)",
            "target": TARGET_DESC,
            "seed": args.seed,
            "stage": "tuned",
            "base_model": name,
            "best_params": {k: str(v) for k, v in best_params.items()},
            "test_metrics": {k: (round(v, 4) if isinstance(v, float) else v)
                             for k, v in res["test"].items()},
            "cv_roc_auc_mean": round(res["cv"]["roc_auc_mean"], 4),
            "cv_f1_mean": round(res["cv"]["f1_mean"], 4),
        }, MODEL_DIR / f"{name}_tuned.joblib")

    elapsed = time.time() - t0
    RES_DIR.mkdir(parents=True, exist_ok=True)
    (RES_DIR / "tuning_searches.json").write_text(
        json.dumps(search_log, indent=2))

    if not tuned_rows:
        print("nothing tuned")
        return 0

    pd.DataFrame(tuned_rows).to_csv(
        RES_DIR / "tuned_benchmark.csv", index=False)

    # Comparison: baseline vs tuned (same test split)
    cmp_rows = []
    for row, payload in zip(tuned_rows, tuned_json):
        base = base_by_name.get(payload["name"])
        cmp_rows.append({
            "model": payload["name"],
            "baseline_cv_roc_auc":
                base["cv"]["roc_auc_mean"] if base else None,
            "tuned_cv_roc_auc": payload["cv"]["roc_auc_mean"],
            "baseline_test_roc_auc": base["test"]["roc_auc"] if base else None,
            "tuned_test_roc_auc": payload["test"]["roc_auc"],
            "baseline_test_f1": base["test"]["f1"] if base else None,
            "tuned_test_f1": payload["test"]["f1"],
            "best_params": payload["best_params"],
        })

    cfg = {
        "stage": "tuned",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "test_size": TEST_SIZE,
        "n_splits": 5,
        "feature_csv": baseline["config"]["feature_csv"],
        "features": FEATURES,
        "n_features": len(FEATURES),
        "n_samples": baseline["config"]["n_samples"],
        "n_train": baseline["config"]["n_train"],
        "n_test": baseline["config"]["n_test"],
        "target": TARGET_DESC,
        "models_run": [r["model"] for r in tuned_rows],
        "missing_optional_packages":
            baseline["config"].get("missing_optional_packages", []),
        "selection_metric": "cv_roc_auc_mean (train CV only)",
        "test_set_used_for_selection": False,
        "script": "scripts/machine_learning/tune_models.py",
        "elapsed_seconds": round(elapsed, 2),
        "baseline_benchmark": str(baseline_path.relative_to(REPO)),
        "comparison": cmp_rows,
    }
    (RES_DIR / "tuned_benchmark.json").write_text(json.dumps({
        "config": cfg,
        "results": tuned_json,
        "comparison_to_baseline": cmp_rows,
    }, indent=2))

    # Report
    lines = [
        "# TP53 hyperparameter tuning report",
        "",
        f"Generated: {cfg['generated_at_utc']}  ",
        "Search metric: mean 5-fold CV ROC-AUC on the **training "
        "partition only**  ",
        f"Seed: {args.seed}  ",
        f"Models tuned: {', '.join(cfg['models_run'])}",
        "",
        "Baseline results are unchanged (see `benchmark_report.md`). "
        "Held-out test metrics below are reported after the search and "
        "were not used to pick hyperparameters.",
        "",
        "| Model | Baseline CV AUC | Tuned CV AUC | Baseline test AUC "
        "| Tuned test AUC | Baseline test F1 | Tuned test F1 | Best params "
        "|",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in cmp_rows:
        lines.append(
            f"| {c['model']} | {c['baseline_cv_roc_auc']:.4f} | "
            f"{c['tuned_cv_roc_auc']:.4f} | "
            f"{c['baseline_test_roc_auc']:.4f} | "
            f"{c['tuned_test_roc_auc']:.4f} | "
            f"{c['baseline_test_f1']:.4f} | {c['tuned_test_f1']:.4f} | "
            f"`{json.dumps(c['best_params'], default=str)}` |")
    lines += [
        "",
        "## Tuned test-set detail",
        "",
        "| Model | Acc | Bal. acc | Precision | Recall | Specificity "
        "| F1 | ROC-AUC | PR-AUC | MCC | TN | FP | FN | TP |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for p in tuned_json:
        t = p["test"]
        lines.append(
            f"| {p['display_name']} | {t['accuracy']:.3f} | "
            f"{t['balanced_accuracy']:.3f} | {t['precision']:.3f} | "
            f"{t['recall']:.3f} | {t['specificity']:.3f} | {t['f1']:.3f} | "
            f"{t['roc_auc']:.3f} | {t['pr_auc']:.3f} | {t['mcc']:.3f} | "
            f"{t['tn']} | {t['fp']} | {t['fn']} | {t['tp']} |")
    lines += [
        "",
        "Search spaces were kept small to limit compute and overfitting "
        "risk on n=310 training rows. Nested CV / external validation "
        "remains future work.",
        "",
        "Same scientific limitations as the baseline benchmark "
        "(random stratified split; possible same-residue leakage across "
        "train/test; research prototype, not clinical performance).",
        "",
    ]
    (RES_DIR / "tuning_report.md").write_text("\n".join(lines))

    print(f"tuned {len(tuned_rows)} models in {elapsed:.1f}s")
    print(f"wrote tuned_benchmark.csv/json + tuning_report.md")
    for c in cmp_rows:
        print(f"  {c['model']}: test AUC {c['baseline_test_roc_auc']:.3f}"
              f" -> {c['tuned_test_roc_auc']:.3f}, "
              f"F1 {c['baseline_test_f1']:.3f} -> {c['tuned_test_f1']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
