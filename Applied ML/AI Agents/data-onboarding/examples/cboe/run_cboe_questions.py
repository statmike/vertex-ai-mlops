"""Run Cboe DataShop questions through agent_chat and collect results.

Run from the data-onboarding project root:

    uv run python examples/cboe/run_cboe_questions.py                    # run all
    uv run python examples/cboe/run_cboe_questions.py --persona "Data Analyst"  # one persona
    uv run python examples/cboe/run_cboe_questions.py --id data-analyst-q3     # one question
    uv run python examples/cboe/run_cboe_questions.py --resume                 # skip already-completed

Requires CHAT_SCOPE=data_onboarding_datashop_cboe_com_bronze in .env to scope
the chat agent to the Cboe data. Results are written to
examples/cboe/results/cboe_results.json (append-safe — existing results are
preserved and new ones are merged in).
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path

# Ensure the project root is on sys.path so agent_chat etc. are importable
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Load .env before any agent imports
from dotenv import load_dotenv

load_dotenv(Path(_project_root) / ".env")

# Set model location early (matches agent_chat/agent.py)
_loc = os.getenv("AGENT_MODEL_LOCATION", "")
if _loc:
    os.environ["GOOGLE_CLOUD_LOCATION"] = _loc

from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("cboe_runner")

# Suppress noisy loggers
for name in (
    "google.adk", "google.auth", "google.genai", "urllib3",
    "httpcore", "httpx", "grpc",
):
    logging.getLogger(name).setLevel(logging.WARNING)

QUESTIONS_FILE = Path(__file__).parent / "cboe_questions.json"
RESULTS_FILE = Path(__file__).parent / "results" / "cboe_results.json"
APP_NAME = "agent_chat"
USER_ID = "cboe_runner"


def load_questions(
    path: Path,
    persona: str | None = None,
    question_id: str | None = None,
) -> list[dict]:
    """Load and optionally filter questions."""
    with open(path) as f:
        questions = json.load(f)
    if question_id:
        questions = [q for q in questions if q["id"] == question_id]
    elif persona:
        questions = [q for q in questions if q["persona"] == persona]
    return questions


def load_existing_results(path: Path) -> dict[str, dict]:
    """Load existing results keyed by question ID."""
    if path.exists():
        with open(path) as f:
            results = json.load(f)
        return {r["id"]: r for r in results}
    return {}


def save_results(path: Path, results: dict[str, dict]) -> None:
    """Save results ordered by question ID."""
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(results.values(), key=lambda r: r["id"])
    with open(path, "w") as f:
        json.dump(ordered, f, indent=2)


async def run_question(runner: InMemoryRunner, question: dict) -> dict:
    """Run a single question through agent_chat and collect the trace."""
    qid = question["id"]
    text = question["question"]
    persona = question["persona"]

    logger.info("[%s] Starting: %s", qid, text)

    # Create a fresh session for this question
    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
    )
    session_id = session.id

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=text)],
    )

    events = []
    start_time = time.time()

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=user_message,
    ):
        elapsed = time.time() - start_time
        entry = {
            "timestamp": event.timestamp,
            "elapsed": round(elapsed, 1),
            "author": event.author,
        }

        # Extract content parts
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

        # Extract actions
        if event.actions:
            if event.actions.transfer_to_agent:
                entry["transfer_to"] = event.actions.transfer_to_agent

        events.append(entry)

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

    # Fallback: if no final text, extract from the last main tool response
    if not final_answer:
        for evt in reversed(events):
            if "parts" not in evt:
                continue
            for part in evt["parts"]:
                if part["type"] == "function_response" and part["name"] in (
                    "conversational_chat", "meta_chat", "search_context", "get_table_columns",
                ):
                    resp = part.get("response", "")
                    # Strip the {'result': '...'} wrapper if present
                    if resp.startswith("{'result':"):
                        try:
                            import ast
                            resp = ast.literal_eval(resp).get("result", resp)
                        except Exception:
                            pass
                    final_answer = resp
                    break
            if final_answer:
                break

    # Build timing breakdown
    timing = []
    for evt in events:
        if evt["author"] == "user":
            continue
        step = {"elapsed": evt["elapsed"], "agent": evt["author"]}
        if "parts" in evt:
            for part in evt["parts"]:
                if part["type"] == "function_call":
                    step["action"] = f"call: {part['name']}"
                elif part["type"] == "function_response":
                    step["action"] = f"resp: {part['name']}"
                elif part["type"] == "text":
                    step["action"] = f"text: {part['text'][:100]}"
        if "transfer_to" in evt:
            step["transfer_to"] = evt["transfer_to"]
        timing.append(step)

    # Extract reranker result if present
    reranker_summary = ""
    for evt in events:
        if "parts" not in evt:
            continue
        for part in evt["parts"]:
            if part["type"] == "function_response" and part["name"] == "rerank_tables":
                reranker_summary = part["response"][:2000]

    # Extract tool responses for the main tool call
    tool_response = ""
    for evt in events:
        if "parts" not in evt:
            continue
        for part in evt["parts"]:
            if part["type"] == "function_response" and part["name"] in (
                "conversational_chat", "meta_chat", "search_context", "get_table_columns",
            ):
                tool_response = part["response"][:5000]

    result = {
        "id": qid,
        "persona": persona,
        "question": text,
        "session_id": session_id,
        "total_time_s": total_time,
        "final_answer": final_answer,
        "reranker_summary": reranker_summary,
        "tool_response": tool_response,
        "timing": timing,
        "event_count": len(events),
    }

    logger.info("[%s] Done in %.1fs (%d events)", qid, total_time, len(events))
    return result


async def main():
    parser = argparse.ArgumentParser(description="Run Cboe questions through agent_chat")
    parser.add_argument("--persona", type=str, help="Filter by persona name")
    parser.add_argument("--id", type=str, help="Run a single question by ID")
    parser.add_argument("--resume", action="store_true", help="Skip already-completed questions")
    parser.add_argument("--delay", type=float, default=5.0, help="Seconds between questions (default: 5)")
    parser.add_argument("--results", type=str, default=str(RESULTS_FILE), help="Output file path")
    args = parser.parse_args()

    # Verify CHAT_SCOPE is set for Cboe data
    chat_scope = os.getenv("CHAT_SCOPE", "")
    if "cboe" not in chat_scope:
        logger.warning(
            "CHAT_SCOPE=%r — does not include Cboe data. "
            "Set CHAT_SCOPE=data_onboarding_datashop_cboe_com_bronze in .env for best results.",
            chat_scope,
        )

    results_path = Path(args.results)
    questions = load_questions(QUESTIONS_FILE, persona=args.persona, question_id=args.id)
    existing = load_existing_results(results_path)

    if args.resume:
        before = len(questions)
        questions = [q for q in questions if q["id"] not in existing]
        logger.info("Resume mode: %d/%d questions remaining", len(questions), before)

    if not questions:
        logger.info("No questions to run.")
        return

    logger.info("Running %d questions sequentially (%.0fs delay between)", len(questions), args.delay)

    # Import agent_chat here (after .env is loaded) — this triggers catalog loading
    from agent_chat.agent import root_agent

    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)

    for i, question in enumerate(questions):
        try:
            result = await run_question(runner, question)
            existing[result["id"]] = result
            save_results(results_path, existing)
            logger.info("Saved result for %s → %s", result["id"], results_path)
        except Exception as e:
            logger.error("[%s] FAILED: %s", question["id"], e, exc_info=True)
            existing[question["id"]] = {
                "id": question["id"],
                "persona": question["persona"],
                "question": question["question"],
                "error": str(e),
                "total_time_s": 0,
                "final_answer": "",
                "timing": [],
            }
            save_results(results_path, existing)

        # Delay between questions to avoid 429s
        if i < len(questions) - 1:
            logger.info("Waiting %.0fs before next question...", args.delay)
            await asyncio.sleep(args.delay)

    logger.info("All done. Results at %s", results_path)


if __name__ == "__main__":
    asyncio.run(main())
