"""Factorial NL2SQL retrieval benchmark: approach × tier × question × run.

Each **approach-run** invokes a single discovery agent *in isolation* (its own
``InMemoryRunner``), not through the orchestrator's ``ParallelAgent``. Isolation
removes the parallel-contention artifact that made per-approach latency
meaningless in the old single-orchestrator design, and lets us attribute
reranker token usage exactly to one approach at a time.

The independent variable is the **enrichment tier**. ``scripts/setup.py``
replicates the identical corpus into one dataset per tier
(``{prefix}_tier0``..``_tier3``); this harness scopes each run to exactly one
tier dataset (see the collision note below) and sweeps all four.

Design::

    for tier in TIERS:                 # repopulate cache + set scope ONCE per tier
        for question in questions:
            for approach in APPROACHES:
                for run_idx in range(n):   # n replicates for spread/CIs
                    run one isolated approach-run

Run from the project root::

    uv run python examples/run_questions.py                     # full factorial
    uv run python examples/run_questions.py --runs 2            # smoke (n=2)
    uv run python examples/run_questions.py --tier 2            # one tier
    uv run python examples/run_questions.py --approach kc_context
    uv run python examples/run_questions.py --id single-q1
    uv run python examples/run_questions.py --category trap
    uv run python examples/run_questions.py --resume           # skip completed cells

Raw results (no scoring — that's ``build_results.py``) are written incrementally
to ``examples/results/results.json`` as ``{"metadata": {...}, "cells": [...]}``.

CORRECTNESS NOTE — short-name scoring collision: every tier dataset holds
identically-named tables, and scoring matches on the short table name. A run
must therefore see EXACTLY ONE tier dataset. We enforce this by calling
``cache.repopulate_for_tier(tier)`` (which flips ``config`` scope to that single
tier) before running any cell for a tier, and by never scoping across tiers.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

# Ensure the project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(_project_root) / ".env")

_loc = os.getenv("AGENT_MODEL_LOCATION", "")
if _loc:
    os.environ["GOOGLE_CLOUD_LOCATION"] = _loc

from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

import config  # noqa: E402
from context_cache import repopulate_for_tier  # noqa: E402
from reranker.util_rerank import get_usage, reset_usage  # noqa: E402
from schemas import RerankerResponse  # noqa: E402

# Single source of truth for the corpus + tier list.
sys.path.insert(0, str(Path(_project_root) / "scripts"))
from setup import CORPUS, TIERS  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("benchmark")

for name in (
    "google.adk",
    "google.auth",
    "google.genai",
    "urllib3",
    "httpcore",
    "httpx",
    "grpc",
):
    logging.getLogger(name).setLevel(logging.WARNING)

QUESTIONS_FILE = Path(__file__).parent / "questions.json"
RESULTS_FILE = Path(__file__).parent / "results" / "results.json"
USER_ID = "benchmark"

# approach key → (import path, human label). The state keys are
# nominated_tables_{key} / reranker_result_{key}, populated by each agent.
APPROACHES = [
    ("bq_tools", "agent_bq_tools.agent", "1: BQ Tools"),
    ("kc_search", "agent_kc_search.agent", "2: KC Search"),
    ("kc_context", "agent_kc_context.agent", "3: KC Context"),
    ("context_prefilter", "agent_context_prefilter.agent", "4: Context Pre-Filter"),
    ("semantic_context", "agent_semantic_context.agent", "5: Semantic Context"),
    ("search_direct", "agent_search_direct.agent", "6: Search Direct"),
]


# ---------------------------------------------------------------------------
# Loading / saving
# ---------------------------------------------------------------------------
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


def cell_key(question_id: str, approach: str, tier: int, run_idx: int) -> str:
    """Stable identifier for one approach-run (used for resume dedup)."""
    return f"{question_id}|{approach}|tier{tier}|run{run_idx}"


def load_existing_cells(path: Path) -> dict[str, dict]:
    if path.exists():
        with open(path) as f:
            doc = json.load(f)
        cells = doc.get("cells", []) if isinstance(doc, dict) else []
        return {c["cell_key"]: c for c in cells}
    return {}


def _pkg_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unknown"


def build_metadata(n_runs: int) -> dict:
    """Reproducibility header (metric F) stamped into the results file."""
    return {
        "agent_model": config.AGENT_MODEL,
        "tool_model": config.TOOL_MODEL,
        "reranker_temperature": 0.0,
        "top_k": config.TOP_K,
        "runs_per_cell": n_runs,
        "tiers": list(TIERS),
        "corpus_size": len(CORPUS),
        "distractor_count": sum(1 for t in CORPUS if t.get("role") == "distractor"),
        "approaches": [k for k, _, _ in APPROACHES],
        "resource_prefix": config.RESOURCE_PREFIX,
        "packages": {
            "google-adk": _pkg_version("google-adk"),
            "google-genai": _pkg_version("google-genai"),
            "google-cloud-dataplex": _pkg_version("google-cloud-dataplex"),
            "google-cloud-bigquery": _pkg_version("google-cloud-bigquery"),
        },
    }


def save_results(path: Path, metadata: dict, cells: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(
        cells.values(),
        key=lambda c: (c["question_id"], c["tier"], c["approach"], c["run_idx"]),
    )
    with open(path, "w") as f:
        json.dump({"metadata": metadata, "cells": ordered}, f, indent=2)


# ---------------------------------------------------------------------------
# One isolated approach-run
# ---------------------------------------------------------------------------
async def run_cell(
    runner: InMemoryRunner,
    app_name: str,
    approach: str,
    tier: int,
    run_idx: int,
    question: dict,
) -> dict:
    """Invoke one discovery agent in isolation and capture raw outputs.

    Latency is wall-clock around the isolated run. Reranker token usage is exact
    (the reranker's Gemini call records into a process-local accumulator we reset
    here). ADK tool-call count is best-effort from the event stream — the
    callback-driven approaches short-circuit the LLM, so they report ~0.
    """
    qid = question["id"]
    text = question["question"]

    session = await runner.session_service.create_session(app_name=app_name, user_id=USER_ID)
    user_message = types.Content(role="user", parts=[types.Part(text=text)])

    reset_usage()
    adk_tool_calls = 0
    start = time.time()
    async for event in runner.run_async(
        user_id=USER_ID, session_id=session.id, new_message=user_message
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call:
                    adk_tool_calls += 1
    latency_s = time.time() - start

    final = await runner.session_service.get_session(
        app_name=app_name, user_id=USER_ID, session_id=session.id
    )
    state = final.state

    nominated = state.get(f"nominated_tables_{approach}", [])
    # Search-based approaches record raw-vs-filtered page stats. With the bare
    # query syntax the ``parent:`` predicate is honored, so raw and in-scope
    # counts should match; the client-side filter is defense-in-depth. Absent for
    # the full-corpus approaches.
    search_stats = state.get(f"search_stats_{approach}")

    ranked_tables = []
    raw = state.get(f"reranker_result_{approach}", "")
    if raw:
        try:
            rr = RerankerResponse.model_validate(json.loads(raw))
            ranked_tables = [
                {
                    "table_id": t.table_id,
                    "rank": t.rank,
                    "confidence": t.confidence,
                }
                for t in rr.ranked_tables
            ]
        except Exception:
            logger.warning("Could not parse reranker result for %s", approach)

    usage = get_usage()

    return {
        "cell_key": cell_key(qid, approach, tier, run_idx),
        "question_id": qid,
        "category": question["category"],
        "question": text,
        "relevance": question.get("relevance", {}),
        "approach": approach,
        "tier": tier,
        "run_idx": run_idx,
        "nominated": nominated,
        "nominated_count": len(nominated),
        "search_stats": search_stats,
        "ranked_tables": ranked_tables,
        "ranked_count": len(ranked_tables),
        "latency_s": round(latency_s, 3),
        "reranker_prompt_tokens": usage["prompt_tokens"],
        "reranker_output_tokens": usage["output_tokens"],
        "reranker_total_tokens": usage["total_tokens"],
        "reranker_calls": usage["calls"],
        "adk_tool_calls": adk_tool_calls,
    }


# ---------------------------------------------------------------------------
# Main factorial sweep
# ---------------------------------------------------------------------------
async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=5, help="Replicates per cell (n)")
    parser.add_argument(
        "--tier", type=int, action="append", help="Restrict to tier(s); repeatable. Default: all."
    )
    parser.add_argument(
        "--approach",
        type=str,
        action="append",
        help="Restrict to approach key(s); repeatable. Default: all.",
    )
    parser.add_argument("--category", type=str, help="Filter questions by category")
    parser.add_argument("--id", type=str, help="Run a single question by ID")
    parser.add_argument("--resume", action="store_true", help="Skip completed cells")
    parser.add_argument(
        "--delay", type=float, default=1.0, help="Seconds between cells (rate-limit cushion)"
    )
    parser.add_argument("--results", type=str, default=str(RESULTS_FILE))
    args = parser.parse_args()

    results_path = Path(args.results)
    questions = load_questions(QUESTIONS_FILE, category=args.category, question_id=args.id)
    if not questions:
        logger.info("No questions match the filter.")
        return

    tiers = args.tier if args.tier else list(TIERS)
    approach_filter = set(args.approach) if args.approach else None
    approaches = [a for a in APPROACHES if not approach_filter or a[0] in approach_filter]

    existing = load_existing_cells(results_path)
    metadata = build_metadata(args.runs)

    # Build one isolated runner per approach (agents are stateless across
    # sessions; scope/cache live in module globals we flip per tier).
    runners: dict[str, tuple[InMemoryRunner, str]] = {}
    for key, module_path, _ in approaches:
        module = __import__(module_path, fromlist=["root_agent"])
        app_name = f"bench_{key}"
        runners[key] = (
            InMemoryRunner(agent=module.root_agent, app_name=app_name),
            app_name,
        )

    total = len(tiers) * len(questions) * len(approaches) * args.runs
    logger.info(
        "Factorial sweep: %d tier(s) × %d question(s) × %d approach(es) × %d run(s) = %d cells",
        len(tiers),
        len(questions),
        len(approaches),
        args.runs,
        total,
    )

    done = 0
    for tier in tiers:
        logger.info(
            "=== TIER %d — repopulating cache + scoping to %s ===", tier, config.tier_dataset(tier)
        )
        # Flips config.SCOPE to the single tier dataset AND rebuilds the cache
        # for the context approaches. Correctness-critical: one tier per run.
        repopulate_for_tier(tier)

        for question in questions:
            for key, _, _label in approaches:
                runner, app_name = runners[key]
                for run_idx in range(args.runs):
                    ck = cell_key(question["id"], key, tier, run_idx)
                    done += 1
                    # Resume skips only *successful* cells; error cells (e.g. a
                    # transient 429) are re-run so a resume pass is self-healing.
                    if args.resume and ck in existing and "error" not in existing[ck]:
                        logger.info("[%d/%d] skip (done): %s", done, total, ck)
                        continue
                    try:
                        cell = await run_cell(runner, app_name, key, tier, run_idx, question)
                        existing[ck] = cell
                        save_results(results_path, metadata, existing)
                        logger.info(
                            "[%d/%d] %s — %.2fs, %d ranked, %d tok",
                            done,
                            total,
                            ck,
                            cell["latency_s"],
                            cell["ranked_count"],
                            cell["reranker_total_tokens"],
                        )
                    except Exception as e:
                        logger.error("[%d/%d] FAILED %s: %s", done, total, ck, e, exc_info=True)
                        existing[ck] = {
                            "cell_key": ck,
                            "question_id": question["id"],
                            "category": question["category"],
                            "question": question["question"],
                            "relevance": question.get("relevance", {}),
                            "approach": key,
                            "tier": tier,
                            "run_idx": run_idx,
                            "error": str(e),
                        }
                        save_results(results_path, metadata, existing)
                    if args.delay:
                        await asyncio.sleep(args.delay)

    logger.info("Sweep complete. %d cells at %s", len(existing), results_path)


if __name__ == "__main__":
    asyncio.run(main())
