# Research questions

None of these questions is answered until the cited analysis exists.

## RQ1 — Sequence reproducibility (ANSWERED 2026-09-18)

Can a reproducible WT TP53 protein sequence be obtained and verified from the
selected TP53 CDS (NM_001126112.3:140–1321)?

- Yes: ORF1 translation (393 aa) is 100% identical to live UniProt P04637
  (SV=4, retrieved 2026-09-18). Evidence:
  `results/sequence/sequence_verification.md`.

## RQ2 — Structural plausibility (ANSWERED quantitatively 2026-09-18)

Can AlphaFold generate a structurally plausible WT TP53 model that can be
quantitatively compared with experimentally determined TP53 data?

- Yes: all five WT models agree with 2OCJ (X-ray, 2.05 Å) at 0.37–0.67 Å
  CA-RMSD over 194 aligned residues (96–289) at 100% identity. Caveats:
  comparison restricted to the core domain; prediction used templates so this
  is consistency, not blind validation; PyMOL cross-check pending. Evidence:
  `results/structure/wt_validation.md`.

## RQ3 — Variant effects (NOT STARTED)

How do selected TP53 variants alter sequence-derived and structure-derived
features relative to the WT reference?

- Blocked on: WT baseline finalisation + documented variant source.

## RQ4 — ML classification (NOT STARTED)

Can sequence and structural features provide useful information for
computational classification of curated TP53 variant annotations?

- Framed as an information/classification question, not a causal claim.

## RQ5 — Explainability (NOT STARTED)

Which features contribute most strongly to the model's predictions?

- Association only; feature importance must never be reported as mechanism.
