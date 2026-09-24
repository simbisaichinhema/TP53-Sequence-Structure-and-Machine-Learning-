# TP53 Mutation Analysis: Sequence, Structure, and Machine Learning

[![Python](https://img.shields.io/badge/Python-%3E%3D3.10-blue?logo=python)](https://www.python.org)
[![NumPy](https://img.shields.io/badge/NumPy-2.x-013243?logo=numpy)](https://numpy.org)
[![matplotlib](https://img.shields.io/badge/matplotlib-figures-11557c)](https://matplotlib.org)
[![PyMOL](https://img.shields.io/badge/PyMOL-cross--check-0a6ebd)](https://pymol.org)
[![AlphaFold](https://img.shields.io/badge/AlphaFold-prediction-00b3e6)](https://alphafoldserver.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Project Description

A complete, reproducible computational workflow for the analysis of TP53
variant effects using sequence verification, **AlphaFold** structural
prediction, structural validation against experimentally determined data
(**PDB 2OCJ**), WT-vs-mutant structural comparison, feature engineering, and
machine learning. The project starts from the TP53 coding sequence
(**NM_001126112.3**, CDS 140–1321), derives and formally verifies a 393-aa
wild-type protein, validates the predicted WT structure against experimental
data, and scaffolds the downstream variant and machine-learning stages.

All results, figures, and scripts are included — the repository is fully
reproducible and suitable for academic review, collaboration, and
portfolio/research presentation.

## Background

TP53 (Homo sapiens, NCBI Gene ID 7157) encodes cellular tumor antigen p53, a
transcription factor and tumor suppressor. The canonical full-length isoform
is 393 amino acids (UniProt P04637): disordered N- and C-terminal regions
flank a structured central DNA-binding (core) domain (~residues 94–292), the
hotspot for cancer-associated missense variants. Most experimentally
determined TP53 structures, including PDB 2OCJ, cover the core domain only —
so any predicted full-length model can only be benchmarked on overlapping
residues. This project establishes that WT structural baseline first, before
any variant or machine-learning analysis. See
`docs/research/biological_background.md`.

## Objectives

The objective of this project is **not** to claim pathogenicity but to:

1. Derive and formally verify a 393-aa WT TP53 sequence from the selected CDS.
2. Analyse all AlphaFold WT models and select a representative on evidence.
3. Validate the WT model against experimental data (2OCJ) on overlapping
   residues, reporting RMSD, aligned residues, and identity.
4. Build a provenance-tracked variant dataset (no invented mutations).
5. Compare WT vs mutant structures with quantitative descriptors.
6. Engineer documented sequence/structural features and evaluate whether
   machine-learning models can learn patterns associated with curated
   variant annotations — reporting association, never causation.

## Research Questions

- **RQ1 (answered):** Can a reproducible WT TP53 sequence be obtained and
  verified from the selected CDS? — Yes: 100% identity to live UniProt P04637.
- **RQ2 (answered):** Can AlphaFold generate a WT model quantitatively
  comparable with experimental TP53 data? — Yes: 0.37–0.67 Å CA-RMSD over
  194 core residues (consistency, not blind validation — templates enabled).
- **RQ3 (answered, prototype):** How do selected variants alter sequence/structure
  features vs WT? — 388 ClinVar missense variants featurized vs the verified
  WT (domain, Grantham/physicochemical deltas, WT pLDDT context); demo table
  in `results/mutations/wt_vs_mutant.md`.
- **RQ4 (answered, prototype):** Can these features inform classification of curated
  variant annotations? — Random forest test F1 0.88 / ROC-AUC 0.94 on 78
  held-out variants (association with ClinVar annotations, never causation).
  Small-data prototype caveats apply.
- **RQ5 (answered, prototype):** Which features contribute most to predictions?
  — WT pLDDT context, Zn-ligand distance, position/core flags rank highest
  (`figures/machine_learning/feature_importance.png`), reported as association.

Details: `docs/research/research_questions.md`.

## Workflow

```
TP53 CDS (NM_001126112.3:140-1321)
        ↓
CDS Verification → ORF Identification → Protein Translation
        ↓
Protein Sequence Verification (UniProt P04637) ✅ RQ1
        ↓
AlphaFold Structural Prediction (5 models)
        ↓
AlphaFold Confidence Analysis (pLDDT / PAE)
        ↓
Representative Model Selection (model_4)
        ↓
Experimental Benchmark Retrieval (PDB 2OCJ, X-ray 2.05 Å)
        ↓
Overlap-Restricted Structural Alignment ✅ RQ2 (RMSD 0.37-0.67 Å)
        ↓
Variant Dataset (ClinVar TP53, 388 missense, traceable VCV IDs) ✅ RQ3
        ↓
Mutant Feature Extraction (21 sequence/structural features, leak-free)
        ↓
Train / Test Split (stratified 80/20, seed 42, scaling fit on train only)
        ↓
Machine Learning (logistic regression + random forest baselines) ✅ RQ4
        ↓
Model Evaluation (held-out test: F1 0.88, ROC-AUC 0.94) + Explainability ✅ RQ5
        ↓
TP53 Variant Prediction (scripts/machine_learning/predict.py)
        ↓
HTML Prediction Dashboard (dashboard/server.py + index.html)
```

Current position: WT baseline + variant/ML/predictor complete (academic
prototype); PyMOL cartoon cross-check figures remain pending.

## Installation

### Prerequisites

- Python (≥ 3.10)
- PyMOL (≥ 2.5) — for the structural cross-check only

### Setup

```bash
# Clone the repository
git clone https://github.com/simbisaichinhema/TP53-Sequence-Structure-and-Machine-Learning-.git
cd TP53-Sequence-Structure-and-Machine-Learning-

# Create the environment
conda env create -f config/environment.yml
conda activate tp53-analysis
```

### Required Python Packages

| Package | Source | Purpose |
|---|---|---|
| numpy | PyPI/conda | Kabsch superposition, confidence statistics |
| matplotlib | PyPI/conda | Publication-quality figures |
| PyMOL | External | Independent alignment cross-check |
| AlphaFold Server | External | WT structure prediction (already run) |

`config/environment.yml` additionally pins Biopython, pandas, scikit-learn,
and PyYAML for the planned variant/ML stages.

## Folder Structure

```
TP53-Mutation-Analysis/
├── README.md                  # This file
├── LICENSE                    # MIT License
├── CITATION.cff               # Machine-readable citation
├── CHANGELOG.md               # Versioned research log
├── .gitignore                 # Exclude generated files
│
├── data/
│   ├── raw/tp53_cds/          # NCBI CDS set, live UniProt retrieval, local copies
│   ├── raw/variants/          # ClinVar esearch IDs + clean provenance (16 MB
│   │                          #   esummary dump git-ignored, regenerable)
│   ├── processed/protein/     # Verified 393-aa WT translation
│   ├── processed/mutations/   # tp53_variant_dataset.csv (388, VCV-traceable)
│   ├── processed/structural_features/  # tp53_features.csv (388×21) + definitions
│   └── metadata/              # sequence/structure/variant provenance CSVs
│
├── structures/
│   ├── alphafold/wt/raw/      # All 5 models + full_data + original bundle
│   ├── alphafold/wt/selected/ # Representative model_4 + record
│   ├── alphafold/wt/confidence/  # Summary JSONs + job request
│   ├── alphafold/wt/inputs/   # MSAs + templates (5XZC/6RZ3/4QO1/2WGX)
│   ├── experimental/2OCJ/     # 2OCJ.cif (X-ray, 2.05 Å)
│   ├── mutants/               # (empty — NOT STARTED)
│   └── aligned/               # (PyMOL session pending)
│
├── scripts/
│   ├── sequence/              # verify_sequence.py
│   ├── structure/             # analyze_confidence.py, superpose_core.py,
│   │                          # plot_validation_figures.py, align_wt_experimental.pml
│   ├── mutation/              # fetch_clinvar_tp53.py (live ClinVar build)
│   └── machine_learning/      # make_features.py, train.py, predict.py,
│                              # write_results_docs.py
│
├── dashboard/
│   ├── server.py              # stdlib inference server (real model)
│   └── index.html             # predictor UI (pos/ref/alt → class + proba)
│
├── results/
│   ├── sequence/              # sequence_verification.md
│   ├── structure/             # alphafold_confidence.md, wt_validation.md,
│   │                          # superposition.json
│   ├── mutations/             # wt_vs_mutant.md (demo-variant comparison)
│   └── machine_learning/      # evaluation.md, metrics.json, model.joblib
│                              # (joblib regenerable, git-ignored)
│
├── figures/
│   ├── structures/            # Per-residue pLDDT plot
│   ├── alignments/            # RMSD heatmap
│   ├── machine_learning/      # Confusion matrix, ROC, importance, class dist
│   └── workflow|sequence/     # (pending)
│
├── notebooks/                 # (conventions README; analyses pending baseline)
├── docs/research/             # Questions, status, background, file audit
├── docs/protocols/            # Sequence + structural validation protocols
├── docs/methods/              # methods.md
└── config/                    # analysis_config.yaml, environment.yml
```

## How to Run

Each script is self-contained and documents its own inputs and outputs. From
the repository root (use `python3` if `python` maps to Python 2):

```bash
# Step 1 — Verify the WT sequence against live UniProt P04637
python scripts/sequence/verify_sequence.py --reference data/raw/tp53_cds/P04637_uniprot_live_20260918.fasta

# Step 2 — Summarise AlphaFold confidence across all 5 models
python scripts/structure/analyze_confidence.py

# Step 3 — Overlap-restricted superposition vs 2OCJ (+ model selection)
python scripts/structure/superpose_core.py

# Step 4 — Generate validation figures
python scripts/structure/plot_validation_figures.py

# Step 5 — PAE heatmap, 3D structure views, superposed-core overlay
python scripts/structure/plot_structure_views.py

# Step 6 — Fetch ClinVar TP53 variants → clean labelled dataset (388 variants)
python3 scripts/mutation/fetch_clinvar_tp53.py

# Step 7 — Feature extraction (21 sequence/structural features, leak-free)
python3 scripts/machine_learning/make_features.py

# Step 8 — Train baselines + evaluate on held-out test set
python3 scripts/machine_learning/train.py

# Step 9 — Predict a single variant with the real model
python3 scripts/machine_learning/predict.py R 175 H

# Step 10 — Launch the HTML prediction dashboard
python3 dashboard/server.py
# open http://127.0.0.1:8000 — demo: R175H, R248Q, R273H, Y220C, G245S, P72R
```

PyMOL cross-check (pending installation verification):

```bash
pymol scripts/structure/align_wt_experimental.pml
```

### Expected Runtime

| Script | Approximate Runtime |
|---|---|
| `verify_sequence.py` | < 1 min |
| `analyze_confidence.py` | < 1 min |
| `superpose_core.py` | < 1 min |
| `plot_validation_figures.py` | 1–2 min |
| `plot_structure_views.py` | 1–2 min |
| `fetch_clinvar_tp53.py` | 2–4 min (live ClinVar E-utilities) |
| `make_features.py` | < 1 min |
| `train.py` | 1–2 min |
| `predict.py` | seconds |
| `dashboard/server.py` | persistent (starts in ~20 s with model preload) |

## Expected Outputs

| Location | Contents |
|---|---|
| `results/sequence/sequence_verification.md` | 100% identity (393/393) vs live P04637 |
| `results/structure/alphafold_confidence.md` | Per-model pLDDT/PAE summary table |
| `results/structure/superposition.json` | RMSD table, all models × 2OCJ chains A–D |
| `results/structure/wt_validation.md` | 2OCJ annotation, selection rationale, RMSD table |
| `structures/alphafold/wt/selected/wt_selected.cif` | Representative model_4 |
| `figures/structures/wt_selected_per_residue_plddt.png` | pLDDT profile (300 dpi) |
| `figures/structures/wt_model4_pae.png` | PAE heatmap, model_4 (300 dpi) |
| `figures/structures/wt_model4_3d_plddt.png` | 3D CA trace by pLDDT (300 dpi) |
| `figures/alignments/rmsd_models_vs_2ocj.png` | RMSD heatmap (300 dpi) |
| `figures/alignments/wt_vs_2ocj_core_overlay_3d.png` | Superposed cores (300 dpi) |
| `data/processed/mutations/tp53_variant_dataset.csv` | 388 ClinVar missense variants with labels + VCV provenance |
| `data/processed/structural_features/tp53_features.csv` | 388 × 21 feature matrix (definitions in `feature_definitions.md`) |
| `results/machine_learning/metrics.json` + `evaluation.md` | Real CV + held-out test metrics |
| `results/machine_learning/model.joblib` | Trained random-forest pipeline (regenerable via `train.py`) |
| `results/mutations/wt_vs_mutant.md` | Demo-variant structural comparison + real predictions |
| `figures/machine_learning/` | Confusion matrix, ROC, feature importance, class distribution |
| `dashboard/` | `server.py` + `index.html` — predictor backed by the real model |
| `data/processed/mutations/mutant_sequences.fasta` | 388 real mutant proteins (validated single substitutions, 393 aa) |
| `results/machine_learning/all_predictions.csv` | Per-variant prediction audit (label, split, pred, proba) |
| `results/machine_learning/cohort_summary.json` | Per-split metrics + misclassified list |
| `results/mutations/variant_proteins.md` | WT-vs-mutant windows + test error analysis |
| `figures/machine_learning/` | + position_enrichment, plddt_by_class, substitution_counts |

## Results Summary

| Metric | Value |
|---|---|
| WT protein length | 393 aa |
| Sequence identity vs live UniProt P04637 (SV=4) | 393/393 (100%) |
| AlphaFold models analysed | 5 (all preserved) |
| Core (94–292) mean pLDDT, selected model_4 | 97.89 |
| N-terminal (1–93) mean pLDDT | 36–39 (disordered, expected) |
| C-terminal (293–393) mean pLDDT | 51–53 (disordered, expected) |
| Experimental benchmark | 2OCJ, X-ray, 2.05 Å, residues 96–289 |
| Aligned residues (overlap only) | 194 CA |
| Sequence identity over overlap | 194/194 (100%) |
| CA-RMSD, all models × chains A–D | 0.37–0.67 Å |
| Variant dataset (ClinVar TP53 missense, traceable VCV) | 388 (232 pathogenic / 156 benign) |
| Features per variant | 21 (position, domain, Zn-distance, Grantham + deltas, WT pLDDT, DNA-contact) |
| ML split | stratified 80/20, seed 42 (train 310 / test 78) |
| Random forest (selected): test accuracy / F1 / ROC-AUC | 0.846 / 0.880 / 0.937 |
| Logistic regression: test accuracy / F1 / ROC-AUC | 0.744 / 0.800 / 0.835 |
| Dashboard | live at `http://127.0.0.1:8000` via `dashboard/server.py` (real model) |

### Key Points

- All five WT models are effectively equivalent — model_4 is a nominal
  representative, not a qualitatively better model.
- Sub-angstrom agreement is restricted to the ordered core; termini are
  low-confidence and unbenchmarked.
- Templates from the same fold family (5XZC/6RZ3/4QO1/2WGX) were enabled at
  prediction, so agreement reads as consistency, not blind validation.

## Figures

### Per-Residue pLDDT, Selected Model (model_4)

![Per-residue pLDDT](figures/structures/wt_selected_per_residue_plddt.png)

Confident core (~98) flanked by low-confidence termini; red hatching marks
the 2OCJ-covered interval (96–289).

### RMSD: All Models vs 2OCJ Chains

![RMSD heatmap](figures/alignments/rmsd_models_vs_2ocj.png)

CA-RMSD (Å) over 194 overlapping residues at 100% identity. Generated by
`scripts/structure/plot_validation_figures.py` from measured data.

### PAE Heatmap, Selected Model (model_4)

![PAE heatmap](figures/structures/wt_model4_pae.png)

Predicted Aligned Error (mean 21.25 Å; low within the core block,
high between the core and the disordered termini).

### Predicted Structure in 3D (model_4, CA trace by pLDDT)

![3D pLDDT](figures/structures/wt_model4_3d_plddt.png)

Schematic CA-trace rendering (matplotlib 3D, not a PyMOL cartoon):
compact high-confidence core with extended low-confidence termini.

### Superposed Cores: Model_4 vs 2OCJ Chain A

![Core overlay](figures/alignments/wt_vs_2ocj_core_overlay_3d.png)

Kabsch-superposed CA traces, residues 96–289 (0.401 Å RMSD). PyMOL
cartoon figures remain pending.

### ML Evaluation: Confusion Matrix (held-out test, n=78)

![Confusion matrix](figures/machine_learning/confusion_matrix.png)

Random forest: TN=22, FP=9, FN=3, TP=44 (accuracy 0.846, F1 0.880).
Generated by `scripts/machine_learning/train.py` from measured predictions.

### ML Evaluation: ROC Curve

![ROC curve](figures/machine_learning/roc_curve.png)

Test ROC-AUC 0.937 (random forest) vs 0.835 (logistic regression).

### Feature Importance (association, not causation)

![Feature importance](figures/machine_learning/feature_importance.png)

WT pLDDT context, Zn-ligand distance, and core/position flags dominate —
consistent with pathogenic missense enriching in the ordered core domain.

## Limitations

- Full-length prediction vs core-domain experiment: only residues 96–289 are
  comparable; terminal regions have no experimental benchmark here.
- Template-enabled prediction against a long-known fold: agreement measures
  consistency, not independent predictive power.
- ML is an academic prototype (n=388 ClinVar germline missense): it associates
  features with curated annotations and is NOT clinically validated or a
  diagnostic tool. Position carries hotspot signal; a position-aware split,
  larger multi-source dataset, and independent testing are future work.
- Mutant structures were not re-predicted; structural features reuse the
  validated WT model context (pLDDT) plus sequence-derived deltas.

## Future Work

PyMOL cartoon cross-check → larger multi-source dataset (COSMIC / IARC TP53 /
cBioPortal) → mutant structure prediction → position-aware splits →
independent test set → calibration.

## Reproducibility

- Raw data are never overwritten; scripts read `raw/` and write
  `processed/` / `results/` / `figures/`.
- Single source of truth: `config/analysis_config.yaml`; environments:
  `config/environment.yml`.
- The Kabsch implementation carries a synthetic rotation-recovery self-test
  (passes at ~1e-15 Å); GUI steps are recorded as PyMOL command scripts.
- Provenance for every external file: `data/metadata/*.csv`.

## References

- NCBI Gene TP53 (GeneID 7157); transcript NM_001126112.3
- UniProt P04637 (P53_HUMAN), SV=4 — https://www.uniprot.org/uniprotkb/P04637
- PDB 2OCJ: Wang, Y., Rosengarth, A., & Luecke, H. (2007). Structure of the
  human p53 core domain in the absence of DNA. *Acta Crystallogr D Biol
  Crystallogr*, 63, 276–281. DOI:
  [10.1107/S0907444906048499](https://doi.org/10.1107/S0907444906048499)
- AlphaFold Server — https://alphafoldserver.com (prediction job request and
  Output Terms of Use preserved in `structures/alphafold/wt/`)

## Citation

If you use this repository, please cite it as below (see `CITATION.cff`).

```bibtex
@software{tp53mutationanalysis2026,
  author  = {{TP53 Mutation Analysis contributors}},
  title   = {TP53 Mutation Analysis: Sequence, Structure, and Machine Learning},
  year    = {2026},
  url     = {TP53-Mutation-Analysis},
  license = {MIT},
  note    = {WT sequence verified vs UniProt P04637; AlphaFold models validated vs PDB 2OCJ}
}
```

## Author

**Simbisai Chinhema** — Bioinformatics

## Contributors

- **Simbisai Chinhema** — Bioinformatics (Author & Developer)

## License

This project is licensed under the [MIT License](LICENSE). Third-party data
(NCBI, UniProt, PDB, AlphaFold output) remain subject to their original
terms — see `data/metadata/` and `structures/alphafold/wt/terms_of_use.md`.

## Acknowledgements

- NCBI, UniProt, and the RCSB PDB for open data; the depositors and authors
  of 2OCJ.
- Google DeepMind / AlphaFold Server for structure prediction.
- The NumPy, matplotlib, and PyMOL communities for open tooling.
