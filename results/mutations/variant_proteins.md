# Results: variant proteins (real mutant sequences)

Inventory: **388 mutant protein sequences**, each exactly 393 aa (single validated substitution on the verified WT; all sequences unique). Source: `data/processed/mutations/mutant_sequences.fasta` (+ `.csv` with length/MD5 per variant). These are exact sequence constructs — no mutant 3D structure is claimed or predicted here.

## Demo variants: WT vs mutant sequence windows (±7 aa)

### p.R175H — ClinVar Pathogenic → model Pathogenic-associated (p=0.99) ✓

Domain DBD (core 94–292) · WT pLDDT 98.82 · Grantham 28.622 · Δcharge 0 · Δhydropathy 1.3
```
WT    168 HMTEVVRRCPHHERC 182
                  ^ 175
mutant168 HMTEVVRHCPHHERC 182
```

### p.R248Q — ClinVar Pathogenic → model Pathogenic-associated (p=0.9875) ✓

Domain DBD (core 94–292) · WT pLDDT 98.48 · Grantham 47.354 · Δcharge -1 · Δhydropathy 1.0
```
WT    241 SCMGGMNRRPILTII 255
                  ^ 248
mutant241 SCMGGMNQRPILTII 255
```

### p.R248W — ClinVar Pathogenic → model Pathogenic-associated (p=0.9975) ✓

Domain DBD (core 94–292) · WT pLDDT 98.48 · Grantham 96.583 · Δcharge -1 · Δhydropathy 3.6
```
WT    241 SCMGGMNRRPILTII 255
                  ^ 248
mutant241 SCMGGMNWRPILTII 255
```

### p.R273H — ClinVar Pathogenic → model Pathogenic-associated (p=0.9625) ✓

Domain DBD (core 94–292) · WT pLDDT 98.9 · Grantham 28.622 · Δcharge 0 · Δhydropathy 1.3
```
WT    266 GRNSFEVRVCACPGR 280
                  ^ 273
mutant266 GRNSFEVHVCACPGR 280
```

### p.Y220C — ClinVar Pathogenic → model Pathogenic-associated (p=0.97) ✓

Domain DBD (core 94–292) · WT pLDDT 98.81 · Grantham 83.029 · Δcharge 0 · Δhydropathy 3.8
```
WT    213 RHSVVVPYEPPEVGS 227
                  ^ 220
mutant213 RHSVVVPCEPPEVGS 227
```

### p.G245S — ClinVar Pathogenic → model Pathogenic-associated (p=0.97) ✓

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
| p.E326V | Likely pathogenic | 0.0625 | outside core domain (atypical for its class) |
| p.L344R | Likely pathogenic | 0.4725 | outside core domain (atypical for its class) |
| p.R337L | Likely pathogenic | 0.49 | outside core domain (atypical for its class) |
| p.G293W | Likely benign | 0.5075 | outside core domain (atypical for its class) |
| p.R333C | Likely benign | 0.515 | outside core domain (atypical for its class) |
| p.C124S | Likely benign | 0.66 | core hotspot pattern shared by both classes |
| p.E287G | Likely benign | 0.675 | core hotspot pattern shared by both classes |
| p.V157I | Likely benign | 0.7975 | small physicochemical shift (Grantham 42.798) |
| p.L111V | Likely benign | 0.8175 | small physicochemical shift (Grantham 32.38) |
| p.G108S | Likely benign | 0.8375 | core hotspot pattern shared by both classes |
| p.E204D | Likely benign | 0.8625 | small physicochemical shift (Grantham 31.966) |
| p.M160I | Likely benign | 0.9375 | small physicochemical shift (Grantham 26.08) |

Cohort figures: `figures/machine_learning/position_enrichment.png`, `plddt_by_class.png`, `substitution_counts.png`. Full per-variant predictions: `results/machine_learning/all_predictions.csv`.

Reading: pathogenic labels concentrate in the ordered core (position_enrichment), benign outside it — the model learns this real biological enrichment; errors cluster where the pattern breaks (disordered-region pathogenic or core benign variants). Association only.
