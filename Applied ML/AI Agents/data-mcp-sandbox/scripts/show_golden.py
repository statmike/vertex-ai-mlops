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
        print(f"\nTier {tier} — {config.TIER_LABELS[tier]}  ({config.tier_dataset(tier)})")
        for key, r in golden.resolve_all(client, tier).items():
            print(f"  {key:32s} {r.value:>16,.2f}")
            if r.trap_value is not None:
                gap = abs(r.trap_value - r.value) / abs(r.value) if r.value else float("inf")
                print(f"  {'  trap: ' + r.trap_name:32s} {r.trap_value:>16,.2f}  ({gap:.0%} off)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
