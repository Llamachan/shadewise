"""One place that builds the model and vector database clients."""
from langchain_openai import ChatOpenAI
from openai import OpenAI
from qdrant_client import QdrantClient

from app import config

openai_client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)

qdrant = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY or None)


def chat_model() -> ChatOpenAI:
    # Swapping provider means swapping these two values, nothing else in the codebase.
    return ChatOpenAI(model=config.CHAT_MODEL, base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)


def embed(texts: list[str]) -> tuple[list[list[float]], int]:
    """Embed a batch of texts. Returns the vectors and the tokens used (for cost tracking)."""
    resp = openai_client.embeddings.create(model=config.EMBED_MODEL, input=texts)
    tokens = getattr(resp.usage, "total_tokens", 0) or 0
    return [d.embedding for d in resp.data], tokens