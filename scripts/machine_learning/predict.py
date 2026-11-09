"""Inference for the trained TP53 pathogenicity model.

Single source of featurization: imports from make_features.py, so training
and prediction can never diverge. Preprocessing (scaling) comes from the
saved sklearn Pipeline itself.

Default model: results/machine_learning/model.joblib (baseline RF from
train.py). Any benchmark artefact can be selected with --model, e.g.
  python3 scripts/machine_learning/predict.py \
      --model results/machine_learning/benchmark/models/svm.joblib R 175 H

Usage:
  python3 scripts/machine_learning/predict.py R 175 H
  python3 scripts/machine_learning/predict.py --pos 248 --ref R --alt Q
  python3 scripts/machine_learning/predict.py --model PATH R 175 H
Returns JSON on stdout; exit code 2 on invalid input (no stack trace).
"""

import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_features import DOMAINS, featurize, read_plddt, read_seq

AA3_TO_1 = {"Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D", "Cys": "C",
            "Glu": "E", "Gln": "Q", "Gly": "G", "His": "H", "Ile": "I",
            "Leu": "L", "Lys": "K", "Met": "M", "Phe": "F", "Pro": "P",
            "Ser": "S", "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V"}

REPO = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = REPO / "results/machine_learning/model.joblib"
WT_FILE = REPO / "data/processed/protein/WT_TP53_ORF1_393aa.fasta"
WT_CIF = REPO / "structures/alphafold/wt/selected/wt_selected.cif"

VALID_AA = set("ARNDCQEGHILKMFPSTWYV")


@lru_cache(maxsize=4)
def _bundle_cached(model_path: str):
    b = joblib.load(model_path)
    wt = read_seq(WT_FILE)
    plddt = read_plddt(WT_CIF)
    return b, wt, plddt


def _bundle(model_path=None):
    if model_path is None:
        path = Path(DEFAULT_MODEL)
    else:
        path = Path(model_path)
        if not path.is_absolute() and not path.exists():
            path = REPO / path
    path = path.resolve()
    if not path.exists():
        raise ValueError(f"Model file not found: {path}")
    return _bundle_cached(str(path))


def _norm_aa(s):
    s = (s or "").strip()
    if len(s) == 3:
        s = AA3_TO_1.get(s.capitalize(), "?")
    return s.upper()


def predict_variant(pos, ref, alt, model_path=None):
    """Returns dict with prediction. Raises ValueError with user-safe message."""
    bundle, wt, plddt = _bundle(model_path)
    try:
        pos = int(pos)
    except (TypeError, ValueError):
        raise ValueError("Position must be an integer between 1 and 393.")
    ref, alt = _norm_aa(ref), _norm_aa(alt)
    if not 1 <= pos <= 393:
        raise ValueError("Position must be between 1 and 393.")
    if ref not in VALID_AA:
        raise ValueError(f"Reference '{ref}' is not a valid amino acid.")
    if alt not in VALID_AA:
        raise ValueError(f"Alternate '{alt}' is not a valid amino acid.")
    if ref != wt[pos - 1]:
        raise ValueError(
            f"Reference mismatch: WT TP53 has {wt[pos - 1]} at position {pos}, "
            f"not {ref}. Check the variant annotation.")
    if alt == ref:
        raise ValueError("Alternate must differ from reference (not a variant).")
    feat = featurize(pos, ref, alt, plddt)
    x = [[feat[f] for f in bundle["features"]]]
    proba = float(bundle["pipeline"].predict_proba(x)[0, 1])
    pred = int(proba >= 0.5)
    domain = next(name for name, lo, hi in DOMAINS if lo <= pos <= hi)
    return {
        "input": {"pos": pos, "ref": ref, "alt": alt,
                  "hgvs_p": f"p.{ref}{pos}{alt}"},
        "prediction": pred,
        "result": ("Pathogenic-associated" if pred else "Benign-associated"),
        "probability_pathogenic": round(proba, 4),
        "model": bundle.get("model_name", "unknown"),
        "model_stage": bundle.get("stage", "baseline"),
        "model_path": str(model_path) if model_path else str(DEFAULT_MODEL),
        "target": bundle.get("target", ""),
        "context": {
            "domain": domain.replace("dom_", ""),
            "in_core": bool(feat["in_core"]),
            "plddt_at_pos": feat["plddt_at_pos"],
            "plddt_window5": feat["plddt_window5"],
            "grantham": feat["grantham"],
            "d_hydro": feat["d_hydro"],
            "d_volume": feat["d_volume"],
            "d_charge": feat["d_charge"],
            "dna_contact": bool(feat["dna_contact"]),
        },
        "disclaimer": ("Research prototype - associates sequence/structural "
                       "features with curated ClinVar annotations; NOT a "
                       "clinical diagnostic tool."),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Predict TP53 variant class")
    ap.add_argument("args", nargs="*", help="[ref pos alt] positionally")
    ap.add_argument("--pos", default=None)
    ap.add_argument("--ref", default=None)
    ap.add_argument("--alt", default=None)
    ap.add_argument("--model", default=None,
                    help="Path to model.joblib (default: "
                         "results/machine_learning/model.joblib)")
    a = ap.parse_args(argv)
    if len(a.args) == 3:
        ref, pos, alt = a.args
    elif a.pos and a.ref and a.alt:
        pos, ref, alt = a.pos, a.ref, a.alt
    else:
        print(json.dumps({"error": "Provide REF POS ALT, e.g. R 175 H."}))
        return 2
    try:
        print(json.dumps(predict_variant(pos, ref, alt, model_path=a.model),
                         indent=1))
        return 0
    except ValueError as e:
        print(json.dumps({"error": str(e)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
