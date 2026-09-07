"""Run the evaluation sweep and write `results/raw/results.json`.

    uv run python examples/run_battery.py --dry-run
    uv run python examples/run_battery.py --configs p1_managed --runs 1
    uv run python examples/run_battery.py --skip-looker    # no Looker instance needed
    uv run python examples/run_battery.py                  # the full 1,440-cell sweep
    uv run python examples/run_battery.py --resume         # pick up after an interrupt

**This costs money and takes hours.** Every cell is a live model call against
live Google Cloud services. `--dry-run` prints the plan *and a measured estimate
of time and tokens*, which is the number to look at before committing. Then
`make smoke` (12 cells) to check the wiring, then `--runs 1`, then the sweep.

Looker is optional. It is the only component behind an annual-commitment
purchase, so `--skip-looker` drops the three arms that need one and leaves nine
that run on BigQuery alone.

Capture only — scoring is `build_results.py`, run afterwards over the same file.
"""

import argparse
import asyncio
import sys
from pathlib import Path

import _bootstrap  # noqa: F401 - import for the sys.path side effect

import battery
import config
import cost
import estimate
import mcp_clients


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--configs",
        nargs="+",
        default=list(mcp_clients.CONFIG_KEYS),
        choices=list(mcp_clients.CONFIG_KEYS),
        help="Which path configurations to run (default: every arm).",
    )
    parser.add_argument(
        "--tiers",
        nargs="+",
        type=int,
        default=list(config.TIERS),
        choices=list(config.TIERS),
        help="Which governance tiers to run (default: both).",
    )
    parser.add_argument(
        "--questions",
        nargs="+",
        default=None,
        help="Question ids to run (default: all). Ids come from questions.json.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=battery.DEFAULT_RUNS,
        help=f"Replicates per cell (default: {battery.DEFAULT_RUNS}).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=battery.RESULTS_PATH,
        help="Where to write results (default: results/raw/results.json).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip cells already recorded as successful; re-run failures.",
    )
    parser.add_argument(
        "--skip-looker",
        action="store_true",
        help="Drop every arm that needs a Looker instance (Path 2 and p4_looker_ca).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the cells that would run and a measured cost estimate, then stop.",
    )
    return parser.parse_args()


def select_configs(config_keys: list[str], skip_looker: bool) -> list[str]:
    """Drop the Looker arms on request, and say which ones went.

    Silently running nine arms when the operator asked for twelve would make the
    results file quietly non-comparable with a full sweep, so this always prints.
    """
    if not skip_looker:
        return config_keys
    kept, dropped = mcp_clients.drop_looker(config_keys)
    if not kept:
        raise SystemExit(
            f"--skip-looker leaves nothing to run: every requested config "
            f"({', '.join(config_keys)}) needs a Looker instance."
        )
    if dropped:
        print(f"--skip-looker: dropping {', '.join(dropped)}\n")
    return kept


def select_questions(ids: list[str] | None) -> list[battery.Question]:
    """The requested questions, or all of them, rejecting unknown ids."""
    questions = battery.load_questions()
    if ids is None:
        return questions
    known = {question.id: question for question in questions}
    unknown = [question_id for question_id in ids if question_id not in known]
    if unknown:
        raise SystemExit(f"Unknown question ids: {unknown}\nKnown ids: {sorted(known)}")
    return [known[question_id] for question_id in ids]


def preflight(config_keys: list[str]) -> None:
    """Refuse to start a sweep whose results could not be interpreted.

    Both of these are cheap to check and expensive to discover an hour in. The
    tier-SA warning is not fatal — a deliberately unfenced run is a legitimate
    thing to do — but it must be a decision rather than an accident, so it is
    recorded in the results header either way.
    """
    config.require_project()

    if any(mcp_clients.CONFIGS[key].needs_looker for key in config_keys) and (
        not config.looker_configured()
    ):
        raise SystemExit(
            "Looker configs were requested but LOOKER_BASE_URL is unset or still the "
            "placeholder. Set it in .env, or re-run with --skip-looker to run the "
            "nine BigQuery-only arms."
        )

    if not config.USE_TIER_SA:
        print(
            "WARNING: USE_TIER_SA is off, so there is NO tier isolation — a tier-0 agent "
            "can read the governed tier-1 dataset and quietly contaminate the control.\n"
            "         Run `make identities` and set USE_TIER_SA=true, or treat these "
            "results as uncontrolled.\n"
        )


def main() -> int:
    args = parse_args()
    config_keys = select_configs(args.configs, args.skip_looker)
    preflight(config_keys)

    current = battery.plan(
        questions=select_questions(args.questions),
        config_keys=config_keys,
        tiers=args.tiers,
        runs=args.runs,
    )

    print(f"Sweep: {len(current.questions)} questions x {len(config_keys)} configs "
          f"x {len(args.tiers)} tiers x {args.runs} runs = {len(current)} cells")
    print(f"Model: {config.AGENT_MODEL} @ {config.MODEL_LOCATION}   "
          f"tier isolation: {'on' if config.USE_TIER_SA else 'OFF'}")
    print(f"Output: {args.out}\n")
    print(estimate.render(
        estimate.estimate([(cell[1], cell[2]) for cell in current.cells]),
        cost.load_prices().input_per_mtok_usd,
    ))
    print()

    cells = asyncio.run(
        battery.run(current, results_path=args.out, resume=args.resume, dry_run=args.dry_run)
    )
    if args.dry_run:
        return 0

    print()
    print(battery.summarize(cells))

    failed = [cell for cell in cells.values() if not cell.ok]
    if failed:
        print(f"\n{len(failed)} cell(s) did not produce an answer. Re-run with --resume.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

