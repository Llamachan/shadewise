"""Loads settings from .env so every module reads config the same way."""
import os
from dotenv import load_dotenv

load_dotenv()

# Gemini speaks the OpenAI API at this base URL, so the standard OpenAI clients work unchanged.
# Chat and embeddings each talk the OpenAI API, so they can come from different providers.
CHAT_BASE_URL = os.environ["CHAT_BASE_URL"]
CHAT_API_KEY = os.environ["CHAT_API_KEY"]
CHAT_MODEL = os.environ["CHAT_MODEL"]

EMBED_BASE_URL = os.environ["EMBED_BASE_URL"]
EMBED_API_KEY = os.environ["EMBED_API_KEY"]
EMBED_MODEL = os.environ["EMBED_MODEL"]

QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
COLLECTION = os.environ.get("QDRANT_COLLECTION", "shadewise")

# USD per 1 million tokens. The free tier costs nothing; these are the paid rates,
# so the app can report what the same traffic would cost in production.
PRICE_IN = float(os.environ.get("PRICE_IN_PER_1M", "0"))
PRICE_OUT = float(os.environ.get("PRICE_OUT_PER_1M", "0"))
PRICE_EMBED = float(os.environ.get("PRICE_EMBED_PER_1M", "0"))

# Shrink embeddings to keep upload payloads small. Blank means the model default.
EMBED_DIMS = int(os.environ["EMBED_DIMS"]) if os.environ.get("EMBED_DIMS") else None