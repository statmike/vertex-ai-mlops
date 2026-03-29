"""Run example questions through agent_orchestrator and collect per-approach results.

Run from the bigquery-context project root:

    uv run python examples/run_questions.py                    # run all
    uv run python examples/run_questions.py --category single-table
    uv run python examples/run_questions.py --id multi-cross-q3
    uv run python examples/run_questions.py --resume           # skip completed

Results are written to examples/results/results.json (append-safe).
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Ensure the project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from dotenv import load_dotenv

load_dotenv(Path(_project_root) / ".env")

_loc = os.getenv("AGENT_MODEL_LOCATION", "")
if _loc:
    os.environ["GOOGLE_CLOUD_LOCATION"] = _loc

from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from schemas import RerankerResponse  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("question_runner")

for name in (
    "google.adk", "google.auth", "google.genai", "urllib3",
    "httpcore", "httpx", "grpc",
):
    logging.getLogger(name).setLevel(logging.WARNING)

QUESTIONS_FILE = Path(__file__).parent / "questions.json"
RESULTS_FILE = Path(__file__).parent / "results" / "results.json"
APP_NAME = "agent_orchestrator"
USER_ID = "question_runner"

APPROACHES = [
    ("bq_tools", "1: BQ Tools"),
    ("dataplex_search", "2: Dataplex Search"),
    ("dataplex_context", "3: Dataplex Context"),
    ("context_prefilter", "4: Context Pre-Filter"),
    ("semantic_context", "5: Semantic Context"),
]

AGENT_NAMES = {
    "agent_bq_tools": "bq_tools",
    "agent_dataplex_search": "dataplex_search",
    "agent_dataplex_context": "dataplex_context",
    "agent_context_prefilter": "context_prefilter",
    "agent_semantic_context": "semantic_context",
    "compare_results": "compare",
}


def load_questions(
    path: Path,
    category: str | None = None,
    question_id: str | None = None,
) -> list[dict]:
    with open(path) as f:
        questions = json.load(f)
    if question_id:
        questions = [q for q in questions if q["id"] == question_id]
    elif category:
        questions = [q for q in questions if q["category"] == category]
    return questions


def load_existing_results(path: Path) -> dict[str, dict]:
    if path.exists():
        with open(path) as f:
            results = json.load(f)
        return {r["id"]: r for r in results}
    return {}


def save_results(path: Path, results: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(results.values(), key=lambda r: r["id"])
    with open(path, "w") as f:
        json.dump(ordered, f, indent=2)


def _table_short_name(full_id: str) -> str:
    """Extract the table name from a fully qualified ID."""
    return full_id.rsplit(".", 1)[-1]


def _score_approach(
    ranked_tables: list[dict],
    nominated_ids: list[str],
    expected_tables: list[str],
) -> dict:
    """Compute precision/recall for an approach against expected tables."""
    ranked_short = {_table_short_name(t["table_id"]) for t in ranked_tables}
    nominated_short = {_table_short_name(t) for t in nominated_ids}
    expected_set = set(expected_tables)

    found_ranked = ranked_short & expected_set
    found_nominated = nominated_short & expected_set
    missed = expected_set - found_ranked

    recall = len(found_ranked) / len(expected_set) if expected_set else 1.0
    precision = len(found_ranked) / len(ranked_short) if ranked_short else 0.0

    return {
        "found_ranked": sorted(found_ranked),
        "found_nominated": sorted(found_nominated),
        "missed": sorted(missed),
        "recall": round(recall, 2),
        "precision": round(precision, 2),
    }


async def run_question(runner: InMemoryRunner, question: dict) -> dict:
    """Run a single question through agent_orchestrator and collect results."""
    qid = question["id"]
    text = question["question"]
    expected = question.get("expected_tables", [])

    logger.info("[%s] Starting: %s", qid, text)

    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
    )
    session_id = session.id

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=text)],
    )

    # Collect events with timestamps
    events = []
    start_time = time.time()

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=user_message,
    ):
        elapsed = time.time() - start_time
        entry = {
            "elapsed": round(elapsed, 1),
            "author": event.author,
        }

        if event.content and event.content.parts:
            parts_summary = []
            for part in event.content.parts:
                if part.text:
                    parts_summary.append({
                        "type": "text",
                        "text": part.text[:500],
                    })
                elif part.function_call:
                    parts_summary.append({
                        "type": "function_call",
                        "name": part.function_call.name,
                    })
                elif part.function_response:
                    parts_summary.append({
                        "type": "function_response",
                        "name": part.function_response.name,
                    })
            entry["parts"] = parts_summary

        events.append(entry)

    total_time = round(time.time() - start_time, 1)

    # Read session state for per-approach results
    final_session = await runner.session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )
    state = final_session.state

    # Extract per-approach results from state
    approaches_result = {}
    for key, label in APPROACHES:
        nominated = state.get(f"nominated_tables_{key}", [])

        ranked_tables = []
        raw_reranker = state.get(f"reranker_result_{key}", "")
        if raw_reranker:
            try:
                rr = RerankerResponse.model_validate(json.loads(raw_reranker))
                ranked_tables = [
                    {
                        "table_id": t.table_id,
                        "rank": t.rank,
                        "confidence": t.confidence,
                        "reasoning": t.reasoning,
                    }
                    for t in rr.ranked_tables
                ]
            except Exception:
                pass

        scoring = _score_approach(ranked_tables, nominated, expected)

        approaches_result[key] = {
            "label": label,
            "nominated": nominated,
            "nominated_count": len(nominated),
            "ranked_tables": ranked_tables,
            "ranked_count": len(ranked_tables),
            **scoring,
        }

    # Compute per-approach timing from events
    approach_events: dict[str, list[float]] = {}
    for evt in events:
        approach_key = AGENT_NAMES.get(evt["author"])
        if approach_key and approach_key != "compare":
            approach_events.setdefault(approach_key, []).append(evt["elapsed"])

    for key, _ in APPROACHES:
        timestamps = approach_events.get(key, [])
        if timestamps:
            approaches_result[key]["first_event_s"] = timestamps[0]
            approaches_result[key]["last_event_s"] = timestamps[-1]
            approaches_result[key]["duration_s"] = round(
                timestamps[-1] - timestamps[0], 1
            )
            approaches_result[key]["completed_s"] = timestamps[-1]
            approaches_result[key]["event_count"] = len(timestamps)
        else:
            approaches_result[key]["duration_s"] = 0
            approaches_result[key]["completed_s"] = 0
            approaches_result[key]["event_count"] = 0

    # Extract compare agent output
    compare_output = ""
    for evt in reversed(events):
        if evt["author"] == "compare_results" and "parts" in evt:
            for part in evt["parts"]:
                if part["type"] == "text":
                    compare_output = part["text"]
                    break
            if compare_output:
                break

    result = {
        "id": qid,
        "category": question["category"],
        "question": text,
        "expected_tables": expected,
        "session_id": session_id,
        "total_time_s": total_time,
        "approaches": approaches_result,
        "compare_output": compare_output[:3000],
        "event_count": len(events),
    }

    logger.info("[%s] Done in %.1fs (%d events)", qid, total_time, len(events))
    return result


async def main():
    parser = argparse.ArgumentParser(
        description="Run example questions through agent_orchestrator"
    )
    parser.add_argument("--category", type=str, help="Filter by category")
    parser.add_argument("--id", type=str, help="Run a single question by ID")
    parser.add_argument(
        "--resume", action="store_true", help="Skip completed questions"
    )
    parser.add_argument(
        "--delay", type=float, default=5.0,
        help="Seconds between questions (default: 5)",
    )
    parser.add_argument(
        "--results", type=str, default=str(RESULTS_FILE),
        help="Output file path",
    )
    args = parser.parse_args()

    results_path = Path(args.results)
    questions = load_questions(
        QUESTIONS_FILE, category=args.category, question_id=args.id
    )
    existing = load_existing_results(results_path)

    if args.resume:
        before = len(questions)
        questions = [q for q in questions if q["id"] not in existing]
        logger.info(
            "Resume mode: %d/%d questions remaining", len(questions), before
        )

    if not questions:
        logger.info("No questions to run.")
        return

    logger.info(
        "Running %d question(s) sequentially (%.0fs delay between)",
        len(questions), args.delay,
    )

    from agent_orchestrator.agent import root_agent

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
                "category": question["category"],
                "question": question["question"],
                "expected_tables": question.get("expected_tables", []),
                "error": str(e),
                "total_time_s": 0,
                "approaches": {},
            }
            save_results(results_path, existing)

        if i < len(questions) - 1:
            logger.info("Waiting %.0fs before next question...", args.delay)
            await asyncio.sleep(args.delay)

    logger.info("All done. Results at %s", results_path)


if __name__ == "__main__":
    asyncio.run(main())
