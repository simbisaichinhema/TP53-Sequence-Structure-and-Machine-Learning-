# PyMOL cross-check: selected WT AlphaFold model (model_4) vs experimental 2OCJ.
# PREREQUISITES MET: structures/alphafold/wt/selected/wt_selected.cif and
# structures/experimental/2OCJ/2OCJ.cif exist. 2OCJ chains A-D each cover
# residues 96-289 (= WT positions; verified by sequence match).
# Run from the repository root:  pymol scripts/structure/align_wt_experimental.pml
# Compare the reported RMSD with results/structure/wt_validation.md
# (expected: ~0.4 A over 194 CA vs chain A for the selected model).

load structures/alphafold/wt/selected/wt_selected.cif, wt
load structures/experimental/2OCJ/2OCJ.cif, exp
align wt and resi 96-289, exp and chain A
rms_cur wt and resi 96-289, exp and chain A
save structures/aligned/wt_vs_2ocj_session.pse
png figures/alignments/wt_vs_2ocj.png, width=1800, height=1200, dpi=300
# Record the reported RMSD, aligned-residue count, and identity in
# results/structure/wt_validation.md — do not invent values.
