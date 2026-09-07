"""LLM-as-a-Judge for the one thing code cannot decide: semantic adherence.

Everything measurable by parsing is measured in `scoring.py`. The judge is
deliberately confined to docs/questions.md's last two rows — *did this agent reason
from the governed definitions, or invent a calculation?* — plus a numeric
fallback for the rare prose answer with no extractable number.

Three properties, all of them load-bearing:

* **Blind to the config.** The prompt never names the path, the variant, the
  tier, or the server. A judge told it is looking at "the governed context arm"
  will find governance in it. Enforced by `test_judge_prompt_is_blind`, which
  greps the rendered prompt for every config key.
* **Judges the reasoning, not the number.** Accuracy is already decided against
  `golden.py`. Asking the judge to re-decide it would add variance to a
  question arithmetic already answered — the same reason Equivalence moved out
  of the judge and into code.
* **Failures are verdicts.** A judge call that errors returns `unclear` with the
  error in its rationale rather than raising, so one bad response cannot void a
  scoring pass over 1,200 cells.
"""

import asyncio
import json
from collections.abc import Container
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types

import config

# Same model and temperature discipline as the agents under test (§9.3). Note
# that 3.7 Flash is a reasoning model, so temperature 0 is not determinism —
# which is why the design runs n=5 replicates rather than trusting one sample.
TEMPERATURE = 0.0

# Judged concurrently, unlike the sweep. Nothing here is timed or token-counted
# per cell, so overlap cannot contaminate a measurement the way it would in
# `battery.py`. Kept modest because Vertex throttles this model on a shared pool
# and the sweep's 429 storm came from exactly this kind of pressure.
CONCURRENCY = 4
ATTEMPTS = 3
BACKOFF_S = 15

ADHERENCE_VALUES = ("governed", "partial", "invented", "unclear")

SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    required=["adherence", "rationale"],
    properties={
        "adherence": types.Schema(type=types.Type.STRING, enum=list(ADHERENCE_VALUES)),
        "rationale": types.Schema(type=types.Type.STRING),
        "stated_value": types.Schema(type=types.Type.NUMBER, nullable=True),
    },
)

SYSTEM = """You are grading how an analyst reasoned, not whether their arithmetic was right.

You will see a question, the business rule that governs the correct answer, the
query the analyst ran, and the answer they gave. Decide how well their reasoning
followed the governed rule.

- governed: the query implements the rule — the right columns, the stated
  exclusions applied.
- partial: the query follows some of the rule and misses a stated part of it.
- invented: the query uses a plausible-looking column or definition the rule
  explicitly rules out, or makes up a definition the rule does not support.
- unclear: there is not enough in the trace to tell.

Judge only what is shown. Do not reward an answer for stating the rule in prose
if the query does not implement it — reciting a definition is not applying it.
If the query is absent, that is `unclear`, not `invented`.

Also report `stated_value`: the single headline number the answer commits to, or
null if it does not commit to one. Do not compute it yourself; read it off."""

TEMPLATE = """Question:
{question}

Governed business rule that applies:
{rule}

Query the analyst ran:
{query}

Answer the analyst gave:
{answer}"""

NO_QUERY = "(none recorded — this analyst's tooling does not disclose the query it ran)"


@dataclass
class Verdict:
    """One judged cell."""

    cell_key: str
    adherence: str = "unclear"
    rationale: str = ""
    stated_value: float | None = None


def reusable(saved: list[dict[str, Any]], keys: Container[str]) -> dict[str, "Verdict"]:
    """Verdicts already reached, for cells that are still in the capture.

    Adding an arm to a capture should not re-grade the arms that were already in
    it. Judging is a model call, so a second pass over a settled cell can reach a
    different verdict for reasons that have nothing to do with the new arm — and
    the published adherence numbers would move with no way to tell which movement
    was the finding and which was the judge changing its mind.

    Trimmed to cells actually present. A `scores.json` from a wider capture would
    otherwise contribute verdicts for cells this report does not contain; nothing
    reads them, but a scores file that describes cells it does not score cannot be
    checked against itself.
    """
    return {v["cell_key"]: Verdict(**v) for v in saved if v["cell_key"] in keys}


def render(question: str, rule: str, query: str, answer: str) -> str:
    """Build the judge prompt. Separate from the call so a test can inspect it."""
    return TEMPLATE.format(
        question=question.strip(),
        rule=rule.strip() or "(no governed rule applies to this question)",
        query=(query.strip() or NO_QUERY)[:6000],
        answer=answer.strip()[:4000],
    )


def _client() -> genai.Client:
    return genai.Client(
        vertexai=True, project=config.PROJECT_ID, location=config.MODEL_LOCATION
    )


async def judge_one(
    client: genai.Client, cell_key: str, question: str, rule: str, query: str, answer: str
) -> Verdict:
    """Grade one cell, retrying on quota. Never raises."""
    prompt = render(question, rule, query, answer)
    settings = types.GenerateContentConfig(
        temperature=TEMPERATURE,
        system_instruction=SYSTEM,
        response_mime_type="application/json",
        response_schema=SCHEMA,
    )

    last = ""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            response = await client.aio.models.generate_content(
                model=config.JUDGE_MODEL, contents=prompt, config=settings
            )
            payload = json.loads(response.text or "{}")
            adherence = str(payload.get("adherence", "unclear"))
            return Verdict(
                cell_key=cell_key,
                adherence=adherence if adherence in ADHERENCE_VALUES else "unclear",
                rationale=str(payload.get("rationale", ""))[:600],
                stated_value=_as_float(payload.get("stated_value")),
            )
        except Exception as e:  # noqa: BLE001 - a bad verdict must not void the pass
            last = f"{type(e).__name__}: {e}"
            if attempt < ATTEMPTS and ("429" in last or "RESOURCE_EXHAUSTED" in last):
                await asyncio.sleep(BACKOFF_S * attempt)
                continue
            break
    return Verdict(cell_key=cell_key, adherence="unclear", rationale=f"judge failed: {last[:300]}")


def _as_float(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


async def judge_all(requests: list[dict[str, str]]) -> dict[str, Verdict]:
    """Grade many cells with bounded concurrency.

    Each request is `{cell_key, question, rule, query, answer}` — deliberately a
    plain dict of exactly what the prompt needs, so a caller cannot accidentally
    hand the judge a whole `Cell` and leak the config name into the context.
    """
    client = _client()
    gate = asyncio.Semaphore(CONCURRENCY)

    async def one(request: dict[str, str]) -> Verdict:
        async with gate:
            return await judge_one(
                client,
                request["cell_key"],
                request["question"],
                request.get("rule", ""),
                request.get("query", ""),
                request["answer"],
            )

    verdicts = await asyncio.gather(*(one(request) for request in requests))
    return {verdict.cell_key: verdict for verdict in verdicts}
