"""Hybrid retrieval: dense vectors from Qdrant, BM25 keyword scores in process, fused with RRF."""
from rank_bm25 import BM25Okapi

from app import tracking
from app.chunking import all_chunks
from app.clients import chat_model, embed, qdrant
from app import config

_chunks = all_chunks()
_bm25 = BM25Okapi([c["content"].lower().split() for c in _chunks])


def _dense(query: str, k: int) -> list[str]:
    vectors, tokens = embed([query])
    tracking.current()["embed_tokens"] += tokens
    hits = qdrant.query_points(config.COLLECTION, query=vectors[0], limit=k, with_payload=True).points
    return [h.payload["id"] for h in hits]


def _keyword(query: str, k: int) -> list[str]:
    scores = _bm25.get_scores(query.lower().split())
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    return [_chunks[i]["id"] for i in ranked if scores[i] > 0]


def search(query: str, k: int = 4, mode: str = "hybrid") -> list[dict]:
    """mode: 'hybrid' (dense + keyword, fused), 'dense' or 'keyword'."""
    by_id = {c["id"]: c for c in _chunks}
    if mode == "dense":
        ids = _dense(query, k)
    elif mode == "keyword":
        ids = _keyword(query, k)
    else:
        # Reciprocal rank fusion: a chunk ranked well by either method rises to the top.
        scores: dict[str, float] = {}
        for ranking in (_dense(query, k * 2), _keyword(query, k * 2)):
            for rank, cid in enumerate(ranking):
                scores[cid] = scores.get(cid, 0) + 1 / (60 + rank)
        ids = sorted(scores, key=scores.get, reverse=True)[:k]
    return [by_id[i] for i in ids if i in by_id]


def format_context(hits: list[dict]) -> str:
    return "\n\n".join(f"[{h['source']}]\n{h['content']}" for h in hits)


ANSWER_PROMPT = """You answer questions about the ShadeWise paint catalog.
Use ONLY the context below. Cite the source file in square brackets after each fact, like [dampguard-primer.md].
If the context does not contain the answer, say: "The catalog doesn't cover that."

Context:
{context}"""


def answer(question: str) -> dict:
    hits = search(question)
    llm = chat_model()
    msg = llm.invoke([("system", ANSWER_PROMPT.format(context=format_context(hits))), ("human", question)])
    return {"answer": msg.text, "sources": sorted({h["source"] for h in hits})}


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "How long should I wait between coats of the silk emulsion?"
    out = answer(q)
    print(out["answer"], "\n\nRetrieved:", out["sources"])