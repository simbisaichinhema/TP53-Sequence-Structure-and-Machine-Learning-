"""Build real mutant protein sequences from the verified WT + ClinVar dataset.

Every mutant = WT 393-aa sequence with exactly one validated substitution.
WT residue re-verified at each position; aborts on mismatch (same rule as
scripts/mutation/generate_mutants.py). No invented variants, no predicted
structures claimed — sequences only.

Inputs:  data/processed/protein/WT_TP53_ORF1_393aa.fasta
         data/processed/mutations/tp53_variant_dataset.csv
Outputs: data/processed/mutations/mutant_sequences.fasta (multi-FASTA, one
  per labelled variant)
         data/processed/mutations/mutant_sequences.csv (id, hgvs, len, md5)

Usage: python3 scripts/mutation/build_mutant_sequences.py
"""

import csv
import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "mutation"))
from generate_mutants import make_mutant, read_seq  # noqa: E402

WT_FILE = REPO / "data/processed/protein/WT_TP53_ORF1_393aa.fasta"
VAR_CSV = REPO / "data/processed/mutations/tp53_variant_dataset.csv"
OUT_FA = REPO / "data/processed/mutations/mutant_sequences.fasta"
OUT_CSV = REPO / "data/processed/mutations/mutant_sequences.csv"


def main():
    wt = read_seq(WT_FILE)
    with open(VAR_CSV) as f:
        variants = list(csv.DictReader(f))
    fa_lines, rows = [], []
    for v in variants:
        pos, ref, alt = int(v["pos"]), v["ref"], v["alt"]
        mut = make_mutant(wt, v["hgvs_p"], pos, ref, alt)  # validates + asserts len
        fa_lines.append(f">{v['variant_id']}|{v['hgvs_p']}|{v['classification']}")
        fa_lines += [mut[i:i + 70] for i in range(0, len(mut), 70)]
        rows.append({"variant_id": v["variant_id"], "hgvs_p": v["hgvs_p"],
                     "length": len(mut),
                     "md5": hashlib.md5(mut.encode()).hexdigest()})
    assert all(r["length"] == 393 for r in rows)
    assert len({r["md5"] for r in rows}) == len(rows), "duplicate mutant sequences!"
    OUT_FA.write_text("\n".join(fa_lines) + "\n")
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["variant_id", "hgvs_p", "length", "md5"])
        w.writeheader()
        w.writerows(rows)
    n1 = sum(1 for v in variants if v["label"] == "1")
    print(f"mutants={len(rows)} (P={n1} B={len(rows)-n1}), all 393 aa, all unique")
    print(f"Wrote {OUT_FA.name} + {OUT_CSV.name}")


if __name__ == "__main__":
    main()
