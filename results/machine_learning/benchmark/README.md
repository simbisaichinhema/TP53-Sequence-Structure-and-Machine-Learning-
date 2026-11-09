# Results: multi-model benchmark

Status: COMPLETED 2026-11-09. Fair comparison of the default 3-model set
(Extra Trees, Random Forest, CatBoost) on the frozen 21-feature ClinVar
matrix (seed 42, stratified 80/20, 5-fold CV on train only). Additional
models available via `--models`.

- `benchmark_report.md` — human-readable consolidated report
- `benchmark_results.csv` / `benchmark_results.json` — all metrics
- `cv_folds.json` — per-fold CV metrics
- `experiment_config.json` — seed, split, features, package availability
- `tuned_benchmark.*`, `tuning_report.md`, `tuning_searches.json` —
  train-only hyperparameter search for top-3 CV models (baseline kept
  separate)
- `models/*.joblib` — fitted pipelines (baseline + tuned)

Figures: `figures/machine_learning/benchmark/`.

Position-aware / leave-one-hotspot-out (separate experiment):
`results/machine_learning/position_aware/`.

**Not clinical performance.** Random stratified splits can place variants
from the same residue or hotspot in both train and test. See
`position_aware/position_aware_report.md` and the limitations section of
`benchmark_report.md`.
