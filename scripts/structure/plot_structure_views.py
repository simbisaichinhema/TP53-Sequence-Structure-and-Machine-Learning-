"""3D structure views + PAE heatmap from measured data (no invented values).

CA-trace renderings via matplotlib 3D (schematic — PyMOL cartoon figures
remain pending). Superposition reuses the validated Kabsch implementation in
superpose_core.py. Reads raw CIFs + full_data_4.json. Writes:
  figures/structures/wt_model4_pae.png
  figures/structures/wt_model4_3d_plddt.png
  figures/alignments/wt_vs_2ocj_core_overlay_3d.png
Run from repository root:  python3 scripts/structure/plot_structure_views.py
Requires: numpy, matplotlib.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from superpose_core import kabsch_rmsd, parse_2ocj, parse_mmcif  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "structures/alphafold/wt/raw"


def fig_pae():
    d = json.loads((RAW / "fold_tp53_predicted_protein_full_data_4.json").read_text())
    pae = np.array(d["pae"])
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(pae, cmap="Greens_r", vmin=0, vmax=32)
    ax.set_xlabel("Scored residue")
    ax.set_ylabel("Aligned residue")
    ax.set_title("WT model_4: Predicted Aligned Error (PAE, Å)")
    fig.colorbar(im, label="Expected position error (Å)")
    out = REPO / "figures/structures/wt_model4_pae.png"
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    print(f"Wrote {out} (mean PAE {pae.mean():.2f} Å)")


def fig_3d_plddt():
    af, _ = parse_mmcif(RAW / "fold_tp53_predicted_protein_model_4.cif")
    seqs = sorted(s for a, s in af if a == "A")
    xyz = np.array([af[("A", s)]["atoms"]["CA"][:3] for s in seqs])
    pl = np.array([np.mean(af[("A", s)]["atoms"]["CA"][3:]) for s in seqs])
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    sc = ax.scatter(xyz[:, 0], xyz[:, 1], xyz[:, 2], c=pl, cmap="coolwarm",
                    vmin=0, vmax=100, s=6)
    ax.plot(xyz[:, 0], xyz[:, 1], xyz[:, 2], color="grey", lw=0.5, alpha=0.5)
    fig.colorbar(sc, label="pLDDT", shrink=0.6)
    ax.set_title("WT model_4: CA trace coloured by pLDDT (schematic)")
    ax.set_xlabel("x (Å)")
    ax.set_ylabel("y (Å)")
    out = REPO / "figures/structures/wt_model4_3d_plddt.png"
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    print(f"Wrote {out}")


def fig_overlay():
    af, _ = parse_mmcif(RAW / "fold_tp53_predicted_protein_model_4.cif")
    ocj = parse_2ocj(REPO / "structures/experimental/2OCJ/2OCJ.cif")
    core = sorted(set(s for a, s in af if a == "A") & set(ocj["A"]))
    P = np.array([af[("A", s)]["atoms"]["CA"][:3] for s in core])
    Q = np.array([ocj["A"][s]["ca"] for s in core])
    rmsd = kabsch_rmsd(P, Q)
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    H = Pc.T @ Qc
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = U @ np.diag([1.0, 1.0, d]) @ Vt
    Pr = Pc @ R
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot(Pr[:, 0], Pr[:, 1], Pr[:, 2], color="#1f4e79", lw=1.2, label="AF model_4 core")
    ax.plot(Qc[:, 0], Qc[:, 1], Qc[:, 2], color="#c5504b", lw=1.2, alpha=0.8,
            label="2OCJ chain A core")
    ax.legend()
    ax.set_title(f"Superposed cores 96-289 (CA-RMSD {rmsd:.3f} Å, schematic)")
    out = REPO / "figures/alignments/wt_vs_2ocj_core_overlay_3d.png"
    fig.tight_layout()
    fig.savefig(out, dpi=300)
    print(f"Wrote {out}")


if __name__ == "__main__":
    fig_pae()
    fig_3d_plddt()
    fig_overlay()
