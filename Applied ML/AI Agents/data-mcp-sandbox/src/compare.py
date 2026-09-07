"""Compare captures that differ on exactly one axis.

`report.py` aggregates *within* one capture. This is its sibling for the case
Amendment C creates: a **family** of captures, each varying one thing, compared
against each other.

The family exists because the harness insisted on it. `traces.MUST_AGREE` holds
both `agent_model` and `tiers`, so a cross-model sweep and a governance-ladder
sweep are refused by `merge_captures.py` *by construction* — they are not more
cells for an existing capture, they are different experiments. Rather than
relaxing that refusal, C keeps it and adds this.

Two jobs, and the first is the one that protects the result:

**Refuse what cannot be aligned.** A comparison declares the axes it is allowed
to vary. Every other field in `MUST_AGREE` that differs is a *conflict*, named
and reported, and the caller is expected to stop. Two captures taken a month
apart on a bumped Toolbox differ in ways no delta can attribute, and the
temptation to subtract them anyway is exactly what a comparator is for.

**Subtract only what the noise floor supports.** Arms are ranked, and a pair of
arms whose accuracy gap is inside the measured floor is reported `unresolved`
rather than ordered. A rank comparison that treats a 0.4-point gap as an
ordering will find "inversions" that are resampling noise, which is how a
cross-model study concludes something it did not measure.
"""

from dataclasses import dataclass, field
from itertools import combinations
from typing import Any

import report
import scoring
import traces

# One accuracy point, measured rather than assumed. `p4_bq_direct` and
# `p4_bq_direct_ctx` differ only by a glossary payload, and at tier 0 that
# payload is empty by design — so those 120 cells send byte-identical requests
# and are an accidental A/A control. They land 1 point apart, 22% vs 23%
# (docs/paths.md). Any difference smaller than this is not a difference.
NOISE_FLOOR = 0.01


@dataclass
class Alignment:
    """Whether two captures may be compared, and on what.

    `varied` is what the caller declared may differ and did. `inert` is what it
    declared may differ and did *not* — a comparison whose axis turns out to be
    constant is measuring nothing, and silently reporting all-zero deltas is a
    worse outcome than saying so.
    """

    axes: tuple[str, ...]
    varied: dict[str, list[Any]] = field(default_factory=dict)
    inert: tuple[str, ...] = ()
    conflicts: dict[str, list[Any]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.conflicts and not self.inert


def align(headers: list[dict[str, Any]], axes: tuple[str, ...]) -> Alignment:
    """Check that captures differ on the declared axes and nothing else that matters.

    Scoped to `traces.MUST_AGREE` on purpose. Fields outside it — `git_commit`,
    `started`, `goldens` — are *expected* to differ between captures and are
    handled elsewhere: each capture carries its own oracle frozen at its own
    sweep start (C.1), which is what makes captures from different days
    comparable at all.

    `runs` is worth declaring rather than fighting. Two captures at different
    replicate counts still yield comparable *rates*; they differ in precision,
    not in meaning. Cells are paired by key, so the extra replicates simply go
    unpaired and `Deltas.unpaired` reports how many.
    """
    result = Alignment(axes=axes)
    for name in traces.MUST_AGREE:
        values = [header.get(name) for header in headers]
        differs = len({_comparable(value) for value in values}) > 1
        if name in axes:
            if differs:
                result.varied[name] = values
            else:
                result.inert = (*result.inert, name)
        elif differs:
            result.conflicts[name] = values
    return result


def _comparable(value: object) -> str:
    """A hashable, order-stable rendering of a header value.

    Header fields hold lists (`tiers`, `configs`, `question_ids`) as well as
    scalars, and a list is unhashable. Sorting rather than preserving order is
    deliberate: two captures that declare the same tiers in a different order
    measured the same thing.

    `None` and `""` collapse to one value, which is what lets this family grow.
    Every field added to `MUST_AGREE` after a capture was taken is missing from
    that capture's header and reads as `None`; without this, adding
    `ca_thinking_mode` would have made the published capture permanently
    incomparable to everything measured against it — the guard would refuse the
    exact comparison it was added for. Both spellings mean *unset*, and unset is
    a real, checkable state: a capture that omitted the field and one that
    explicitly left it empty sent the same request.
    """
    if isinstance(value, list):
        return repr(sorted(str(item) for item in value))
    if value is None or value == "":
        return "<unset>"
    return repr(value)


@dataclass
class Delta:
    """One arm's accuracy on the cells both captures share."""

    config: str
    tier: int
    pairs: int
    correct_a: int
    correct_b: int

    @property
    def accuracy_a(self) -> float | None:
        return self.correct_a / self.pairs if self.pairs else None

    @property
    def accuracy_b(self) -> float | None:
        return self.correct_b / self.pairs if self.pairs else None

    @property
    def points(self) -> float | None:
        """B minus A, in accuracy points, or None when nothing paired."""
        if not self.pairs:
            return None
        return 100 * (self.correct_b - self.correct_a) / self.pairs

    @property
    def resolved(self) -> bool:
        """True when the gap clears the measured A/A floor."""
        return self.points is not None and abs(self.points) >= 100 * NOISE_FLOOR


@dataclass
class Deltas:
    """Per-arm deltas plus an honest account of what did not line up."""

    entries: list[Delta] = field(default_factory=list)
    unpaired_a: int = 0
    unpaired_b: int = 0
    only_in_a: tuple[str, ...] = ()
    only_in_b: tuple[str, ...] = ()


def deltas(scores_a: dict[str, scoring.Score], scores_b: dict[str, scoring.Score]) -> Deltas:
    """Pair cells across two captures by key and difference them per arm.

    Paired cell-for-cell rather than pooled per arm, for the same reason
    `scoring.compare_arms` pairs within a capture: a pooled mean can hide two
    captures that are each right half the time on disjoint halves of the
    battery. Pairing by `cell_key` also means a question, tier or replicate
    present in only one capture is *dropped and counted* rather than quietly
    changing a denominator.
    """
    shared = scores_a.keys() & scores_b.keys()
    grouped: dict[tuple[str, int], Delta] = {}
    for key in shared:
        score_a, score_b = scores_a[key], scores_b[key]
        entry = grouped.setdefault(
            (score_a.config, score_a.tier),
            Delta(config=score_a.config, tier=score_a.tier, pairs=0, correct_a=0, correct_b=0),
        )
        entry.pairs += 1
        entry.correct_a += int(score_a.correct)
        entry.correct_b += int(score_b.correct)

    arms_a = {score.config for score in scores_a.values()}
    arms_b = {score.config for score in scores_b.values()}
    return Deltas(
        entries=sorted(grouped.values(), key=lambda d: (d.config, d.tier)),
        unpaired_a=len(scores_a) - len(shared),
        unpaired_b=len(scores_b) - len(shared),
        only_in_a=tuple(sorted(arms_a - arms_b)),
        only_in_b=tuple(sorted(arms_b - arms_a)),
    )


@dataclass
class RankCheck:
    """Whether the *ordering* of arms survived the axis change.

    The headline claims are rankings — Path 3 beats Path 1, direct beats the
    wrapper. Absolute accuracy is expected to move when the model changes; the
    ranking moving is what would invalidate a published conclusion. So this
    counts ordered pairs, not points.
    """

    tier: int
    concordant: int = 0
    discordant: int = 0
    unresolved: int = 0
    inversions: list[tuple[str, str]] = field(default_factory=list)

    @property
    def tau(self) -> float | None:
        """Rank agreement over *resolved* pairs only, in [-1, 1].

        Unresolved pairs are excluded rather than counted as agreement. Counting
        them as concordant would let a comparison in which nothing separated any
        arm report perfect rank stability.
        """
        decided = self.concordant + self.discordant
        return (self.concordant - self.discordant) / decided if decided else None


def rank_stability(entries: list[Delta], floor: float = NOISE_FLOOR) -> list[RankCheck]:
    """Per tier, how many arm orderings held across the axis change.

    A pair is `unresolved` when either capture separates the two arms by less
    than the noise floor. That is not a hedge: with a measured 1-point A/A
    floor, calling a 0.4-point gap an ordering and then calling its reversal an
    inversion manufactures a finding out of resampling noise.
    """
    checks: list[RankCheck] = []
    for tier in sorted({entry.tier for entry in entries}):
        at_tier = [
            entry for entry in entries
            if entry.tier == tier and entry.accuracy_a is not None
        ]
        check = RankCheck(tier=tier)
        for left, right in combinations(at_tier, 2):
            gap_a = (left.accuracy_a or 0) - (right.accuracy_a or 0)
            gap_b = (left.accuracy_b or 0) - (right.accuracy_b or 0)
            if abs(gap_a) < floor or abs(gap_b) < floor:
                check.unresolved += 1
            elif (gap_a > 0) == (gap_b > 0):
                check.concordant += 1
            else:
                check.discordant += 1
                check.inversions.append((left.config, right.config))
        checks.append(check)
    return checks


# --- Rendering -----------------------------------------------------------------


# What `scripts/export_capture.py` writes over the real project id on the way to
# publication. Duplicated rather than imported because `src/` must not depend on
# `scripts/`, and because the value is a published artifact — it appears in
# `results/capture.json.gz` and cannot be changed without reissuing that file.
PLACEHOLDER_PROJECT = "example-project"


def _scrub_hint(conflicts: dict[str, list[Any]]) -> list[str]:
    """Tell a `project` conflict apart from an unexported capture.

    The published capture is scrubbed, so its `project` reads `example-project`
    while a capture just taken reads the operator's real id. That is a genuine
    disagreement on a `MUST_AGREE` field and the refusal is correct — but the
    reader's next move is one command, not an investigation, and a refusal that
    does not say so reads as "these can never be compared".
    """
    values = conflicts.get("project")
    if not values or PLACEHOLDER_PROJECT not in values:
        return []
    return [
        f"`project` differs only because one side is scrubbed. `{PLACEHOLDER_PROJECT}` is "
        "the placeholder `make export` writes over the real id on the way to publication, "
        "so this is a publication difference rather than a measured one — but the "
        "comparator cannot tell the two apart from the header alone, and guessing is how "
        "captures from two different projects get subtracted. Export the unscrubbed side "
        "first (`make export RESULTS=<raw> OUT=<exported>`) and compare the exported files.",
        "",
    ]


def render(
    alignment: Alignment,
    result: Deltas,
    checks: list[RankCheck],
    labels: tuple[str, str],
) -> str:
    """A markdown section for one comparison.

    A refusal renders *instead of* the numbers, never above them. Both refusal
    kinds withhold: a conflict because the deltas would be unattributable, an
    inert axis because they would be zero by construction. The script exits
    non-zero for both, and printing tables under an exit-1 banner is how a
    refusal gets quoted as a finding.
    """
    label_a, label_b = labels
    lines = [f"# {label_a} vs {label_b}", ""]

    if alignment.conflicts:
        lines += [
            "## ⛔ Not comparable",
            "",
            "These captures disagree on fields the comparison does not vary, so a "
            "delta between them cannot be attributed to the declared axis:",
            "",
            report.table(
                ["field", label_a, label_b],
                [[name, *[str(value) for value in values]]
                 for name, values in sorted(alignment.conflicts.items())],
            ),
            "",
            *_scrub_hint(alignment.conflicts),
        ]
        return "\n".join(lines)

    if alignment.inert:
        lines += [
            f"## ⛔ Axis did not vary: {', '.join(alignment.inert)}",
            "",
            "Both captures hold the same value on the declared axis, so every delta "
            "would be zero by construction rather than by measurement. The numbers "
            "are withheld for the same reason a conflict withholds them: a table "
            "printed under a warning gets read as a result with an asterisk.",
            "",
        ]
        return "\n".join(lines)

    for name, values in sorted(alignment.varied.items()):
        lines.append(f"**{name}:** {values[0]} → {values[1]}")
    lines.append("")

    lines += [
        "## Accuracy delta, on paired cells only",
        "",
        report.table(
            ["arm", "tier", "pairs", label_a, label_b, "delta (pts)", "resolved"],
            [
                [
                    entry.config,
                    str(entry.tier),
                    str(entry.pairs),
                    report.fmt(entry.accuracy_a, ".0%"),
                    report.fmt(entry.accuracy_b, ".0%"),
                    report.fmt(entry.points, "+.1f"),
                    "yes" if entry.resolved else f"< {100 * NOISE_FLOOR:.0f} pt floor",
                ]
                for entry in result.entries
            ],
        ),
        "",
        _unpaired_note(result, labels),
        "",
        "## Rank stability",
        "",
        report.table(
            ["tier", "concordant", "inverted", "unresolved", "tau (resolved only)"],
            [
                [
                    str(check.tier),
                    str(check.concordant),
                    str(check.discordant),
                    str(check.unresolved),
                    report.fmt(check.tau, "+.2f"),
                ]
                for check in checks
            ],
        ),
        "",
    ]

    inversions = [pair for check in checks for pair in check.inversions]
    if inversions:
        named = "; ".join(f"{left} vs {right}" for left, right in inversions)
        lines += [f"**Orderings that reversed:** {named}.", ""]
    else:
        lines += ["**No ordering reversed** above the noise floor.", ""]
    return "\n".join(lines)


def _unpaired_note(result: Deltas, labels: tuple[str, str]) -> str:
    """What was dropped, always stated — a silent drop moves a denominator."""
    label_a, label_b = labels
    parts = []
    if result.unpaired_a or result.unpaired_b:
        parts.append(
            f"Unpaired cells excluded: {result.unpaired_a} in {label_a}, "
            f"{result.unpaired_b} in {label_b}."
        )
    if result.only_in_a:
        parts.append(f"Arms only in {label_a}: {', '.join(result.only_in_a)}.")
    if result.only_in_b:
        parts.append(f"Arms only in {label_b}: {', '.join(result.only_in_b)}.")
    return " ".join(parts) if parts else "Every cell paired."
