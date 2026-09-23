"""Per-request usage tracking: tokens, cost, sources and tool calls."""
from contextvars import ContextVar

from app import config

_current: ContextVar[dict] = ContextVar("request_usage")


def start() -> dict:
    usage = {"tokens_in": 0, "tokens_out": 0, "embed_tokens": 0, "sources": [], "retrieved": [], "context": []}
    _current.set(usage)
    return usage


def current() -> dict:
    try:
        return _current.get()
    except LookupError:
        return start()


def cost_usd(u: dict) -> float:
    return round(
        u["tokens_in"] / 1e6 * config.PRICE_IN
        + u["tokens_out"] / 1e6 * config.PRICE_OUT
        + u["embed_tokens"] / 1e6 * config.PRICE_EMBED,
        6,
    )