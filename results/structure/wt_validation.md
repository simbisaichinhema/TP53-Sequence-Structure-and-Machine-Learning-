# Results: WT structural validation (AlphaFold vs experimental)

Status: COMPLETED (computational measurement; PyMOL cross-check PENDING).

Method: `scripts/structure/superpose_core.py` — CA-only Kabsch superposition
(numpy; implementation carries a synthetic rotation-recovery self-test,
passing at 1.59e-15 Å). 2OCJ auth numbering was verified to equal WT
positions by sequence match before superposition.

## Experimental benchmark (retrieved 2026-09-18)

- PDB ID: 2OCJ — "Human p53 core domain in the absence of DNA"
- Experimental method: X-RAY DIFFRACTION
- Resolution: 2.05 Å (R-work 0.209 / R-free 0.246)
- Chains: 4 (A–D), each modelling residues 96–289 (194 residues, homomeric)
- Biological region: TP53 core (DNA-binding) domain only — NOT full length
- Non-polymer component: ZN (zinc, expected for the core domain)
- Source file: `structures/experimental/2OCJ/2OCJ.cif` (RCSB download)
- Primary citation: Wang, Rosengarth & Luecke, Acta Crystallogr D 63:276–281
  (2007), DOI 10.1107/S0907444906048499, PubMed 17327663

## Representative AlphaFold model

- `structures/alphafold/wt/selected/wt_selected.cif` = model_4
- Rationale: highest mean per-residue pLDDT over the experimentally covered
  core region 94–292 (97.89 vs 97.79–97.87 for the others). The spread is
  negligible — all five models are effectively equivalent; model_4 is the
  nominal representative, not a qualitatively better model.

## Region-wise mean pLDDT (per model; core 94–292 vs termini)

| Model | N-term 1–93 | Core 94–292 | C-term 293–393 |
|---|---|---|---|
| model_0 | 36.90 | 97.79 | 52.56 |
| model_1 | 36.54 | 97.85 | 51.63 |
| model_2 | 39.04 | 97.85 | 52.05 |
| model_3 | 37.50 | 97.87 | 52.32 |
| model_4 | 37.68 | 97.89 | 52.06 |

## RMSD: CA superposition over residues 96–289 (194 CA, overlap only)

| Model | vs 2OCJ-A | vs 2OCJ-B | vs 2OCJ-C | vs 2OCJ-D |
|---|---|---|---|---|
| model_0 | 0.392 | 0.373 | 0.378 | 0.614 |
| model_1 | 0.382 | 0.370 | 0.374 | 0.630 |
| model_2 | 0.416 | 0.394 | 0.398 | 0.633 |
| model_3 | 0.393 | 0.380 | 0.393 | 0.646 |
| model_4 (selected) | 0.401 | 0.389 | 0.407 | 0.666 |

- Aligned residues: 194 CA (positions 96–289)
- Sequence identity over overlap: 194/194 (100%) for every pair
- Compared region: residues 96–289 (the 2OCJ-modelled subset of the core domain)
- Raw values: `results/structure/superposition.json`

## Interpretation (Discussion, not Results)

The predicted core domain shows sub-angstrom agreement (0.37–0.67 Å RMSD
across 194 aligned CA atoms at 100% sequence identity) with the
experimentally determined core-domain structure. This indicates the
AlphaFold-predicted WT core fold is structurally consistent with
experimental data. It does NOT prove correctness: the prediction ran with
structure templates enabled, and 2OCJ (deposited 2006) was very likely
available as a template/at training time, so this measures consistency with
known structural data rather than independent blind prediction. Agreement is
also restricted to the ordered core; the disordered termini (pLDDT ~37–52)
have no experimental benchmark here.

## Outstanding

- Independent PyMOL cross-check of the superposition
  (`scripts/structure/align_wt_experimental.pml`) — PENDING
- PyMOL cartoon figures — PENDING (matplotlib 3D schematics done:
  `figures/structures/wt_model4_3d_plddt.png`,
  `figures/alignments/wt_vs_2ocj_core_overlay_3d.png`,
  `figures/structures/wt_model4_pae.png` via
  `scripts/structure/plot_structure_views.py`)
