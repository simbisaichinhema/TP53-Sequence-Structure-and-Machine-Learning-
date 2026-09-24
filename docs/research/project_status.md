# Project status

Date of last update: 2026-09-24.

## Verified state (COMPLETED)

- Gene TP53, Homo sapiens, NCBI GeneID 7157.
- Transcript NM_001126112.3; selected CDS 140–1321 (1182 nt).
- ORF Finder: range 1–1182, min 100 aa, standard code → ORF1 (+, frame 1,
  1–1182, 393 aa, starts MEEPQSDPSV…).
- AlphaFold prediction on the 393-aa sequence: 5 models (.cif) + full_data
  JSONs + summary confidence JSONs + job request — all preserved in
  `structures/alphafold/wt/`.

## WT baseline (COMPLETED 2026-09-18)

- Formal sequence verification vs live UniProt P04637 (SV=4): 100% identity
  over 393 aa — RQ1 answered.
- Representative model: model_4 (nominal; core 94–292 mean pLDDT 97.89; all
  models effectively equivalent) → `structures/alphafold/wt/selected/`.
- 2OCJ retrieved and annotated: X-ray, 2.05 Å, chains A–D residues 96–289.
- CA Kabsch superposition (self-tested implementation): 0.37–0.67 Å RMSD
  over 194 CA at 100% identity, all models × all chains — RQ2 answered
  quantitatively (consistency, not blind validation: templates were enabled).
- Implementation note: an incorrect rotation-matrix variant in the first
  version of `superpose_core.py` produced 17–27 Å artefacts; caught by the
  synthetic rotation-recovery self-test and corrected. Method retained with
  the self-test as regression guard.

## Variant + ML + predictor (COMPLETED 2026-09-24, prototype scope)

- ClinVar TP53 build: 4034 records -> 388 missense (232 P/LP, 156 B/LB),
  VCV-traceable, WT-verified (`data/processed/mutations/`).
- 21 leak-free features; stratified 80/20 split (seed 42); random forest
  test acc 0.846 / F1 0.880 / ROC-AUC 0.937 (`results/machine_learning/`).
- Inference + HTML dashboard backed by the real model (`dashboard/`),
  verified end-to-end incl. invalid-input handling.
- RQ3-RQ5 answered at prototype scope. Remaining: PyMOL cartoon figures,
  larger multi-source data, position-aware splits, independent testing.

## Pending / next

- PyMOL cross-check of the superposition — PENDING (unchanged)
- Structural comparison figures — PENDING
- Variant dataset, mutants, features, ML — NOT STARTED (next workstream)
