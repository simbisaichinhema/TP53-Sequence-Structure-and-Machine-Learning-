# Kaggle deployment

`TP53_Kaggle_Demo.ipynb` reproduces the full ML pipeline on Kaggle
(WT check → ClinVar fetch + **conflict-majority expansion to ~800 variants**
→ features → baseline training → **3-model side-by-side benchmark** →
tuning → position-aware validation → cohort audit → prediction panel).

## How to deploy (5 minutes)

1. Go to [kaggle.com](https://www.kaggle.com) → **Create → New Notebook**.
2. **File → Import Notebook** (or drag-drop) → upload `kaggle/TP53_Kaggle_Demo.ipynb`.
3. Right-side **Settings** panel → turn **Internet ON**
   (needed for the `git clone`, live ClinVar fetch, and conflict expansion).
4. Accelerator: **None** (CPU is enough). Environment: latest.
5. **Run All** (or Shift+Enter cell by cell). Expected runtime: ~10–15 min total.

## What each part does

| Cells | Stage | Output |
|---|---|---|
| 1 | Clone repo + install pandas/sklearn/matplotlib + boosters | env ready |
| 2 | WT baseline re-check | 100% identity, RMSD table |
| 3–4 | ClinVar clear labels + **conflicting majority-vote expansion** + summary | **n≈818** (405 P / 413 B), `label_basis` provenance |
| 5–6 | Features + baseline train | 21 features, RF vs LogReg |
| 7 | **Multi-model benchmark (3 algorithms)** | CSV/JSON/report + figures |
| **8** | **Side-by-side comparison tables** | Test metrics ranked; CV±SD vs test; Δ vs baselines |
| **9** | **Side-by-side comparison figures** | Accuracy/F1/AUC/PR bars, ROC+PR curves, CM grid, CV variability |
| 10 | Baseline metrics + classic figures | train.py outputs |
| 11 | Train-only hyperparameter tuning (top-3) | baseline vs tuned table |
| 12 | Position-aware GroupKFold-by-residue | leakage check vs random split |
| 13–14 | Mutant proteins + full-cohort audit | sequences, misclassified table |
| 15 | Prediction panel + **multi-model inference side-by-side** | hotspot DataFrame + per-artefact P(pathogenic) |
| 16 | Static 3D WT structure with hotspots | render-safe PNG |
| 17 | Smoke tests | all PASS |
| 18 | Closing summary | reproducibility + limitation statement |

## Side-by-side comparison (section 8)

- **Table A** — every metric on the held-out test set, ranked by ROC-AUC
- **Table B** — CV mean±SD and test scores for all models, baseline vs challenger
- **Table C** — Δ ROC-AUC and Δ F1 versus each baseline present in the run
  (baselines missing from the default 3-model set are skipped)
- **Section 9** — bar charts, overlay ROC/PR curves, confusion-matrix grid

## Notes

- The notebook **retrains from scratch** (no pickle-version issues across sklearn releases).
- Optional boosters (xgboost/lightgbm/catboost) are pip-installed; if one fails,
  the benchmark skips that model and records it in `experiment_config.json`.
- Dataset expansion never invents labels: VUS stay excluded; only conflicting
  records with a **strict majority** of submitter germline votes are added
  (`scripts/mutation/expand_clinvar_conflicts.py`, audit JSON under
  `data/raw/variants/`).
- If the GitHub remote is unavailable, upload the repo folder as a Kaggle
  Dataset and replace the clone cell with `%cd /kaggle/input/<dataset-name>/...`.
- The HTML dashboard (`dashboard/`) cannot be served from Kaggle (no public
  web hosting) — demo it locally via `python3 dashboard/server.py`.
