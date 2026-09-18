"""WT validation: overlap-restricted CA superposition of AlphaFold WT models vs 2OCJ.

Method: parse mmCIF CA coordinates, map 2OCJ auth numbering onto WT positions
by sequence match, superpose with the Kabsch algorithm (numpy), report RMSD
over common CA atoms per model x per 2OCJ chain, plus sequence identity over
the overlap. Also reports region-wise mean pLDDT (N-term 1-93 / core 94-292 /
C-term 293-393) to support representative-model selection.

Cross-check with the PyMOL protocol (scripts/structure/align_wt_experimental.pml)
is still recommended; see results/structure/wt_validation.md.

Outputs: results/structure/superposition.json + selected model copy.
Run from repository root:  python3 scripts/structure/superpose_core.py
Requires: numpy.
"""
import json
import shutil
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "structures/alphafold/wt/raw"
EXP = REPO / "structures/experimental/2OCJ/2OCJ.cif"
OUT_JSON = REPO / "results/structure/superposition.json"
SELECTED = REPO / "structures/alphafold/wt/selected/wt_selected.cif"

AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
       "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
       "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
       "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V"}


def parse_mmcif(path):
    """Return (residues, header_cols). residues: {(asym, seq_id): {'comp', 'atoms': {name: (x,y,z,b)}} }."""
    lines = Path(path).read_text().splitlines()
    hdr = [l.strip() for l in lines if l.startswith("_atom_site.")]
    cols = {c: i for i, c in enumerate(hdr)}
    start = next(i for i, l in enumerate(lines) if l.strip() == hdr[0]) + len(hdr)
    res = {}
    for line in lines[start:]:
        if not line.startswith(("ATOM", "HETATM")):
            break
        p = line.split()
        if p[cols["_atom_site.group_PDB"]] != "ATOM":
            continue
        if p[cols["_atom_site.label_alt_id"]] not in (".", "A"):
            continue
        key = (p[cols["_atom_site.label_asym_id"]], int(p[cols["_atom_site.label_seq_id"]]))
        entry = res.setdefault(key, {"comp": p[cols["_atom_site.label_comp_id"]], "atoms": {}})
        name = p[cols["_atom_site.label_atom_id"]]
        if name not in entry["atoms"]:
            entry["atoms"][name] = (float(p[cols["_atom_site.Cartn_x"]]),
                                    float(p[cols["_atom_site.Cartn_y"]]),
                                    float(p[cols["_atom_site.Cartn_z"]]),
                                    float(p[cols["_atom_site.B_iso_or_equiv"]]))
    auth = {}
    for (asym, seq), entry in res.items():
        auth[(asym, seq)] = entry  # caller maps asym/auth numbering as needed
    return res, cols


def parse_2ocj(path):
    lines = Path(path).read_text().splitlines()
    hdr = [l.strip() for l in lines if l.startswith("_atom_site.")]
    cols = {c: i for i, c in enumerate(hdr)}
    start = next(i for i, l in enumerate(lines) if l.strip() == hdr[0]) + len(hdr)
    chains = defaultdict(dict)  # auth_asym -> {auth_seq: {'comp', 'ca'}}
    for line in lines[start:]:
        if not line.startswith(("ATOM", "HETATM")):
            break
        p = line.split()
        if p[cols["_atom_site.group_PDB"]] != "ATOM":
            continue
        if p[cols["_atom_site.label_alt_id"]] not in (".", "A"):
            continue
        if p[cols["_atom_site.label_atom_id"]] != "CA":
            continue
        chain = p[cols["_atom_site.auth_asym_id"]]
        seq = int(p[cols["_atom_site.auth_seq_id"]])
        if seq not in chains[chain]:
            chains[chain][seq] = {
                "comp": p[cols["_atom_site.auth_comp_id"]],
                "ca": np.array([float(p[cols["_atom_site.Cartn_x"]]),
                                float(p[cols["_atom_site.Cartn_y"]]),
                                float(p[cols["_atom_site.Cartn_z"]])]),
            }
    return dict(chains)


def kabsch_rmsd(P, Q):
    """Optimal-superposition CA RMSD (Kabsch). Minimises ||P@R - Q|| over rotations R.

    Validated in-script by _self_test() (known rotation+translation recovery).
    """
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    H = Pc.T @ Qc
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = U @ np.diag([1.0, 1.0, d]) @ Vt
    return float(np.sqrt(((Pc @ R - Qc) ** 2).sum() / len(P)))


def _self_test():
    """Synthetic validation: a known rotation+translation must be recovered at ~0 RMSD."""
    rng = np.random.default_rng(1)
    P = rng.normal(size=(50, 3))
    Qm, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    if np.linalg.det(Qm) < 0:
        Qm[:, 0] *= -1
    Q = P @ Qm + np.array([5.0, -3.0, 2.0])
    r = kabsch_rmsd(P, Q)
    assert r < 1e-6, f"Kabsch self-test failed: {r}"
    return r


def read_fasta(path):
    return "".join(l.strip() for l in Path(path).read_text().splitlines()
                   if l.strip() and not l.startswith(">"))


def main():
    self_test_rmsd = _self_test()
    print(f"Kabsch self-test (synthetic rotation recovery): {self_test_rmsd:.2e} A")
    wt = read_fasta(REPO / "data/processed/protein/WT_TP53_ORF1_393aa.fasta")
    chains_2ocj = parse_2ocj(EXP)
    print("2OCJ chains:", {c: (min(v), max(v), len(v)) for c, v in chains_2ocj.items()})

    # Verify numbering: 2OCJ auth_seq should equal UniProt positions; check by sequence match.
    numbering_ok = {}
    for chain, residues in chains_2ocj.items():
        ok = all(AA3.get(r["comp"], "?") == wt[s - 1] for s, r in residues.items() if 1 <= s <= len(wt))
        numbering_ok[chain] = ok
    print("auth numbering == WT positions:", numbering_ok)

    result = {"wt_length": len(wt), "chains_2ocj": {}, "models": {}, "regions": {}}
    for chain, residues in chains_2ocj.items():
        seqs = sorted(residues)
        result["chains_2ocj"][chain] = {"n_residues": len(seqs), "range": [seqs[0], seqs[-1]],
                                        "numbering_matches_wt": numbering_ok[chain]}

    for i in range(5):
        af, _ = parse_mmcif(RAW / f"fold_tp53_predicted_protein_model_{i}.cif")
        ca = {seq: (np.array(v[:3]), v[3]) for (a, seq), e in af.items()
              for k, v in e["atoms"].items() if k == "CA" and a == "A"}
        pl = [b for _, b in sorted(ca.items())]
        items = [(s, b) for s, (xyz, b) in sorted(ca.items())]
        regions = {"N_term_1_93": np.mean([b for s, b in items if s <= 93]),
                   "core_94_292": np.mean([b for s, b in items if 94 <= s <= 292]),
                   "C_term_293_393": np.mean([b for s, b in items if s >= 293])}
        result["regions"][f"model_{i}"] = {k: round(float(v), 2) for k, v in regions.items()}
        result["models"][f"model_{i}"] = {}
        for chain, residues in chains_2ocj.items():
            common = sorted(set(ca) & set(residues))
            P = np.array([ca[s][0] for s in common])
            Q = np.array([residues[s]["ca"] for s in common])
            ident = sum(1 for s in common if wt[s - 1] == AA3.get(residues[s]["comp"], "?"))
            result["models"][f"model_{i}"][chain] = {
                "n_aligned_ca": len(common),
                "range": [common[0], common[-1]],
                "rmsd_angstrom": round(kabsch_rmsd(P, Q), 3),
                "sequence_identity": f"{ident}/{len(common)}",
            }
        print(f"model_{i}: regions={result['regions'][f'model_{i}']}")
        for chain, m in result["models"][f"model_{i}"].items():
            print(f"  vs 2OCJ chain {chain}: RMSD {m['rmsd_angstrom']} A over "
                  f"{m['n_aligned_ca']} CA ({m['range'][0]}-{m['range'][1]}), identity {m['sequence_identity']}")

    # Representative selection: highest core-region mean pLDDT (documented rationale).
    best = max(result["regions"], key=lambda m: result["regions"][m]["core_94_292"])
    result["representative_model"] = {
        "model": best,
        "rationale": "Highest mean per-residue pLDDT over the experimentally covered core region (94-292).",
        "core_plddt": result["regions"][best]["core_94_292"],
    }
    src = RAW / f"fold_tp53_predicted_protein_model_{best[-1]}.cif"
    shutil.copy(src, SELECTED)
    OUT_JSON.write_text(json.dumps(result, indent=1))
    print(f"Representative: {best} (core pLDDT {result['representative_model']['core_plddt']}) -> {SELECTED}")
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
