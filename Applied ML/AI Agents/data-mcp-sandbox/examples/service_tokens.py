"""Read back the Gemini tokens Conversational Analytics spent on our behalf.

`build_results.py` publishes Path 4 cost as a floor, because the CA API reports no
usage. Cloud Monitoring does. This puts the missing component next to the recorded
one so the two Path 4 arms can be compared to the MCP arms on equal terms.

    uv run python examples/service_tokens.py
    uv run python examples/service_tokens.py --results results/capture.json.gz
    uv run python examples/service_tokens.py --baseline 2026-08-27 2026-09-03

Read-only: it queries a metrics API and writes nothing. Run `--baseline` over a
quiet week first — the metric has no per-caller label, so anything else in the
project using CA during a sweep is silently added to these numbers.

Requires `roles/monitoring.viewer`. Metrics retain for six weeks, so an old
capture cannot be attributed retroactively.
"""

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401 - import for the sys.path side effect

import battery
import service_tokens
import traces


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--results", type=Path, default=battery.RESULTS_PATH,
        help="Capture to attribute (default: results/raw/results.json).",
    )
    parser.add_argument(
        "--baseline", nargs=2, metavar=("START", "END"),
        help="Instead of attributing, report project-wide CA usage between two dates.",
    )
    return parser.parse_args()


def _rfc3339(day: str) -> str:
    """Accept a bare date for the baseline window; the API wants a full stamp."""
    return day if "T" in day else f"{day}T00:00:00Z"


def main() -> int:
    args = parse_args()

    if args.baseline:
        start, end = (_rfc3339(d) for d in args.baseline)
        usage = service_tokens.baseline(start, end)
        print(f"project-wide Conversational Analytics usage, {start} -> {end}")
        print(f"  turns        {usage.turns:>15,}")
        print(f"  model calls  {usage.model_calls:>15,}")
        print(f"  tokens       {usage.total_tokens:>15,}")
        print()
        print(
            "Large numbers here mean something other than the sweep is using CA in "
            "this project, and a sweep window cannot be attributed cleanly."
        )
        return 0

    cells = list(traces.load(args.results).values())
    measured = service_tokens.measure(cells)
    if not measured:
        print("no Path 4 arms in this capture - nothing to attribute")
        return 0

    recorded = {
        (c.config, c.tier): 0 for c in cells if (c.config, c.tier) in {
            (m.config, m.tier) for m in measured
        }
    }
    counts = dict.fromkeys(recorded, 0)
    for cell in cells:
        key = (cell.config, cell.tier)
        if key in recorded:
            recorded[key] += int(cell.usage.get("total_tokens", 0) or 0)
            counts[key] += 1

    header = (
        f"{'arm':<16}{'tier':>5}{'cells':>7}"
        f"{'recorded':>13}{'server-side':>14}{'true/cell':>12}"
    )
    print(header)
    print("-" * len(header))
    unattributed = []
    for usage in measured:
        key = (usage.config, usage.tier)
        client, cells_n = recorded[key], counts[key]
        if not usage.attributed:
            # Printing the spillover tokens in a "server-side" column would be
            # asserting a measurement this block does not have.
            print(
                f"{usage.config:<16}{usage.tier:>5}{cells_n:>7}{client:>13,}"
                f"{'--':>14}{'--':>12}"
            )
            unattributed.append(usage)
            continue
        total = client + usage.total_tokens
        print(
            f"{usage.config:<16}{usage.tier:>5}{cells_n:>7}{client:>13,}"
            f"{usage.total_tokens:>14,}{total // max(cells_n, 1):>12,}"
        )

    print()
    for usage in measured:
        if usage.attributed:
            client = recorded[(usage.config, usage.tier)]
            print(
                f"{usage.config} tier {usage.tier}: recorded cost understates the real "
                f"figure by {(client + usage.total_tokens) / max(client, 1):.0f}x "
                f"({usage.turns:,} turns, {usage.model_calls:,} server-side model calls)."
            )
    for usage in unattributed:
        print(
            f"{usage.config} tier {usage.tier}: emits nothing on this metric across its "
            "whole block. Its server-side spend is still unmeasured - this is not a "
            "measurement of zero."
        )

    print()
    print(
        "The metric is project-wide and has no caller label. Confirm with "
        "`--baseline` over a quiet week before treating these as measured."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
