# Position-aware validation (separate experiment)

Generated: 2026-11-09T19:14:06.518441+00:00  
Seed: 42  
Purpose: quantify how much a random stratified split may overestimate performance when variants from the same residue or hotspot leak across the train/test boundary.

## Protocol 1 — GroupKFold by residue position

All substitutions at the same TP53 position stay in one fold.

| Model | Acc | Bal. acc | F1 | ROC-AUC | PR-AUC | MCC | Folds |
|---|---|---|---|---|---|---|---|
| CatBoost | 0.830±0.032 | 0.831±0.034 | 0.831±0.035 | 0.922±0.024 | 0.907±0.034 | 0.661±0.067 | 5 |
| Random Forest | 0.845±0.033 | 0.847±0.034 | 0.847±0.038 | 0.920±0.025 | 0.900±0.037 | 0.693±0.068 | 5 |
| Extra Trees | 0.836±0.030 | 0.838±0.031 | 0.838±0.031 | 0.914±0.025 | 0.896±0.034 | 0.674±0.061 | 5 |

## Protocol 2 — Leave-one-hotspot-out

Hotspots tested: R175, G245, R248, R249, Y220, R273, R280, R282. Training excludes the held-out residue; the test set is every dataset variant at that residue (often n=1–6 — high variance).

| Model | Hotspot | n_test | ROC-AUC | F1 | Acc | MCC |
|---|---|---|---|---|---|---|
| CatBoost | R175 | 4 | nan | 1.000 | 1.000 | 0.000 |
| CatBoost | Y220 | 6 | 1.000 | 0.909 | 0.833 | 0.000 |
| CatBoost | G245 | 6 | nan | 1.000 | 1.000 | 0.000 |
| CatBoost | R248 | 5 | nan | 1.000 | 1.000 | 0.000 |
| CatBoost | R249 | 6 | nan | 1.000 | 1.000 | 0.000 |
| CatBoost | R273 | 6 | nan | 1.000 | 1.000 | 0.000 |
| CatBoost | R280 | 5 | nan | 1.000 | 1.000 | 0.000 |
| CatBoost | R282 | 4 | nan | 1.000 | 1.000 | 0.000 |
| Extra Trees | R175 | 4 | nan | 1.000 | 1.000 | 0.000 |
| Extra Trees | Y220 | 6 | 1.000 | 0.909 | 0.833 | 0.000 |
| Extra Trees | G245 | 6 | nan | 1.000 | 1.000 | 0.000 |
| Extra Trees | R248 | 5 | nan | 1.000 | 1.000 | 0.000 |
| Extra Trees | R249 | 6 | nan | 0.909 | 0.833 | 0.000 |
| Extra Trees | R273 | 6 | nan | 1.000 | 1.000 | 0.000 |
| Extra Trees | R280 | 5 | nan | 1.000 | 1.000 | 0.000 |
| Extra Trees | R282 | 4 | nan | 1.000 | 1.000 | 0.000 |
| Random Forest | R175 | 4 | nan | 1.000 | 1.000 | 0.000 |
| Random Forest | Y220 | 6 | 1.000 | 0.909 | 0.833 | 0.000 |
| Random Forest | G245 | 6 | nan | 1.000 | 1.000 | 0.000 |
| Random Forest | R248 | 5 | nan | 1.000 | 1.000 | 0.000 |
| Random Forest | R249 | 6 | nan | 1.000 | 1.000 | 0.000 |
| Random Forest | R273 | 6 | nan | 1.000 | 1.000 | 0.000 |
| Random Forest | R280 | 5 | nan | 1.000 | 1.000 | 0.000 |
| Random Forest | R282 | 4 | nan | 1.000 | 1.000 | 0.000 |

## Interpretation guide

- Compare GroupKFold metrics against the random-split benchmark in `results/machine_learning/benchmark/benchmark_report.md`. A large drop indicates position leakage in the random split.
- Leave-one-hotspot-out numbers are descriptive stress tests, not headline metrics — test folds are tiny.
- Do not select production models on these scores alone.

## Limitations

- Same small ClinVar cohort (n=818); no external test set.
- Hotspot list is literature-curated, not exhaustive.
- Research prototype only; not a clinical diagnostic tool.
