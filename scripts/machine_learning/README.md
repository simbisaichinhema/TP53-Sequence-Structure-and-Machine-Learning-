# scripts/machine_learning

Status: NOT STARTED — no training code yet by design.

When the validated feature dataset exists, add here:

- `make_dataset.py` — build ML dataset from validated features (leak-free
  train/validation/test split; preprocessing statistics from train only).
- `baselines.py` — logistic regression, random forest, gradient boosting, SVM
  with fixed seeds, recorded hyperparameters and software versions.
- `evaluate.py` — accuracy, precision, recall, F1, ROC-AUC, PR-AUC,
  confusion matrix; class-imbalance discussion.
- `explain.py` — permutation importance / SHAP / linear coefficients,
  reported as association, not causation.

Do not create these before the WT baseline and feature pipeline are complete.
