"""One place that builds the model and vector database clients."""
from langchain_openai import ChatOpenAI
from openai import OpenAI
from qdrant_client import QdrantClient

from app import config

embed_client = OpenAI(base_url=config.EMBED_BASE_URL, api_key=config.EMBED_API_KEY)

qdrant = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY or None, timeout=120)


def chat_model() -> ChatOpenAI:
    # Swapping provider means swapping these two values, nothing else in the codebase.
    return ChatOpenAI(model=config.CHAT_MODEL, base_url=config.CHAT_BASE_URL, api_key=config.CHAT_API_KEY)


def embed(texts: list[str]) -> tuple[list[list[float]], int]:
    """Embed a batch of texts. Returns the vectors and the tokens used (for cost tracking)."""
    extra = {"dimensions": config.EMBED_DIMS} if config.EMBED_DIMS else {}
    resp = embed_client.embeddings.create(model=config.EMBED_MODEL, input=texts, **extra)
    tokens = getattr(resp.usage, "total_tokens", 0) or 0
    return [d.embedding for d in resp.data], tokens