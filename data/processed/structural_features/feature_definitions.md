# Feature definitions (tp53_features.csv)

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
