# Results: WT vs mutant comparison (demo variants)

Features from the frozen WT reference (verified 393-aa sequence + selected AlphaFold model_4 pLDDT); predictions from results/machine_learning/model.joblib. Labels are ClinVar germline classifications (curated annotations, not model output).

| Variant | ClinVar (VCV) | Domain | pLDDT@pos | Grantham | d_charge | Prediction (p) |
|---|---|---|---|---|---|---|
| p.R175H | Pathogenic (VCV000012374) | DBD | 98.82 | 28.622 | 0 | Pathogenic-associated (0.99) |
| p.R248Q | Pathogenic (VCV000012356) | DBD | 98.48 | 47.354 | -1 | Pathogenic-associated (0.9875) |
| p.R248W | Pathogenic (VCV000012347) | DBD | 98.48 | 96.583 | -1 | Pathogenic-associated (0.9975) |
| p.R273H | Pathogenic (VCV000012366) | DBD | 98.9 | 28.622 | 0 | Pathogenic-associated (0.9625) |
| p.Y220C | Pathogenic (VCV000127819) | DBD | 98.81 | 83.029 | 0 | Pathogenic-associated (0.97) |
| p.G245S | Pathogenic (VCV000012365) | DBD | 98.18 | 88.843 | 0 | Pathogenic-associated (0.97) |
| p.P72R | Benign (VCV000012351) | PRR | 38.33 | 104.112 | 1 | Benign-associated (0.0025) |

Reading: core-domain (DBD) pathogenic variants sit in high-pLDDT ordered regions with large physicochemical shifts (e.g. R->H/Q/W charge change); the benign P72R sits outside the core. Association only - structural difference never proves causation.
