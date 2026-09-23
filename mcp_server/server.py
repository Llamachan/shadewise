"""ShadeWise MCP server: deterministic paint tools."""
import json
import math
from itertools import product
from pathlib import Path

from mcp.server.fastmcp import FastMCP

CATALOG = json.loads((Path(__file__).parent.parent / "data" / "catalog.json").read_text())
WASTAGE = 0.10

mcp = FastMCP("shadewise-paint-tools", log_level="WARNING")


def _lookup(sku: str) -> dict:
    item = CATALOG.get(sku.strip().upper())
    if item is None:
        raise ValueError(f"Unknown SKU '{sku}'. Valid SKUs: {', '.join(CATALOG)}")
    return item


@mcp.tool()
def get_product(sku: str) -> dict:
    """Look up one paint product by SKU (for example SW-INT-101).
    Returns name, category, coverage in sq ft per litre, pack sizes and pack prices in INR."""
    return {"sku": sku.strip().upper(), **_lookup(sku)}


@mcp.tool()
def estimate_litres(area_sqft: float, coats: int, sku: str) -> dict:
    """Estimate litres of a product needed to paint an area.
    area_sqft: total wall area in square feet (length x height, minus doors and windows).
    coats: number of coats, usually 2 for paint and 1 for primer.
    Adds 10% wastage and rounds up to the nearest 0.5 litre."""
    if area_sqft <= 0 or coats <= 0:
        raise ValueError("area_sqft and coats must both be greater than zero")
    item = _lookup(sku)
    raw = area_sqft * coats / item["coverage_sqft_per_litre"]
    litres = math.ceil(raw * (1 + WASTAGE) * 2) / 2
    return {"sku": sku.strip().upper(), "litres_needed": litres,
            "coverage_sqft_per_litre": item["coverage_sqft_per_litre"], "wastage_pct": int(WASTAGE * 100)}


@mcp.tool()
def quote_packs(sku: str, litres: float) -> dict:
    """Find the cheapest combination of pack sizes that covers the litres needed.
    Returns the packs to buy and the total price in INR."""
    if litres <= 0:
        raise ValueError("litres must be greater than zero")
    item = _lookup(sku)
    sizes = item["pack_sizes_litres"]
    prices = {int(k): v for k, v in item["price_per_pack_inr"].items()}
    best = None
    for counts in product(*(range(math.ceil(litres / s) + 1) for s in sizes)):
        vol = sum(c * s for c, s in zip(counts, sizes))
        if vol < litres:
            continue
        cost = sum(c * prices[s] for c, s in zip(counts, sizes))
        if best is None or (cost, vol) < (best[0], best[1]):
            best = (cost, vol, counts)
    cost, vol, counts = best
    packs = {f"{s}L": c for s, c in zip(sizes, counts) if c}
    return {"sku": sku.strip().upper(), "packs": packs, "total_litres": vol, "total_price_inr": cost}


if __name__ == "__main__":
    mcp.run()