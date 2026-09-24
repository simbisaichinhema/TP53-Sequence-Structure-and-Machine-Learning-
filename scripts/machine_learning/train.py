"""Train + evaluate baseline classifiers on TP53 features.

Protocol (leak-free): stratified 80/20 train/test split (seed 42); scaling
statistics fit on train only via sklearn Pipeline; 5-fold stratified CV on
train; final metrics on the held-out test set. Class imbalance handled with
balanced class weights (232 pathogenic vs 156 benign).

Inputs:  data/processed/structural_features/tp53_features.csv
Outputs: results/machine_learning/model.joblib  (best-F1 pipeline + metadata)
         results/machine_learning/metrics.json
         figures/machine_learning/confusion_matrix.png, roc_curve.png,
         feature_importance.png, class_distribution.png

Usage: python3 scripts/machine_learning/train.py
"""

import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score,
                             roc_curve)
from sklearn.model_selection import (StratifiedKFold, cross_validate,
                                     train_test_split)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

REPO = Path(__file__).resolve().parents[2]
FEAT_CSV = REPO / "data/processed/structural_features/tp53_features.csv"
RES_DIR = REPO / "results/machine_learning"
FIG_DIR = REPO / "figures/machine_learning"
SEED = 42

FEATURES = ["pos_norm", "in_core", "dom_TAD1", "dom_TAD2", "dom_PRR",
            "dom_DBD", "dom_hinge", "dom_TET", "dom_CTD", "dist_to_zn",
            "grantham", "d_hydro", "d_volume", "d_charge", "d_polarity",
            "ref_hydro", "ref_volume", "ref_charge", "plddt_at_pos",
            "plddt_window5", "dna_contact"]


def metrics_dict(y_true, y_pred, y_prob):
    return {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_true, y_prob), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def main():
    RES_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(FEAT_CSV)
    X, y = df[FEATURES].values, df["label"].astype(int).values
    print(f"dataset: n={len(df)} features={len(FEATURES)} "
          f"P={int(y.sum())} B={len(y) - int(y.sum())}")

    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED)
    print(f"train={len(ytr)} (P={int(ytr.sum())}) test={len(yte)} "
          f"(P={int(yte.sum())})")

    models = {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced",
                                       random_state=SEED))]),
        "random_forest": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(n_estimators=400, random_state=SEED,
                                           class_weight="balanced_subsample",
                                           n_jobs=-1))]),
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    out = {"seed": SEED, "n_train": len(ytr), "n_test": len(yte),
           "features": FEATURES, "models": {}}
    fitted = {}
    for name, pipe in models.items():
        cvres = cross_validate(pipe, Xtr, ytr, cv=cv, scoring="f1")
        pipe.fit(Xtr, ytr)
        prob = pipe.predict_proba(Xte)[:, 1]
        pred = pipe.predict(Xte)
        m = metrics_dict(yte, pred, prob)
        m["cv_f1_mean"] = round(float(cvres["test_score"].mean()), 4)
        m["cv_f1_std"] = round(float(cvres["test_score"].std()), 4)
        out["models"][name] = m
        fitted[name] = (pipe, prob, pred)
        print(f"{name}: CV-F1={m['cv_f1_mean']}±{m['cv_f1_std']} "
              f"test acc={m['accuracy']} P/R/F1={m['precision']}/"
              f"{m['recall']}/{m['f1']} AUC={m['roc_auc']}")

    best = max(fitted, key=lambda n: out["models"][n]["f1"])
    out["selected_model"] = best
    pipe, prob, pred = fitted[best]
    joblib.dump({"pipeline": pipe, "features": FEATURES,
                 "model_name": best, "target": "ClinVar pathogenicity (1=P/LP, 0=B/LB)",
                 "seed": SEED},
                RES_DIR / "model.joblib")
    print(f"selected: {best} -> results/machine_learning/model.joblib")

    # --- figures (test set, selected model) ---
    cm = confusion_matrix(yte, pred)
    fig, ax = plt.subplots()
    ax.imshow(cm)
    ax.set_xticks([0, 1], ["Benign (0)", "Pathogenic (1)"])
    ax.set_yticks([0, 1], ["Benign (0)", "Pathogenic (1)"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True (ClinVar)")
    ax.set_title(f"Confusion matrix - {best} (held-out test, n={len(yte)})")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, cm[i, j], ha="center", va="center")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "confusion_matrix.png", dpi=150)
    plt.close(fig)

    fpr, tpr, _ = roc_curve(yte, prob)
    fig, ax = plt.subplots()
    ax.plot(fpr, tpr, label=f"AUC={out['models'][best]['roc_auc']}")
    ax.plot([0, 1], [0, 1], "--")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title(f"ROC - {best} (held-out test)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "roc_curve.png", dpi=150)
    plt.close(fig)

    clf = pipe.named_steps["clf"]
    if hasattr(clf, "feature_importances_"):
        imp = clf.feature_importances_
    else:
        imp = abs(clf.coef_[0])
    order = sorted(range(len(FEATURES)), key=lambda i: imp[i], reverse=True)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh([FEATURES[i] for i in order[::-1]], [imp[i] for i in order[::-1]])
    ax.set_title(f"Feature importance - {best} (association, not causation)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "feature_importance.png", dpi=150)
    plt.close(fig)
    out["feature_importance_ranking"] = [FEATURES[i] for i in order]

    fig, ax = plt.subplots()
    ax.bar(["Benign (0)", "Pathogenic (1)"],
           [len(y) - int(y.sum()), int(y.sum())])
    ax.set_title(f"ClinVar TP53 dataset class distribution (n={len(y)})")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "class_distribution.png", dpi=150)
    plt.close(fig)

    (RES_DIR / "metrics.json").write_text(json.dumps(out, indent=1))
    print("Wrote metrics.json + 4 figures")


if __name__ == "__main__":
    main()
