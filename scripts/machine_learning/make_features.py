"""Build the ML feature matrix from the ClinVar TP53 variant dataset.

Every feature derives ONLY from (pos, ref, alt) + WT context (WT sequence,
verified WT AlphaFold pLDDT). No label information is used - no leakage.

Features (see data/processed/structural_features/feature_definitions.md):
  pos_norm, in_core, domain one-hot (7), dist_to_zn, grantham,
  d_hydro, d_volume, d_charge, d_polarity, ref_hydro, ref_volume, ref_charge,
  plddt_at_pos, plddt_window5, dna_contact

Inputs:
  data/processed/mutations/tp53_variant_dataset.csv
  data/processed/protein/WT_TP53_ORF1_393aa.fasta
  structures/alphafold/wt/selected/wt_selected.cif  (per-residue pLDDT)
Outputs:
  data/processed/structural_features/tp53_features.csv
  data/processed/structural_features/feature_definitions.md

Usage: python3 scripts/machine_learning/make_features.py
"""

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VAR_CSV = REPO / "data/processed/mutations/tp53_variant_dataset.csv"
WT_FILE = REPO / "data/processed/protein/WT_TP53_ORF1_393aa.fasta"
WT_CIF = REPO / "structures/alphafold/wt/selected/wt_selected.cif"
OUT_CSV = REPO / "data/processed/structural_features/tp53_features.csv"
OUT_DEF = REPO / "data/processed/structural_features/feature_definitions.md"

# --- amino-acid property tables (standard published values) ---
# Kyte-Doolittle hydropathy; Zamyatnin volumes (A^3); charge at pH 7;
# Grantham composition (c), polarity (p), volume (v) - Grantham 1974.
HYDRO = {"A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "E": -3.5,
         "Q": -3.5, "G": -0.4, "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9,
         "M": 1.9, "F": 2.8, "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9,
         "Y": -1.3, "V": 4.2}
VOLUME = {"A": 88.6, "R": 173.4, "N": 114.1, "D": 111.1, "C": 108.5,
          "E": 138.4, "Q": 143.9, "G": 60.1, "H": 153.2, "I": 166.7,
          "L": 166.7, "K": 168.6, "M": 162.9, "F": 189.9, "P": 112.7,
          "S": 89.0, "T": 116.1, "W": 227.8, "Y": 193.6, "V": 140.0}
CHARGE = {"A": 0, "R": 1, "N": 0, "D": -1, "C": 0, "E": -1, "Q": 0,
          "G": 0, "H": 1, "I": 0, "L": 0, "K": 1, "M": 0, "F": 0,
          "P": 0, "S": 0, "T": 0, "W": 0, "Y": 0, "V": 0}
GRANTHAM = {  # c, p, v
    "A": (1.80, 8.1, 31), "R": (2.56, 10.5, 124), "N": (2.05, 11.6, 56),
    "D": (1.89, 13.0, 54), "C": (2.75, 5.5, 55), "E": (1.97, 12.3, 83),
    "Q": (2.18, 10.5, 85), "G": (0.74, 9.0, 3), "H": (2.51, 10.4, 96),
    "I": (2.36, 5.2, 111), "L": (2.00, 4.9, 111), "K": (2.29, 11.3, 119),
    "M": (2.71, 5.7, 105), "F": (2.44, 5.2, 132), "P": (2.23, 8.0, 32),
    "S": (1.96, 9.2, 32), "T": (2.16, 8.6, 61), "W": (2.83, 5.4, 170),
    "Y": (2.67, 6.2, 136), "V": (1.91, 5.9, 84)}


def grantham_dist(a, b):
    """Grantham 1974 distance: rho*sqrt(alpha*dc^2 + beta*dp^2 + gamma*dv^2)
    with alpha=1.833, beta=0.1018, gamma=0.000399, rho=50.723 (Table 2 scale,
    mean pairwise distance 100). Sanity: R-H = 28.6 (~29 published)."""
    ca, pa, va = GRANTHAM[a]
    cb, pb, vb = GRANTHAM[b]
    import math
    return 50.723 * math.sqrt(1.833 * (ca - cb) ** 2
                              + 0.1018 * (pa - pb) ** 2
                              + 0.000399 * (va - vb) ** 2)


# P04637 domain architecture (UniProt annotation, disordered termini flank
# structured core; DNA-binding domain ~94-292 per repo biological_background.md)
DOMAINS = [
    ("dom_TAD1", 1, 42), ("dom_TAD2", 43, 61), ("dom_PRR", 62, 93),
    ("dom_DBD", 94, 292), ("dom_hinge", 293, 325), ("dom_TET", 326, 356),
    ("dom_CTD", 357, 393),
]
ZN_LIGANDS = (176, 179, 238, 242)  # zinc-coordinating residues, core domain
# Approximate literature DNA-contact positions in the core domain (p53-DNA
# complex PDB 1TUP, Cho et al. 1994: contacts incl. K120, S241, R248, R273,
# R280, R282). Binary proximity flag only - never a pathogenicity claim.
DNA_CONTACT = {120, 241, 248, 273, 280, 282}


def read_seq(path):
    return "".join(l.strip() for l in path.read_text().splitlines()
                    if l.strip() and not l.startswith(">"))


def read_plddt(cif_path):
    """Per-residue CA pLDDT from an AlphaFold mmCIF (B-factor column)."""
    wanted = ["label_seq_id", "label_atom_id", "B_iso_or_equiv"]
    cols, idx, vals = [], {}, []
    in_loop = False
    for line in cif_path.read_text().splitlines():
        s = line.strip()
        if s == "loop_":
            in_loop, cols, idx, vals = True, [], {}, []
            continue
        if in_loop and s.startswith("_atom_site."):
            cols.append(s.split(".")[1])
            continue
        if in_loop and cols and s and not s.startswith("_") and s != "loop_":
            if s.startswith("ATOM") or s[0].isdigit():
                parts = s.split()
                if len(parts) < len(cols):
                    continue
                if not idx:
                    for w in wanted:
                        if w not in cols:
                            raise ValueError(f"{w} not in atom_site loop")
                        idx[w] = cols.index(w)
                vals.append((int(parts[idx["label_seq_id"]]),
                             parts[idx["label_atom_id"]],
                             float(parts[idx["B_iso_or_equiv"]])))
            elif s.startswith("#") or s.startswith("data_"):
                in_loop = False
    plddt = {}
    for seq_id, atom, b in vals:
        if atom == "CA":
            plddt[seq_id] = b
    return plddt


FEATURES = (["pos_norm", "in_core"]
            + [d[0] for d in DOMAINS]
            + ["dist_to_zn", "grantham", "d_hydro", "d_volume", "d_charge",
               "d_polarity", "ref_hydro", "ref_volume", "ref_charge",
               "plddt_at_pos", "plddt_window5", "dna_contact"])


def featurize(pos, ref, alt, plddt):
    dom = [1 if lo <= pos <= hi else 0 for _, lo, hi in DOMAINS]
    window = [plddt.get(p, 0.0) for p in range(pos - 5, pos + 6) if p in plddt]
    return {
        "pos_norm": round(pos / 393, 4),
        "in_core": 1 if 94 <= pos <= 292 else 0,
        **{d[0]: v for d, v in zip(DOMAINS, dom)},
        "dist_to_zn": round(min(abs(pos - z) for z in ZN_LIGANDS) / 393, 4),
        "grantham": round(grantham_dist(ref, alt), 3),
        "d_hydro": round(HYDRO[alt] - HYDRO[ref], 3),
        "d_volume": round(VOLUME[alt] - VOLUME[ref], 3),
        "d_charge": CHARGE[alt] - CHARGE[ref],
        "d_polarity": round(GRANTHAM[alt][1] - GRANTHAM[ref][1], 3),
        "ref_hydro": HYDRO[ref],
        "ref_volume": VOLUME[ref],
        "ref_charge": CHARGE[ref],
        "plddt_at_pos": round(plddt.get(pos, 0.0), 2),
        "plddt_window5": round(sum(window) / len(window), 2) if window else 0.0,
        "dna_contact": 1 if pos in DNA_CONTACT else 0,
    }


def main():
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    wt = read_seq(WT_FILE)
    plddt = read_plddt(WT_CIF)
    assert len(plddt) == 393, f"pLDDT residues {len(plddt)} != 393"
    core_mean = sum(plddt[p] for p in range(94, 293)) / 199
    print(f"pLDDT parsed: {len(plddt)} residues; core(94-292) mean={core_mean:.2f} "
          f"(expected ~97.89 for model_4)")

    with open(VAR_CSV) as f:
        variants = list(csv.DictReader(f))
    rows = []
    for v in variants:
        pos, ref, alt = int(v["pos"]), v["ref"], v["alt"]
        assert wt[pos - 1] == ref, f"WT mismatch {v['hgvs_p']}"
        feat = featurize(pos, ref, alt, plddt)
        rows.append({**{k: v[k] for k in
                        ("variant_id", "hgvs_p", "pos", "ref", "alt", "label")},
                     **feat})

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["variant_id", "hgvs_p", "pos",
                                          "ref", "alt", "label"] + FEATURES)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    n1 = sum(r["label"] == "1" for r in rows)
    print(f"variants={len(rows)} pathogenic={n1} benign={len(rows) - n1} "
          f"features={len(FEATURES)} missing=0")
    OUT_DEF.write_text(DEFINITIONS)
    print(f"Wrote {OUT_CSV} + feature_definitions.md")


DEFINITIONS = """# Feature definitions (tp53_features.csv)

Target `label`: 1 = ClinVar Pathogenic/Likely pathogenic, 0 = Benign/Likely
benign germline classification. VUS/conflicting/unclassified excluded upstream.

| Feature | Meaning | Source |
|---|---|---|
| pos_norm | TP53 protein position / 393 | variant |
| in_core | 1 if position 94-292 (structured DNA-binding domain) | UniProt P04637 architecture |
| dom_TAD1/TAD2/PRR/DBD/hinge/TET/CTD | one-hot domain (1-42/43-61/62-93/94-292/293-325/326-356/357-393) | UniProt P04637 |
| dist_to_zn | min distance to Zn ligands (176/179/238/242) / 393 | core-domain chemistry |
| grantham | Grantham 1974 physicochemical distance ref->alt | Grantham et al. 1974 |
| d_hydro/d_volume/d_charge/d_polarity | alt-minus-ref property deltas (Kyte-Doolittle; Zamyatnin vol; pH7 charge; Grantham polarity) | standard AA tables |
| ref_hydro/ref_volume/ref_charge | WT residue context at the site | standard AA tables |
| plddt_at_pos | AlphaFold WT pLDDT at the position (order proxy) | structures/alphafold/wt/selected/wt_selected.cif |
| plddt_window5 | mean pLDDT over +/-5 residues | same |
| dna_contact | 1 if position in literature DNA-contact set {120,241,248,273,280,282} (p53-DNA complex 1TUP) | literature flag |

Leakage statement: no feature uses the label or any ClinVar-derived
statistic; all are computable at prediction time from (pos, ref, alt) + the
frozen WT reference. Preprocessing statistics (scaling) are fit on train only
(see train.py).
"""

if __name__ == "__main__":
    main()
