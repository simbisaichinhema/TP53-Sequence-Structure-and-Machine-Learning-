# scripts/machine_learning

Status: IMPLEMENTED 2026-09-24 (prototype).

- `fetch` lives in `scripts/mutation/fetch_clinvar_tp53.py` (ClinVar build).
- `make_features.py` — 388x21 leak-free feature matrix (+ definitions doc).
- `train.py` — baselines (logistic regression, random forest), seed 42,
  stratified 80/20, scaler-in-Pipeline, 5-fold CV + held-out metrics/figures.
- `predict.py` — single-source inference (imports featurization; no duplication).
- `evaluate` output — `results/machine_learning/evaluation.md` + `metrics.json`.
- `explain` output — `figures/machine_learning/feature_importance.png`
  (association, not causation).
- `write_results_docs.py` — regenerates results docs from artefacts.
