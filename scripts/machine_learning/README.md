# scripts/machine_learning

Status: IMPLEMENTED 2026-09-24 (prototype); benchmark 2026-11-09;
re-run on expanded n=818 cohort 2026-11-09.

- `fetch` lives in `scripts/mutation/fetch_clinvar_tp53.py` (ClinVar build);
  conflict expansion in `scripts/mutation/expand_clinvar_conflicts.py`.
- `make_features.py` — Nx21 leak-free feature matrix (+ definitions doc).
- `train.py` — baselines (logistic regression, random forest), seed 42,
  stratified 80/20, scaler-in-Pipeline, 5-fold CV + held-out metrics/figures.
- `benchmark_models.py` — fair 3-model benchmark default (see `benchmark/` outputs).
- `tune_models.py` — train-only grid for top-3 CV models.
- `position_aware_validation.py` — GroupKFold-by-position + leave-hotspot-out.
- `predict.py` — single-source inference (imports featurization; no duplication).
  `--model PATH` selects any saved artefact (default `model.joblib`).
- `audit_predictions.py` — full-cohort prediction audit + figures.
- `evaluate` output — `results/machine_learning/evaluation.md` + `metrics.json`.
- `explain` output — `figures/machine_learning/feature_importance.png`
  (association, not causation).
- `write_results_docs.py` — regenerates results docs from artefacts.
- `test_benchmark_smoke.py` — smoke tests for the fair protocol.
