"""Shared metric suite for the TP53 multi-model benchmark.

All reported metrics are computed from (y_true, y_pred, y_prob) with a
single implementation so baseline and tuned runs stay comparable.

Positive class = 1 (ClinVar Pathogenic/Likely pathogenic).
Sensitivity = recall of the positive class; specificity = recall of class 0.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)

# Scalar metrics reported per fold / per test set (confusion counts separate)
RATE_METRICS = (
    "accuracy",
    "balanced_accuracy",
    "precision",
    "recall",
    "specificity",
    "f1",
    "roc_auc",
    "pr_auc",
    "mcc",
)

COUNT_METRICS = ("tn", "fp", "fn", "tp")


def binary_metrics(y_true, y_pred, y_prob) -> dict:
    """Full binary classification metric dict for one evaluation set."""
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    y_prob = np.asarray(y_prob, dtype=float)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    denom = tn + fp
    specificity = float(tn) / denom if denom else float("nan")

    try:
        roc_auc = float(roc_auc_score(y_true, y_prob))
    except ValueError:
        roc_auc = float("nan")
    try:
        pr_auc = float(average_precision_score(y_true, y_prob))
    except ValueError:
        pr_auc = float("nan")

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "specificity": specificity,
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def mean_std(values) -> tuple[float, float]:
    arr = np.asarray([v for v in values if v is not None and np.isfinite(v)],
                     dtype=float)
    if arr.size == 0:
        return float("nan"), float("nan")
    return float(arr.mean()), float(arr.std(ddof=0))


def aggregate_cv_metrics(fold_metrics: list[dict]) -> dict:
    """Mean ± std for rate metrics; summed confusion counts across folds."""
    out: dict = {}
    for key in RATE_METRICS:
        m, s = mean_std([fm[key] for fm in fold_metrics])
        out[f"{key}_mean"] = m
        out[f"{key}_std"] = s
    for key in COUNT_METRICS:
        out[key] = int(sum(fm[key] for fm in fold_metrics))
    out["n_folds"] = len(fold_metrics)
    out["folds"] = fold_metrics
    return out


def round_metrics(d, ndigits: int = 4):
    """Round floats for JSON/CSV readability; recurse into dict/list."""
    if isinstance(d, list):
        return [round_metrics(v, ndigits) for v in d]
    if not isinstance(d, dict):
        if isinstance(d, float):
            return round(d, ndigits)
        return d
    out = {}
    for k, v in d.items():
        out[k] = round_metrics(v, ndigits)
    return out
