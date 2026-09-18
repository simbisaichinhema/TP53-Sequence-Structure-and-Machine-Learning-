# CHANGELOG

All notable changes to this research repository are documented here.
Status labels: COMPLETED | IN PROGRESS | PENDING | NOT STARTED | BLOCKED

## [Unreleased]

### Added
- Repository scaffold (data, structures, scripts, notebooks, results, figures,
  docs, config) — COMPLETED
- Raw-data preservation: NCBI CDS dataset copy, local protein FASTAs,
  all five AlphaFold WT models + full_data + confidence JSONs — COMPLETED
- Local sequence cross-check (ORF translation vs local P04637-labelled file):
  393 aa, 100% identical — COMPLETED (live UniProt verification still PENDING)
- AlphaFold WT confidence summary computed from local files (per-residue pLDDT
  from CIF B-factors; PAE means) — COMPLETED
- Research questions, project status, methods, and protocols documentation —
  COMPLETED
- Reproducible scripts: sequence verification, confidence analysis, PyMOL
  alignment scaffold, mutant generator scaffold — COMPLETED

### Pending
- PyMOL cross-check of the superposition; structural comparison figures — PENDING
- Variant dataset sourcing, mutant sequences/structures, features, ML — NOT STARTED

## [2026-09-18] — WT structural baseline completed

### Added
- Live UniProt P04637 retrieval (`data/raw/tp53_cds/P04637_uniprot_live_20260918.fasta`);
  formal verification: 100% identity over 393 aa — RQ1 answered.
- 2OCJ retrieval + annotation (X-ray 2.05 Å; chains A–D, residues 96–289).
- `scripts/structure/superpose_core.py`: CA Kabsch superposition with synthetic
  self-test; all models × all chains 0.37–0.67 Å RMSD over 194 CA at 100%
  identity — RQ2 answered quantitatively.
- Representative model model_4 → `structures/alphafold/wt/selected/`.

### Fixed
- Rotation-matrix variant bug in `superpose_core.py` (produced 17–27 Å
  artefacts) caught by the synthetic rotation-recovery self-test; corrected to
  R = U·diag(1,1,d)·Vᵀ. Self-test retained as regression guard.

## [2026-09-18] — TP53 root audit: all files filed + documented

### Added
- `msas/` (paired + unpaired A3M) → `structures/alphafold/wt/inputs/msas/`.
- `templates/` (hits JSON + 4 CIFs: PDB 5XZC/6RZ3/4QO1/2WGX) →
  `structures/alphafold/wt/inputs/templates/`.
- Original AF bundle `fold_tp53_predicted_protein.zip` →
  `structures/alphafold/wt/raw/` (with `.gitignore` exception).
- `terms_of_use.md` → `structures/alphafold/wt/terms_of_use.md`.
- Original NCBI download `TP53 CDS data` (verified ZIP) →
  `data/raw/tp53_cds/` (original filename kept).
- `docs/research/file_audit.md`: every former root file mapped to its
  destination with MD5 verification record.
- `structures/alphafold/wt/selected/README.md`: best-model (model_4) record.
- Provenance rows STR06–STR09, SEQ04.

## [2026-09-18] — README rewritten + first real figures

### Added
- `scripts/structure/plot_validation_figures.py` with two measured-data
  figures: `figures/structures/wt_selected_per_residue_plddt.png` and
  `figures/alignments/rmsd_models_vs_2ocj.png` (300 dpi).

### Changed
- README rewritten in portfolio style (badges, background, objectives,
  workflow, install/package table, folder tree, run guide, runtime/outputs
  tables, results summary, figures, references, citation, author) using
  measured values only; no fabricated numbers or figures.

### Added
- `scripts/structure/plot_structure_views.py` with PAE heatmap
  (`figures/structures/wt_model4_pae.png`), 3D CA-trace by pLDDT
  (`figures/structures/wt_model4_3d_plddt.png`), and superposed-core overlay
  (`figures/alignments/wt_vs_2ocj_core_overlay_3d.png`) — all from measured
  data and embedded in the README. PyMOL cartoon figures still pending.

### Changed
- All 29 loose root files + `msas/`, `templates/`, `TP53 CDS data~/` moved
  into the repository after checksum verification; workspace root now holds
  only `TP53-Mutation-Analysis/`. No mutation/ML work started (out of scope).
