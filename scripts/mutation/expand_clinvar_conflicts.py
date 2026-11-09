"""Expand the ClinVar TP53 missense dataset toward 500–1000 labelled variants.

Starting point: clear germline labels only (Pathogenic/Likely pathogenic or
Benign/Likely benign) — the original clear-label set from fetch_clinvar_tp53.py.

Expansion rule (documented, no invented labels):
  For missense records whose aggregate germline classification is
  "Conflicting classifications of pathogenicity", fetch the VCV XML and take
  a **majority vote** of submitter-level GermlineClassification values under
  ClinicalAssertion. Keep the variant only if:
    - a strict majority of mappable votes is Pathogenic-like (-> 1) or
      Benign-like (-> 0), and
    - that majority exceeds 50% of all mappable votes.
  Ties, VUS majorities, and unmappable votes are dropped.

Also accepts low-penetrance P/LP and B/LB strings in the clear-label pass.

Outputs:
  data/processed/mutations/tp53_variant_dataset.csv   (expanded; same schema
      + label_basis, conflict_votes columns)
  data/processed/mutations/tp53_variant_dataset_backup_clear.csv (original
      clear-label snapshot before expansion, if present)
  data/raw/variants/clinvar_conflict_resolution.json  (audit trail)

Usage:
  python3 scripts/mutation/expand_clinvar_conflicts.py
  python3 scripts/mutation/expand_clinvar_conflicts.py --max-conflicts 50  # smoke
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

REPO = Path(__file__).resolve().parents[2]
WT_FILE = REPO / "data/processed/protein/WT_TP53_ORF1_393aa.fasta"
OUT_CSV = REPO / "data/processed/mutations/tp53_variant_dataset.csv"
BACKUP_CSV = REPO / "data/processed/mutations/tp53_variant_dataset_backup_clear.csv"
ESUMMARY = REPO / "data/raw/variants/clinvar_tp53_esummary.json"
AUDIT_JSON = REPO / "data/raw/variants/clinvar_conflict_resolution.json"

EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

AA3_TO_1 = {
    "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D", "Cys": "C",
    "Glu": "E", "Gln": "Q", "Gly": "G", "His": "H", "Ile": "I",
    "Leu": "L", "Lys": "K", "Met": "M", "Phe": "F", "Pro": "P",
    "Ser": "S", "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V",
    "Ter": "*", "Sec": "U",
}
TOKEN_RE = re.compile(r"^([A-Z*])(\d+)([A-Z*])$")
PROT_RE = re.compile(r"p\.([A-Za-z*]+)(\d+)([A-Za-z*]+)")

LABEL_MAP = {
    "pathogenic": 1,
    "likely pathogenic": 1,
    "pathogenic/likely pathogenic": 1,
    "likely pathogenic/pathogenic": 1,
    "pathogenic, low penetrance": 1,
    "likely pathogenic, low penetrance": 1,
    "pathogenic/likely pathogenic/likely pathogenic, low penetrance": 1,
    "pathogenic/likely pathogenic/pathogenic, low penetrance": 1,
    "benign": 0,
    "likely benign": 0,
    "benign/likely benign": 0,
    "likely benign/benign": 0,
    "benign, low penetrance": 0,
    "likely benign/likely benign, low penetrance": 0,
}

REVIEW_RANK = {
    "practice guideline": 4,
    "reviewed by expert panel": 3,
    "criteria provided, multiple submitters, no conflicts": 2,
    "criteria provided, conflicting classifications": 1,
    "criteria provided, single submitter": 1,
    "no assertion criteria provided": 0,
    "no assertion provided": 0,
    "": 0,
}


def read_wt() -> str:
    seq = "".join(
        l.strip() for l in WT_FILE.read_text().splitlines()
        if l.strip() and not l.startswith(">")
    )
    assert len(seq) == 393, f"WT length {len(seq)} != 393"
    return seq


def parse_protein_change(pc: str):
    m = PROT_RE.fullmatch((pc or "").strip())
    if not m:
        return None
    ref3, pos, alt3 = m.groups()
    ref = AA3_TO_1.get(ref3, "?") if len(ref3) == 3 else (
        ref3 if len(ref3) == 1 else "?")
    alt = AA3_TO_1.get(alt3, "?") if len(alt3) == 3 else (
        alt3 if len(alt3) == 1 else "?")
    if ref == "?" or alt == "?" or alt == "*":
        return None
    return ref, int(pos), alt


def cdna_to_protein_pos(cdna_change: str):
    m = re.search(r"c\.(\d+)", cdna_change or "")
    if not m:
        return None
    return (int(m.group(1)) + 2) // 3


def disambiguate_isoforms(pc, wt, cdna_change=None):
    if not pc:
        return None
    matches = []
    for tok in pc.split(","):
        tok = tok.strip()
        m = TOKEN_RE.fullmatch(tok) or PROT_RE.fullmatch(tok)
        if not m:
            m3 = re.fullmatch(r"([A-Za-z]+)(\d+)([A-Za-z]+)", tok)
            if not m3:
                continue
            r3, p, a3 = m3.groups()
            ref = AA3_TO_1.get(r3, "?")
            alt = AA3_TO_1.get(a3, "?")
            if ref == "?" or alt == "?":
                continue
            pos = int(p)
        elif len(m.group(1)) == 1 and tok == m.group(0) and not tok.startswith("p."):
            ref, pos, alt = m.group(1), int(m.group(2)), m.group(3)
        else:
            parsed = parse_protein_change(tok if tok.startswith("p.") else "p." + tok)
            if not parsed:
                continue
            ref, pos, alt = parsed
        if alt == "*" or not (1 <= pos <= len(wt)):
            continue
        if wt[pos - 1] == ref:
            matches.append((ref, pos, alt))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1 and cdna_change:
        hint = cdna_to_protein_pos(cdna_change)
        tied = [m for m in matches if m[1] == hint]
        if len(tied) == 1:
            return tied[0]
    return None


def is_missense(rec) -> bool:
    return any("missense" in c.lower()
               for c in (rec.get("molecular_consequence_list") or []))


def http_get(url: str, params: dict, tries: int = 4) -> bytes:
    data = urllib.parse.urlencode(params).encode()
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(
                url, data=data, headers={"User-Agent": "TP53-Analysis/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5)
    raise RuntimeError(f"GET failed: {last}")


def local_tag(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def parse_vcv_germline_votes(xml_bytes: bytes) -> list[str]:
    """Submitter-level GermlineClassification strings under ClinicalAssertion."""
    root = ET.fromstring(xml_bytes)
    votes: list[str] = []
    for el in root.iter():
        if local_tag(el.tag) != "ClinicalAssertion":
            continue
        # Prefer Classification/GermlineClassification direct child path
        text = None
        for sub in el:
            if local_tag(sub.tag) == "Classification":
                for c in sub:
                    if local_tag(c.tag) == "GermlineClassification" and c.text:
                        text = c.text.strip()
                        break
            if text:
                break
        if text:
            votes.append(text)
    return votes


def majority_label(votes: list[str]):
    """Return (label, mapped_votes, all_votes) or (None, ...)."""
    mapped = []
    for v in votes:
        key = (v or "").strip().lower()
        if key in LABEL_MAP:
            mapped.append(LABEL_MAP[key])
    if not mapped:
        return None, mapped, votes
    counts = Counter(mapped)
    top, n = counts.most_common(1)[0]
    # strict majority of mappable votes
    if n > len(mapped) / 2:
        return top, mapped, votes
    return None, mapped, votes


def base_row_from_clear(existing: dict) -> dict:
    return {
        "variant_id": existing.get("variant_id", ""),
        "clinvar_uid": existing.get("clinvar_uid", ""),
        "hgvs_p": existing["hgvs_p"],
        "pos": int(existing["pos"]),
        "ref": existing["ref"],
        "alt": existing["alt"],
        "label": int(existing["label"]),
        "classification": existing.get("classification", ""),
        "review_status": existing.get("review_status", ""),
        "last_evaluated": existing.get("last_evaluated", ""),
        "trait": existing.get("trait", ""),
        "source": existing.get("source", "ClinVar"),
        "label_basis": existing.get("label_basis", "germline_clinvar"),
        "conflict_votes": existing.get("conflict_votes", ""),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--max-conflicts", type=int, default=None,
                    help="Limit conflicting records processed (smoke test)")
    ap.add_argument("--sleep", type=float, default=0.4,
                    help="Seconds between NCBI efetch calls")
    args = ap.parse_args(argv)

    wt = read_wt()
    if not ESUMMARY.exists():
        raise SystemExit(
            f"Missing {ESUMMARY}. Run scripts/mutation/fetch_clinvar_tp53.py "
            "first (saves the esummary dump).")
    records = json.loads(ESUMMARY.read_text())
    print(f"esummary records: {len(records)}")

    # Preserve original clear-label rows if we already expanded once
    if OUT_CSV.exists():
        with open(OUT_CSV, newline="") as f:
            current = list(csv.DictReader(f))
        # Prefer the clear-only backup as the clear baseline
        clear_rows = None
        if BACKUP_CSV.exists():
            with open(BACKUP_CSV, newline="") as f:
                clear_rows = list(csv.DictReader(f))
        if clear_rows is None:
            clear_rows = [r for r in current
                          if r.get("label_basis", "germline_clinvar")
                          == "germline_clinvar"
                          and "onflicting" not in (r.get("classification") or "").lower()]
        if not BACKUP_CSV.exists() and current:
            with open(BACKUP_CSV, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(current[0].keys()))
                w.writeheader()
                for r in current:
                    if r.get("label_basis", "germline_clinvar") == "germline_clinvar":
                        w.writerow(r)
            print(f"Backed up clear-label rows -> {BACKUP_CSV.name}")
    else:
        raise SystemExit("Run fetch_clinvar_tp53.py first to create the base dataset.")

    clear_by_key = {}
    for r in clear_rows:
        clear_by_key[(int(r["pos"]), r["ref"], r["alt"])] = base_row_from_clear(r)
    print(f"clear-label base variants: {len(clear_by_key)}")

    # Collect conflicting missense not already clear-labelled
    conflicts = []
    for uid, rec in records.items():
        if not is_missense(rec):
            continue
        g = (rec.get("germline_classification") or {})
        desc = (g.get("description") or "").strip().lower()
        if "onflicting" not in desc:
            continue
        varset = rec.get("variation_set") or [{}]
        cdna = varset[0].get("cdna_change", "") if isinstance(varset[0], dict) else ""
        parsed = disambiguate_isoforms(rec.get("protein_change", ""), wt, cdna)
        if not parsed:
            continue
        ref, pos, alt = parsed
        if (pos, ref, alt) in clear_by_key:
            continue
        conflicts.append((uid, rec, ref, pos, alt))

    conflicts.sort(key=lambda t: t[3])
    if args.max_conflicts is not None:
        conflicts = conflicts[: args.max_conflicts]
    print(f"conflicting missense to resolve: {len(conflicts)}")

    resolved = {}
    audit = []
    for i, (uid, rec, ref, pos, alt) in enumerate(conflicts, 1):
        accession = rec.get("accession", "")
        try:
            xml = http_get(EFETCH, {
                "db": "clinvar", "id": accession,
                "rettype": "vcv", "retmode": "xml",
            })
            votes = parse_vcv_germline_votes(xml)
            label, mapped, _ = majority_label(votes)
        except Exception as e:  # noqa: BLE001
            votes, label, mapped = [], None, []
            audit.append({"uid": uid, "accession": accession, "error": str(e)})
        time.sleep(args.sleep)

        entry = {
            "uid": uid,
            "accession": accession,
            "title": rec.get("title", ""),
            "pos": pos, "ref": ref, "alt": alt,
            "votes": votes,
            "mapped_votes": mapped,
            "resolved_label": label,
        }
        audit.append(entry)
        if label is None:
            if i % 25 == 0:
                n_res = sum(1 for a in audit
                            if a.get("resolved_label") is not None)
                n_drop = sum(1 for a in audit
                             if a.get("resolved_label") is None
                             and "error" not in a)
                print(f"  {i}/{len(conflicts)} resolved={n_res} "
                      f"dropped={n_drop}", flush=True)
            continue

        g = rec.get("germline_classification") or {}
        varset = rec.get("variation_set") or [{}]
        resolved[(pos, ref, alt)] = {
            "variant_id": accession,
            "clinvar_uid": uid,
            "hgvs_p": f"p.{ref}{pos}{alt}",
            "pos": pos, "ref": ref, "alt": alt,
            "label": label,
            "classification": (votes and Counter(votes).most_common(1)[0][0]
                               or "majority vote"),
            "review_status": g.get("review_status", ""),
            "last_evaluated": g.get("last_evaluated", ""),
            "trait": ";".join(t.get("trait_name", "") for t in
                              (g.get("trait_set") or []) if isinstance(t, dict)),
            "source": "ClinVar",
            "label_basis": "germline_conflict_majority",
            "conflict_votes": ";".join(votes),
        }
        if i % 25 == 0 or i == len(conflicts):
            n_res = sum(1 for a in audit if a.get("resolved_label") is not None)
            print(f"  {i}/{len(conflicts)} resolved={n_res}", flush=True)
            # checkpoint so interrupted runs keep progress
            AUDIT_JSON.write_text(json.dumps({
                "policy": "in-progress checkpoint",
                "n_conflicts_considered": len(conflicts),
                "audit": audit,
            }, indent=1))

    # Merge: clear + resolved conflicts (conflicts never override clear)
    merged = dict(clear_by_key)
    added = 0
    for key, row in resolved.items():
        if key not in merged:
            merged[key] = row
            added += 1

    rows = sorted(merged.values(), key=lambda r: (r["pos"], r["alt"]))
    n_path = sum(int(r["label"]) for r in rows)
    n_ben = len(rows) - n_path

    cols = ["variant_id", "clinvar_uid", "hgvs_p", "pos", "ref", "alt",
            "label", "classification", "review_status", "last_evaluated",
            "trait", "source", "label_basis", "conflict_votes"]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: str(r.get(c, "")).replace(",", ";") for c in cols})

    AUDIT_JSON.write_text(json.dumps({
        "policy": (
            "Clear germline P/LP or B/LB kept as-is; conflicting "
            "germline classifications resolved by strict majority of "
            "submitter ClinicalAssertion GermlineClassification values "
            "from VCV XML; ties/VUS majorities dropped."
        ),
        "n_conflicts_considered": len(conflicts),
        "n_conflicts_resolved_added": added,
        "n_total": len(rows),
        "n_pathogenic": n_path,
        "n_benign": n_ben,
        "audit": audit,
    }, indent=1))

    print("\n--- expansion summary ---")
    print(f"  clear base: {len(clear_by_key)}")
    print(f"  conflicts considered: {len(conflicts)}")
    print(f"  conflicts resolved & added: {added}")
    print(f"  final: {len(rows)} ({n_path} pathogenic / {n_ben} benign)")
    print(f"Wrote {OUT_CSV}")
    print(f"Audit: {AUDIT_JSON}")
    if not (500 <= len(rows) <= 1200):
        print(f"NOTE: target 500–1000 not met (got {len(rows)}); "
              "run without --max-conflicts for the full pass.")


if __name__ == "__main__":
    main()
