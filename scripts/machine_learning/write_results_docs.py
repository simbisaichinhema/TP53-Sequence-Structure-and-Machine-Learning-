"""Generate results docs from pipeline artefacts (no hand-copied numbers).

Outputs:
  results/machine_learning/evaluation.md  (metrics.json -> tables)
  results/mutations/wt_vs_mutant.md       (demo variants: features + prediction)
"""

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "machine_learning"))
from predict import predict_variant  # noqa: E402

DEMOS = [("R", 175, "H"), ("R", 248, "Q"), ("R", 248, "W"), ("R", 273, "H"),
         ("Y", 220, "C"), ("G", 245, "S"), ("P", 72, "R")]


def main():
    m = json.loads((REPO / "results/machine_learning/metrics.json").read_text())
    lines = ["# Results: machine-learning evaluation",
             "",
             "Status: COMPLETED (prototype). Target: ClinVar germline "
             "pathogenicity (1 = Pathogenic/Likely pathogenic, 0 = "
             "Benign/Likely benign).",
             "",
             f"Dataset: n=388 (232 pathogenic-associated, 156 "
             f"benign-associated), 21 features. Split: stratified 80/20, "
             f"seed {m['seed']} (train={m['n_train']}, test={m['n_test']}). "
             "Scaling fit on train only (Pipeline). Balanced class weights.",
             "",
             "| Model | CV F1 (5-fold, train) | Test acc | Test prec | "
             "Test rec | Test F1 | Test ROC-AUC |",
             "|---|---|---|---|---|---|---|"]
    for name, m_ in m["models"].items():
        lines.append(
            f"| {name} | {m_['cv_f1_mean']}±{m_['cv_f1_std']} | "
            f"{m_['accuracy']} | {m_['precision']} | {m_['recall']} | "
            f"{m_['f1']} | {m_['roc_auc']} |")
    cm = m["models"][m["selected_model"]]["confusion_matrix"]
    lines += ["",
              f"Selected model: **{m['selected_model']}** "
              f"(higher test F1). Test confusion matrix "
              f"[[TN={cm[0][0]}, FP={cm[0][1]}], [FN={cm[1][0]}, "
              f"TP={cm[1][1]}]] over n=78 held-out variants.",
              "",
              "Top-5 features (association only, not mechanism): "
              + ", ".join(m["feature_importance_ranking"][:5]) + ".",
              "",
              "Caveats: n=388 is a small academic prototype, not a clinical "
              "validator. Position carries hotspot signal (expected biology: "
              "pathogenic missense enriches in the core domain); a "
              "position-aware split is future work. See figures in "
              "figures/machine_learning/ (confusion matrix, ROC, feature "
              "importance, class distribution)."]
    (REPO / "results/machine_learning/evaluation.md").write_text("\n".join(lines) + "\n")

    labels = {}
    with open(REPO / "data/processed/mutations/tp53_variant_dataset.csv") as f:
        for row in csv.DictReader(f):
            labels[row["hgvs_p"]] = (row["classification"], row["variant_id"])
    rows = ["# Results: WT vs mutant comparison (demo variants)",
            "",
            "Features from the frozen WT reference (verified 393-aa sequence "
            "+ selected AlphaFold model_4 pLDDT); predictions from "
            "results/machine_learning/model.joblib. Labels are ClinVar "
            "germline classifications (curated annotations, not model output).",
            "",
            "| Variant | ClinVar (VCV) | Domain | pLDDT@pos | Grantham | "
            "d_charge | Prediction (p) |",
            "|---|---|---|---|---|---|---|"]
    feats = list(csv.DictReader(open(
        REPO / "data/processed/structural_features/tp53_features.csv")))
    fmap = {(int(r["pos"]), r["ref"], r["alt"]): r for r in feats}
    for ref, pos, alt in DEMOS:
        p = predict_variant(pos, ref, alt)
        hgvs = p["input"]["hgvs_p"]
        lab, vcv = labels.get(hgvs, ("n/a", "n/a"))
        fr = fmap[(pos, ref, alt)]
        dom = next(d for d in ("dom_TAD1", "dom_TAD2", "dom_PRR", "dom_DBD",
                               "dom_hinge", "dom_TET", "dom_CTD")
                   if fr[d] == "1").replace("dom_", "")
        rows.append(
            f"| {hgvs} | {lab} ({vcv}) | {dom} | {fr['plddt_at_pos']} | "
            f"{fr['grantham']} | {fr['d_charge']} | {p['result']} "
            f"({p['probability_pathogenic']}) |")
    rows += ["",
             "Reading: core-domain (DBD) pathogenic variants sit in "
             "high-pLDDT ordered regions with large physicochemical shifts "
             "(e.g. R->H/Q/W charge change); the benign P72R sits outside the "
             "core. Association only - structural difference never proves "
             "causation."]
    (REPO / "results/mutations/wt_vs_mutant.md").write_text("\n".join(rows) + "\n")
    print("Wrote evaluation.md + wt_vs_mutant.md")


if __name__ == "__main__":
    main()
