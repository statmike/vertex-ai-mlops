"""Compare two captures that differ on one declared axis.

    uv run python scripts/compare_captures.py \
        --base results/capture.json.gz \
        --against results/capture-thinking.json.gz \
        --axis thinking_mode

    uv run python scripts/compare_captures.py \
        --base results/capture.json.gz \
        --against results/capture-model-x.json.gz \
        --axis agent_model --axis runs

`--aa` is the opposite mode: two captures that varied *nothing*, compared to
measure the noise floor rather than to find an effect.

    uv run python scripts/compare_captures.py \
        --base results/capture.json.gz \
        --against results/capture-thinking-default.json.gz --aa

That is how `compare.NOISE_FLOOR` was set, and it is the reason this mode is
shipped rather than done in a scratch script: a floor is a number every other
comparison is judged against, so a reader has to be able to re-measure it in
their own project instead of inheriting ours.

The counterpart to `merge_captures.py`, for the case merging is right to refuse.
`traces.MUST_AGREE` holds `agent_model` and `tiers`, so a cross-model sweep and a
governance-ladder sweep can never join the published capture — they are
different experiments, and Amendment C compares them instead of flattening them.

**Exits non-zero when the captures cannot be compared**, and prints why rather
than printing a delta with a warning above it. A caveat above a table of numbers
gets read as a result with an asterisk; a refusal gets read as a refusal.

Deterministic scoring only — no judge, no cost pass. Both are model calls or
billed queries, and the judge's ~1.3% verdict wobble would let two captures
differ because they were graded twice.
"""

import argparse
import sys
from pathlib import Path

import _bootstrap  # noqa: F401 - import for the sys.path side effect

import compare
import rescore
import traces


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--base", type=Path, required=True, help="The reference capture.")
    parser.add_argument("--against", type=Path, required=True, help="The capture to compare.")
    parser.add_argument(
        "--axis", action="append", dest="axes", default=None, metavar="FIELD",
        help=f"A field allowed to differ. Repeatable. One of: {', '.join(traces.MUST_AGREE)}",
    )
    parser.add_argument(
        "--aa", action="store_true",
        help="A/A mode: assert nothing varied and report the deltas as a noise floor.",
    )
    parser.add_argument("--out", type=Path, default=None, help="Write markdown here as well.")
    return parser.parse_args()


def scored(path: Path) -> tuple[dict, dict]:
    """A capture's header and its deterministic scores."""
    cells = traces.load(path)
    meta = traces.read_header(path)
    print(f"{path}: {len(cells)} cells")
    return meta, rescore.score_all(cells, rescore.resolve_goldens(cells, meta))


def main() -> int:
    args = parse_args()
    axes = tuple(args.axes or ())
    if args.aa and axes:
        raise SystemExit(
            "--aa and --axis are opposites. An A/A measures what stays the same; "
            "declaring an axis says something changed. Pick one."
        )
    if not axes and not args.aa:
        raise SystemExit(
            "Give at least one --axis. A comparison with no declared axis cannot "
            "say what a difference is attributable to. To measure the noise floor "
            "between two captures that varied nothing, use --aa."
        )
    unknown = [axis for axis in axes if axis not in traces.MUST_AGREE]
    if unknown:
        raise SystemExit(
            f"Not comparison axes: {', '.join(unknown)}. Only fields in "
            f"traces.MUST_AGREE gate a comparison: {', '.join(traces.MUST_AGREE)}"
        )
    for path in (args.base, args.against):
        if not path.exists():
            raise SystemExit(f"No such capture: {path}")

    meta_a, scores_a = scored(args.base)
    meta_b, scores_b = scored(args.against)

    labels = (_label(args.base), _label(args.against))
    alignment = compare.align([meta_a, meta_b], axes, aa=args.aa)
    result = compare.deltas(scores_a, scores_b)
    checks = compare.rank_stability(result.entries)
    text = compare.render(alignment, result, checks, labels)

    print()
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"wrote {args.out}")

    if alignment.conflicts and args.aa:
        print(f"REFUSED: not an A/A — these captures differ on "
              f"{', '.join(sorted(alignment.conflicts))}. The deltas would be an effect "
              "published under the name of noise, which raises the floor and suppresses "
              "real findings everywhere downstream.")
        return 1
    if alignment.conflicts:
        print("REFUSED: these captures differ on more than the declared axis.")
        return 1
    if args.aa:
        return 0
    if alignment.inert:
        print(f"REFUSED: {', '.join(alignment.inert)} is identical in both captures, "
              "so this comparison varies nothing.")
        return 1
    return 0


def _label(path: Path) -> str:
    """A short name for a capture, from its filename.

    `capture-model-x.json.gz` -> `model-x`. Two suffixes come off because the
    captures are gzipped, and `Path.stem` only removes one.
    """
    name = path.name
    for suffix in (".gz", ".json"):
        name = name.removesuffix(suffix)
    return name.removeprefix("capture-").removeprefix("capture") or "base"


if __name__ == "__main__":
    sys.exit(main())
