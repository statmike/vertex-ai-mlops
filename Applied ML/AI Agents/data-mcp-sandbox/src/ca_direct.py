"""Call Conversational Analytics directly, with no MCP tool in between.

Every other arm in the sweep runs a local ADK loop that calls tools. These two
do not: they hand the whole question to a service that runs its own loop in the
cloud and streams back what it did. So this module builds no `Agent` and no
runner — it builds a `ChatRequest` and reads the stream.

**Why it exists.** `p4_bq_ca` reaches this same service through Toolbox's
`bigquery-conversational-analytics` tool, which takes a question and returns
prose. The capture therefore holds no SQL for Path 4, and evidence recall, rule
acquisition, and per-cell BigQuery cost all print `--`. The API beneath the tool
streams a `DataMessage` carrying `generated_sql` and the `big_query_job` that
ran it — so the opacity was the transport's, not the service's (Amendment B.1).
Calling it directly fills those cells with the *existing* rubric, unchanged.

**What is still a floor.** Nothing in the response reports the Gemini calls the
service makes on our behalf, so token usage here is not merely unmeasured — it
is structurally absent, and there is no local model turn to stand in for it.
`mcp_clients.has_unmeasured_service` is true for every Path 4 arm, which is what
keeps these numbers labelled `floor` downstream (Amendment A.3.1).

Pinned to `google-cloud-geminidataanalytics` 0.13.2. The `Context` fields read
below are the measurement surface, and they can move between releases exactly as
vendor tool schemas do.
"""

import asyncio
import time
from typing import Any

from google.cloud import geminidataanalytics as gda

import agents
import config
import corpus
import identity
import mcp_clients
import usage

# CA is a global-endpoint service; there is no per-region variant to choose, so
# this is not derived from `config.BQ_LOCATION` the way BigQuery resources are.
CA_LOCATION = "global"

# Deliberately *not* `agents.BASE_INSTRUCTION`. That prompt tells the model to
# use its tools and to inspect metadata before querying, neither of which means
# anything to a service that owns its own loop. What survives is the answer
# format, verbatim in intent: the scorer parses a number out of the final text,
# so an arm that answers in a different shape would be measuring formatting
# rather than architecture.
#
# It is held IDENTICAL across both direct arms. `p4_bq_direct_ctx` differs from
# `p4_bq_direct` by its glossary payload and nothing else — one variable per
# pair, as with the `_matched` arms. (Amendment B.3 listed the instruction as
# part of the context payload; separating them is what keeps that pair a clean
# A/B, and it says nothing the ungoverned arm does not already know.)
ANSWER_FORMAT = """Finish with a short, direct answer. When the answer is a number, state that
number plainly. Do not hedge between two candidate numbers — commit to one."""


def _table_references(tier: int) -> list[dict[str, str]]:
    """The tier's corpus, as CA datasource references.

    The same three tables every other arm is pointed at, so the datasource is
    not a variable. Tier isolation does not rest on this list — it rests on the
    credentials the client is built with — but naming the tier's dataset keeps
    the arm from spending turns discovering it.
    """
    return [
        {
            "project_id": config.require_project(),
            "dataset_id": config.tier_dataset(tier),
            "table_id": table,
        }
        for table in corpus.TABLE_NAMES
    ]


def _glossary_terms(config_key: str, tier: int) -> list[dict[str, str]]:
    """Business definitions to inject, which is the whole `_ctx` variable.

    Empty for `p4_bq_direct` (no governance channel at all) and empty at tier 0
    for both arms, because tier 0 is the ungoverned control — injecting the
    rules there would hand the agent the answer the experiment measures it
    discovering, and would break the tier comparison on this arm alone.

    `example_queries` is NOT sent, though `Context` accepts it and Amendment B.3
    proposed it. `ExampleQuery` carries a `sql_query`, and the only queries we
    have that are both correct and relevant are the golden oracle's — sending
    one would leak the answer into the prompt. There is no way to supply that
    field honestly, so the field goes unused.
    """
    if config_key != "p4_bq_direct_ctx" or tier == 0:
        return []
    return [
        {"display_name": term.display, "description": term.description}
        for term in corpus.GLOSSARY_TERMS
    ]


def build_request(config_key: str, tier: int, question: str) -> gda.ChatRequest:
    """The whole arm, as one stateless request.

    `inline_context` rather than a `Conversation` or a `DataAgent`: the battery
    asks one question per cell with no history, so a stateful provider would add
    a resource to manage without changing what is measured. CA's stateful modes
    are held for the multi-turn work (Amendment B.3, deferred).
    """
    context = gda.Context(
        system_instruction=ANSWER_FORMAT,
        datasource_references={"bq": {"table_references": _table_references(tier)}},
        glossary_terms=_glossary_terms(config_key, tier),
    )
    return gda.ChatRequest(
        parent=f"projects/{config.require_project()}/locations/{CA_LOCATION}",
        inline_context=context,
        messages=[{"user_message": {"text": question}}],
    )


def _client(tier: int) -> gda.DataChatServiceClient:
    """A client bound to the tier's identity.

    This is the tier fence for these arms. There is no `allowedDatasets` knob
    and no scoping parameter on the request — a table the tier's service account
    cannot read comes back as a permission error from CA, the same 403 every
    other arm gets (`make verify-isolation`).
    """
    return gda.DataChatServiceClient(credentials=identity.credentials(tier))


def _collect(message: gda.Message, outcome: agents.Outcome) -> None:
    """Fold one streamed message into the outcome.

    Three of the stream's message kinds matter and the rest are progress. `text`
    accumulates because CA narrates across several messages and the answer is
    the whole narration, not its last fragment — taking only the last one lost
    the number on roughly half the probe runs. `data` is the payload this arm
    exists for: `generated_sql` is the evidence the MCP transport discards, and
    `big_query_job` turns Path 4's BigQuery cost from a time-window estimate
    into a per-cell fact. `error` is captured rather than raised, matching
    `agents._attempt` — a cell that fails on its own merits is an observation.

    `DataMessage.kind` is itself a **oneof**, so `generated_sql` and
    `big_query_job` arrive in *separate* messages and can never be read off the
    same one. The two lists are therefore parallel only by accident: index `i` of
    `emitted_sql` is not the query that ran as job `i`. Nothing downstream needs
    that pairing — evidence reads the SQL in bulk and cost sums the jobs — but
    anything that starts to would need the `group_id` on the enclosing
    `SystemMessage` to reconstruct it.
    """
    system = message.system_message
    kind = gda.SystemMessage.pb(system).WhichOneof("kind")

    if kind == "text":
        parts = [part for part in system.text.parts if part]
        if parts:
            outcome.answer = f"{outcome.answer}\n{' '.join(parts)}".strip()
    elif kind == "data":
        if system.data.generated_sql:
            outcome.emitted_sql.append(system.data.generated_sql)
        job_id = system.data.big_query_job.job_id
        if job_id and job_id not in outcome.bq_job_ids:
            outcome.bq_job_ids.append(job_id)
    elif kind == "error":
        outcome.error = f"CAError: {system.error.text}".strip()


def _chat(config_key: str, tier: int, question: str) -> tuple[list[Any], str]:
    """Drain the response stream. Blocking — callers run it off the event loop."""
    request = build_request(config_key, tier, question)
    try:
        return list(_client(tier).chat(request=request)), ""
    except Exception as e:  # noqa: BLE001 - a failed cell is an observation, not a crash
        return [], f"{type(e).__name__}: {e}"


async def ask(config_key: str, tier: int, question: str) -> agents.Outcome:
    """Run one direct-API cell, with the same retry policy as every MCP arm.

    Reuses `agents.is_transient` and its backoff rather than restating them, so
    a 429 cannot be forgiven on one transport and charged as a defect on the
    other — which would make the `p4_bq_ca` vs `p4_bq_direct` comparison this
    arm exists for measure quota pressure instead of transport.
    """
    for attempt in range(1, agents.RETRY_ATTEMPTS + 1):
        outcome = await _attempt(config_key, tier, question)
        outcome.attempts = attempt
        if not outcome.error or not agents.is_transient(Exception(outcome.error)):
            return outcome
        if attempt < agents.RETRY_ATTEMPTS:
            await asyncio.sleep(agents.RETRY_BACKOFF_S * 2 ** (attempt - 1))
    return outcome


async def _attempt(config_key: str, tier: int, question: str) -> agents.Outcome:
    """One try at a cell. See `ask` for why failures are captured, not raised."""
    usage.reset()
    outcome = agents.Outcome(started_at=agents.now())
    started = time.monotonic()

    messages, error = await asyncio.to_thread(_chat, config_key, tier, question)
    for message in messages:
        _collect(message, outcome)
    if error:
        outcome.error = error

    outcome.ended_at = agents.now()
    outcome.latency_s = round(time.monotonic() - started, 3)
    # Zeros, and they are true: no local model turn happened. The service's own
    # spend is invisible here, which is what `has_unmeasured_service` exists to
    # flag — see this module's docstring, and `report.py` for the `--` it forces.
    outcome.usage = usage.get().as_dict()
    return outcome


def tool_surface(config_key: str) -> dict[str, int]:
    """Zero tools, zero schema characters — recorded, not omitted.

    A direct arm genuinely binds nothing, and that is the point of the
    comparison: the schema-size-versus-cost correlation in Amendment A.1 needs
    this row present at zero. Dropping it instead would quietly change the
    denominator of a published result (Amendment B.4.5).
    """
    if not mcp_clients.is_direct(config_key):
        raise ValueError(f"{config_key} binds MCP tools; measure them, do not assume zero")
    return {"tools": 0, "schema_chars": 0}
