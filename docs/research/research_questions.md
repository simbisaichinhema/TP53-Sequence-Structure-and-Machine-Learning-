# Research questions

None of these questions is answered until the cited analysis exists.

## RQ1 — Sequence reproducibility (ANSWERED 2026-09-18)

Can a reproducible WT TP53 protein sequence be obtained and verified from the
selected TP53 CDS (NM_001126112.3:140–1321)?

- Yes: ORF1 translation (393 aa) is 100% identical to live UniProt P04637
  (SV=4, retrieved 2026-09-18). Evidence:
  `results/sequence/sequence_verification.md`.

## RQ2 — Structural plausibility (ANSWERED quantitatively 2026-09-18)

Can AlphaFold generate a structurally plausible WT TP53 model that can be
quantitatively compared with experimentally determined TP53 data?

- Yes: all five WT models agree with 2OCJ (X-ray, 2.05 Å) at 0.37–0.67 Å
  CA-RMSD over 194 aligned residues (96–289) at 100% identity. Caveats:
  comparison restricted to the core domain; prediction used templates so this
  is consistency, not blind validation; PyMOL cross-check pending. Evidence:
  `results/structure/wt_validation.md`.

## RQ3 — Variant effects (ANSWERED 2026-09-24, prototype)

How do selected TP53 variants alter sequence-derived and structure-derived
features relative to the WT reference?

- 388 ClinVar missense variants featurized vs verified WT; demo comparison
  (R175H/R248Q/R248W/R273H/Y220C/G245S vs P72R) in
  `results/mutations/wt_vs_mutant.md`. Pathogenic core variants sit in
  high-pLDDT regions with large physicochemical shifts; association only.

## RQ4 — ML classification (ANSWERED 2026-09-24, prototype)

Can sequence and structural features provide useful information for
computational classification of curated TP53 variant annotations?

- Yes at prototype scope: random forest test F1 0.88 / ROC-AUC 0.94 (n=78
  held out). Framed as association with ClinVar annotations, not causality
  or clinical validity.

## RQ5 — Explainability (ANSWERED 2026-09-24, prototype)

Which features contribute most strongly to the model's predictions?

- WT pLDDT context, Zn-ligand distance, position/core flags
  (`figures/machine_learning/feature_importance.png`). Association only;
  never reported as mechanism.
