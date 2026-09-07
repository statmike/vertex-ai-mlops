"""Score a capture and write the report.

    uv run python examples/build_results.py --no-judge --no-cost   # free, offline-ish
    uv run python examples/build_results.py                        # the full pass
    uv run python examples/build_results.py --reuse-verdicts results/scores.json

Reads `results/raw/results.json`, writes `results/report.md` and
`results/scores.json`. Nothing here re-runs an agent, so a rubric change costs a
minute rather than a day — which is the whole reason `battery.py` captures and
never scores.

Three passes, each independently skippable because they have different costs:

* **Deterministic** — always runs. Free apart from the golden queries, and free
  *and offline* on a capture exported by `scripts/export_capture.py`, which
  freezes the goldens into the header. That is the combination a reader needs to
  dispute this rubric without a project of their own.
* **Cost** — one `INFORMATION_SCHEMA` query over the sweep window. Needs the
  capture to carry `started_at`/`ended_at`; older captures cannot be attributed.
* **Judge** — one model call per governed cell. Skip it while iterating, or
  `--reuse-verdicts` an existing `scores.json` to grade only the cells it has no
  verdict for. That is what adding an arm to a published capture needs: the
  judge is a model call, and re-grading settled cells would move published
  adherence numbers for reasons unrelated to the new arm.
"""

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401 - import for the sys.path side effect
from google.cloud import bigquery

import battery
import config
import cost
import golden
import judge
import report
import scoring
import traces

RESULTS_DIR = Path(config.PROJECT_ROOT) / "results"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--results", type=Path, default=battery.RESULTS_PATH,
        help="Capture to score (default: results/raw/results.json).",
    )
    parser.add_argument(
        "--out", type=Path, default=RESULTS_DIR,
        help="Directory for report.md and scores.json.",
    )
    parser.add_argument(
        "--no-judge", action="store_true",
        help="Skip the LLM judge. Adherence columns will be empty.",
    )
    parser.add_argument(
        "--from-scores", type=Path, default=None, metavar="SCORES_JSON",
        help="Re-render report.md from an existing scores.json. No judge, no BigQuery.",
    )
    parser.add_argument(
        "--no-cost", action="store_true",
        help="Skip BigQuery job attribution. Cost columns will be empty.",
    )
    parser.add_argument(
        "--reuse-verdicts", type=Path, default=None, metavar="SCORES_JSON",
        help="Judge only cells this scores.json has no verdict for. For adding an arm.",
    )
    return parser.parse_args()


def resolve_goldens(
    cells: dict[str, traces.Cell], meta: dict[str, Any]
) -> dict[int, dict[str, golden.Resolved]]:
    """The oracle for every tier in the capture, frozen if the file carries it.

    A capture written by `export_capture.py` embeds the goldens as they stood
    when the sweep ran. Preferring those is not just an optimization: it is what
    lets a reader with no corpus, no project, and no credentials re-run this
    rubric and argue with it. Otherwise resolve live, which is right for the
    operator because the corpus anchors its timestamps to build time and a stored
    number rots as the sandbox ages (`golden.py`).
    """
    frozen = meta.get("goldens")
    if frozen:
        print(f"using goldens frozen into the capture (tiers {', '.join(sorted(frozen))})")
        return {
            int(tier): {key: golden.Resolved(**value) for key, value in entries.items()}
            for tier, entries in frozen.items()
        }
    client = bigquery.Client(project=config.PROJECT_ID)
    return {
        tier: golden.resolve_all(client, tier) for tier in sorted({c.tier for c in cells.values()})
    }


def score_all(
    cells: dict[str, traces.Cell], resolved: dict[int, dict[str, golden.Resolved]]
) -> dict[str, scoring.Score]:
    """Deterministic scoring for every cell against the resolved oracle."""
    questions = {question.id: question for question in battery.load_questions()}
    scores = {}
    for key, cell in cells.items():
        question = questions.get(cell.question_id)
        if question is None:
            continue
        scores[key] = scoring.score_cell(
            cell, question.evidence, resolved[cell.tier].get(question.golden_key)
        )
    return scores


def judge_requests(
    cells: dict[str, traces.Cell], scores: dict[str, scoring.Score]
) -> list[dict[str, str]]:
    """Which cells to judge, and the blind payload for each.

    Only cells that answered *and* depend on a governed rule. A plain row count
    has no rule to adhere to, and grading it would spend a model call to learn
    nothing. Note what is deliberately absent from the payload: the config key,
    the tier, and the server names — §9.3 requires the judge be blind, and the
    cheapest way to guarantee that is never to assemble the string.
    """
    requests = []
    for key, cell in cells.items():
        score = scores.get(key)
        if score is None or not score.answered or not score.rules_required:
            continue
        requests.append({
            "cell_key": key,
            "question": cell.question,
            "rule": scoring.rule_statement(score.rules_required),
            "query": scoring.evidence_text(cell),
            "answer": cell.answer,
        })
    return requests


def reusable_verdicts(
    path: Path | None, cells: dict[str, traces.Cell]
) -> dict[str, judge.Verdict]:
    """Load and report on the verdicts `--reuse-verdicts` can carry over."""
    if path is None:
        return {}
    saved = json.loads(path.read_text())["verdicts"]
    verdicts = judge.reusable(saved, cells)
    dropped = len(saved) - len(verdicts)
    print(
        f"reusing {len(verdicts)} verdicts from {path}"
        + (f" ({dropped} for cells not in this capture, dropped)" if dropped else "")
    )
    return verdicts


def rerender(args: argparse.Namespace) -> int:
    """Rebuild report.md from a previous run's scores.json, changing nothing else.

    A change to the report's *prose* — a new caveat, a reworded note — otherwise
    costs a full judge pass to publish, because `--no-judge` does not reuse the
    old verdicts, it drops the adherence columns entirely. Everything the report
    needs is already in scores.json, keyed by cell, so re-rendering is free and
    the resulting diff is the change and nothing else.

    Deliberately does not re-score: if you changed the rubric, run the real pass.
    """
    saved = json.loads(args.from_scores.read_text())
    cells = traces.load(args.results)
    meta = saved["header"]

    scores = {s["cell_key"]: scoring.Score(**s) for s in saved["scores"]}
    costs = {c["cell_key"]: cost.CellCost(**c) for c in saved["costs"]}
    verdicts = {v["cell_key"]: judge.Verdict(**v) for v in saved["verdicts"]}
    prices = cost.Prices(**saved["prices"])
    print(
        f"re-rendering from {args.from_scores}: {len(scores)} scores, "
        f"{len(costs)} costs, {len(verdicts)} verdicts"
    )

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.md").write_text(
        report.build(cells, scores, costs, verdicts, prices, meta)
    )
    print(f"wrote {args.out / 'report.md'} (scores.json untouched)")
    return 0


def main() -> int:
    args = parse_args()
    if not args.results.exists():
        print(f"No capture at {args.results} - run examples/run_battery.py first.")
        return 1
    if args.from_scores:
        return rerender(args)

    cells = traces.load(args.results)
    meta = traces.read_header(args.results)
    print(f"{len(cells)} cells from {args.results}")

    scores = score_all(cells, resolve_goldens(cells, meta))
    print(f"scored {len(scores)}")

    costs: dict[str, cost.CellCost] = {}
    prices = cost.load_prices()
    if not args.no_cost:
        try:
            costs, attribution = cost.measure(list(cells.values()), prices)
            print(
                f"attributed {sum(len(v) for v in attribution.by_cell.values())} BigQuery jobs; "
                f"{len(attribution.unattributed)} fell between cells "
                f"({attribution.unattributed_bytes / 2**20:.0f} MiB)"
            )
        except ValueError as e:
            # A capture without timestamps is not a crash — it is an older file,
            # and the rest of the report is still worth producing.
            print(f"cost attribution skipped: {e}")

    verdicts = reusable_verdicts(args.reuse_verdicts, cells)
    if not args.no_judge:
        requests = [r for r in judge_requests(cells, scores) if r["cell_key"] not in verdicts]
        print(f"judging {len(requests)} cells...")
        fresh = asyncio.run(judge.judge_all(requests))
        unclear = sum(1 for v in fresh.values() if v.adherence == "unclear")
        failed = sum(1 for v in fresh.values() if v.rationale.startswith("judge failed"))
        print(f"judged {len(fresh)} - {unclear} unclear, {failed} judge errors")
        verdicts |= fresh

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.md").write_text(
        report.build(cells, scores, costs, verdicts, prices, meta)
    )
    (args.out / "scores.json").write_text(
        json.dumps(
            {
                "header": meta,
                "prices": asdict(prices),
                "scores": [asdict(score) for score in scores.values()],
                "costs": [asdict(entry) for entry in costs.values()],
                "verdicts": [asdict(verdict) for verdict in verdicts.values()],
            },
            indent=2,
            default=str,
        )
    )
    print(f"\nwrote {args.out / 'report.md'} and {args.out / 'scores.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
