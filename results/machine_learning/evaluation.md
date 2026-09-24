# Results: machine-learning evaluation

Status: COMPLETED (prototype). Target: ClinVar germline pathogenicity (1 = Pathogenic/Likely pathogenic, 0 = Benign/Likely benign).

Dataset: n=388 (232 pathogenic-associated, 156 benign-associated), 21 features. Split: stratified 80/20, seed 42 (train=310, test=78). Scaling fit on train only (Pipeline). Balanced class weights.

| Model | CV F1 (5-fold, train) | Test acc | Test prec | Test rec | Test F1 | Test ROC-AUC |
|---|---|---|---|---|---|---|
| logistic_regression | 0.8797±0.0449 | 0.7436 | 0.7547 | 0.8511 | 0.8 | 0.8346 |
| random_forest | 0.9296±0.0208 | 0.8462 | 0.8302 | 0.9362 | 0.88 | 0.9369 |

Selected model: **random_forest** (higher test F1). Test confusion matrix [[TN=22, FP=9], [FN=3, TP=44]] over n=78 held-out variants.

Top-5 features (association only, not mechanism): plddt_at_pos, plddt_window5, dist_to_zn, pos_norm, in_core.

Caveats: n=388 is a small academic prototype, not a clinical validator. Position carries hotspot signal (expected biology: pathogenic missense enriches in the core domain); a position-aware split is future work. See figures in figures/machine_learning/ (confusion matrix, ROC, feature importance, class distribution).
