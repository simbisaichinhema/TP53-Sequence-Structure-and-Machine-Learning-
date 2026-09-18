# File audit: TP53 root → repository (2026-09-18)

All loose files formerly in the `TP53/` workspace root were checksum-verified
(MD5, 29 files + 6 extracted files, zero mismatches) and moved into the
repository paths below. The workspace root now contains only
`TP53-Mutation-Analysis/`. Nothing was deleted without a verified copy.

## AlphaFold Server output bundle (job `fold_tp53_predicted_protein`, seed 555867540)

| Original root file(s) | Repository destination | Purpose |
|---|---|---|
| `fold_tp53_predicted_protein.zip` (1.69 MB, 24 entries: 12 JSON / 9 CIF / 2 A3M / 1 MD) | `structures/alphafold/wt/raw/fold_tp53_predicted_protein.zip` | Original download artefact; superset of the extracted files below |
| `fold_tp53_predicted_protein_model_{0..4}.cif` | `structures/alphafold/wt/raw/` (same names) | The 5 predicted WT models (393 aa each); all preserved, none deleted |
| `fold_tp53_predicted_protein_full_data_{0..4}.json` | `structures/alphafold/wt/raw/` (same names) | Per-atom pLDDT, 393×393 PAE, contact probabilities, token maps |
| `fold_tp53_predicted_protein_summary_confidences_{0..4}.json` | `structures/alphafold/wt/confidence/` (same names) | ranking_score 0.8 / ptm 0.55 / fraction_disordered 0.5 (all models) |
| `fold_tp53_predicted_protein_job_request.json` | `structures/alphafold/wt/confidence/` (same name) | Input sequence, seed, template-enabled setting, AF version |
| `msas/fold_tp53_predicted_protein_paired_msa_chains_a.a3m` (2.25 MB) | `structures/alphafold/wt/inputs/msas/` (same name) | Paired chain-A multiple sequence alignment used at prediction |
| `msas/fold_tp53_predicted_protein_unpaired_msa_chains_a.a3m` (1.12 MB) | `structures/alphafold/wt/inputs/msas/` (same name) | Unpaired chain-A MSA used at prediction |
| `templates/fold_tp53_predicted_protein_template_hits_chains_a_query_to_hit.json` | `structures/alphafold/wt/inputs/templates/` (same name) | Query→template residue index mapping |
| `templates/fold_tp53_predicted_protein_template_hit_{0..3}_chains_a.cif` | `structures/alphafold/wt/inputs/templates/` (same names) | Structural templates actually used, by PDB ID: hit_0 = **5XZC**, hit_1 = **6RZ3**, hit_2 = **4QO1**, hit_3 = **2WGX** (all p53 core-domain structures) |
| `terms_of_use.md` | `structures/alphafold/wt/terms_of_use.md` | AlphaFold Server Output Terms of Use (governs all prediction data) |

Implication recorded for RQ2: the prediction used experimental templates from
the same p53 core-domain fold family, so WT-vs-2OCJ agreement (0.37–0.67 Å)
is consistency with known structural data, not independent blind prediction.

## Sequence / CDS files

| Original root file(s) | Repository destination | Purpose |
|---|---|---|
| `TP53 CDS data` (17 KB; verified ZIP archive by PK header/`zipfile`) | `data/raw/tp53_cds/TP53 CDS data` (original name kept) | Original NCBI CDS download artefact (6 entries: README, md5sum, cds.fna, data/catalog/product reports) |
| `TP53 CDS data~/` (extracted copy; `cds.fna` MD5-identical to the zipped copy) | `data/raw/tp53_cds/ncbi_dataset/` | Working copy of the 25-transcript CDS set incl. NM_001126112.3 |
| `ORF1.fa` | `data/processed/protein/WT_TP53_ORF1_393aa.fasta` | Translated ORF1 (393 aa); formally verified vs live P04637 |
| `TP53.fasta` (header `sp\|P04637\|…`) | `data/raw/tp53_cds/TP53_P04637_reference_local.fasta` | Pre-existing local reference copy (superseded by live retrieval `P04637_uniprot_live_20260918.fasta`) |
| `tp53.txt` (same sequence as `TP53.fasta`) | `data/raw/tp53_cds/tp53_local_copy.fasta` | Duplicate local copy, kept for traceability |

## Best (representative) model

**model_4** → `structures/alphafold/wt/selected/wt_selected.cif`.
Basis: highest core-region (94–292) mean pLDDT (97.89); all five models
effectively equivalent (spread 97.79–97.89; RMSD 0.37–0.67 Å vs 2OCJ for all).
Full rationale: `results/structure/wt_validation.md`;
selection record: `structures/alphafold/wt/selected/README.md`.
