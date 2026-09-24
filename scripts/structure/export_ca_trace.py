"""Export WT CA trace (coordinates + pLDDT) for the dashboard 3D viewer.

Input:  structures/alphafold/wt/selected/wt_selected.cif
Output: dashboard/ca_trace.json  ({pos, x, y, z, plddt} for 393 CA atoms)

Usage: python3 scripts/structure/export_ca_trace.py
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CIF = REPO / "structures/alphafold/wt/selected/wt_selected.cif"
OUT = REPO / "dashboard/ca_trace.json"


def main():
    wanted = ["label_seq_id", "label_atom_id", "Cartn_x", "Cartn_y",
              "Cartn_z", "B_iso_or_equiv"]
    cols, idx, rows = [], {}, []
    in_loop = False
    for line in CIF.read_text().splitlines():
        s = line.strip()
        if s == "loop_":
            in_loop, cols, idx = True, [], {}
            continue
        if in_loop and s.startswith("_atom_site."):
            cols.append(s.split(".")[1])
            continue
        if in_loop and cols and s and not s.startswith(("_", "loop_")):
            if s.startswith("ATOM") or (s[0].isdigit()):
                parts = s.split()
                if len(parts) < len(cols):
                    continue
                if not idx:
                    idx = {w: cols.index(w) for w in wanted}
                if parts[idx["label_atom_id"]] == "CA":
                    rows.append({
                        "pos": int(parts[idx["label_seq_id"]]),
                        "x": float(parts[idx["Cartn_x"]]),
                        "y": float(parts[idx["Cartn_y"]]),
                        "z": float(parts[idx["Cartn_z"]]),
                        "plddt": round(float(parts[idx["B_iso_or_equiv"]]), 2),
                    })
            elif s.startswith(("#", "data_")):
                in_loop = False
    rows.sort(key=lambda r: r["pos"])
    assert len(rows) == 393, f"CA count {len(rows)} != 393"
    assert [r["pos"] for r in rows] == list(range(1, 394))
    OUT.write_text(json.dumps({"source": "structures/alphafold/wt/selected/wt_selected.cif (model_4)",
                               "residues": rows}))
    print(f"Wrote {OUT} ({len(rows)} CA atoms)")


if __name__ == "__main__":
    main()
