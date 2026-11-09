# Results: machine-learning evaluation

Status: COMPLETED (prototype). Target: ClinVar germline pathogenicity (1 = Pathogenic/Likely pathogenic, 0 = Benign/Likely benign).

Dataset: n=818 (405 pathogenic-associated, 413 benign-associated), 21 features. Split: stratified 80/20, seed 42 (train=654, test=164). Scaling fit on train only (Pipeline). Balanced class weights. Includes clear ClinVar labels + conflicting majority-vote expansion (see data/metadata/variant_sources.csv).

| Model | CV F1 (5-fold, train) | Test acc | Test prec | Test rec | Test F1 | Test ROC-AUC |
|---|---|---|---|---|---|---|
| logistic_regression | 0.8482±0.0394 | 0.8415 | 0.7723 | 0.963 | 0.8571 | 0.9173 |
| random_forest | 0.8841±0.0384 | 0.8841 | 0.8605 | 0.9136 | 0.8862 | 0.9452 |

Selected model: **random_forest** (higher test F1). Test confusion matrix [[TN=71, FP=12], [FN=7, TP=74]] over n=164 held-out variants.

Top-5 features (association only, not mechanism): plddt_at_pos, plddt_window5, dist_to_zn, pos_norm, dom_DBD.

Caveats: n=818 is a small academic prototype, not a clinical validator. Position carries hotspot signal (expected biology: pathogenic missense enriches in the core domain); random stratified splits can leak same-residue variants — see results/machine_learning/position_aware/. See figures in figures/machine_learning/ (confusion matrix, ROC, feature importance, class distribution). Multi-model benchmark: results/machine_learning/benchmark/.
