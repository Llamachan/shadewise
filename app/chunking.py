"""Splits the Markdown catalog into chunks. Used by the ingestion script and by BM25 at query time."""
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "data" / "docs"


def chunk_markdown(path: Path) -> list[dict]:
    """One chunk per '## ' section. Every chunk repeats the doc title so it makes sense on its own."""
    text = path.read_text(encoding="utf-8")
    title = text.splitlines()[0].lstrip("# ").strip()
    sku_match = re.search(r"SKU:\s*([A-Z]{2}-[A-Z]{3}-\d{3})", text)
    sku = sku_match.group(1) if sku_match else ""
    chunks = []
    for i, section in enumerate(re.split(r"\n(?=## )", text)):
        body = section.strip()
        if not body:
            continue
        chunks.append({
            "id": f"{path.stem}-{i}",
            "title": title,
            "sku": sku,
            "source": path.name,
            "content": body if i == 0 else f"{title}\n{body}",
        })
    return chunks


def all_chunks() -> list[dict]:
    return [c for p in sorted(DOCS.glob("*.md")) for c in chunk_markdown(p)]