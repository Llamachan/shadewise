"""Checks golden.jsonl is well formed: no duplicate ids, real sources, real SKUs."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
catalog = json.loads((ROOT / "data" / "catalog.json").read_text())
sources = {p.name for p in (ROOT / "data" / "docs").glob("*.md")}
required = {"knowledge": "expected_source", "calculation": "expected_value",
            "decline": "expected_behavior", "clarify": "expected_behavior"}

rows, problems, seen = [], 0, set()
for n, line in enumerate((ROOT / "eval" / "golden.jsonl").read_text().splitlines(), 1):
    if not line.strip():
        continue
    try:
        row = json.loads(line)
    except json.JSONDecodeError as e:
        print(f"line {n}: not valid JSON ({e})")
        problems += 1
        continue
    rows.append(row)
    if row.get("id") in seen:
        print(f"line {n}: duplicate id {row.get('id')}")
        problems += 1
    seen.add(row.get("id"))
    if row.get("type") not in required:
        print(f"line {n}: unknown type {row.get('type')}")
        problems += 1
        continue
    if required[row["type"]] not in row:
        print(f"line {n}: missing {required[row['type']]}")
        problems += 1
    if row["type"] == "knowledge" and row.get("expected_source") not in sources:
        print(f"line {n}: no such document {row.get('expected_source')}")
        problems += 1
    for sku in re.findall(r"SW-[A-Z]{3}-\d{3}", row.get("question", "")):
        if sku not in catalog:
            print(f"line {n}: no such SKU {sku}")
            problems += 1
    if row["type"] == "calculation" and "expected_tool" not in row:
        print(f"line {n}: missing expected_tool")
        problems += 1

by_type = {t: sum(1 for r in rows if r.get("type") == t) for t in required}
print(f"\n{len(rows)} cases {by_type}, {problems} problem(s)")