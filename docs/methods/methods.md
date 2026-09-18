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

## Mutation analysis (NOT STARTED — scaffold only)

Variant source undecided (record in `data/metadata/variant_sources.csv`
first). Mutant generation: apply substitution to verified WT only after
confirming the expected WT residue at that position (see
`scripts/mutation/generate_mutants.py`); abort on mismatch. Mutant structure
prediction mirrors WT standards; WT-vs-mutant comparison uses RMSD, local
displacement, confidence/solvent-accessibility changes — never visual
inspection alone.

## Machine learning (NOT STARTED — scaffold only)

Dataset only from validated features. Document target, definitions, class
balance, missingness, scaling/encoding, feature selection, and a leak-free
train/validation/test split (preprocessing statistics from train only;
consider position-aware splits). Baselines (logistic regression, random
forest, gradient boosting, SVM) before complex models; fixed seeds and
versions recorded. Metrics beyond accuracy (precision, recall, F1, ROC-AUC,
PR-AUC, confusion matrix); explainability via permutation/SHAP/coefficients,
reported as association, not causation.
