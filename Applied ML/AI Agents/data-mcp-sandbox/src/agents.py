"""Build and run one isolated agent per evaluation cell.

Every cell gets a fresh `InMemoryRunner` and a fresh session, run one at a time.
Reusing a runner would let one question's context bleed into the next, and
running cells concurrently would make per-config latency and token attribution
meaningless (docs/method.md).

The instruction is deliberately **uniform across all 10 configs and both tiers**.
It names the data location and asks for a number; it says nothing about
governance, refunds, or which revenue column is real. Anything more would hand
the agent the answer the experiment is trying to measure it discovering.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

import config
import corpus
import mcp_clients
import traces
import usage

APP_NAME = "data_mcp_sandbox"
USER_ID = "evaluator"

# Temperature 0 for every cell. It is not determinism on a reasoning model —
# 3.7 Flash still varies its thinking — which is exactly why the design runs
# n=5 replicates rather than trusting a single sample (docs/questions.md).
TEMPERATURE = 0.0

BASE_INSTRUCTION = """You are a data analyst answering questions about a company's data.

{location}

Work out the answer using the tools available to you. Inspect the data's
metadata before you query it, so that you use the columns that actually mean
what the question is asking about.

Finish with a short, direct answer. When the answer is a number, state that
number plainly, and state the SQL or query you used to get it. Do not hedge
between two candidate numbers — commit to one.
"""

BIGQUERY_LOCATION = """The data is in BigQuery, in the dataset `{dataset}`, which contains
these tables:
{tables}

Use only this dataset. Do not query any other dataset."""

LOOKER_LOCATION = """The data is in Looker, in the LookML model `{model}`, which has a single
Explore named `{explore}`.

Use only this model."""


@dataclass
class Outcome:
    """What one agent run produced. Raw — no scoring happens here."""

    answer: str = ""
    tool_calls: list[traces.ToolCall] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)
    latency_s: float = 0.0
    error: str = ""
    started_at: str = ""
    ended_at: str = ""
    attempts: int = 1
    # SQL a service disclosed about its own work, and the BigQuery jobs it ran.
    # Empty for every MCP arm, where SQL is already visible in the tool results
    # and jobs are attributed by time window. Populated by the direct
    # Conversational Analytics arms, which are the only place a service hands
    # back its query plan (Amendment B.4.2). Defaulted so the published capture
    # deserializes and re-scores unchanged.
    emitted_sql: list[str] = field(default_factory=list)
    bq_job_ids: list[str] = field(default_factory=list)


def now() -> str:
    """RFC3339 UTC. The join key for post-hoc BigQuery job attribution."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def instruction(config_key: str, tier: int) -> str:
    """The system instruction for one config at one tier.

    Table and model names are the only thing that varies. Every agent is told
    where the data is and nothing about what the columns mean, so tier 0 and
    tier 1 differ only in what the *tools* return.
    """
    spec = mcp_clients.CONFIGS[config_key]
    if spec.needs_looker:
        location = LOOKER_LOCATION.format(
            model=config.looker_model(tier), explore=config.LOOKER_EXPLORE
        )
    else:
        tables = "\n".join(
            f"  - `{config.table_ref(tier, name)}`" for name in corpus.TABLE_NAMES
        )
        location = BIGQUERY_LOCATION.format(dataset=config.dataset_ref(tier), tables=tables)
    return BASE_INSTRUCTION.format(location=location)


def build(config_key: str, tier: int) -> tuple[Agent, mcp_clients.Bound]:
    """Construct a fresh agent and its tool bindings.

    The caller must `close()` the returned binding, or Toolbox subprocesses
    accumulate one per cell.
    """
    bound = mcp_clients.bind(config_key, tier)
    agent = Agent(
        name=f"{config_key}_t{tier}",
        model=config.AGENT_MODEL,
        instruction=instruction(config_key, tier),
        tools=list(bound.toolsets),
        generate_content_config=types.GenerateContentConfig(temperature=TEMPERATURE),
    )
    return agent, bound


# Conditions of the Vertex endpoint, not properties of any path. Retried because
# a 429 that lands on `p3_managed` and not on `p1_managed` is measurement noise
# that reads as a Path 3 defect — the first sweep lost 33% of Path 3's cells to it
# while Path 1 lost 0.8%, purely because quota pressure rose over the run
# (DEV_NOTES 2026-09-02).
RETRY_ATTEMPTS = 5
RETRY_BACKOFF_S = 20


def is_transient(error: BaseException) -> bool:
    """Whether a failure is the endpoint misbehaving rather than a real result.

    Matched on text because ADK re-wraps the Vertex error in its own
    `_ResourceExhaustedError`, a private class that cannot be caught by name from
    here without importing an underscore-prefixed symbol.

    503 UNAVAILABLE is in here for the same reason 429 is, and was added after
    watching it skew a live sweep: four cells died to it and all four landed on
    two arms, so keeping them would have charged a transient service blip to
    `p2_toolbox` and `p3_managed` as if it were an architectural defect. The test
    that matters is not "how severe is this error" but "would it have happened on
    a different arm" — and neither of these tells you anything about the arm.
    """
    text = f"{type(error).__name__}: {error}"
    return any(
        marker in text for marker in ("RESOURCE_EXHAUSTED", "429", "UNAVAILABLE", "503")
    )


async def ask(config_key: str, tier: int, question: str) -> Outcome:
    """Run one question end to end, retrying only on transient endpoint failures.

    Every other error is returned in the outcome rather than raised. A cell that
    blows up on its own merits is a data point — docs/method.md counts it as a
    failure instead of dropping it, which would flatter whichever architecture
    crashes most. A 429 or a 503 is the opposite: it says nothing about the
    architecture, so keeping it would poison exactly the comparison the sweep
    exists to make. See `is_transient` for where that line is drawn.

    The retry restarts the *whole* cell — fresh agent, fresh runner, fresh
    session. A 429 can land mid-stream, after some tool calls have been
    collected, and resuming into a half-filled Outcome would report a trace that
    never happened as one run.
    """
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        outcome = await _attempt(config_key, tier, question)
        outcome.attempts = attempt
        if not outcome.error or not is_transient(Exception(outcome.error)):
            return outcome
        if attempt < RETRY_ATTEMPTS:
            await asyncio.sleep(RETRY_BACKOFF_S * 2 ** (attempt - 1))
    return outcome


async def _attempt(config_key: str, tier: int, question: str) -> Outcome:
    """One try at a cell. See `ask` for why failures are captured, not raised."""
    usage.reset()
    outcome = Outcome(started_at=now())
    started = time.monotonic()
    bound: mcp_clients.Bound | None = None

    try:
        agent, bound = build(config_key, tier)
        runner = InMemoryRunner(agent=agent, app_name=APP_NAME)
        session = await runner.session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID
        )
        message = types.Content(role="user", parts=[types.Part(text=question)])
        issued: dict[int, float] = {}

        async for event in runner.run_async(
            user_id=USER_ID, session_id=session.id, new_message=message
        ):
            usage.record(getattr(event, "usage_metadata", None))
            _collect(event, outcome, issued)
    except Exception as e:  # noqa: BLE001 - a failed cell is an observation, not a crash
        outcome.error = f"{type(e).__name__}: {e}"
    finally:
        if bound is not None:
            bound.close()

    outcome.ended_at = now()
    outcome.latency_s = round(time.monotonic() - started, 3)
    outcome.usage = usage.get().as_dict()
    return outcome


def _collect(event: object, outcome: Outcome, issued: dict[int, float]) -> None:
    """Pull tool calls, tool results, and answer text off one ADK event.

    Calls and results arrive in separate events, so results are matched back to
    the most recent unfilled call of the same name. Tool results are kept in
    full (within `traces.RESULT_CHAR_LIMIT`) because they are the only evidence
    that a governed rule reached the agent at all.

    `issued` maps a call's `seq` to the monotonic clock when it was dispatched,
    which is how `duration_s` gets filled when the matching result arrives. It is
    threaded as a parameter rather than kept on `Outcome` because `Outcome` is
    serialized wholesale and this is scaffolding, not a result.
    """
    content = getattr(event, "content", None)
    if content is None or not getattr(content, "parts", None):
        return

    for part in content.parts:
        call = getattr(part, "function_call", None)
        if call is not None:
            issued[len(outcome.tool_calls)] = time.monotonic()
            outcome.tool_calls.append(
                traces.ToolCall(
                    seq=len(outcome.tool_calls),
                    name=call.name or "",
                    args=dict(call.args or {}),
                )
            )
            continue

        response = getattr(part, "function_response", None)
        if response is not None:
            _attach_result(outcome, response, issued)
            continue

        text = getattr(part, "text", None)
        if text and not getattr(part, "thought", False):
            outcome.answer = text.strip()


def _failed(payload: object) -> bool:
    """Whether a tool result represents a failure.

    Read the protocol's own flag rather than searching the text. An MCP result
    is `{"content": [...], "isError": false}`, and `"iserror"` contains
    `"error"` — so a substring test marks every successful MCP call as failed,
    which is every tool call this sandbox makes. Caught by eyeballing a trace
    where the tool plainly worked and the flag said otherwise.
    """
    if isinstance(payload, dict):
        if "isError" in payload:
            return bool(payload["isError"])
        if "error" in payload:
            return True
    return False


def _attach_result(outcome: Outcome, response: object, issued: dict[int, float]) -> None:
    """Store a tool result on its matching call, timing it from when it was issued."""
    name = getattr(response, "name", "") or ""
    payload = getattr(response, "response", None)
    text = traces.truncate(str(payload))
    is_error = _failed(payload)

    for call in reversed(outcome.tool_calls):
        if call.name == name and not call.result:
            call.result = text
            call.is_error = is_error
            if call.seq in issued:
                call.duration_s = round(time.monotonic() - issued[call.seq], 3)
            return
    outcome.tool_calls.append(
        traces.ToolCall(seq=len(outcome.tool_calls), name=name, result=text, is_error=is_error)
    )
