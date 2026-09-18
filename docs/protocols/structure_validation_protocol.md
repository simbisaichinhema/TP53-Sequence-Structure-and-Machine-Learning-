# Protocol: WT structural validation

## 1. AlphaFold confidence review (COMPLETED — summary)

- Inspect all 5 models; never assume model_0 is best.
- Summary scores are identical across models here (ranking_score 0.8,
  ptm 0.55), so selection must use per-residue pLDDT (see
  `results/structure/alphafold_confidence.md`).
- Definitions: pLDDT = per-residue confidence in predicted local structure;
  PAE = confidence in predicted relative positioning of residue pairs. Neither
  is experimental certainty.
- Reproduce: `python scripts/structure/analyze_confidence.py`.

## 2. Experimental benchmark (PENDING)

- Candidate: PDB 2OCJ (TP53 core domain, not full length).
- On retrieval into `structures/experimental/2OCJ/`, record: experimental
  method, resolution, chain used, residue coverage, biological region,
  limitations. Restrict all comparisons to overlapping residues.

## 3. PyMOL alignment (PENDING)

Reproducible commands (also saved as
`scripts/structure/align_wt_experimental.pml`):

```pymol
load structures/alphafold/wt/selected/wt_selected.cif, wt
load structures/experimental/2OCJ/2ocj.cif, exp
# identify overlapping residue ranges first (see 2OCJ annotation), e.g.:
align wt and resi 94-292, exp and chain A
rms_cur wt and resi 94-292, exp and chain A
# record: RMSD, aligned residues, sequence identity; save session to
# structures/aligned/ and export figure to figures/alignments/
```

Record in `results/structure/wt_validation.md`: RMSD, aligned-residue count,
sequence identity, compared region, model ID, PyMOL version, exact commands.
Report as "X Å RMSD across Y aligned residues" with cautious interpretation —
never "AlphaFold was proven correct".
