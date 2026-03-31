"""Run Medicare Provider questions through the deployed agent_chat on Agent Engine.

Unlike the CBOE example (which uses a local InMemoryRunner), this example
demonstrates querying a **deployed** agent via the Vertex AI Python SDK.

Run from the data-onboarding project root:

    uv run python examples/medicare-provider/run_medicare_questions.py                    # run all
    uv run python examples/medicare-provider/run_medicare_questions.py --persona "Data Analyst"
    uv run python examples/medicare-provider/run_medicare_questions.py --id data-analyst-q3
    uv run python examples/medicare-provider/run_medicare_questions.py --resume

Results are written to examples/medicare-provider/results/medicare_results.json.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Ensure the project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from dotenv import load_dotenv

load_dotenv(Path(_project_root) / ".env")

import vertexai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("medicare_runner")

# Suppress noisy loggers
for name in (
    "google.adk", "google.auth", "google.genai", "urllib3",
    "httpcore", "httpx", "grpc",
):
    logging.getLogger(name).setLevel(logging.WARNING)

QUESTIONS_FILE = Path(__file__).parent / "medicare_questions.json"
RESULTS_FILE = Path(__file__).parent / "results" / "medicare_results.json"

# Load deployment info for the chat agent
DEPLOY_FILE = Path(_project_root) / "deploy" / "chat" / "deployment.json"
USER_ID = "medicare_runner"


def _get_deployed_agent():
    """Get the deployed chat agent from Agent Engine."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    if not project:
        logger.error("GOOGLE_CLOUD_PROJECT not set")
        sys.exit(1)

    if not DEPLOY_FILE.exists():
        logger.error("No chat deployment found at %s", DEPLOY_FILE)
        logger.error("Deploy first: uv run python deploy/deploy.py chat")
        sys.exit(1)

    meta = json.loads(DEPLOY_FILE.read_text())
    resource_name = meta.get("resource_name", "")
    if not resource_name:
        logger.error("No resource_name in %s", DEPLOY_FILE)
        sys.exit(1)

    vertexai.init(project=project, location=location)
    client = vertexai.Client(project=project, location=location)
    agent = client.agent_engines.get(name=resource_name)

    logger.info("Connected to deployed agent: %s", resource_name)
    return agent


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


async def run_question(agent, question: dict) -> dict:
    """Run a single question through the deployed chat agent."""
    qid = question["id"]
    text = question["question"]
    persona = question["persona"]

    logger.info("[%s] Starting: %s", qid, text)

    # Create a fresh session for this question
    session = await agent.async_create_session(user_id=USER_ID)
    session_id = session["id"]

    events = []
    start_time = time.time()

    async for event in agent.async_stream_query(
        user_id=USER_ID,
        session_id=session_id,
        message=text,
    ):
        elapsed = time.time() - start_time
        entry = {
            "elapsed": round(elapsed, 1),
            "author": event.get("author", ""),
        }

        # Extract content
        content = event.get("content")
        if content:
            content_str = str(content)
            entry["content"] = content_str[:5000]

        # Extract parts if available
        parts = event.get("parts", [])
        if parts:
            parts_summary = []
            for part in parts:
                if isinstance(part, dict):
                    if part.get("function_call"):
                        fc = part["function_call"]
                        parts_summary.append({
                            "type": "function_call",
                            "name": fc.get("name", ""),
                            "args": fc.get("args", {}),
                        })
                    elif part.get("text"):
                        parts_summary.append({
                            "type": "text",
                            "text": part["text"][:5000],
                        })
            if parts_summary:
                entry["parts"] = parts_summary

        events.append(entry)

    total_time = round(time.time() - start_time, 1)

    # Extract the final answer — last content from a non-user author
    final_answer = ""
    for evt in reversed(events):
        content = evt.get("content", "")
        author = evt.get("author", "")
        if author and author != "user" and content:
            # The content from Agent Engine is often a dict-like string
            # Try to extract the text
            if isinstance(content, str) and "'text'" in content:
                # Try to find text parts
                import re
                text_matches = re.findall(r"'text': '((?:[^'\\]|\\.)*)'", content)
                if text_matches:
                    final_answer = text_matches[-1]
                    break
            final_answer = content[:5000]
            break

    # Build timing breakdown
    timing = []
    for evt in events:
        if evt.get("author") == "user":
            continue
        step = {"elapsed": evt["elapsed"], "agent": evt.get("author", "")}
        if "parts" in evt:
            for part in evt["parts"]:
                if part["type"] == "function_call":
                    step["action"] = f"call: {part['name']}"
                elif part["type"] == "text":
                    step["action"] = f"text: {part['text'][:100]}"
        timing.append(step)

    # Clean up session
    try:
        await agent.async_delete_session(user_id=USER_ID, session_id=session_id)
    except Exception:
        pass

    result = {
        "id": qid,
        "persona": persona,
        "question": text,
        "session_id": session_id,
        "total_time_s": total_time,
        "final_answer": final_answer,
        "timing": timing,
        "event_count": len(events),
    }

    logger.info("[%s] Done in %.1fs (%d events)", qid, total_time, len(events))
    return result


async def main():
    parser = argparse.ArgumentParser(
        description="Run Medicare questions through deployed agent_chat"
    )
    parser.add_argument("--persona", type=str, help="Filter by persona name")
    parser.add_argument("--id", type=str, help="Run a single question by ID")
    parser.add_argument("--resume", action="store_true", help="Skip already-completed questions")
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
    questions = load_questions(QUESTIONS_FILE, persona=args.persona, question_id=args.id)
    existing = load_existing_results(results_path)

    if args.resume:
        before = len(questions)
        questions = [q for q in questions if q["id"] not in existing]
        logger.info("Resume mode: %d/%d questions remaining", len(questions), before)

    if not questions:
        logger.info("No questions to run.")
        return

    logger.info(
        "Running %d questions sequentially (%.0fs delay between)",
        len(questions), args.delay,
    )

    agent = _get_deployed_agent()

    for i, question in enumerate(questions):
        try:
            result = await run_question(agent, question)
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
