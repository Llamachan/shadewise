"""Run the golden set through the agent and write eval/results.md."""
import asyncio
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent import ask
from app.clients import chat_model

HERE = Path(__file__).resolve().parent

JUDGE_PROMPT = """You grade a paint assistant. Given the retrieved context and the answer,
rate groundedness from 1 to 5: 5 means every factual claim is supported by the context, 1 means mostly unsupported.
Reply with the number only.

Context:
{context}

Answer:
{answer}"""

BEHAVIOR_PROMPT = """Did this assistant reply {behavior}? For "decline": it refuses because the topic is outside painting.
For "clarify": it asks the user for missing information instead of giving numbers. Reply YES or NO only.

Reply:
{answer}"""


def numbers_in(text: str) -> list[float]:
    return [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*\.?\d*", text)]


async def judge(prompt: str) -> str:
    msg = await chat_model().ainvoke(prompt)
    return msg.text.strip()


async def run_case(case: dict) -> dict:
    out = await ask(case["question"])
    row = {"id": case["id"], "type": case["type"], "question": case["question"], "answer": out["answer"],
           "cost_usd": out["cost_usd"], "latency_ms": out["latency_ms"], "passed": False}

    if case["type"] == "knowledge":
        row["hit"] = case["expected_source"] in out["retrieved"]
        score = await judge(JUDGE_PROMPT.format(context=out["context"], answer=out["answer"]))
        row["groundedness"] = int(re.search(r"[1-5]", score).group()) if re.search(r"[1-5]", score) else None
        row["passed"] = row["hit"]
    elif case["type"] == "calculation":
        called = [t["name"] for t in out["tool_calls"]]
        tool_ok = case["expected_tool"] in called
        value_ok = any(abs(n - case["expected_value"]) <= 0.01 * case["expected_value"] for n in numbers_in(out["answer"]))
        row["tool_correct"] = tool_ok and value_ok
        row["passed"] = row["tool_correct"]
    else:
        verdict = await judge(BEHAVIOR_PROMPT.format(behavior=case["expected_behavior"], answer=out["answer"]))
        row["passed"] = verdict.upper().startswith("YES")
    return row


def pct(xs):
    return f"{100 * sum(xs) / len(xs):.0f}%" if xs else "n/a"


async def main():
    cases = [json.loads(line) for line in (HERE / "golden.jsonl").read_text().splitlines() if line.strip()]
    rows = []
    for case in cases:  # one at a time keeps latency numbers honest
        print("Running", case["id"])
        rows.append(await run_case(case))

    k = [r for r in rows if r["type"] == "knowledge"]
    c = [r for r in rows if r["type"] == "calculation"]
    d = [r for r in rows if r["type"] in ("decline", "clarify")]
    g = [r["groundedness"] for r in k if r.get("groundedness")]
    lat = sorted(r["latency_ms"] for r in rows)
    costs = [r["cost_usd"] for r in rows]

    lines = [
        "# ShadeWise evaluation results", "",
        f"Cases: {len(rows)}", "",
        "| Metric | Result |", "|---|---|",
        f"| Retrieval hit@4 (knowledge) | {pct([r['hit'] for r in k])} |",
        f"| Groundedness, LLM judge (1 to 5) | {statistics.mean(g):.1f} |" if g else "| Groundedness | n/a |",
        f"| Tool and value correct (calculation) | {pct([r['tool_correct'] for r in c])} |",
        f"| Correct decline or clarify | {pct([r['passed'] for r in d])} |",
        f"| Overall pass rate | {pct([r['passed'] for r in rows])} |",
        f"| Avg cost per query (USD) | {statistics.mean(costs):.5f} |",
        f"| Cost per 1,000 queries (USD) | {1000 * statistics.mean(costs):.2f} |",
        f"| Latency p50 / p95 (ms) | {lat[len(lat) // 2]} / {lat[min(len(lat) - 1, int(len(lat) * 0.95))]} |",
        "", "## Failures", "",
    ]
    fails = [r for r in rows if not r["passed"]]
    lines += [f"- **{r['id']}** ({r['type']}): {r['question']}\n  - Answer: {r['answer'][:300]}" for r in fails] or ["None."]
    (HERE / "results.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    asyncio.run(main())