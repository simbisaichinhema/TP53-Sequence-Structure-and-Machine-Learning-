# TP53 multi-model benchmark report

Generated: 2026-11-09T19:05:35.052400+00:00  
Stage: **baseline** (baseline hyperparameters, no tuning)  
Random seed: **42**

## Protocol

- Dataset: `data/processed/structural_features/tp53_features.csv` — n=818, features=21 (same matrix for every model)
- Labels: ClinVar pathogenicity (1=P/LP, 0=B/LB)
- Split: stratified 80/20 train/test, seed 42 (train=654, test=164)
- CV: 5-fold stratified on the **training partition only**
- Preprocessing: `StandardScaler` inside the pipeline for linear models and SVM; tree ensembles unscaled
- Class imbalance: balanced class weights or balanced sample weights fitted per training fold
- Held-out test: used once per model for final metrics; **not** used for model or hyperparameter selection

## Optional packages

All optional packages available (xgboost, lightgbm, catboost).

## Consolidated test-set results (held-out, n=164)

| Model | Accuracy | Bal. acc | Precision | Recall | Specificity | F1 | ROC-AUC | PR-AUC | MCC | TN | FP | FN | TP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CatBoost | 0.878 | 0.878 | 0.886 | 0.864 | 0.892 | 0.875 | 0.956 | 0.958 | 0.756 | 74 | 9 | 11 | 70 |
| Extra Trees | 0.884 | 0.885 | 0.860 | 0.914 | 0.855 | 0.886 | 0.949 | 0.948 | 0.770 | 71 | 12 | 7 | 74 |
| Random Forest | 0.890 | 0.891 | 0.862 | 0.926 | 0.855 | 0.893 | 0.946 | 0.939 | 0.783 | 71 | 12 | 6 | 75 |

## Cross-validation (train partition, mean ± SD)

| Model | Acc | Bal. acc | F1 | ROC-AUC | PR-AUC | MCC |
|---|---|---|---|---|---|---|
| Extra Trees | 0.875±0.043 | 0.875±0.043 | 0.880±0.038 | 0.949±0.013 | 0.946±0.016 | 0.754±0.083 |
| CatBoost | 0.879±0.045 | 0.879±0.045 | 0.881±0.045 | 0.948±0.020 | 0.941±0.024 | 0.761±0.089 |
| Random Forest | 0.879±0.041 | 0.880±0.041 | 0.884±0.038 | 0.947±0.016 | 0.941±0.019 | 0.763±0.080 |

## Selection notes

- Highest mean CV ROC-AUC (selection criterion, train only): **Extra Trees** (0.949±0.013)
- Highest held-out test ROC-AUC (reported, not used for selection): CatBoost (0.956)

Model selection and any hyperparameter search use CV on the training partition only. Test metrics are descriptive of the fixed split.

## Scientific limitations

- These are **research prototype scores on a random stratified split of 818 ClinVar missense variants**, not clinical performance estimates.
- Variants from the same residue (and from the same hotspot) can appear in both train and test. Position carries strong signal; random splitting therefore risks optimistic estimates.
- Position-aware (group-by-residue) and leave-one-hotspot-out evaluation are prepared as a separate experiment (`scripts/machine_learning/position_aware_validation.py`).
- No difficult variants were removed and no labels were modified to improve scores.
- n=818 is small; results need external validation before any downstream use.

## Artefacts

- `results/machine_learning/benchmark/benchmark_results.csv`
- `results/machine_learning/benchmark/benchmark_results.json`
- `results/machine_learning/benchmark/cv_folds.json`
- `results/machine_learning/benchmark/experiment_config.json`
- `results/machine_learning/benchmark/models/*.joblib`
- `figures/machine_learning/benchmark/*.png`
- Prediction: `python3 scripts/machine_learning/predict.py --model results/machine_learning/benchmark/models/<name>.joblib R 175 H`
