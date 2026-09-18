# Project status

Date of last update: 2026-09-18.

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

## Pending / next

- PyMOL cross-check of the superposition — PENDING
- Structural comparison figures — PENDING
- Variant dataset, mutants, features, ML — NOT STARTED (next workstream)
