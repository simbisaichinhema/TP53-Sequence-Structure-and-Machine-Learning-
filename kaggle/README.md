# Kaggle deployment

`TP53_Kaggle_Demo.ipynb` reproduces the full ML pipeline on Kaggle
(WT check → ClinVar fetch → features → training → metrics/figures →
interactive widget predictor with the real model).

## How to deploy (5 minutes)

1. Go to [kaggle.com](https://www.kaggle.com) → **Create → New Notebook**.
2. **File → Import Notebook** (or drag-drop) → upload `kaggle/TP53_Kaggle_Demo.ipynb`.
3. Right-side **Settings** panel → turn **Internet ON**
   (needed for the `git clone` and the live ClinVar fetch).
4. Accelerator: **None** (CPU is enough). Environment: latest.
5. **Run All** (or Shift+Enter cell by cell). Expected runtime: ~5–8 min total.

## What each part does

| Cells | Stage | Output |
|---|---|---|
| 1 | Clone repo + install pandas/scikit-learn/matplotlib | env ready |
| 2 | WT baseline re-check | 100% identity, RMSD table |
| 3–4 | Live ClinVar fetch + dataset summary | 388 variants (skipped if cached) |
| 5–6 | Features + training | 21 features, RF vs LogReg |
| 7–8 | Metrics, figures, full-cohort audit | real plots, 12 mistakes listed |
| 9–11 | Mutant proteins, cohort audit, prediction panel | windows, audit tables, hotspot DataFrame |
| 12 | Static 3D WT structure with hotspots | render-safe PNG (no WebGL/JS needed) |
| 13 | Closing summary | reproducibility statement |

## Notes

- The notebook **retrains from scratch** (no pickle-version issues across sklearn releases).
- If the GitHub remote is unavailable, upload the `TP53-Mutation-Analysis/` folder
  as a Kaggle Dataset, attach it to the notebook, and replace the clone cell with
  `%cd /kaggle/input/<dataset-name>/TP53-Mutation-Analysis`.
- The HTML dashboard (`dashboard/`) cannot be served from Kaggle (no public
  web hosting) — demo it locally via `python3 dashboard/server.py`, or deploy
  `predict.py` behind Gradio on Hugging Face Spaces for a public link.
