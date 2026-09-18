# Protocol: sequence processing

## 1. CDS retrieval (COMPLETED)

- Source: NCBI Datasets CDS FASTA (`data/raw/tp53_cds/ncbi_dataset/…/cds.fna`,
  25 TP53 transcripts) + `data_report.jsonl`.
- Selected: NM_001126112.3:140–1321 (1182 nt), GeneID 7157.
- Verification step: extract the NM_001126112.3 record, confirm length 1182.

## 2. ORF identification (COMPLETED)

- Tool/settings: ORF Finder; From 1, To 1182, minimum ORF length 100 aa,
  standard genetic code.
- Selected: ORF1, strand +, frame 1, 1–1182, 393 aa.

## 3. Translation (COMPLETED)

- Product starts MEEPQSDPSV…, length 393 aa.
- Stored: `data/processed/protein/WT_TP53_ORF1_393aa.fasta`.

## 4. Verification (IN PROGRESS)

- Local cross-check vs P04637-labelled FASTA: 100% identity over 393 aa —
  see `results/sequence/sequence_verification.md`.
- Formal step still required: live UniProt P04637 retrieval (record accession,
  length, retrieval date), then re-run `scripts/sequence/verify_sequence.py`
  against the live file and record identity/differences.
- Reproduce: `python scripts/sequence/verify_sequence.py`.
