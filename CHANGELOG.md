# CHANGELOG

All notable changes to this research repository are documented here.
Status labels: COMPLETED | IN PROGRESS | PENDING | NOT STARTED | BLOCKED

## [2026-11-09] — Dataset expansion + Kaggle side-by-side upgrade

### Added
- `scripts/mutation/expand_clinvar_conflicts.py`: resolve ClinVar
  *conflicting* missense by strict majority of submitter germline votes
  (ties/VUS dropped; no invented labels). Audit:
  `data/raw/variants/clinvar_conflict_resolution.json`.
- Expanded dataset: **818 variants** (405 P/LP / 413 B/LB) with
  `label_basis` (`germline_clinvar` vs `germline_conflict_majority`);
  clear-only backup `tp53_variant_dataset_backup_clear.csv`.
- Kaggle notebook (`kaggle/TP53_Kaggle_Demo.ipynb`) sections for
  side-by-side model comparison (Tables A/B/C + comparison figures),
  multi-model inference panel, tuning, position-aware, smoke tests.

### Changed
- Features, baseline train, default 3-model benchmark (Extra Trees /
  Random Forest / CatBoost — top by train CV ROC-AUC), tuning,
  position-aware validation, audit, mutant sequences, and results docs
  regenerated on n=818 (split: train 654 / test 164).
- Default benchmark reduced from 10 algorithms to the 3 best; full
  registry still available via `--models` (`include_extra=True`).
- README / methods / research docs updated for expanded counts and
  measured metrics; dashboard numbers driven from `cohort_summary.json`.
- Benchmark/report scripts now use dynamic `n` (no hard-coded 388/78).

### Notes
- Conflict expansion never invents labels; VUS remain excluded.
- Baseline RF test on expanded set: acc 0.884 / F1 0.886 / ROC-AUC 0.945
  (`metrics.json`). Benchmark CSV/JSON remain the source of truth for
  model ranking.

## [2026-11-09] — Multi-model benchmark upgrade

### Added
- `scripts/machine_learning/model_registry.py`: registry of 10
  classifiers (LR/RF baselines + SVM, Extra Trees, Gradient Boosting,
  HistGradientBoosting, XGBoost, LightGBM, CatBoost, AdaBoost) with
  optional-package probing and documented imbalance/scaling policy.
- `scripts/machine_learning/metrics_utils.py`: shared metric suite
  (accuracy, balanced accuracy, precision, recall/sensitivity,
  specificity, F1, ROC-AUC, PR-AUC, MCC, TN/FP/FN/TP; CV mean±SD).
- `scripts/machine_learning/benchmark_models.py`: fair multi-model
  benchmark — same 21-feature matrix, stratified 80/20 seed 42,
  5-fold stratified CV on train only, test held out for final metrics
  only. Writes CSV/JSON, per-model joblib artefacts, experiment config,
  markdown report, and 8 comparison figures under
  `figures/machine_learning/benchmark/`.
- `scripts/machine_learning/tune_models.py`: small train-only grid
  search for top-3 CV models; baseline vs tuned comparison written to
  separate files (`tuned_benchmark.*`, `tuning_report.md`).
- `scripts/machine_learning/position_aware_validation.py`: separate
  experiment — GroupKFold by residue + leave-one-hotspot-out (same
  registry; results in `results/machine_learning/position_aware/`).
- `config/requirements-benchmark.txt`; `config/environment.yml` updated
  with optional boosters.
- `predict.py --model PATH`: run any saved benchmark/tuned artefact
  through the same featurization pipeline (default model.joblib
  unchanged).

### Notes
- Existing `train.py`, `model.joblib`, dashboard, and audit scripts
  unchanged in behaviour (baselines reproduce: LR/RF test metrics match
  `metrics.json`).
- Benchmark results are research-prototype associations on a random
  stratified split — not clinical performance. Same-residue leakage
  across random splits documented; position-aware protocol prepared.

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

## [2026-09-24] — Variant proteins + cohort audit + dashboard visuals

### Added
- `scripts/mutation/build_mutant_sequences.py`: 388 real mutant protein
  sequences (WT-validated single substitutions, all 393 aa, all unique) +
  length/MD5 ledger.
- `scripts/machine_learning/audit_predictions.py`: full-cohort audit
  (`all_predictions.csv`, `cohort_summary.json`; test metrics reproduce
  exactly) + 3 figures (position enrichment, pLDDT by class, substitutions).
- `scripts/mutation/write_variant_protein_results.py`:
  `results/mutations/variant_proteins.md` — WT-vs-mutant ±7 windows for demo
  variants + honest test error analysis (12 mistakes with reasons).
- `scripts/structure/export_ca_trace.py` → `dashboard/ca_trace.json`
  (393 real CA coordinates + pLDDT from model_4).
- Dashboard: interactive 3D WT viewer (rotate/zoom, residue highlight,
  pLDDT/domain colouring), per-query pLDDT charts, staged pipeline stepper,
  cohort-results section (stats + figures + clickable misclassified table
  served via new `/cohort` and `/fig/<name>` endpoints).
- `/predict` now also returns a `context` block (domain, pLDDT, Grantham,
  charge delta) from the same training featurization.

## [2026-09-24] — Variant dataset + ML prototype + HTML predictor completed

### Added
- `scripts/mutation/fetch_clinvar_tp53.py`: live ClinVar build (4034 TP53
  records → 388 missense with P/LP-or-B/LB labels, WT-verified, VCV-traceable;
  VUS/conflicting excluded with logged counts). Multi-isoform tokens resolved
  via WT match + MANE cDNA tiebreak.
- `scripts/machine_learning/make_features.py`: 21 leak-free features
  (domain, Zn-distance, Grantham 1974 with rho=50.723 scale, physicochemical
  deltas, WT AlphaFold pLDDT context, literature DNA-contact flag).
  pLDDT parser self-validated (core mean 97.89 reproduces reported value).
- `scripts/machine_learning/train.py`: stratified 80/20 split (seed 42),
  scaler-in-Pipeline, balanced weights, 5-fold CV + held-out test. Random
  forest test acc 0.846 / F1 0.880 / ROC-AUC 0.937; logistic regression
  0.744 / 0.800 / 0.835. Figures in `figures/machine_learning/`.
- `scripts/machine_learning/predict.py`: single-source inference (imports
  featurization from make_features; user-safe errors, no stack traces).
- `dashboard/server.py` + `dashboard/index.html`: predictor UI backed by the
  real model (verified: R175H/R248Q/R273H/Y220C/G245S→pathogenic,
  P72R→benign; invalid inputs return clean 400 JSON).
- `results/machine_learning/evaluation.md`,
  `results/mutations/wt_vs_mutant.md` (generated from artefacts, no
  hand-copied numbers); README/CHANGELOG/docs updated; RQ3–RQ5 answered
  (prototype scope).

### Fixed
- Grantham distance constants corrected to rho*sqrt(alpha*dc^2+...) per
  Grantham 1974 Table 2 scale (R-H sanity 28.6 ≈ 29); model retrained after fix.

### Changed
- `data/raw/variants/clinvar_tp53_esummary.json` (~16 MB) git-ignored as
  regenerable; IDs + clean dataset + script remain versioned.

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
