"""Scaffold: generate validated mutant protein sequences from verified WT.

NOT READY TO RUN — requires a documented variant source in
data/metadata/variant_sources.csv first. When ready, provide variants as
(name, position_1indexed, ref_aa, alt_aa); the generator verifies the WT
residue, checks length, writes data/processed/mutations/<name>.fasta, and
ABORTS on any WT-residue mismatch instead of silently editing.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WT_FILE = REPO / "data/processed/protein/WT_TP53_ORF1_393aa.fasta"
OUT_DIR = REPO / "data/processed/mutations"


def read_seq(path: Path) -> str:
    return "".join(l.strip() for l in path.read_text().splitlines()
                   if l.strip() and not l.startswith(">"))


def make_mutant(wt: str, name: str, pos: int, ref: str, alt: str) -> str:
    if not 1 <= pos <= len(wt):
        raise ValueError(f"{name}: position {pos} out of range (len {len(wt)})")
    if wt[pos - 1] != ref:
        raise ValueError(f"{name}: expected WT residue {ref} at {pos}, "
                         f"found {wt[pos - 1]} — STOPPING, check annotation/reference.")
    mut = wt[:pos - 1] + alt + wt[pos:]
    assert len(mut) == len(wt)
    return mut


def main() -> None:
    raise SystemExit("No variant source documented yet — see "
                     "data/metadata/variant_sources.csv. Refusing to invent mutations.")


if __name__ == "__main__":
    main()
