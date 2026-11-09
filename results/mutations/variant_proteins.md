# Results: variant proteins (real mutant sequences)

Inventory: **818 mutant protein sequences**, each exactly 393 aa (single validated substitution on the verified WT; all sequences unique). Source: `data/processed/mutations/mutant_sequences.fasta` (+ `.csv` with length/MD5 per variant). These are exact sequence constructs — no mutant 3D structure is claimed or predicted here.

## Demo variants: WT vs mutant sequence windows (±7 aa)

### p.R175H — ClinVar Pathogenic → model Pathogenic-associated (p=0.8275) ✓

Domain DBD (core 94–292) · WT pLDDT 98.82 · Grantham 28.622 · Δcharge 0 · Δhydropathy 1.3
```
WT    168 HMTEVVRRCPHHERC 182
                  ^ 175
mutant168 HMTEVVRHCPHHERC 182
```

### p.R248Q — ClinVar Pathogenic → model Pathogenic-associated (p=0.9575) ✓

Domain DBD (core 94–292) · WT pLDDT 98.48 · Grantham 47.354 · Δcharge -1 · Δhydropathy 1.0
```
WT    241 SCMGGMNRRPILTII 255
                  ^ 248
mutant241 SCMGGMNQRPILTII 255
```

### p.R248W — ClinVar Pathogenic → model Pathogenic-associated (p=0.98) ✓

Domain DBD (core 94–292) · WT pLDDT 98.48 · Grantham 96.583 · Δcharge -1 · Δhydropathy 3.6
```
WT    241 SCMGGMNRRPILTII 255
                  ^ 248
mutant241 SCMGGMNWRPILTII 255
```

### p.R273H — ClinVar Pathogenic → model Pathogenic-associated (p=0.935) ✓

Domain DBD (core 94–292) · WT pLDDT 98.9 · Grantham 28.622 · Δcharge 0 · Δhydropathy 1.3
```
WT    266 GRNSFEVRVCACPGR 280
                  ^ 273
mutant266 GRNSFEVHVCACPGR 280
```

### p.Y220C — ClinVar Pathogenic → model Pathogenic-associated (p=0.9825) ✓

Domain DBD (core 94–292) · WT pLDDT 98.81 · Grantham 83.029 · Δcharge 0 · Δhydropathy 3.8
```
WT    213 RHSVVVPYEPPEVGS 227
                  ^ 220
mutant213 RHSVVVPCEPPEVGS 227
```

### p.G245S — ClinVar Pathogenic → model Pathogenic-associated (p=0.9725) ✓

Domain DBD (core 94–292) · WT pLDDT 98.18 · Grantham 88.843 · Δcharge 0 · Δhydropathy -0.4
```
WT    238 CNSSCMGGMNRRPIL 252
                  ^ 245
mutant238 CNSSCMGSMNRRPIL 252
```

### p.P72R — ClinVar Benign → model Benign-associated (p=0.0025) ✓

Domain outside core · WT pLDDT 38.33 · Grantham 104.112 · Δcharge 1 · Δhydropathy -2.9
```
WT     65 RMPEAAPPVAPAPAA  79
                  ^ 72
mutant 65 RMPEAAPRVAPAPAA  79
```

## Test-set error analysis (honest mistakes, n=12)

Every held-out variant the model got wrong, with the context that explains the difficulty:

| Variant | ClinVar | Model p(pathogenic) | Why it is hard |
|---|---|---|---|
| p.P27L | Uncertain significance | 0.0 | outside core domain (atypical for its class); low pLDDT 48.01 (disordered region) |
| p.A119G | Likely pathogenic | 0.09 | core hotspot pattern shared by both classes |
| p.T211P | Pathogenic | 0.2275 | small physicochemical shift (Grantham 31.317) |
| p.R342P | Pathogenic | 0.245 | outside core domain (atypical for its class) |
| p.G187R | Pathogenic | 0.3175 | core hotspot pattern shared by both classes |
| p.G334W | Likely pathogenic | 0.4075 | outside core domain (atypical for its class) |
| p.E204D | Likely benign | 0.575 | small physicochemical shift (Grantham 31.966) |
| p.V157I | Likely benign | 0.585 | small physicochemical shift (Grantham 42.798) |
| p.D148Y | Uncertain significance | 0.6175 | core hotspot pattern shared by both classes |
| p.L111V | Likely benign | 0.67 | small physicochemical shift (Grantham 32.38) |
| p.R283C | Likely benign | 0.6725 | core hotspot pattern shared by both classes |
| p.P128T | Uncertain significance | 0.6825 | small physicochemical shift (Grantham 31.317) |
| p.P222S | Likely benign | 0.6925 | small physicochemical shift (Grantham 26.851) |
| p.V217M | Likely benign | 0.7325 | small physicochemical shift (Grantham 59.004) |
| p.L145V | Uncertain significance | 0.745 | small physicochemical shift (Grantham 32.38) |
| p.A129D | Benign | 0.7575 | core hotspot pattern shared by both classes |
| p.H214Q | Likely benign | 0.885 | small physicochemical shift (Grantham 25.306) |
| p.S269C | Benign | 0.9825 | core hotspot pattern shared by both classes |

Cohort figures: `figures/machine_learning/position_enrichment.png`, `plddt_by_class.png`, `substitution_counts.png`. Full per-variant predictions: `results/machine_learning/all_predictions.csv`.

Reading: pathogenic labels concentrate in the ordered core (position_enrichment), benign outside it — the model learns this real biological enrichment; errors cluster where the pattern breaks (disordered-region pathogenic or core benign variants). Association only.
