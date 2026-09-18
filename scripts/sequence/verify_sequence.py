"""Verify the translated WT TP53 ORF product against a reference FASTA.

Compares data/processed/protein/WT_TP53_ORF1_393aa.fasta against a reference
(default: the locally held P04637-labelled copy). To complete formal
verification, retrieve live UniProt P04637, save it, and pass it as
--reference. Exits non-zero on any mismatch so it can gate downstream steps.
"""
import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read_seq(path: Path) -> tuple[str, str]:
    header, seq = "", []
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            header = line
        elif line.strip():
            seq.append(line.strip())
    return header, "".join(seq)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default=str(REPO / "data/processed/protein/WT_TP53_ORF1_393aa.fasta"))
    ap.add_argument("--reference", default=str(REPO / "data/raw/tp53_cds/TP53_P04637_reference_local.fasta"))
    args = ap.parse_args()

    qh, q = read_seq(Path(args.query))
    rh, r = read_seq(Path(args.reference))
    print(f"query: {qh} len={len(q)}")
    print(f"reference: {rh} len={len(r)}")
    matches = sum(a == b for a, b in zip(q, r))
    print(f"identity: {matches}/{max(len(q), len(r))} "
          f"({100 * matches / max(len(q), len(r)):.2f}%)")
    diffs = [(i + 1, a, b) for i, (a, b) in enumerate(zip(q, r)) if a != b]
    if len(q) != len(r):
        print(f"LENGTH MISMATCH: {len(q)} vs {len(r)}")
    for pos, a, b in diffs[:20]:
        print(f"  pos {pos}: query {a} vs ref {b}")
    print(f"N-terminus: {q[:10]}  C-terminus: {q[-10:]}")
    print(f"position 175 (1-indexed): {q[174] if len(q) >= 175 else 'NA'}")
    if q != r:
        raise SystemExit("MISMATCH — sequences differ; see above.")
    print("OK — sequences identical.")


if __name__ == "__main__":
    main()
