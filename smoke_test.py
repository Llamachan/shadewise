"""Checks that .env is filled in, the chat model answers, embeddings work, and Qdrant is reachable."""
from app import config
from app.clients import chat_model, embed, qdrant

print("Chat model:", config.CHAT_MODEL)
print("Chat reply:", chat_model().invoke("Reply with exactly: ShadeWise is alive").text)

vectors, tokens = embed(["hello paint"])
print("Embedding dimensions:", len(vectors[0]))

print("Qdrant collections:", [c.name for c in qdrant.get_collections().collections])
print("All good.")