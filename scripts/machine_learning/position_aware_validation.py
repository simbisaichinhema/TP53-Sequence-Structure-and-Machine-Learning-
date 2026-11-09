"""Position-aware validation experiment (separate from the main benchmark).

Motivation: a random stratified split can place different substitutions at
the SAME residue (and different variants from the SAME hotspot) in both
training and testing. Position features (pos_norm, domain flags, pLDDT)
carry strong signal, so random splits may be optimistic.

This script prepares and runs two group-aware protocols on the same
feature matrix — it does NOT replace the random-split benchmark:

  1. GroupKFold by residue position
     (all substitutions at residue i stay in the same fold)
  2. Leave-one-hotspot-out
     (train on everything except one hotspot; test on that hotspot)

Models: the same registry as benchmark_models.py (baselines + available
boosters). Results are written to results/machine_learning/position_aware/.

Usage:
  python3 scripts/machine_learning/position_aware_validation.py
  python3 scripts/machine_learning/position_aware_validation.py --models random_forest logistic_regression

Outputs:
  results/machine_learning/position_aware/position_aware_results.csv
  results/machine_learning/position_aware/position_aware_results.json
  results/machine_learning/position_aware/hotspot_results.csv
  results/machine_learning/position_aware/position_aware_report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, train_test_split
from sklearn.utils.class_weight import compute_sample_weight

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from metrics_utils import (RATE_METRICS, aggregate_cv_metrics,  # noqa: E402
                           binary_metrics, round_metrics)
from model_registry import all_specs  # noqa: E402

FEAT_CSV = REPO / "data/processed/structural_features/tp53_features.csv"
RES_DIR = REPO / "results/machine_learning/position_aware"

FEATURES = ["pos_norm", "in_core", "dom_TAD1", "dom_TAD2", "dom_PRR",
            "dom_DBD", "dom_hinge", "dom_TET", "dom_CTD", "dist_to_zn",
            "grantham", "d_hydro", "d_volume", "d_charge", "d_polarity",
            "ref_hydro", "ref_volume", "ref_charge", "plddt_at_pos",
            "plddt_window5", "dna_contact"]

SEED = 42
N_SPLITS = 5

# Well-known TP53 core-domain hotspots (literature; used for leave-one-out)
HOTSPOTS = {
    "R175": ("R", 175, "H"),
    "G245": ("G", 245, "S"),
    "R248": ("R", 248, "Q"),
    "R249": ("R", 249, "S"),
    "Y220": ("Y", 220, "C"),
    "R273": ("R", 273, "H"),
    "R280": ("R", 280, "W"),
    "R282": ("R", 282, "W"),
}


def fit_predict(est, spec, X_tr, y_tr, X_ev):
    fit_params = {}
    if spec.balance_mode == "sample_weight":
        w = compute_sample_weight("balanced", y_tr)
        step = est.steps[-1][0]
        fit_params[f"{step}__sample_weight"] = w
    est.fit(X_tr, y_tr, **fit_params)
    proba = est.predict_proba(X_ev)[:, 1]
    return (proba >= 0.5).astype(int), proba


def group_position_cv(spec, X, y, groups, seed):
    """GroupKFold by residue — no residue appears in more than one fold."""
    gkf = GroupKFold(n_splits=min(N_SPLITS, len(np.unique(groups))))
    folds = []
    for tr_i, va_i in gkf.split(X, y, groups):
        # Both classes must be present for metric stability
        if len(np.unique(y[va_i])) < 2 or len(np.unique(y[tr_i])) < 2:
            continue
        est = spec.builder(seed)
        pred, proba = fit_predict(est, spec, X[tr_i], y[tr_i], X[va_i])
        folds.append(binary_metrics(y[va_i], pred, proba))
    return aggregate_cv_metrics(folds) if folds else None


def leave_one_hotspot_out(spec, df, X, y, seed):
    rows = []
    for label, (ref, pos, alt) in HOTSPOTS.items():
        # Dataset may contain several substitutions at this residue
        mask_pos = (df["pos"].to_numpy() == pos)
        if mask_pos.sum() == 0:
            continue
        tr_idx = np.where(~mask_pos)[0]
        te_idx = np.where(mask_pos)[0]
        y_tr, y_te = y[tr_idx], y[te_idx]
        if len(np.unique(y_tr)) < 2:
            continue
        est = spec.builder(seed)
        pred, proba = fit_predict(est, spec, X[tr_idx], y_tr, X[te_idx])
        m = binary_metrics(y_te, pred, proba)
        rows.append({
            "hotspot": label,
            "pos": pos,
            "n_test": int(mask_pos.sum()),
            "test_labels": [int(v) for v in y_te],
            **{k: m[k] for k in RATE_METRICS},
            "tn": m["tn"], "fp": m["fp"], "fn": m["fn"], "tp": m["tp"],
        })
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args(argv)

    RES_DIR.mkdir(parents=True, exist_ok=True)
    specs = all_specs(include_extra=bool(args.models))
    if args.models:
        specs = [s for s in specs if s.name in set(args.models)]

    df = pd.read_csv(FEAT_CSV)
    X = df[FEATURES].to_numpy(dtype=float)
    y = df["label"].astype(int).to_numpy()
    groups = df["pos"].to_numpy()

    print(f"position-aware validation: n={len(y)}, "
          f"unique positions={len(np.unique(groups))}, "
          f"models={[s.name for s in specs]}")

    group_rows = []
    group_json = []
    hotspot_all = []
    for spec in specs:
        g = group_position_cv(spec, X, y, groups, args.seed)
        if g is None:
            print(f"  {spec.name}: insufficient class balance in folds, skip")
            continue
        row = {"model": spec.name, "display_name": spec.display_name,
               "protocol": "GroupKFold-by-position"}
        for k in RATE_METRICS:
            row[f"cv_{k}_mean"] = g[f"{k}_mean"]
            row[f"cv_{k}_std"] = g[f"{k}_std"]
        row["n_folds"] = g["n_folds"]
        group_rows.append(row)
        group_json.append({
            "model": spec.name,
            "display_name": spec.display_name,
            "cv": round_metrics({k: v for k, v in g.items()
                                 if k != "folds"}),
            "folds": round_metrics(g["folds"]),
        })
        print(f"  {spec.name} GroupKFold: "
              f"AUC={g['roc_auc_mean']:.3f}±{g['roc_auc_std']:.3f} "
              f"F1={g['f1_mean']:.3f}±{g['f1_std']:.3f} "
              f"({g['n_folds']} folds)")

        hs = leave_one_hotspot_out(spec, df, X, y, args.seed)
        for r in hs:
            r["model"] = spec.name
            r["display_name"] = spec.display_name
            hotspot_all.append(r)

    if group_rows:
        pd.DataFrame(group_rows).to_csv(
            RES_DIR / "position_aware_results.csv", index=False)
    if hotspot_all:
        pd.DataFrame(hotspot_all).to_csv(
            RES_DIR / "hotspot_results.csv", index=False)

    # Hotspot summary per model
    hs_summary = {}
    for r in hotspot_all:
        hs_summary.setdefault(r["model"], []).append(r)

    payload = {
        "config": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "seed": args.seed,
            "protocol": ["GroupKFold-by-position", "leave-one-hotspot-out"],
            "n_splits": N_SPLITS,
            "n_samples": int(len(y)),
            "n_positions": int(len(np.unique(groups))),
            "hotspots": list(HOTSPOTS.keys()),
            "features": FEATURES,
            "disclaimer": (
                "Experimental protocol separate from the random-split "
                "benchmark. Scores on tiny hotspot test sets (often "
                "1-6 variants) are high-variance and must not be read "
                "as clinical performance."
            ),
        },
        "group_kfold": group_json,
        "leave_one_hotspot_out": [
            {k: (round(v, 4) if isinstance(v, float) else v)
             for k, v in r.items()} for r in hotspot_all
        ],
    }
    (RES_DIR / "position_aware_results.json").write_text(
        json.dumps(payload, indent=2))

    # Report
    lines = [
        "# Position-aware validation (separate experiment)",
        "",
        f"Generated: {payload['config']['generated_at_utc']}  ",
        f"Seed: {args.seed}  ",
        "Purpose: quantify how much a random stratified split may "
        "overestimate performance when variants from the same residue "
        "or hotspot leak across the train/test boundary.",
        "",
        "## Protocol 1 — GroupKFold by residue position",
        "",
        "All substitutions at the same TP53 position stay in one fold.",
        "",
        "| Model | Acc | Bal. acc | F1 | ROC-AUC | PR-AUC | MCC "
        "| Folds |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(group_rows, key=lambda x: x["cv_roc_auc_mean"],
                    reverse=True):
        lines.append(
            f"| {r['display_name']} | "
            f"{r['cv_accuracy_mean']:.3f}±{r['cv_accuracy_std']:.3f} | "
            f"{r['cv_balanced_accuracy_mean']:.3f}"
            f"±{r['cv_balanced_accuracy_std']:.3f} | "
            f"{r['cv_f1_mean']:.3f}±{r['cv_f1_std']:.3f} | "
            f"{r['cv_roc_auc_mean']:.3f}±{r['cv_roc_auc_std']:.3f} | "
            f"{r['cv_pr_auc_mean']:.3f}±{r['cv_pr_auc_std']:.3f} | "
            f"{r['cv_mcc_mean']:.3f}±{r['cv_mcc_std']:.3f} | "
            f"{r['n_folds']} |")

    lines += [
        "",
        "## Protocol 2 — Leave-one-hotspot-out",
        "",
        f"Hotspots tested: {', '.join(HOTSPOTS)}. Training excludes the "
        "held-out residue; the test set is every dataset variant at that "
        "residue (often n=1–6 — high variance).",
        "",
        "| Model | Hotspot | n_test | ROC-AUC | F1 | Acc | MCC |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in sorted(hotspot_all,
                    key=lambda x: (x["model"], x["pos"])):
        lines.append(
            f"| {r['display_name']} | {r['hotspot']} | {r['n_test']} | "
            f"{r['roc_auc']:.3f} | {r['f1']:.3f} | {r['accuracy']:.3f} | "
            f"{r['mcc']:.3f} |")

    lines += [
        "",
        "## Interpretation guide",
        "",
        "- Compare GroupKFold metrics against the random-split benchmark "
        "in `results/machine_learning/benchmark/benchmark_report.md`. "
        "A large drop indicates position leakage in the random split.",
        "- Leave-one-hotspot-out numbers are descriptive stress tests, "
        "not headline metrics — test folds are tiny.",
        "- Do not select production models on these scores alone.",
        "",
        "## Limitations",
        "",
        "- Same small ClinVar cohort (n="
        + str(payload["config"]["n_samples"])
        + "); no external test set.",
        "- Hotspot list is literature-curated, not exhaustive.",
        "- Research prototype only; not a clinical diagnostic tool.",
        "",
    ]
    (RES_DIR / "position_aware_report.md").write_text("\n".join(lines))
    print(f"wrote {RES_DIR.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
