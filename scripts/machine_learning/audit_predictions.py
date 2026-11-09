"""Full-cohort prediction audit: run the trained model over ALL variants.

Outputs (all from real model predictions, no hand-written numbers):
  results/machine_learning/all_predictions.csv  (every variant: label, split, pred, proba)
  results/machine_learning/cohort_summary.json  (per-split metrics + misclassified lists)
  figures/machine_learning/position_enrichment.png (pathogenic fraction by position)
  figures/machine_learning/plddt_by_class.png      (pLDDT pathogenic vs benign)
  figures/machine_learning/substitution_counts.png (top ref->alt pairs)

Train/test flags reuse the exact split from train.py (seed 42, same shuffle)
so test metrics here match metrics.json.

Usage: python3 scripts/machine_learning/audit_predictions.py
"""

import csv
import json
import sys
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "machine_learning"))
from predict import _bundle  # noqa: E402

FEAT_CSV = REPO / "data/processed/structural_features/tp53_features.csv"
VAR_CSV = REPO / "data/processed/mutations/tp53_variant_dataset.csv"
RES_DIR = REPO / "results/machine_learning"
FIG_DIR = REPO / "figures/machine_learning"
SEED = 42


def main():
    RES_DIR.mkdir(parents=True, exist_ok=True)
    bundle, _, _ = _bundle()
    pipe, feats = bundle["pipeline"], bundle["features"]
    df = pd.read_csv(FEAT_CSV)
    meta = pd.read_csv(VAR_CSV).set_index("hgvs_p")[["variant_id", "classification"]]

    idx_tr, idx_te = train_test_split(df.index.values, test_size=0.2,
                                      stratify=df["label"].values,
                                      random_state=SEED)
    split = pd.Series("train", index=df.index)
    split.loc[idx_te] = "test"

    proba = pipe.predict_proba(df[feats].values)[:, 1]
    pred = (proba >= 0.5).astype(int)
    out = pd.DataFrame({"hgvs_p": df["hgvs_p"], "pos": df["pos"],
                        "ref": df["ref"], "alt": df["alt"],
                        "label": df["label"].astype(int), "split": split.values,
                        "pred": pred, "proba_pathogenic": proba.round(4),
                        "correct": (pred == df["label"].astype(int).values)})
    out["variant_id"] = out["hgvs_p"].map(meta["variant_id"])
    out["classification"] = out["hgvs_p"].map(meta["classification"])
    out.to_csv(RES_DIR / "all_predictions.csv", index=False)

    summary = {}
    for sp in ("train", "test", "all"):
        d = out if sp == "all" else out[out.split == sp]
        summary[sp] = {"n": len(d),
                       "accuracy": round(accuracy_score(d.label, d.pred), 4),
                       "f1": round(f1_score(d.label, d.pred), 4),
                       "roc_auc": round(roc_auc_score(d.label, d.proba_pathogenic), 4)}
    mis = out[~out.correct].sort_values("proba_pathogenic")
    summary["misclassified"] = mis[["hgvs_p", "variant_id", "classification",
                                    "split", "proba_pathogenic"]].to_dict("records")
    summary["n_misclassified"] = len(mis)
    summary["n_total"] = len(out)
    summary["n_pos"] = int(out.label.sum())
    summary["n_neg"] = int(len(out) - out.label.sum())
    (RES_DIR / "cohort_summary.json").write_text(json.dumps(summary, indent=1))
    print(f"all={len(out)} test_acc={summary['test']['accuracy']} "
          f"test_f1={summary['test']['f1']} misclassified={len(mis)}")

    # Fig 1: pathogenic fraction by position (real labels + real predictions)
    g = out.groupby("pos")
    xs = sorted(g.groups.keys())
    frac = [out[out.pos == x].label.mean() for x in xs]
    n = [len(out[out.pos == x]) for x in xs]
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.bar(xs, frac, color="#1b2a4a")
    ax.set_xlabel("TP53 position")
    ax.set_ylabel("Pathogenic fraction")
    ax.set_title(f"Pathogenic fraction by position (ClinVar labels, "
                 f"n={len(out)}; core 94–292 shaded)")
    ax.axvspan(94, 292, color="#0e7c7b", alpha=0.12)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "position_enrichment.png", dpi=150)
    plt.close(fig)

    # Fig 2: pLDDT by class (uses feature matrix values)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist([df[df.label == 1]["plddt_at_pos"], df[df.label == 0]["plddt_at_pos"]],
            bins=20,
            label=[f"Pathogenic ({int(df.label.sum())})",
                   f"Benign ({int((1 - df.label).sum())})"],
            color=["#b4232a", "#1c7a3d"], alpha=0.65)
    ax.set_xlabel("WT pLDDT at variant position")
    ax.set_ylabel("Variants")
    ax.set_title("Local order (pLDDT) separates the classes")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "plddt_by_class.png", dpi=150)
    plt.close(fig)

    # Fig 3: top substitutions
    top = out.groupby(["ref", "alt"]).size().sort_values(ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh([f"{r[0]}→{r[1]}" for r in top.index[::-1]], top.values[::-1], color="#1b2a4a")
    ax.set_xlabel("Variants in dataset")
    ax.set_title(f"Most frequent ref→alt substitutions (n={len(out)})")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "substitution_counts.png", dpi=150)
    plt.close(fig)
    print("Wrote all_predictions.csv + cohort_summary.json + 3 figures")


if __name__ == "__main__":
    main()
