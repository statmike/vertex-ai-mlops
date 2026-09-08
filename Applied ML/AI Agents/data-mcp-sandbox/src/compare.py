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

# The floor a CROSS-CAPTURE delta has to clear, measured rather than assumed.
#
# The published 1-point A/A floor is the wrong one for this module, and using it
# here was a defect. That figure comes from `p4_bq_direct` and `p4_bq_direct_ctx`
# at tier 0, which send byte-identical requests and land 1 point apart (22% vs
# 23%, docs/paths.md) — but they do so *inside a single run*, sharing a sweep, an
# oracle and an hour of service weather. Two captures share none of that.
#
# C.4 measured the real thing. `capture-thinking-default` re-runs the published
# direct arms with the identical configuration a day later, so it is a true A/A
# across captures. Same arms, same tiers, same 240 cells:
#
#     p4_bq_direct      tier 0    21.7% → 28.3%    +6.7
#     p4_bq_direct_ctx  tier 0    23.3% → 28.3%    +5.0
#     p4_bq_direct_ctx  tier 1    95.0% → 90.0%    -5.0
#     p4_bq_direct      tier 1    88.3% → 90.0%    +1.7
#
# Nothing varied but the day. So a cross-capture delta under ~7 points is inside
# the noise, and the 1-point floor was quietly promoting several of those to
# "resolved". Set from the largest observed swing, not the mean, because the
# floor's job is to stop a false finding rather than to describe typical drift.
#
# Measured on the two direct arms at n=5. Sweeps whose arms run a local model
# have their own variance and this may understate them; a comparison that turns
# on a delta near the floor should measure its own A/A rather than trust this.
NOISE_FLOOR = 0.067

# Which tiers two different tier vocabularies are declared to agree on.
#
# `tier_semantics` says what the integers in `tiers` mean. Under plain equality a
# ladder capture (`ladder-v1`) could never be compared to the published one
# (unset) on any tier — which would defeat the reason the ladder appends rungs as
# 2/3/4 instead of renumbering. Tiers 0 and 1 were held fixed *precisely* so the
# two remain comparable, and a guard that forbids it is enforcing the opposite of
# the invariant it was built for.
#
# So compatibility is declared per pair and per tier, not assumed. Keyed by the
# unordered pair of scheme names; the value is the tiers on which they mean the
# same condition. A pair not on this table shares nothing and is refused — the
# default is refusal, and adding a scheme means stating what it is compatible
# with rather than inheriting compatibility by silence.
#
# `""` is the original two-tier scheme. It is spelled empty rather than
# `tiers-v1` so it collapses with the published capture's *missing* field, which
# predates this field existing at all.
SEMANTICS_SHARE: dict[frozenset[str], tuple[int, ...]] = {
    frozenset({"", "ladder-v1"}): (0, 1),
}


@dataclass
class Alignment:
    """Whether two captures may be compared, and on what.

    `varied` is what the caller declared may differ and did. `inert` is what it
    declared may differ and did *not* — a comparison whose axis turns out to be
    constant is measuring nothing, and silently reporting all-zero deltas is a
    worse outcome than saying so.

    `aa` inverts that last rule and nothing else. An A/A run *wants* every field
    constant, because the deltas it produces are the noise floor rather than a
    finding, so `inert` stops being a refusal. Everything else still holds: a
    conflict is still fatal, and more so here — an A/A that varied something is
    not a loose floor, it is a mislabelled experiment.

    `restricted` names the tiers the comparison was narrowed to, and is carried
    here rather than left to the caller because it changes what the numbers
    below mean. A floor measured on tier 0 alone is a tier-0 floor.
    """

    axes: tuple[str, ...]
    varied: dict[str, list[Any]] = field(default_factory=dict)
    inert: tuple[str, ...] = ()
    conflicts: dict[str, list[Any]] = field(default_factory=dict)
    aa: bool = False
    restricted: tuple[int, ...] = ()

    @property
    def ok(self) -> bool:
        if self.aa:
            return not self.conflicts
        return not self.conflicts and not self.inert


def restrict(scores: dict[str, scoring.Score], tiers: tuple[int, ...]) -> dict[str, scoring.Score]:
    """The subset of a capture's scores at the named tiers. Empty means all of them."""
    if not tiers:
        return scores
    return {key: score for key, score in scores.items() if score.tier in tiers}


def align(
    headers: list[dict[str, Any]],
    axes: tuple[str, ...],
    aa: bool = False,
    restricted: tuple[int, ...] = (),
) -> Alignment:
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

    **`restricted` changes how the two tier fields are checked**, and only for
    the tiers named. A capture holding tiers `(0, 2, 3, 4, 1)` and one holding
    `(0,)` describe different sweeps, but their tier-0 cells describe the same
    condition, and a comparison restricted to tier 0 looks at nothing else. C.2
    cannot run without this: the ladder's replication check is its rungs 0 and 4
    against the published capture's tiers 0 and 1, and the ladder declares five
    tiers where the published capture declares two.

    * `tiers` — *which* tiers ran — goes from equality to **presence**. A tier
      asked for and absent from either side is a conflict, not an empty result;
      a restriction that silently matches nothing pairs zero cells and reports
      0.0 drift, which is the "unmeasured reported as zero" mistake in its most
      convincing disguise.
    * `tier_semantics` — what the integers **mean** — goes from equality to
      **declared compatibility on the restricted tiers**, via `SEMANTICS_SHARE`.
      Not to presence, and not waived. It is the field that catches a capture
      whose `tier1` is a different condition, so relaxing it wholesale would
      remove the only thing making the `tiers` relaxation safe.

    Unrestricted, both stay under plain equality. Comparing two whole captures
    that ran different tier sets is still refused, because then the tier sets
    are part of what is being claimed to match.
    """
    result = Alignment(axes=axes, aa=aa, restricted=restricted)
    for name in traces.MUST_AGREE:
        values = [header.get(name) for header in headers]
        if name == "tiers" and restricted:
            if any(set(restricted) - _tier_set(value) for value in values):
                result.conflicts[name] = values
            continue
        if name == "tier_semantics" and restricted:
            if not set(restricted) <= shared_tiers(values):
                result.conflicts[name] = values
            continue
        differs = len({_comparable(value) for value in values}) > 1
        if name in axes:
            if differs:
                result.varied[name] = values
            else:
                result.inert = (*result.inert, name)
        elif differs:
            result.conflicts[name] = values
    return result


ALL_TIERS = frozenset(range(1000))


def shared_tiers(values: list[Any]) -> set[int]:
    """The tiers on which every capture's tier vocabulary means the same thing.

    All one scheme — the overwhelmingly common case, including two runs of the
    same harness — means every tier is shared. Otherwise the pair has to be on
    `SEMANTICS_SHARE`, and anything not declared there shares nothing.

    Unknown schemes returning the empty set rather than raising is deliberate:
    a capture from someone else's fork declares a name this table has never
    heard of, and the right answer is "these cannot be compared", printed, not
    a traceback.
    """
    schemes = {_scheme(value) for value in values}
    if len(schemes) <= 1:
        return set(ALL_TIERS)
    shared = set(ALL_TIERS)
    for pair in combinations(sorted(schemes), 2):
        shared &= set(SEMANTICS_SHARE.get(frozenset(pair), ()))
    return shared


def _scheme(value: object) -> str:
    """A capture's tier vocabulary, with unset spelled one way."""
    return "" if value is None else str(value)


def _tier_set(value: object) -> set[int]:
    """A header's `tiers` field as integers, tolerating the JSON round trip.

    A capture read back from gzipped JSON can hold these as strings; comparing
    `{0}` against `{"0"}` would report the published control as absent and
    refuse the comparison this exists to allow.
    """
    if not isinstance(value, list):
        return set()
    found = set()
    for item in value:
        try:
            found.add(int(item))
        except (TypeError, ValueError):
            continue
    return found


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
    than the noise floor. That is not a hedge: against a ~7-point cross-capture
    floor, calling a 3-point gap an ordering and then calling its reversal an
    inversion manufactures a finding out of day-to-day drift.
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


def _restriction_hint(alignment: Alignment) -> list[str]:
    """Say which requested tier is missing, rather than printing two tier lists.

    Under `restricted`, a `tiers` conflict means one side does not hold a tier
    that was asked for — not that the sweeps disagree. The generic conflict
    table shows `[0, 2, 3, 4, 1]` against `[0, 1]` and leaves the reader to
    work out which of the five was the problem.
    """
    if not alignment.restricted:
        return []
    hint: list[str] = []

    if "tiers" in alignment.conflicts:
        missing_lines = []
        for value in alignment.conflicts["tiers"]:
            missing = sorted(set(alignment.restricted) - _tier_set(value))
            if missing:
                missing_lines.append(
                    f"- a capture declaring `tiers = {value}` is missing tier(s) {missing}"
                )
        hint += [
            "The restriction asked for tiers that are not in both captures:",
            "",
            *missing_lines,
            "",
            "Restrict to a tier both sides actually ran. An absent tier pairs zero cells, "
            "and a comparison over zero cells reports 0.0 drift — a missing measurement "
            "rendered as a perfect one.",
            "",
        ]

    if "tier_semantics" in alignment.conflicts:
        schemes = sorted({_scheme(v) or "(unset)" for v in alignment.conflicts["tier_semantics"]})
        shared = sorted(shared_tiers(alignment.conflicts["tier_semantics"]))
        hint += [
            f"These captures number their tiers differently — {' vs '.join(schemes)} — and "
            f"`compare.SEMANTICS_SHARE` declares them to agree on "
            f"{'tier(s) ' + str(shared) if shared else '**no tiers at all**'}, "
            f"not on {list(alignment.restricted)}.",
            "",
            "A restriction cannot bridge that. Two files whose `tier2` means different "
            "things would pair a rung against a condition it never ran, and report the "
            "difference as a finding. Either restrict to a tier the two schemes share, "
            "or declare the compatibility in `SEMANTICS_SHARE` if it is genuinely true.",
            "",
        ]
    return hint


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

    if alignment.restricted:
        tiers = ", ".join(str(tier) for tier in alignment.restricted)
        lines += [
            f"Restricted to **tier {tiers}**. Cells at every other tier are excluded "
            "from the pairing, so the numbers below describe that tier and no other — "
            "a floor measured here is a tier-specific floor.",
            "",
        ]

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
            *_restriction_hint(alignment),
        ]
        return "\n".join(lines)

    if alignment.aa:
        return "\n".join(lines + _aa_section(result, labels))

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
                    "yes" if entry.resolved else f"< {100 * NOISE_FLOOR:.1f} pt floor",
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


def measured_floor(result: Deltas) -> float:
    """The largest swing an A/A produced, as a fraction — the floor it measured.

    The largest and not the mean. A noise floor exists to stop a false finding,
    so it has to cover the worst drift actually observed; a floor set at typical
    drift is exceeded about half the time by definition.

    Entries with nothing paired hold `points is None` and are skipped rather than
    counted as zero drift — an arm that failed to pair measured no floor, and
    scoring it as perfect agreement would drag the maximum down.
    """
    return max(
        (abs(entry.points) / 100 for entry in result.entries if entry.points is not None),
        default=0.0,
    )


def _aa_section(result: Deltas, labels: tuple[str, str]) -> list[str]:
    """The A/A report: deltas read as a floor rather than as findings.

    Deliberately does *not* print rank stability. Ranks here are noise being
    sorted, and a `tau` next to an A/A table is an invitation to read
    reproducible ordering into two captures that measured the same thing.
    """
    label_a, label_b = labels
    floor = measured_floor(result)
    verdict = (
        "covers this" if floor <= NOISE_FLOOR
        else f"is EXCEEDED by this — consider raising it to {floor:.3f}"
    )
    return [
        "## A/A: these captures varied nothing",
        "",
        "Every field in `MUST_AGREE` is identical, so the deltas below are what "
        "the same configuration produces against itself. They are a **noise "
        "floor**, not a result — read them as the size a real finding has to "
        "beat.",
        "",
        report.table(
            ["arm", "tier", "pairs", label_a, label_b, "drift (pts)"],
            [
                [
                    entry.config,
                    str(entry.tier),
                    str(entry.pairs),
                    report.fmt(entry.accuracy_a, ".0%"),
                    report.fmt(entry.accuracy_b, ".0%"),
                    report.fmt(entry.points, "+.1f"),
                ]
                for entry in result.entries
            ],
        ),
        "",
        _unpaired_note(result, labels),
        "",
        f"**Largest drift: {100 * floor:.1f} points.** The floor `compare` "
        f"currently applies is {100 * NOISE_FLOOR:.1f} points, and it {verdict}.",
        "",
        "Two caveats before reusing this number. It is measured on whichever "
        "arms these captures happen to hold, and an arm running a local model "
        "has variance of its own. And an A/A taken minutes apart measures less "
        "than one taken a day apart — the floor grows with the gap it has to "
        "span, so measure it over the same interval your real comparison spans.",
        "",
    ]


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
