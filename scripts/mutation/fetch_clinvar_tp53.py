"""Fetch TP53 missense variants from ClinVar (NCBI E-utilities) and build a
traceable, labelled variant dataset.

Source: ClinVar, gene TP53 (GeneID 7157), via E-utilities esearch+esummary.
No variants are invented: every row comes from a live ClinVar record (VCV).

Filtering (documented, reproducible):
  - molecular_consequence_list must contain 'missense variant'
  - protein_change must parse as p.<Ref><pos><Alt> (3-letter code)
  - germline_classification must be Pathogenic / Likely pathogenic (-> label 1)
    or Benign / Likely benign (-> label 0). VUS, Conflicting, unclassified: dropped.
  - reference AA must match the verified WT sequence at that position
    (data/processed/protein/WT_TP53_ORF1_393aa.fasta); mismatches dropped + logged.
  - duplicate (pos, ref, alt): conflicting labels -> dropped; else best review status kept.

Outputs:
  data/raw/variants/clinvar_tp53_esearch_ids.json   (ClinVar UIDs queried)
  data/raw/variants/clinvar_tp53_esummary.json      (raw ClinVar records used)
  data/processed/mutations/tp53_variant_dataset.csv (clean labelled dataset)

Usage:
  python3 scripts/mutation/fetch_clinvar_tp53.py
"""

import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WT_FILE = REPO / "data/processed/protein/WT_TP53_ORF1_393aa.fasta"
RAW_DIR = REPO / "data/raw/variants"
OUT_CSV = REPO / "data/processed/mutations/tp53_variant_dataset.csv"

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

AA3_TO_1 = {
    "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D", "Cys": "C",
    "Glu": "E", "Gln": "Q", "Gly": "G", "His": "H", "Ile": "I",
    "Leu": "L", "Lys": "K", "Met": "M", "Phe": "F", "Pro": "P",
    "Ser": "S", "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V",
    "Ter": "*", "Sec": "U",
}
PROT_RE = re.compile(r"p\.([A-Za-z*]+)(\d+)([A-Za-z*]+)")
# ClinVar esummary protein_change is 1-letter, often multi-isoform:
# e.g. 'P33R, P72R' or 'F138L, F231L, F270L, F111L'. Tokens look like R175H.
TOKEN_RE = re.compile(r"^([A-Z*])(\d+)([A-Z*])$")

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

LABEL_MAP = {
    "pathogenic": 1,
    "likely pathogenic": 1,
    "pathogenic/likely pathogenic": 1,
    "likely pathogenic/pathogenic": 1,
    "benign": 0,
    "likely benign": 0,
    "benign/likely benign": 0,
    "likely benign/benign": 0,
}


def http_get_json(url, params, tries=4):
    data = urllib.parse.urlencode(params).encode()
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, data=data,
                                         headers={"User-Agent": "TP53-Analysis/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 - retry transient network errors
            last = e
            time.sleep(2)
    raise RuntimeError(f"GET failed for {url}: {last}")


def read_wt():
    seq = "".join(
        l.strip() for l in WT_FILE.read_text().splitlines()
        if l.strip() and not l.startswith(">")
    )
    assert len(seq) == 393, f"WT length {len(seq)} != 393"
    return seq


def parse_protein_change(pc):
    """Parse legacy 3-letter p.Arg175His format (kept for completeness)."""
    m = PROT_RE.fullmatch((pc or "").strip())
    if not m:
        return None
    ref3, pos, alt3 = m.groups()
    ref = AA3_TO_1.get(ref3, "?") if len(ref3) == 3 else (ref3 if len(ref3) == 1 else "?")
    alt = AA3_TO_1.get(alt3, "?") if len(alt3) == 3 else (alt3 if len(alt3) == 1 else "?")
    if ref == "?" or alt == "?" or alt == "*":
        return None
    return ref, int(pos), alt


def cdna_to_protein_pos(cdna_change):
    """Map MANE cDNA (e.g. NM_000546.6:c.743G>A) to protein position.

    NM_000546.6 encodes NP_000537.3 (393 aa = our verified WT), CDS starts at
    c.1, so codon number = ceil(cDNA_pos / 3). Returns None if unparseable.
    """
    m = re.search(r"c\.(\d+)", cdna_change or "")
    if not m:
        return None
    return (int(m.group(1)) + 2) // 3


def disambiguate_isoforms(pc, wt, cdna_change=None):
    """Resolve multi-isoform tokens ('R248Q, R116Q, R209Q, R89Q') to the
    canonical 393-aa WT.

    Tokens are the same biological variant annotated on alternative isoforms
    (N-terminal truncations shift numbering down). Resolution order:
      1. tokens whose ref matches WT at that position;
      2. if several match, the cDNA-derived codon (MANE NM_000546.6) breaks
         the tie — it points at the full-length isoform;
      3. otherwise None (dropped, counted).
    """
    if not pc:
        return None
    matches = []
    for tok in pc.split(","):
        tok = tok.strip()
        # strip optional 'p.' prefix / 3-letter fallback
        m = TOKEN_RE.fullmatch(tok) or PROT_RE.fullmatch(tok)
        if not m:
            # try 3-letter token like Arg175His
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
    return None  # zero matches (non-canonical isoform) or ambiguous


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    wt = read_wt()

    # 1. All ClinVar UIDs for TP53
    res = http_get_json(ESEARCH, {"db": "clinvar", "term": "TP53[gene]",
                                  "retmax": "10000", "retmode": "json"})
    ids = res["esearchresult"]["idlist"]
    total = int(res["esearchresult"]["count"])
    print(f"ClinVar TP53 records: {total}; IDs retrieved: {len(ids)}")
    (RAW_DIR / "clinvar_tp53_esearch_ids.json").write_text(
        json.dumps({"count": total, "ids": ids}, indent=1))

    # 2. Summaries in batches
    records = {}
    batch = 150
    for i in range(0, len(ids), batch):
        chunk = ids[i:i + batch]
        r = http_get_json(ESUMMARY, {"db": "clinvar",
                                     "id": ",".join(chunk), "retmode": "json"})
        for uid in r["result"]["uids"]:
            records[uid] = r["result"][uid]
        print(f"  esummary {min(i + batch, len(ids))}/{len(ids)}", flush=True)
        time.sleep(0.4)
    (RAW_DIR / "clinvar_tp53_esummary.json").write_text(json.dumps(records, indent=1))
    print(f"Raw records saved: {len(records)}")

    # 3. Filter -> candidate rows
    stats = Counter()
    cands = []
    for uid, rec in records.items():
        stats["records"] += 1
        cons = rec.get("molecular_consequence_list") or []
        if not any("missense" in c.lower() for c in cons):
            stats["non_missense"] += 1
            continue
        varset = rec.get("variation_set") or [{}]
        cdna = varset[0].get("cdna_change", "") if isinstance(varset[0], dict) else ""
        parsed = disambiguate_isoforms(rec.get("protein_change", ""), wt, cdna)
        if not parsed:
            stats["unparsed_or_noncanonical_protein_change"] += 1
            continue
        ref, pos, alt = parsed
        g = (rec.get("germline_classification") or {})
        desc = (g.get("description") or "").strip().lower()
        if desc not in LABEL_MAP:
            stats[f" skipped_label:{desc or 'empty'}"] += 1
            continue
        cands.append({
            "variant_id": rec.get("accession", ""),
            "clinvar_uid": uid,
            "pos": pos, "ref": ref, "alt": alt,
            "hgvs_p": f"p.{ref}{pos}{alt}",
            "label": LABEL_MAP[desc],
            "classification": g.get("description", ""),
            "review_status": g.get("review_status", ""),
            "last_evaluated": g.get("last_evaluated", ""),
            "trait": ";".join(t.get("trait_name", "") for t in
                              (g.get("trait_set") or []) if isinstance(t, dict)),
            "source": "ClinVar",
        })
        stats["kept"] += 1

    # 4. Deduplicate on (pos, ref, alt); drop inter-record label conflicts
    by_key = {}
    for c in cands:
        by_key.setdefault((c["pos"], c["ref"], c["alt"]), []).append(c)
    rows, dropped_conflict = [], 0
    for key, group in by_key.items():
        labels = {g["label"] for g in group}
        if len(labels) > 1:
            dropped_conflict += 1
            continue
        group.sort(key=lambda g: REVIEW_RANK.get((g["review_status"] or "").lower(), 0),
                   reverse=True)
        rows.append(group[0])
    rows.sort(key=lambda r: (r["pos"], r["alt"]))
    stats["duplicate_conflicts_dropped"] = dropped_conflict
    stats["final_variants"] = len(rows)
    stats["final_pathogenic"] = sum(r["label"] for r in rows)
    stats["final_benign"] = len(rows) - stats["final_pathogenic"]

    # 5. Write CSV
    cols = ["variant_id", "clinvar_uid", "hgvs_p", "pos", "ref", "alt",
            "label", "classification", "review_status", "last_evaluated",
            "trait", "source"]
    with open(OUT_CSV, "w") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r[c]).replace(",", ";") for c in cols) + "\n")

    print("\n--- dataset summary ---")
    for k in ["records", "non_missense", "unparsed_or_noncanonical_protein_change",
              "kept", "duplicate_conflicts_dropped", "final_variants",
              "final_pathogenic", "final_benign"]:
        print(f"  {k}: {stats.get(k, 0)}")
    for k in sorted(stats):
        if k.startswith(" skipped_label:"):
            print(f"  {k}: {stats[k]}")
    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
