"""Print live golden-truth values for every tier.

    uv run python scripts/show_golden.py

Read this before trusting a score: if the correct and trap answers for a question
are close together, that question cannot discriminate and the trap needs
recalibrating in `corpus.py`.
"""

import sys

import _bootstrap  # noqa: F401 - import for the sys.path side effect
from google.cloud import bigquery

import config
import golden


def main() -> int:
    client = bigquery.Client(project=config.require_project())
    for tier in config.TIERS:
        print(f"\n{config.tier_label(tier)}  ({config.tier_dataset(tier)})")
        for key, r in golden.resolve_all(client, tier).items():
            print(f"  {key:32s} {r.value:>16,.2f}")
            # Every trap, not just the designed one. A compound trap that sits
            # close to the golden is the same discrimination failure as a plain
            # one sitting close, and it would be invisible here otherwise.
            for value, name in golden.traps_of(r):
                gap = abs(value - r.value) / abs(r.value) if r.value else float("inf")
                print(f"  {'  trap: ' + name:32s} {value:>16,.2f}  ({gap:.0%} off)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
