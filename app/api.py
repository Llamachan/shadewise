"""HTTP API around the agent."""
import json
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from app.agent import ask, get_agent

LOG = Path(__file__).resolve().parent.parent / "logs" / "requests.jsonl"
LOG.parent.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_agent()  # start the MCP server and load tools once, at startup
    yield


app = FastAPI(title="ShadeWise", description="Paint advisor: hybrid RAG + agent + MCP tools", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    out = await ask(req.message)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "question": req.message, **{k: v for k, v in out.items() if k not in ("answer", "context")}}) + "\n")
    return {k: out[k] for k in ("answer", "sources", "tool_calls", "cost_usd", "latency_ms")}