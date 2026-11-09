"""Model registry for the TP53 multi-model pathogenicity benchmark.

Default benchmark set (3 best by train CV ROC-AUC on the expanded cohort):
  1. extra_trees
  2. random_forest        (existing baseline; train.py settings)
  3. catboost             (optional dependency)

Additional classifiers remain available via `all_specs()` / `--models`
(logistic_regression, svm, gradient_boosting, hist_gradient_boosting,
xgboost, lightgbm, adaboost) but are not part of the default comparison.

Optional libraries (xgboost / lightgbm / catboost) are probed at import
time; missing packages are skipped with a documented reason rather than
crashing the benchmark.

Scaling policy: StandardScaler only where it matters (linear models, SVM).
Tree ensembles are left unscaled (monotone-invariant; avoids needless
pipeline steps). All scalers live inside the sklearn Pipeline so they are
fit on training folds only.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Callable, Optional

from sklearn.ensemble import (
    AdaBoostClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

# Default fair-protocol comparison set (order = display order in reports).
DEFAULT_BENCHMARK_MODELS: tuple[str, ...] = (
    "extra_trees",
    "random_forest",
    "catboost",
)


@dataclass
class ModelSpec:
    name: str
    display_name: str
    builder: Callable[[int], object]
    needs_scaling: bool
    # How class imbalance is handled inside each fit:
    #   class_weight  - estimator class_weight parameter (fit-fold labels)
    #   sample_weight - compute_sample_weight('balanced') passed at fit time
    #   native        - library-specific balanced mode (class_weights=...)
    #   none          - no explicit reweighting
    balance_mode: str = "class_weight"
    optional: bool = False
    package: Optional[str] = None
    family: str = "scikit-learn"
    notes: str = ""


def _has(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def _pipe(steps, seed: int) -> Pipeline:
    return Pipeline(steps)


# --- builders (hyperparameters fixed for the baseline benchmark) ---

def _logistic_regression(seed: int):
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced",
                                   random_state=seed)),
    ])


def _random_forest(seed: int):
    # Matches scripts/machine_learning/train.py baseline RF settings.
    # Scaler intentionally omitted (trees are scale-invariant).
    return Pipeline([
        ("clf", RandomForestClassifier(n_estimators=400, random_state=seed,
                                       class_weight="balanced_subsample",
                                       n_jobs=-1)),
    ])


def _svm(seed: int):
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", SVC(kernel="rbf", C=1.0, gamma="scale", probability=True,
                    class_weight="balanced", random_state=seed)),
    ])


def _extra_trees(seed: int):
    return Pipeline([
        ("clf", ExtraTreesClassifier(n_estimators=400, random_state=seed,
                                     class_weight="balanced_subsample",
                                     n_jobs=-1)),
    ])


def _gradient_boosting(seed: int):
    return Pipeline([
        ("clf", GradientBoostingClassifier(
            n_estimators=300, learning_rate=0.1, subsample=1.0,
            max_depth=3, random_state=seed)),
    ])


def _hist_gradient_boosting(seed: int):
    return Pipeline([
        ("clf", HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.1, class_weight="balanced",
            random_state=seed)),
    ])


def _xgboost(seed: int):
    from xgboost import XGBClassifier
    return Pipeline([
        ("clf", XGBClassifier(
            n_estimators=400, learning_rate=0.1, max_depth=4,
            subsample=0.9, colsample_bytree=0.9,
            objective="binary:logistic", eval_metric="logloss",
            tree_method="hist", random_state=seed, n_jobs=1, verbosity=0,
        )),
    ])


def _lightgbm(seed: int):
    from lightgbm import LGBMClassifier
    return Pipeline([
        ("clf", LGBMClassifier(
            n_estimators=400, learning_rate=0.1, max_depth=-1,
            num_leaves=31, subsample=0.9, colsample_bytree=0.9,
            class_weight="balanced", random_state=seed, n_jobs=1,
            verbose=-1,
        )),
    ])


def _catboost(seed: int):
    from catboost import CatBoostClassifier
    return Pipeline([
        ("clf", CatBoostClassifier(
            iterations=400, learning_rate=0.1, depth=6,
            class_weights={0: 1.0, 1: 1.0},  # overridden per-fit via sample_weight
            random_state=seed, verbose=False, allow_writing_files=False,
            loss_function="Logloss",
        )),
    ])


def _adaboost(seed: int):
    return Pipeline([
        ("clf", AdaBoostClassifier(
            n_estimators=400, learning_rate=0.1, random_state=seed)),
    ])


def all_specs(include_extra: bool = False) -> list[ModelSpec]:
    """Default: DEFAULT_BENCHMARK_MODELS only; include_extra=True for all."""
    optional_defs = [
        ModelSpec(
            name="xgboost", display_name="XGBoost", builder=_xgboost,
            needs_scaling=False, balance_mode="sample_weight",
            optional=True, package="xgboost", family="XGBoost",
            notes="scale via sample_weight(balanced); hist tree method",
        ),
        ModelSpec(
            name="lightgbm", display_name="LightGBM", builder=_lightgbm,
            needs_scaling=False, balance_mode="class_weight",
            optional=True, package="lightgbm", family="LightGBM",
            notes="class_weight=balanced",
        ),
        ModelSpec(
            name="catboost", display_name="CatBoost", builder=_catboost,
            needs_scaling=False, balance_mode="sample_weight",
            optional=True, package="catboost", family="CatBoost",
            notes="balanced sample weights at fit; CPU, no GPU",
        ),
    ]

    base = [
        ModelSpec(
            name="logistic_regression", display_name="Logistic Regression",
            builder=_logistic_regression, needs_scaling=True,
            balance_mode="class_weight",
            notes="existing baseline (train.py settings)",
        ),
        ModelSpec(
            name="random_forest", display_name="Random Forest",
            builder=_random_forest, needs_scaling=False,
            balance_mode="class_weight",
            notes="existing baseline (train.py settings)",
        ),
        ModelSpec(
            name="svm", display_name="SVM (RBF)",
            builder=_svm, needs_scaling=True, balance_mode="class_weight",
            notes="SVC probability=True (Platt scaling inside sklearn)",
        ),
        ModelSpec(
            name="extra_trees", display_name="Extra Trees",
            builder=_extra_trees, needs_scaling=False,
            balance_mode="class_weight",
        ),
        ModelSpec(
            name="gradient_boosting", display_name="Gradient Boosting",
            builder=_gradient_boosting, needs_scaling=False,
            balance_mode="sample_weight",
        ),
        ModelSpec(
            name="hist_gradient_boosting",
            display_name="Hist Gradient Boosting",
            builder=_hist_gradient_boosting, needs_scaling=False,
            balance_mode="class_weight",
        ),
        ModelSpec(
            name="adaboost", display_name="AdaBoost",
            builder=_adaboost, needs_scaling=False,
            balance_mode="sample_weight",
        ),
    ]

    # Stable order: sklearn first, then optional boosters if available
    ordered = base + optional_defs
    by_name = {s.name: s for s in ordered}
    resolved: list[ModelSpec] = []
    if include_extra:
        candidates = ordered
    else:
        candidates = [by_name[n] for n in DEFAULT_BENCHMARK_MODELS
                      if n in by_name]
    for spec in candidates:
        if spec.optional and spec.package and not _has(spec.package):
            continue
        resolved.append(spec)
    return resolved


def missing_optional_packages() -> list[dict]:
    out = []
    # Only packages needed by the default set (plus known extras if requested)
    needed = set(DEFAULT_BENCHMARK_MODELS)
    for name in ("xgboost", "lightgbm", "catboost"):
        if name in needed and not _has(name):
            out.append({
                "package": name,
                "pip": f"pip install {name}",
                "models_skipped": [name],
            })
    return out


def display_names() -> dict[str, str]:
    return {s.name: s.display_name
            for s in all_specs(include_extra=True)}
