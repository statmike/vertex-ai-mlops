"""Charts for the results notebook.

Lives here rather than in the notebook because notebooks hold narrative and
execution, never logic (Golden Rule #1). Each function takes scored cells and
returns a Figure; nothing here writes files or calls `show`, so the caller
decides where a chart ends up.

The same rule the tables follow applies to every axis: **an unmeasured value is
absent, not zero.** A bar of height zero on an accuracy chart is a claim the arm
got everything wrong. Arms that cannot be measured on a metric are dropped from
that chart and named in its subtitle instead.

A partly-measured value gets a third treatment, because dropping it would hide a
real arm and plotting it plain would overstate it: a **floor** is drawn hollow
with an arrow in the direction the true value lies. Path 4 is the case — see
`cost_vs_accuracy`, where a floor happens to land on the flattering end of the
axis, which is the one place this distinction changes a reader's conclusion.
"""

from collections import defaultdict
from collections.abc import Iterable

import matplotlib
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
from matplotlib.transforms import Bbox

import mcp_clients
import scoring

# Names, not the module. `config` is a loop variable throughout this file (it is
# the arm key), so `import config` would be shadowed inside `cost_vs_accuracy`
# and read as if it were not.
from config import TIER_LABELS, carries, rung_key, rung_of

# No `matplotlib.use(...)` here on purpose. Nothing in this module touches
# pyplot — figures are constructed directly and `_label` attaches its own Agg
# canvas when it needs to measure text — so the global backend is irrelevant
# headless, and forcing one would break `%matplotlib inline` in a notebook.

# Keyed by tier integer, ordered by rung: red control, warming through the
# intermediate rungs, blue at the fully governed top. The two published tiers keep
# the colours the committed figures already use, so a ladder capture adds rungs to
# these charts rather than restyling them.
TIER_COLOR = {0: "#c44e52", 2: "#dd8452", 3: "#c9a227", 4: "#8172b3", 1: "#4c72b0"}
TIER_LABEL = {0: "tier 0 · ungoverned", 1: "tier 1 · governed"}


def _tiers_in(scores: Iterable[scoring.Score]) -> list[int]:
    """Every tier present, in ladder reading order — never sorted by the integer.

    Read off the capture rather than off `config.TIERS`, because a chart is
    rendered from a file and the reader's `LADDER` env var says nothing about
    what that file holds.
    """
    return sorted({score.tier for score in scores}, key=rung_key)


def _is_ladder(tiers: Iterable[int]) -> bool:
    """Whether these tiers are a ladder rather than the published pair."""
    return bool(set(tiers) - {0, 1})


def _tier_label(tier: int, ladder: bool) -> str:
    """A tier's legend entry.

    Two-tier captures keep their published wording verbatim; the ladder prints
    the rung position and the increment, because `tier 4 · governed` would be
    wrong twice over — 4 is not the position and the tier is not the top rung.
    """
    if not ladder:
        return TIER_LABEL[tier]
    return f"rung {rung_of(tier)} · {TIER_LABELS[tier]}"


def _by_arm(scores: Iterable[scoring.Score]) -> dict[tuple[str, int], list[scoring.Score]]:
    """Group scored cells by (config, tier)."""
    grouped: dict[tuple[str, int], list[scoring.Score]] = defaultdict(list)
    for score in scores:
        grouped[(score.config, score.tier)].append(score)
    return grouped


def _is_floor(config_key: str) -> bool:
    """Is this arm's recorded cost a lower bound rather than a total?

    One definition, in `mcp_clients`, next to the config table it reads — a chart
    that disagreed with the report's `coverage` column about which arms are
    floors would be worse than either being wrong alone.
    """
    return mcp_clients.has_unmeasured_service(config_key)


def _rate(cells: list[scoring.Score], predicate: str) -> float:
    return sum(getattr(cell, predicate) for cell in cells) / len(cells) if cells else 0.0


def accuracy_by_tier(scores: dict[str, scoring.Score]) -> Figure:
    """Accuracy per arm, tier 0 beside tier 1. The headline chart.

    Paired bars rather than two panels: the governance effect is a *within-arm*
    difference, and putting the pair side by side is the only layout where that
    reads at a glance.
    """
    grouped = _by_arm(scores.values())
    configs = sorted({config for config, _ in grouped})
    positions = np.arange(len(configs))
    tiers = _tiers_in(scores.values())
    ladder = _is_ladder(tiers)
    # 0.76 total across however many tiers there are. At two that is 0.38 with
    # offsets at ∓0.19 — exactly the published geometry, so adding ladder support
    # does not redraw the committed two-tier figures.
    width = 0.76 / len(tiers)

    fig, ax = _figure(9, 4.5)
    for index, tier in enumerate(tiers):
        offset = (index - (len(tiers) - 1) / 2) * width
        values = [_rate(grouped.get((config, tier), []), "correct") for config in configs]
        ax.bar(positions + offset, values, width,
               label=_tier_label(tier, ladder), color=TIER_COLOR[tier])

    ax.set_xticks(positions)
    ax.set_xticklabels(configs, rotation=30, ha="right")
    ax.set_ylabel("correct answers")
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
    ax.set_title("Governance roughly doubles accuracy, on every path")
    ax.legend(frameon=False)
    return fig


def cost_vs_accuracy(scores: dict[str, scoring.Score]) -> Figure:
    """Tokens spent per correct answer against accuracy, log x.

    The procurement chart. Log scale because the arms span two orders of
    magnitude, which is itself the finding — a linear axis collapses ten arms
    into one indistinguishable column.

    **Path 4 is drawn hollow, with an arrow.** Conversational Analytics runs its
    own Gemini loop server-side and reports none of it, so those two arms are
    plotted at a floor, not a cost. Left is cheap on this axis, so a floor lands
    an arm exactly where a reader concludes "cheapest" — and metering
    `p4_looker_ca` from Cloud Monitoring moved it 22x to the right, from first
    place to third-most-expensive. A solid dot there would be the most
    consequential wrong pixel in the whole report. The arrow says *at least*.
    """
    fig, ax = _figure(8, 5)
    points, floors, unpriced = [], [], []
    for (config, tier), cells in sorted(_by_arm(scores.values()).items()):
        correct = sum(cell.correct for cell in cells)
        tokens = sum(cell.total_tokens for cell in cells)
        if correct and not tokens:
            # An arm that answered and spent nothing this process could see. It
            # has no x, and putting it at zero would place the two most accurate
            # tier-1 arms at "free" on a chart whose whole point is that cheap
            # and wrong is not cheap.
            unpriced.append(config)
        if not correct or not tokens:
            continue  # no correct answers means no cost-per-correct, not an infinite one
        x, y = tokens / correct, correct / len(cells)
        if _is_floor(config):
            # Hollow, so it reads as an open bound rather than a measurement.
            ax.scatter(x, y, s=70, facecolors="none", edgecolors=TIER_COLOR[tier], linewidths=1.6)
            # A patch, not `annotate("")`. An empty annotation is still a Text,
            # and it lands in `ax.texts` alongside the real labels — where the
            # placement tests read them, and where an invisible zero-width box
            # would quietly satisfy an overlap check on behalf of nothing.
            ax.add_patch(FancyArrowPatch(
                (x * 1.13, y), (x * 2.2, y), arrowstyle="->", mutation_scale=9,
                color=TIER_COLOR[tier], linewidth=1.2, alpha=0.8,
            ))
            floors.append((x, y, f"{config} t{tier} ≥"))
        else:
            ax.scatter(x, y, s=70, color=TIER_COLOR[tier], alpha=0.85)
            points.append((x, y, f"{config} t{tier}"))

    ax.set_xscale("log")
    # Cheap is *left* on a cost axis. An earlier version of this label said
    # "righter is better", which inverts the whole chart for anyone skimming it.
    ax.set_xlabel("tokens per correct answer  (log scale — cheaper is left)")
    ax.set_ylabel("accuracy")
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
    # Derived, not written down. A spread quoted in a title is the kind of number
    # that survives three captures after it stopped being true. Measured across
    # the fully-attributed arms only — a floor cannot bound a range.
    spread = max(x for x, _, _ in points) / min(x for x, _, _ in points)
    ax.set_title(f"Best is top-left: accurate and cheap. "
                 f"{spread:.0f}x spread across the measured arms.")
    _tier_legend(ax, _tiers_in(scores.values()), floors=bool(floors))
    _excluded_note(fig, unpriced, "no model runs in this process, so they have no cost axis")
    _label(fig, ax, points + floors)  # last: it measures the finished axes
    return fig


def schema_size_vs_cost(
    scores: dict[str, scoring.Score], schemas: dict[str, dict[str, int]]
) -> Figure:
    """Measured tool-schema size against observed median tokens, both log.

    `schemas` is the `tool_schemas` block from a capture header. This is the
    Amendment A.1 finding as a picture: declarations are re-sent every turn, so
    their serialized size sets a prompt-token floor — and it predicts observed
    cost almost exactly, across arms that differ in nothing else.
    """
    fig, ax = _figure(7.5, 5)
    points, toolless = [], []
    for (config, tier), cells in sorted(_by_arm(scores.values()).items()):
        entry = schemas.get(config, {})
        chars = entry.get("schema_chars")
        tokens = [cell.total_tokens for cell in cells if cell.total_tokens]
        if not chars and not tokens:
            # Neither axis exists: no tools to declare and no local model to
            # charge for declaring them. Genuinely not applicable rather than
            # missing, but a reader counting arms still deserves to be told.
            toolless.append(config)
        if not chars or not tokens:
            continue
        ax.scatter(chars, float(np.median(tokens)), s=70, color=TIER_COLOR[tier], alpha=0.85)
        points.append((float(chars), float(np.median(tokens)), f"{config} t{tier}"))

    if not points:
        # Schema measurement was added part-way through the project, so an older
        # capture has no sizes to plot. Drawing empty axes under a title that
        # asserts a finding is the worst possible output here: it looks like a
        # measured null result. Say what is missing instead.
        ax.set_title("Tool schema sizes were not measured in this capture")
        ax.set_axis_off()
        ax.text(0.5, 0.5, "This capture's header carries no `tool_schemas` block.\n"
                          "Re-run the sweep to record one.",
                ha="center", va="center", fontsize=9, color="#555555")
        return fig

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("tool schema size (characters, measured at sweep time)")
    ax.set_ylabel("median tokens per cell")
    ax.set_title("Schema verbosity, not tool count, predicts what an arm costs")
    _tier_legend(ax, _tiers_in(scores.values()))
    _excluded_note(fig, toolless, "they bind no tools, so neither axis applies")
    _label(fig, ax, points)  # last: it measures the finished axes
    return fig


def acquisition_vs_application(scores: dict[str, scoring.Score]) -> Figure:
    """Where governed cells are lost: never acquired the rule, or acquired and misapplied.

    Only arms where acquisition is *observable* appear. Acquisition is read off
    the tool trace — did the agent call `lookup_context` and get a rule back —
    and no Path 4 arm has one, because the loop runs inside Conversational
    Analytics. That holds even for the direct-API arms, which do disclose their
    SQL: evidence and acquisition are different metrics, and recovering one does
    not recover the other. Excluded rather than drawn as zero bars, and named in
    the subtitle so the absence is a statement instead of an omission.
    """
    # `carries(tier, "rules")`, not `tier == 1`. Those agree on the published
    # capture and disagree on the ladder, where rung 3 (`tier4`) is the rung that
    # *adds* business rules — filtering it out would drop the one rung this chart
    # exists to explain and leave the top rung claiming the whole effect.
    grouped = _by_arm(
        score for score in scores.values()
        if score.rules_required and carries(score.tier, "rules")
    )
    opaque = sorted({
        config for (config, _), cells in grouped.items()
        if not any(cell.acquisition_observable for cell in cells)
    })
    # By rung within an arm, not by the tier integer: sorting `(config, tier)`
    # would put the top rung (`tier1`) to the left of the rung below it (`tier4`).
    rule_tiers = sorted({tier for _, tier in grouped}, key=rung_key)
    ladder = _is_ladder(rule_tiers)
    arms = sorted(
        (key for key in grouped if key[0] not in opaque),
        key=lambda key: (key[0], rung_key(key[1])),
    )

    fig, ax = _figure(8, 4.5)
    positions = np.arange(len(arms))
    applied = [_rate(grouped[arm], "correct") for arm in arms]
    lost = [_rate(grouped[arm], "application_loss") for arm in arms]
    missed = [1 - a - loss for a, loss in zip(applied, lost, strict=True)]

    ax.bar(positions, applied, 0.6, label="rule applied, answer correct", color="#55a868")
    ax.bar(positions, lost, 0.6, bottom=applied, label="rule acquired, misapplied",
           color="#dd8452")
    ax.bar(positions, missed, 0.6, bottom=np.add(applied, lost),
           label="other failure", color="#b0b0b0")

    ax.set_xticks(positions)
    # On the ladder each arm appears once per rule-carrying rung, so the arm name
    # alone would label two different bars identically.
    ax.set_xticklabels(
        [f"{config} · r{rung_of(tier)}" if ladder else f"{config}" for config, tier in arms],
        rotation=30, ha="right",
    )
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
    ax.set_ylabel(
        "cells carrying the rule, by rung" if ladder else "governed cells, tier 1"
    )
    ax.set_title("Acquiring the rule is solved. Applying it is not.")
    if opaque:
        ax.set_xlabel(f"excluded — no tool trace, so acquisition is unobservable: "
                      f"{', '.join(opaque)}", fontsize=8)
    ax.legend(frameon=False, fontsize=8)
    return fig


# Where a label may sit relative to its point: (dx, dy in points, alignment).
# Both axes matter. Stacking alone left two arms overlapping *horizontally* —
# an arm's name is ~70px of text and reaches into its neighbour — so the slots
# alternate side as well as height.
#
# Right of the point first, then left, then the rows above and below. The
# outward rows are tried before the far side of the same row so that a label
# never gets aimed into the narrow gap between two neighbouring points.
_SLOTS = (
    (8, 4, "left"),
    (-8, 4, "right"),
    (8, -12, "left"),
    (-8, -12, "right"),
    (8, 17, "left"),
    (-8, 17, "right"),
    (8, -25, "left"),
    (-8, -25, "right"),
)

_MARKER_HALF = 7.0  # px; keeps a label off its own dot and its neighbours'


def _label(
    fig: Figure, ax: "matplotlib.axes.Axes", points: list[tuple[float, float, str]]
) -> None:
    """Annotate scatter points, placing each label where nothing else already is.

    The plotted arms land in two tight clusters on both scatters and their labels
    collided. Two heuristics on point *proximity* were tried first and both
    left overlaps, because what collides is the rendered text box — an arm's
    name is ~70px wide, so two points a comfortable distance apart can still
    have labels that meet in the middle.

    So this measures instead of guessing: draw once to get a renderer, then for
    each label try the slots in order and keep the first whose real bounding box
    hits neither a marker, the legend, another label, nor the axes edge. Falls
    back to the first slot if a point is genuinely boxed in.
    """
    # A `Figure` built without pyplot has no renderer until something draws it,
    # and text has no measurable size without one.
    # The Agg backend ships no stubs for these two, hence the ignores.
    canvas = FigureCanvasAgg(fig)
    canvas.draw()  # type: ignore[no-untyped-call]
    renderer = canvas.get_renderer()  # type: ignore[no-untyped-call]

    frame = ax.get_window_extent(renderer)
    occupied = [_marker_box(ax, x, y) for x, y, _ in points]
    legend = ax.get_legend()
    if legend is not None:
        occupied.append(legend.get_window_extent(renderer))

    for x, y, text in sorted(points):
        for index, (dx, dy, align) in enumerate(_SLOTS):
            annotation = ax.annotate(text, (x, y), textcoords="offset points",
                                     xytext=(dx, dy), ha=align, fontsize=7)
            box = annotation.get_window_extent(renderer)
            # Both axes, not just x. Checking width alone let a label on a
            # top-row point escape above the axes and render across the title —
            # it never overlapped another *label*, so the collision test passed
            # while the chart was visibly broken.
            inside = (frame.x0 <= box.x0 and box.x1 <= frame.x1
                      and frame.y0 <= box.y0 and box.y1 <= frame.y1)
            last = index == len(_SLOTS) - 1
            if last or (inside and not any(box.overlaps(other) for other in occupied)):
                occupied.append(box)
                break
            annotation.remove()


def _marker_box(ax: "matplotlib.axes.Axes", x: float, y: float) -> Bbox:
    """The dot itself, in display coordinates, so no label lands on top of one."""
    px, py = ax.transData.transform((x, y))
    return Bbox.from_extents(
        px - _MARKER_HALF, py - _MARKER_HALF, px + _MARKER_HALF, py + _MARKER_HALF
    )


def _tier_legend(
    ax: "matplotlib.axes.Axes",
    tiers: list[int] | None = None,
    floors: bool = False,
) -> None:
    """Name the two colours on charts that carry no labelled series.

    The bar charts get a legend from their own artists; the scatters encode tier
    in colour alone, which is an unreadable chart without this. `floors` adds the
    hollow marker, which encodes something stronger than a colour and so must be
    spelled out rather than left to the caption.
    """
    # Room for the outermost labels, which otherwise clip. `y` matters as much as
    # `x`: without it the top-row arms have nowhere above them to put a label and
    # all fall back to their below-slot, straight into the cluster underneath.
    ax.margins(x=0.14, y=0.10)
    shown = list(tiers) if tiers else [0, 1]
    ladder = _is_ladder(shown)
    handles = [Line2D([], [], marker="o", linestyle="", color=TIER_COLOR[tier],
                      label=_tier_label(tier, ladder)) for tier in shown]
    if floors:
        handles.append(Line2D([], [], marker="o", linestyle="", markerfacecolor="none",
                              markeredgecolor="#555555", color="#555555",
                              label="floor — true cost is further right"))
    ax.legend(handles=handles, frameon=False, fontsize=8, loc="lower right")


def _excluded_note(fig: Figure, arms: list[str], because: str) -> None:
    """Name the arms a chart could not plot, on the chart.

    Both scatters drop an arm with no x value, and after the direct-API arms
    landed that is two of twelve — including the two most accurate arms at tier
    1. A `continue` says nothing to a reader, so a chart that silently omits them
    reads as a chart of every arm that ran. That is the same mistake as printing
    an unmeasured cell as 0, moved from a table into a picture, and it is harder
    to catch there because nothing is visibly missing.

    Callers append per *cell*, so an arm excluded at both tiers arrives twice.
    Deduplicated here rather than at each call site: the note names arms, and
    "p4_bq_direct, p4_bq_direct" reads as a bug in the chart, which undermines
    the one thing the note exists to do.
    """
    if not arms:
        return
    fig.text(
        0.5, -0.01, f"Not plotted: {', '.join(sorted(set(arms)))} — {because}.",
        ha="center", va="top", fontsize=7.5, color="#555555",
    )


def _figure(width: float, height: float) -> tuple[Figure, "matplotlib.axes.Axes"]:
    """A bare figure with the chrome turned down, so the data carries the chart."""
    fig = Figure(figsize=(width, height), dpi=130, layout="constrained")
    ax = fig.add_subplot()
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    return fig, ax
