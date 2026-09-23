"""Chunk the Markdown docs, embed them, and load them into Qdrant.
Safe to re-run: it recreates the collection each time."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qdrant_client.models import Distance, PointStruct, VectorParams

from app import config
from app.chunking import all_chunks
from app.clients import embed, qdrant


def main():
    chunks = all_chunks()
    print(f"{len(chunks)} chunks")

    vectors, total_tokens = [], 0
    for start in range(0, len(chunks), 16):
        batch = chunks[start:start + 16]
        vecs, tokens = embed([c["content"] for c in batch])
        vectors.extend(vecs)
        total_tokens += tokens
    dims = len(vectors[0])
    print(f"Embedded with {total_tokens} tokens, {dims} dimensions per vector")

    if qdrant.collection_exists(config.COLLECTION):
        qdrant.delete_collection(config.COLLECTION)
    qdrant.create_collection(
        collection_name=config.COLLECTION,
        vectors_config=VectorParams(size=dims, distance=Distance.COSINE),
    )

    points = [PointStruct(id=i, vector=v, payload=c) for i, (c, v) in enumerate(zip(chunks, vectors))]
    for start in range(0, len(points), 16):
        qdrant.upsert(collection_name=config.COLLECTION, points=points[start:start + 16], wait=True)
        print(f"  uploaded {min(start + 16, len(points))}/{len(points)}")

    print(f"Uploaded {qdrant.count(config.COLLECTION).count} chunks to collection '{config.COLLECTION}'")


if __name__ == "__main__":
    main()