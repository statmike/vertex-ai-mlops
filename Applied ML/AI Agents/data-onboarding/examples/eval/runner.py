"""General question runner — executes a question against agent_chat.

Supports setting the Conversational Analytics API thinking mode per-run
by patching the config module before each execution.
"""

from __future__ import annotations

import logging
import time

from google.adk.runners import InMemoryRunner
from google.genai import types

from .schemas import RunResult, TimingEntry

logger = logging.getLogger("eval.runner")

APP_NAME = "agent_chat"
USER_ID = "eval_runner"


def set_thinking_mode(mode: str) -> None:
    """Patch the thinking mode in the config module.

    Because ``util_conversational_api.py`` re-imports
    ``CONVO_THINKING_MODE`` from the config module inside the function
    body on each call, changing the module attribute here takes effect
    on the next API call.
    """
    import agent_orchestrator.config as config

    config.CONVO_THINKING_MODE = mode.upper()
    logger.info("Set CONVO_THINKING_MODE = %s", mode.upper())


async def run_question(
    runner: InMemoryRunner,
    question: dict,
    mode: str = "thinking",
) -> RunResult:
    """Run a single question through agent_chat and collect the trace.

    Args:
        runner: An initialized InMemoryRunner for agent_chat.
        question: Dict with ``id``, ``question``, ``persona`` keys.
        mode: Thinking mode — ``"thinking"``, ``"fast"``, or ``"single"``
            (for questions that don't use the Convo API, like Catalog Explorer).

    Returns:
        RunResult with timing, answer, and trace data.
    """
    qid = question["id"]
    text = question["question"]

    if mode in ("thinking", "fast"):
        set_thinking_mode(mode)

    logger.info("[%s] Running with mode=%s: %s", qid, mode, text[:80])

    # Fresh session per run
    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=text)],
    )

    events = []
    start_time = time.time()

    try:
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=user_message,
        ):
            elapsed = time.time() - start_time
            entry = {
                "timestamp": event.timestamp,
                "elapsed": round(elapsed, 1),
                "author": event.author,
            }

            if event.content and event.content.parts:
                parts_summary = []
                for part in event.content.parts:
                    if part.text:
                        parts_summary.append({"type": "text", "text": part.text})
                    elif part.function_call:
                        parts_summary.append({
                            "type": "function_call",
                            "name": part.function_call.name,
                            "args": dict(part.function_call.args) if part.function_call.args else {},
                        })
                    elif part.function_response:
                        resp = part.function_response.response
                        resp_str = str(resp) if resp else ""
                        parts_summary.append({
                            "type": "function_response",
                            "name": part.function_response.name,
                            "response": resp_str[:5000],
                        })
                entry["parts"] = parts_summary

            if event.actions and event.actions.transfer_to_agent:
                entry["transfer_to"] = event.actions.transfer_to_agent

            events.append(entry)

    except Exception as e:
        logger.error("[%s] FAILED: %s", qid, e, exc_info=True)
        return RunResult(
            mode=mode,
            total_time_s=round(time.time() - start_time, 1),
            final_answer="",
            error=str(e),
        )

    total_time = round(time.time() - start_time, 1)

    # Extract the final answer (last text from a non-user author)
    final_answer = ""
    for evt in reversed(events):
        if evt["author"] != "user" and "parts" in evt:
            for part in evt["parts"]:
                if part["type"] == "text":
                    final_answer = part["text"]
                    break
            if final_answer:
                break

    # Fallback: extract from the last main tool response
    if not final_answer:
        for evt in reversed(events):
            if "parts" not in evt:
                continue
            for part in evt["parts"]:
                if part["type"] == "function_response" and part["name"] in (
                    "conversational_chat", "meta_chat", "search_context",
                    "get_table_columns", "list_all_tables",
                ):
                    final_answer = part.get("response", "")
                    break
            if final_answer:
                break

    # Build timing breakdown
    timing = []
    for evt in events:
        if evt["author"] == "user":
            continue
        te = TimingEntry(elapsed=evt["elapsed"], agent=evt["author"])
        if "parts" in evt:
            for part in evt["parts"]:
                if part["type"] == "function_call":
                    te.action = f"call: {part['name']}"
                elif part["type"] == "text":
                    te.action = f"text: {part['text'][:100]}"
        if "transfer_to" in evt:
            te.transfer_to = evt["transfer_to"]
        timing.append(te)

    # Extract reranker summary
    reranker_summary = ""
    for evt in events:
        if "parts" not in evt:
            continue
        for part in evt["parts"]:
            if part["type"] == "function_response" and part["name"] == "rerank_tables":
                reranker_summary = part["response"][:2000]

    # Extract tool response
    tool_response = ""
    for evt in events:
        if "parts" not in evt:
            continue
        for part in evt["parts"]:
            if part["type"] == "function_response" and part["name"] in (
                "conversational_chat", "meta_chat", "search_context",
                "get_table_columns", "list_all_tables",
            ):
                tool_response = part["response"][:5000]

    logger.info("[%s] mode=%s done in %.1fs (%d events)", qid, mode, total_time, len(events))

    return RunResult(
        mode=mode,
        total_time_s=total_time,
        final_answer=final_answer,
        tool_response=tool_response,
        reranker_summary=reranker_summary,
        timing=timing,
        event_count=len(events),
    )
