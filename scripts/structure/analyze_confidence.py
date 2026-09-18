"""Summarise AlphaFold WT confidence from preserved local files.

Reads structures/alphafold/wt/raw/full_data_*.json (atom pLDDT, PAE) and
model_*.cif B-factors (per-residue pLDDT), plus
structures/alphafold/wt/confidence/summary_confidences_*.json.
Prints the table recorded in results/structure/alphafold_confidence.md.
"""
import json
import statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "structures/alphafold/wt/raw"
CONF = REPO / "structures/alphafold/wt/confidence"


def residue_plddts(cif: Path) -> list[float]:
    res: dict[int, list[float]] = defaultdict(list)
    for line in cif.read_text().splitlines():
        if line.startswith("ATOM"):
            p = line.split()
            res[int(p[8])].append(float(p[14]))
    return [sum(v) / len(v) for _, v in sorted(res.items())]


def main() -> None:
    for i in range(5):
        d = json.loads((RAW / f"fold_tp53_predicted_protein_full_data_{i}.json").read_text())
        s = json.loads((CONF / f"fold_tp53_predicted_protein_summary_confidences_{i}.json").read_text())
        vals = residue_plddts(RAW / f"fold_tp53_predicted_protein_model_{i}.cif")
        pae = [x for row in d["pae"] for x in row]
        atom = d["atom_plddts"]
        print(f"model_{i}: rank={s['ranking_score']} ptm={s['ptm']} "
              f"disordered={s['fraction_disordered']} clash={s['has_clash']}")
        print(f"  res_plddt mean={sum(vals)/len(vals):.2f} "
              f"median={statistics.median(vals):.2f} "
              f"frac>70={sum(1 for x in vals if x > 70)/len(vals):.3f} "
              f"frac>90={sum(1 for x in vals if x > 90)/len(vals):.3f} "
              f"frac<50={sum(1 for x in vals if x < 50)/len(vals):.3f}")
        print(f"  atom_plddt mean={sum(atom)/len(atom):.2f} "
              f"pae mean={sum(pae)/len(pae):.2f}")


if __name__ == "__main__":
    main()
