"""Combine captures from separate sweeps into one file the scorer can read.

    uv run python scripts/merge_captures.py results/raw/results.json \
        results/raw/b6-direct.json --out results/raw/results.json

The normal way to add arms to a capture is `run_battery.py --resume` against the
same file, which merges as it goes. This exists for the case that is not: a
sweep run into its own file, deliberately, so a defect in a new arm could not
corrupt a published one. Amendment B.6 was exactly that — 240 direct-API cells
captured separately, then merged once they had been inspected.

Merging is refused rather than reconciled whenever two captures disagree about
what they measured, or when the same arm appears twice. See
`traces.merge_headers` for the list and why each field is on it.
"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import _bootstrap  # noqa: F401 - import for the sys.path side effect

import traces


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("captures", nargs="+", type=Path, help="Capture files, in order.")
    parser.add_argument("--out", type=Path, required=True, help="Where to write the merge.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    missing = [path for path in args.captures if not path.exists()]
    if missing:
        raise SystemExit(f"No such capture: {', '.join(str(p) for p in missing)}")
    if len(args.captures) < 2:
        raise SystemExit("Give at least two captures to merge.")

    headers = [traces.read_header(path) for path in args.captures]
    captures = [traces.load(path) for path in args.captures]
    for path, cells in zip(args.captures, captures, strict=True):
        print(f"{path}: {len(cells)} cells")

    header = traces.merge_headers(headers)
    cells = traces.merge_cells(captures)

    # Overwriting an input is the normal case — the merge *is* the new capture —
    # so this writes through a temporary and renames, rather than refusing. A
    # crash mid-write would otherwise destroy the base capture it was reading.
    args.out.parent.mkdir(parents=True, exist_ok=True)
    staged = args.out.with_suffix(args.out.suffix + ".partial")
    payload = {"header": header, "cells": [asdict(cell) for cell in cells.values()]}
    traces.write_text(staged, json.dumps(payload, indent=2))
    staged.replace(args.out)

    print(f"\nwrote {args.out}: {len(cells)} cells, {len(header['configs'])} arms")
    print(f"arms: {', '.join(header['configs'])}")
    if header["total_cells"] != len(cells):
        print(
            f"NOTE: header says {header['total_cells']} planned cells but {len(cells)} "
            "were captured - some cells did not run."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
