# Methods

## Sequence processing

Source NCBI Gene 7157 CDS set; accession NM_001126112.3; coordinates 140–1321;
extraction from `cds.fna`; ORF Finder (1–1182, ≥100 aa, standard code);
translation of ORF1 (393 aa); verification vs UniProt P04637 (local
cross-check done, live retrieval pending). Full protocol:
`docs/protocols/sequence_processing.md`.

## Structure prediction

Input: verified 393-aa WT sequence. Platform: AlphaFold Server (job
`fold_tp53_predicted_protein`, seed 555867540, structure templates enabled).
Outputs: 5 CIF models + per-model full_data (atom pLDDT, PAE, contact probs)
+ summary confidence JSONs. Selection: pending documented rationale; all
models preserved.

## Structural validation (COMPLETED 2026-09-18)

Benchmark PDB 2OCJ (X-ray, 2.05 Å, chains A–D residues 96–289; auth numbering
verified equal to WT positions by sequence match). Alignment:
CA-only Kabsch superposition (`scripts/structure/superpose_core.py`, numpy,
synthetic self-test passing at 1.59e-15 Å) over the 194-residue overlap.
Result: 0.37–0.67 Å RMSD at 100% identity for all models × chains;
representative model_4 (nominal — all models equivalent). Full record:
`results/structure/wt_validation.md`; raw values:
`results/structure/superposition.json`. PyMOL cross-check pending.
Caveat recorded: templates were enabled at prediction, so agreement is
consistency with known structural data, not independent blind validation.

## Mutation analysis (COMPLETED 2026-09-24 — ClinVar build)

Variant source: ClinVar TP53 via E-utilities (`scripts/mutation/
fetch_clinvar_tp53.py`, recorded in `data/metadata/variant_sources.csv`).
Multi-isoform protein tokens resolved to the canonical 393-aa WT by residue
match + MANE NM_000546.6 cDNA tiebreak; every variant WT-verified, VCV IDs
retained, VUS/conflicting excluded with counts. Mutant structure prediction
was deferred by design: structural features reuse the validated WT pLDDT
context + sequence-derived deltas (see feature definitions).

## Machine learning (COMPLETED 2026-09-24 — prototype)

Dataset: 388 ClinVar missense (232 P/LP vs 156 B/LB), 21 documented features,
no label-derived statistics. Stratified 80/20 split (seed 42); scaler fit on
train only (Pipeline); balanced class weights. Baselines: logistic
regression + random forest (fixed seeds). Test (n=78): RF acc 0.846,
F1 0.880, ROC-AUC 0.937. Explainability: RF importances, association only.
Inference (`predict.py`) shares featurization with training; dashboard
(`dashboard/`) serves the real model. Known limits: n=388, hotspot position
signal, no position-aware split or independent test set yet.
