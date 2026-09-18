"""Publication figures from measured WT validation data (no invented values).

Reads structures/alphafold/wt/raw/*.cif (per-residue pLDDT) and
results/structure/superposition.json (RMSD table). Writes:
  figures/structures/wt_selected_per_residue_plddt.png
  figures/alignments/rmsd_models_vs_2ocj.png
Run from repository root:  python3 scripts/structure/plot_validation_figures.py
Requires: numpy, matplotlib.
"""
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "structures/alphafold/wt/raw"


def residue_plddt(cif):
    res = defaultdict(list)
    for line in Path(cif).read_text().splitlines():
        if line.startswith("ATOM"):
            p = line.split()
            res[int(p[8])].append(float(p[14]))
    return [sum(v) / len(v) for _, v in sorted(res.items())]


def fig_plddt():
    vals = residue_plddt(RAW / "fold_tp53_predicted_protein_model_4.cif")
    x = np.arange(1, len(vals) + 1)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axvspan(1, 93, color="0.9", label="N-terminal (disordered)")
    ax.axvspan(94, 292, color="0.82", label="Core domain 94-292")
    ax.axvspan(293, 393, color="0.9", label="C-terminal (disordered)")
    ax.axvspan(96, 289, color="none", edgecolor="red", hatch="//", linewidth=0,
               label="2OCJ coverage 96-289")
    ax.plot(x, vals, color="#1f4e79", lw=1.2)
    ax.axhline(70, color="grey", ls="--", lw=0.8)
    ax.axhline(90, color="grey", ls=":", lw=0.8)
    ax.set_xlabel("Residue (WT TP53 position)")
    ax.set_ylabel("pLDDT")
    ax.set_title("WT TP53 model_4 (selected): per-residue pLDDT")
    ax.set_xlim(1, 393)
    ax.legend(fontsize=8, loc="lower center")
    out = REPO / "figures/structures/wt_selected_per_residue_plddt.png"
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    print(f"Wrote {out}")


def fig_rmsd():
    data = json.loads((REPO / "results/structure/superposition.json").read_text())
    models = [f"model_{i}" for i in range(5)]
    chains = ["A", "B", "C", "D"]
    m = np.array([[data["models"][mo][c]["rmsd_angstrom"] for c in chains] for mo in models])
    fig, ax = plt.subplots(figsize=(6, 4.5))
    im = ax.imshow(m, cmap="viridis", vmin=0.3, vmax=0.7)
    ax.set_xticks(range(4), [f"2OCJ-{c}" for c in chains])
    ax.set_yticks(range(5), models)
    for i in range(5):
        for j in range(4):
            ax.text(j, i, f"{m[i, j]:.3f}", ha="center", va="center",
                    color="white", fontsize=9)
    ax.set_title("CA-RMSD (Å): 194 residues 96-289, 100% identity")
    fig.colorbar(im, label="Å")
    out = REPO / "figures/alignments/rmsd_models_vs_2ocj.png"
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    print(f"Wrote {out}")


if __name__ == "__main__":
    fig_plddt()
    fig_rmsd()
