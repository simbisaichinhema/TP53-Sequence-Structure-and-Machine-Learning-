# Results: sequence verification

Status: COMPLETED (formal live verification performed 2026-09-18).

## What was measured

Local comparison of the translated ORF1 product
(`data/processed/protein/WT_TP53_ORF1_393aa.fasta`) against the live UniProt
retrieval below, using `scripts/sequence/verify_sequence.py --reference
data/raw/tp53_cds/P04637_uniprot_live_20260918.fasta`:

- Accession: sp|P04637|P53_HUMAN Cellular tumor antigen p53, Homo sapiens,
  GN=TP53, PE=1, SV=4
- Source: live retrieval from https://rest.uniprot.org/uniprotkb/P04637.fasta
  on 2026-09-18 (stored verbatim as
  `data/raw/tp53_cds/P04637_uniprot_live_20260918.fasta`)
- ORF translation length: 393 aa
- UniProt reference length: 393 aa
- Sequence identity: 100% (393/393 residues)
- Sequence differences: none
- N-terminus: MEEPQSDPSV…
- C-terminus: …KTEGPDSD
- Spot check relevant to downstream hotspot notation: position 175 (1-indexed)
  = R (consistent with the format of the R175H annotation; no variant claim made)

## Interpretation

The 393-aa ORF translation is formally verified against live UniProt P04637
(SV=4): the selected sequence corresponds to the intended canonical human
TP53 reference. RQ1 is answered for the WT sequence.

## Outstanding

- None for WT verification. Downstream mutant generation must re-verify the
  expected WT residue at each variant position before substitution.
