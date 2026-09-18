# Selected representative WT model

- File: `wt_selected.cif` — byte-identical copy of
  `../raw/fold_tp53_predicted_protein_model_4.cif` (model_4).
- Selection date: 2026-09-18. Method: `scripts/structure/superpose_core.py`.
- Rationale: highest mean per-residue pLDDT over the experimentally covered
  core region 94–292 (97.89 vs 97.79–97.87 for models 0–3).
- Scope of claim: nominal representative only. All five models are
  effectively equivalent (global summary scores identical; all agree with
  2OCJ at 0.37–0.67 Å CA-RMSD). No model is qualitatively superior.
- Validation: 0.401 / 0.389 / 0.407 / 0.666 Å CA-RMSD vs 2OCJ chains A–D
  over residues 96–289 (194 CA, 100% identity).
- Full evidence: `results/structure/wt_validation.md`.
- Use this file (not `raw/model_0.cif`) as the WT reference for all
  downstream mutant comparisons.
