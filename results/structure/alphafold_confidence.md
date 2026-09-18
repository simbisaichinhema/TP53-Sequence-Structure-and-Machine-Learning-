# Results: AlphaFold WT confidence analysis

Status: COMPLETED (summary from local files; representative model SELECTED —
see `wt_validation.md` for rationale and region-wise values).

Computed with `scripts/structure/analyze_confidence.py` from the preserved
`full_data_*.json` (atom pLDDT, PAE) and CIF B-factors (per-residue pLDDT),
2026-09-18.

## Summary scores (identical across all 5 models)

| Metric | All models |
|---|---|
| ranking_score | 0.8 |
| ptm | 0.55 |
| fraction_disordered | 0.5 |
| has_clash | 0.0 |

Because the ranking scores do not discriminate, model_0 must NOT be assumed
best; selection requires per-residue evidence below.

## Per-residue pLDDT from CIF B-factors (393 residues each)

| Model | Mean | Median | Fraction > 70 | Fraction > 90 | Fraction < 50 |
|---|---|---|---|---|---|
| model_0 | 69.36 | 85.83 | 0.598 | 0.463 | 0.366 |
| model_1 | 69.08 | 85.58 | 0.585 | 0.468 | 0.364 |
| model_2 | 69.73 | 85.56 | 0.593 | 0.461 | 0.366 |
| model_3 | 69.49 | 86.87 | 0.588 | 0.473 | 0.366 |
| model_4 | 69.43 | 85.83 | 0.593 | 0.468 | 0.364 |

## Atom-level pLDDT means (3060 atoms each)

model_0: 69.75 | model_1: 69.46 | model_2: 70.09 | model_3: 69.85 |
model_4: 69.82 (per-atom minima ~8–11, maxima ~98.9–99.0).

## Mean PAE (393×393 matrices)

model_0: 21.22 | model_1: 21.28 | model_2: 21.36 | model_3: 21.48 |
model_4: 21.25 (global min 0.80, max 31.70).

## Interpretation (Results only)

- All five models are near-identical on every summary and global metric; the
  spread in mean per-residue pLDDT is < 0.7 points.
- Median pLDDT (~85–87) far exceeds the mean (~69), indicating a confident
  core with low-confidence tails — consistent with a structured DNA-binding
  domain flanked by disordered termini (fraction_disordered = 0.5).
- No model is demonstrably superior on these globals; representative-model
  selection needs region-aware analysis (e.g. pLDDT restricted to the
  core-domain residue range) — PENDING.

## Outstanding

- Representative AlphaFold model: SELECTED — model_4 (nominal; all models
  effectively equivalent), copied to `structures/alphafold/wt/selected/`.
  Region-wise pLDDT and selection rationale: `wt_validation.md`.
- Confidence visualisation figures: PENDING
