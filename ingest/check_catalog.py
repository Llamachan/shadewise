"""Data quality check: every SKU in catalog.json has a doc, and the coverage numbers agree."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
catalog = json.loads((ROOT / "data" / "catalog.json").read_text())
docs = {p.name: p.read_text(encoding="utf-8") for p in (ROOT / "data" / "docs").glob("*.md")}

problems = 0
for sku, item in catalog.items():
    matches = [name for name, text in docs.items() if f"SKU: {sku}" in text]
    if not matches:
        print(f"MISSING DOC  {sku} {item['name']}")
        problems += 1
        continue
    text = docs[matches[0]]
    m = re.search(r"Coverage:\s*(\d+)", text)
    if not m or int(m.group(1)) != item["coverage_sqft_per_litre"]:
        print(f"MISMATCH     {sku} coverage: doc says {m.group(1) if m else 'nothing'}, "
              f"catalog says {item['coverage_sqft_per_litre']}")
        problems += 1
    for size in item["pack_sizes_litres"]:
        if str(size) not in item["price_per_pack_inr"]:
            print(f"NO PRICE     {sku} has a {size} L pack with no price")
            problems += 1

print(f"\n{len(catalog)} products, {len(docs)} docs, {problems} problem(s)")