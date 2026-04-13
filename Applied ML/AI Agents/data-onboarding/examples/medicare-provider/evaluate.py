"""Evaluate Medicare Provider questions with dual-mode comparison (THINKING vs FAST).

For each Data Analyst and Data Engineer question, runs agent_chat twice —
once with THINKING mode and once with FAST mode — then uses an LLM judge
to pick the better answer. Catalog Explorer questions run once (no
thinking mode applies).

Run from the data-onboarding project root:

    uv run python examples/medicare-provider/evaluate.py                      # run all
    uv run python examples/medicare-provider/evaluate.py --persona "Data Analyst"  # one persona
    uv run python examples/medicare-provider/evaluate.py --id data-analyst-q3     # one question
    uv run python examples/medicare-provider/evaluate.py --resume                 # skip completed
    uv run python examples/medicare-provider/evaluate.py --report                 # just build report
    uv run python examples/medicare-provider/evaluate.py --report --write         # update readme.md

Results are saved to examples/medicare-provider/results/eval_results.json.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("medicare_eval")

# Suppress noisy loggers
for name in (
    "google.adk", "google.auth", "google.genai", "urllib3",
    "httpcore", "httpx", "grpc",
):
    logging.getLogger(name).setLevel(logging.WARNING)

QUESTIONS_FILE = Path(__file__).parent / "medicare_questions.json"
RESULTS_FILE = Path(__file__).parent / "results" / "eval_results.json"

# Personas that use the Conversational Analytics API (support thinking mode)
CONVO_PERSONAS = {"Data Analyst", "Data Engineer"}


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
    """Load existing eval results keyed by question ID."""
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
        json.dump(ordered, f, indent=2, default=str)


async def evaluate_question(runner, question: dict) -> dict:
    """Evaluate a single question — dual mode for Convo personas, single for Catalog."""
    from examples.eval.runner import run_question
    from examples.eval.judge import judge_answers
    from examples.eval.schemas import EvalResult

    qid = question["id"]
    persona = question["persona"]
    text = question["question"]

    if persona in CONVO_PERSONAS:
        # Dual mode: run THINKING and FAST, then judge
        logger.info("[%s] === THINKING mode ===", qid)
        thinking_result = await run_question(runner, question, mode="thinking")

        # Brief pause between runs to avoid rate limiting
        await asyncio.sleep(3)

        logger.info("[%s] === FAST mode ===", qid)
        fast_result = await run_question(runner, question, mode="fast")

        # Judge the two answers
        logger.info("[%s] === Judging ===", qid)
        try:
            verdict = judge_answers(
                question=text,
                thinking_answer=thinking_result.final_answer,
                fast_answer=fast_result.final_answer,
                persona=persona,
            )
        except Exception as e:
            logger.error("[%s] Judge failed: %s", qid, e)
            verdict = None

        # Select the winning answer
        if verdict:
            if verdict.winner == "thinking":
                selected_mode = "thinking"
                selected_answer = thinking_result.final_answer
                selected_time = thinking_result.total_time_s
            elif verdict.winner == "fast":
                selected_mode = "fast"
                selected_answer = fast_result.final_answer
                selected_time = fast_result.total_time_s
            else:  # tie — prefer fast for lower latency
                selected_mode = "fast"
                selected_answer = fast_result.final_answer
                selected_time = fast_result.total_time_s
        else:
            # No verdict — default to thinking
            selected_mode = "thinking"
            selected_answer = thinking_result.final_answer
            selected_time = thinking_result.total_time_s

        eval_result = EvalResult(
            id=qid,
            persona=persona,
            question=text,
            thinking_result=thinking_result,
            fast_result=fast_result,
            verdict=verdict,
            selected_mode=selected_mode,
            selected_answer=selected_answer,
            selected_time_s=selected_time,
        )

    else:
        # Single mode (Catalog Explorer — no Convo API)
        logger.info("[%s] === Single mode ===", qid)
        single_result = await run_question(runner, question, mode="single")

        eval_result = EvalResult(
            id=qid,
            persona=persona,
            question=text,
            single_result=single_result,
            selected_mode="single",
            selected_answer=single_result.final_answer,
            selected_time_s=single_result.total_time_s,
        )

    logger.info(
        "[%s] Done — selected=%s (%.1fs)",
        qid,
        eval_result.selected_mode,
        eval_result.selected_time_s,
    )
    return eval_result.model_dump()


def build_report(results_path: Path, output_path: Path | None = None) -> str:
    """Build the markdown report from eval results."""
    from examples.eval.report import build_results_markdown
    from examples.eval.schemas import EvalResult

    with open(results_path) as f:
        raw = json.load(f)

    eval_results = [EvalResult.model_validate(r) for r in raw]
    completed = [r for r in eval_results if r.selected_answer or (r.single_result and r.single_result.error)]

    logger.info("Building report from %d/%d completed results", len(completed), len(eval_results))
    markdown = build_results_markdown(completed)

    if output_path:
        # Update the target markdown file — replace everything after "## Results"
        target_text = output_path.read_text()
        marker = "\n## Results"
        marker_pos = target_text.find(marker)
        if marker_pos >= 0:
            new_text = target_text[:marker_pos] + "\n" + markdown + "\n"
        else:
            new_text = target_text.rstrip() + "\n\n---\n\n" + markdown + "\n"
        output_path.write_text(new_text)
        logger.info("Updated %s", output_path)

    return markdown


async def main():
    parser = argparse.ArgumentParser(description="Evaluate Medicare Provider questions with dual-mode comparison")
    parser.add_argument("--persona", type=str, help="Filter by persona name")
    parser.add_argument("--id", type=str, help="Run a single question by ID")
    parser.add_argument("--resume", action="store_true", help="Skip already-completed questions")
    parser.add_argument("--delay", type=float, default=5.0, help="Seconds between questions (default: 5)")
    parser.add_argument("--report", action="store_true", help="Just build report from existing results")
    parser.add_argument("--write", action="store_true", help="Write report into readme.md")
    args = parser.parse_args()

    if args.report:
        readme_md = Path(__file__).parent / "readme.md" if args.write else None
        markdown = build_report(RESULTS_FILE, output_path=readme_md)
        if not args.write:
            print(markdown)
        return

    # Verify CHAT_SCOPE is set for CMS data
    chat_scope = os.getenv("CHAT_SCOPE", "")
    if "cms_gov" not in chat_scope:
        logger.warning(
            "CHAT_SCOPE=%r — does not include CMS data. "
            "Set CHAT_SCOPE=data_onboarding_cms_gov_bronze in .env.",
            chat_scope,
        )

    questions = load_questions(QUESTIONS_FILE, persona=args.persona, question_id=args.id)
    existing = load_existing_results(RESULTS_FILE)

    if args.resume:
        before = len(questions)
        questions = [q for q in questions if q["id"] not in existing]
        logger.info("Resume mode: %d/%d questions remaining", len(questions), before)

    if not questions:
        logger.info("No questions to run.")
        return

    # Count expected runs
    convo_count = sum(1 for q in questions if q["persona"] in CONVO_PERSONAS)
    single_count = len(questions) - convo_count
    total_runs = convo_count * 2 + single_count
    logger.info(
        "Evaluating %d questions: %d dual-mode (%d runs) + %d single = %d total runs",
        len(questions), convo_count, convo_count * 2, single_count, total_runs,
    )

    # Import agent_chat here (after .env is loaded) — triggers catalog loading
    from google.adk.runners import InMemoryRunner
    from agent_chat.agent import root_agent

    runner = InMemoryRunner(agent=root_agent, app_name="agent_chat")

    for i, question in enumerate(questions):
        try:
            result = await evaluate_question(runner, question)
            existing[result["id"]] = result
            save_results(RESULTS_FILE, existing)
            logger.info("Saved result for %s → %s", result["id"], RESULTS_FILE)
        except Exception as e:
            logger.error("[%s] FAILED: %s", question["id"], e, exc_info=True)

        # Delay between questions
        if i < len(questions) - 1:
            logger.info("Waiting %.0fs before next question...", args.delay)
            await asyncio.sleep(args.delay)

    logger.info("All done. Results at %s", RESULTS_FILE)
    logger.info("Run with --report to preview, or --report --write to update readme.md")


if __name__ == "__main__":
    asyncio.run(main())
