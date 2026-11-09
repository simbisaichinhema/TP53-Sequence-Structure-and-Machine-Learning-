# TP53 hyperparameter tuning report

Generated: 2026-11-09T19:09:52.502051+00:00  
Search metric: mean 5-fold CV ROC-AUC on the **training partition only**  
Seed: 42  
Models tuned: extra_trees, catboost, random_forest

Baseline results are unchanged (see `benchmark_report.md`). Held-out test metrics below are reported after the search and were not used to pick hyperparameters.

| Model | Baseline CV AUC | Tuned CV AUC | Baseline test AUC | Tuned test AUC | Baseline test F1 | Tuned test F1 | Best params |
|---|---|---|---|---|---|---|---|
| extra_trees | 0.9488 | 0.9488 | 0.9486 | 0.9486 | 0.8862 | 0.8862 | `{"clf__max_depth": null, "clf__min_samples_leaf": 1, "clf__n_estimators": 400}` |
| catboost | 0.9479 | 0.9495 | 0.9564 | 0.9561 | 0.8750 | 0.8765 | `{"clf__depth": 6, "clf__iterations": 300, "clf__learning_rate": 0.05}` |
| random_forest | 0.9475 | 0.9487 | 0.9456 | 0.9450 | 0.8929 | 0.8929 | `{"clf__max_depth": 12, "clf__min_samples_leaf": 1, "clf__n_estimators": 600}` |

## Tuned test-set detail

| Model | Acc | Bal. acc | Precision | Recall | Specificity | F1 | ROC-AUC | PR-AUC | MCC | TN | FP | FN | TP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Extra Trees (tuned) | 0.884 | 0.884 | 0.861 | 0.914 | 0.855 | 0.886 | 0.949 | 0.948 | 0.770 | 71 | 12 | 7 | 74 |
| CatBoost (tuned) | 0.878 | 0.878 | 0.876 | 0.876 | 0.879 | 0.876 | 0.956 | 0.956 | 0.756 | 73 | 10 | 10 | 71 |
| Random Forest (tuned) | 0.890 | 0.891 | 0.862 | 0.926 | 0.855 | 0.893 | 0.945 | 0.942 | 0.783 | 71 | 12 | 6 | 75 |

Search spaces were kept small to limit compute and overfitting risk on n=310 training rows. Nested CV / external validation remains future work.

Same scientific limitations as the baseline benchmark (random stratified split; possible same-residue leakage across train/test; research prototype, not clinical performance).
