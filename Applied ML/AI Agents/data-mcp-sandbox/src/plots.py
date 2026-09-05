"""Charts for the results notebook.

Lives here rather than in the notebook because notebooks hold narrative and
execution, never logic (Golden Rule #1). Each function takes scored cells and
returns a Figure; nothing here writes files or calls `show`, so the caller
decides where a chart ends up.

The same rule the tables follow applies to every axis: **an unmeasured value is
absent, not zero.** A bar of height zero on an accuracy chart is a claim the arm
got everything wrong. Arms that cannot be measured on a metric are dropped from
that chart and named in its subtitle instead.
"""

from collections import defaultdict
from collections.abc import Iterable

import matplotlib
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.transforms import Bbox

import scoring

# No `matplotlib.use(...)` here on purpose. Nothing in this module touches
# pyplot — figures are constructed directly and `_label` attaches its own Agg
# canvas when it needs to measure text — so the global backend is irrelevant
# headless, and forcing one would break `%matplotlib inline` in a notebook.

TIER_COLOR = {0: "#c44e52", 1: "#4c72b0"}
TIER_LABEL = {0: "tier 0 · ungoverned", 1: "tier 1 · governed"}


def _by_arm(scores: Iterable[scoring.Score]) -> dict[tuple[str, int], list[scoring.Score]]:
    """Group scored cells by (config, tier)."""
    grouped: dict[tuple[str, int], list[scoring.Score]] = defaultdict(list)
    for score in scores:
        grouped[(score.config, score.tier)].append(score)
    return grouped


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
    width = 0.38

    fig, ax = _figure(9, 4.5)
    for offset, tier in ((-width / 2, 0), (width / 2, 1)):
        values = [_rate(grouped.get((config, tier), []), "correct") for config in configs]
        ax.bar(positions + offset, values, width, label=TIER_LABEL[tier], color=TIER_COLOR[tier])

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
    magnitude, which is itself the finding — a linear axis collapses nine arms
    into one indistinguishable column.
    """
    fig, ax = _figure(8, 5)
    points = []
    for (config, tier), cells in sorted(_by_arm(scores.values()).items()):
        correct = sum(cell.correct for cell in cells)
        tokens = sum(cell.total_tokens for cell in cells)
        if not correct or not tokens:
            continue  # no correct answers means no cost-per-correct, not an infinite one
        ax.scatter(tokens / correct, correct / len(cells), s=70,
                   color=TIER_COLOR[tier], alpha=0.85)
        points.append((tokens / correct, correct / len(cells), f"{config} t{tier}"))

    ax.set_xscale("log")
    # Cheap is *left* on a cost axis. An earlier version of this label said
    # "righter is better", which inverts the whole chart for anyone skimming it.
    ax.set_xlabel("tokens per correct answer  (log scale — cheaper is left)")
    ax.set_ylabel("accuracy")
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
    # Derived, not written down. A spread quoted in a title is the kind of number
    # that survives three captures after it stopped being true.
    spread = max(x for x, _, _ in points) / min(x for x, _, _ in points)
    ax.set_title(f"Best is top-left: accurate and cheap. The spread is {spread:.0f}x.")
    _tier_legend(ax)
    _label(fig, ax, points)  # last: it measures the finished axes
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
    points = []
    for (config, tier), cells in sorted(_by_arm(scores.values()).items()):
        entry = schemas.get(config, {})
        chars = entry.get("schema_chars")
        tokens = [cell.total_tokens for cell in cells if cell.total_tokens]
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
    _tier_legend(ax)
    _label(fig, ax, points)  # last: it measures the finished axes
    return fig


def acquisition_vs_application(scores: dict[str, scoring.Score]) -> Figure:
    """Where governed cells are lost: never acquired the rule, or acquired and misapplied.

    Only arms where acquisition is *observable* appear — Path 4 discloses no tool
    evidence, so it is excluded rather than drawn as a zero bar, and named in the
    subtitle so its absence is a statement instead of an omission.
    """
    grouped = _by_arm(
        score for score in scores.values() if score.rules_required and score.tier == 1
    )
    opaque = sorted({
        config for (config, _), cells in grouped.items()
        if not any(cell.acquisition_observable for cell in cells)
    })
    arms = sorted(key for key in grouped if key[0] not in opaque)

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
    ax.set_xticklabels([f"{config}" for config, _ in arms], rotation=30, ha="right")
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
    ax.set_ylabel("governed cells, tier 1")
    ax.set_title("Acquiring the rule is solved. Applying it is not.")
    if opaque:
        ax.set_xlabel(f"excluded — no tool evidence to inspect: {', '.join(opaque)}", fontsize=8)
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

    Ten arms land in two tight clusters on both scatters and their labels
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


def _tier_legend(ax: "matplotlib.axes.Axes") -> None:
    """Name the two colours on charts that carry no labelled series.

    The bar charts get a legend from their own artists; the scatters encode tier
    in colour alone, which is an unreadable chart without this.
    """
    # Room for the outermost labels, which otherwise clip. `y` matters as much as
    # `x`: without it the top-row arms have nowhere above them to put a label and
    # all fall back to their below-slot, straight into the cluster underneath.
    ax.margins(x=0.14, y=0.10)
    ax.legend(
        handles=[Line2D([], [], marker="o", linestyle="", color=TIER_COLOR[tier],
                        label=TIER_LABEL[tier]) for tier in (0, 1)],
        frameon=False, fontsize=8, loc="lower right",
    )


def _figure(width: float, height: float) -> tuple[Figure, "matplotlib.axes.Axes"]:
    """A bare figure with the chrome turned down, so the data carries the chart."""
    fig = Figure(figsize=(width, height), dpi=130, layout="constrained")
    ax = fig.add_subplot()
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    return fig, ax
