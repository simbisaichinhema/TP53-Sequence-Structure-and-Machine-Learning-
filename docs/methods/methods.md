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

## Mutation analysis (COMPLETED 2026-09-24 — ClinVar build; expanded 2026-11-09)

Variant source: ClinVar TP53 via E-utilities (`scripts/mutation/
fetch_clinvar_tp53.py`, recorded in `data/metadata/variant_sources.csv`).
Multi-isoform protein tokens resolved to the canonical 393-aa WT by residue
match + MANE NM_000546.6 cDNA tiebreak; every variant WT-verified, VCV IDs
retained. Clear germline P/LP and B/LB labels kept as-is; conflicting
germline missense resolved by strict majority of submitter
`GermlineClassification` values (ties/VUS dropped;
`scripts/mutation/expand_clinvar_conflicts.py`). Expanded set: 818
variants (405 P/LP, 413 B/LB); `label_basis` distinguishes sources. VUS
never labelled. Mutant structure prediction was deferred by design:
structural features reuse the validated WT pLDDT context + sequence-derived
deltas (see feature definitions).

## Machine learning (COMPLETED 2026-09-24 — prototype; re-run on expanded set)

Dataset: 818 ClinVar missense (405 P/LP vs 413 B/LB), 21 documented
features, no label-derived statistics. Stratified 80/20 split (seed 42);
scaler fit on train only (Pipeline); balanced class weights. Baselines:
logistic regression + random forest (fixed seeds). Test (n=164): RF acc
0.884, F1 0.886, ROC-AUC 0.945 (see `metrics.json`). Explainability: RF
importances, association only. Inference (`predict.py`) shares
featurization with training; dashboard (`dashboard/`) serves the real
model. Known limits: n=818 still small, hotspot position signal, random
split can leak same-residue variants across train/test.

## Multi-model benchmark (COMPLETED 2026-11-09)

Default comparison of 3 best classifiers under one fair protocol
(`scripts/machine_learning/benchmark_models.py` + `model_registry.py` +
`metrics_utils.py`): Extra Trees, Random Forest (baseline, train.py
settings), CatBoost. Selected by train CV ROC-AUC on the expanded
cohort (n=818). Additional models remain available via `--models`.
Optional boosters are skipped with a documented reason if not installed.

Protocol: identical 21-feature matrix; stratified 80/20 train/test
(seed 42, train=654 / test=164); 5-fold stratified CV on train only;
scalers inside the pipeline for linear/SVM models only; balanced class or
sample weights fitted per training fold; held-out test never used for
model or hyperparameter selection. Metrics: accuracy, balanced accuracy,
precision, recall (sensitivity), specificity, F1, ROC-AUC, PR-AUC,
MCC, confusion counts — CV mean±SD and per-model test values.

Hyperparameter search (`tune_models.py`) runs only on the training
partition for the top-3 CV models with small grids; baseline and tuned
results are stored separately.

Position-aware validation (`position_aware_validation.py`) is a separate
experiment: GroupKFold by residue position and leave-one-hotspot-out, to
quantify same-residue leakage risk under random splits.

Outputs: `results/machine_learning/benchmark/`,
`figures/machine_learning/benchmark/`,
`results/machine_learning/position_aware/`. Research prototype only —
scores are associations with curated ClinVar labels on a random split,
not clinical performance.
