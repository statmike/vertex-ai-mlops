"""Invariants for the charts.

A chart is the part of a result most people will look at and the part least
likely to be checked, because the code that draws a wrong chart runs perfectly.
So the two failures pinned here are both silent ones: a chart that asserts a
finding over no data, and labels that overlap into unreadable mush.
"""

import plots
import scoring


def _score(config: str, tier: int, *, correct: bool, tokens: int, index: int) -> scoring.Score:
    return scoring.Score(
        cell_key=f"{config}-{tier}-{index}",
        config=config,
        tier=tier,
        question_id=f"q{index}",
        category="direct",
        answered=True,
        correct=correct,
        total_tokens=tokens,
    )


def _scores(arms: dict[str, int]) -> dict[str, scoring.Score]:
    out = {}
    for index, (config, tokens) in enumerate(arms.items()):
        for tier in (0, 1):
            for replicate in range(2):
                score = _score(config, tier, correct=bool(tier), tokens=tokens,
                               index=index * 10 + replicate)
                out[score.cell_key] = score
    return out


def test_schema_chart_says_so_when_the_capture_measured_nothing():
    # Captures written before schema measurement existed carry no sizes. Drawing
    # empty axes under "schema verbosity predicts cost" would read as a measured
    # null result, which is the exact false finding this project refuses to make.
    figure = plots.schema_size_vs_cost(_scores({"p1_managed": 500_000}), schemas={})
    axes = figure.axes[0]
    assert not axes.collections, "nothing should be plotted"
    assert "not measured" in axes.get_title()
    assert any("tool_schemas" in text.get_text() for text in axes.texts)


def test_schema_chart_skips_arms_the_header_does_not_cover():
    scores = _scores({"p1_managed": 500_000, "p1_toolbox": 50_000})
    figure = plots.schema_size_vs_cost(scores, schemas={"p1_managed": {"schema_chars": 120_009}})
    labels = {text.get_text() for text in figure.axes[0].texts}
    assert labels == {"p1_managed t0", "p1_managed t1"}


def test_every_point_gets_exactly_one_label():
    scores = _scores({"p1_managed": 500_000, "p1_toolbox": 50_000, "p4_bq_ca": 9_000})
    figure = plots.cost_vs_accuracy(scores)
    # Tier 0 is never correct in the fixture, so it has no cost-per-correct and
    # is dropped rather than plotted at infinity. `p4_bq_ca` carries a floor
    # marker; only real labels may reach `ax.texts`, so an arrow drawn as an
    # empty annotation would show up here as a stray ''.
    assert {text.get_text() for text in figure.axes[0].texts} == {
        "p1_managed t1", "p1_toolbox t1", "p4_bq_ca t1 ≥",
    }


def test_a_floor_is_drawn_as_a_bound_not_a_measurement():
    # The one place this matters: cheap is *left*, so an arm whose cost is only a
    # lower bound lands where a reader concludes "cheapest". Metering
    # `p4_looker_ca` server-side moved it 22x right, off first place entirely. A
    # solid dot there is a wrong finding, not a rounding error.
    scores = _scores({"p1_toolbox": 50_000, "p4_bq_ca": 9_000})
    axes = plots.cost_vs_accuracy(scores).axes[0]

    hollow = [c for c in axes.collections if not len(c.get_facecolor())
              or c.get_facecolor()[0][3] == 0]
    assert len(hollow) == 1, "exactly the Path 4 arm should be hollow"
    assert axes.patches, "a floor needs an arrow saying which way the truth lies"
    assert any("floor" in text.get_text() for text in axes.get_legend().get_texts())
    # The spread in the title is quoted across measured arms only; a bound
    # cannot widen a range.
    assert "measured arms" in axes.get_title()


def test_an_arm_with_no_cost_axis_is_named_rather_than_dropped():
    # The direct-API arms record 0 tokens because no model runs in this process,
    # so they have no x on a cost chart and are skipped. They are also the two
    # most accurate arms at tier 1 — dropping them without a word leaves a
    # procurement chart that looks complete and is missing its winners.
    scores = _scores({"p1_toolbox": 50_000, "p4_bq_direct": 0})
    figure = plots.cost_vs_accuracy(scores)
    assert "p4_bq_direct t1" not in {text.get_text() for text in figure.axes[0].texts}
    note = " ".join(text.get_text() for text in figure.texts)
    assert "p4_bq_direct" in note and "Not plotted" in note
    # Excluded at both tiers, named once. The fixture carries two tiers per arm
    # and the caller appends per cell, so the first draft of this note read
    # "p4_bq_direct, p4_bq_direct".
    assert note.count("p4_bq_direct") == 1


def test_an_arm_with_tools_and_tokens_gets_no_exclusion_note():
    # The note must fire on the structural case only. An arm the *header* happens
    # not to cover is a different bug, already covered above, and labelling it
    # "binds no tools" would send a reader to look for a cause that is not there.
    figure = plots.schema_size_vs_cost(
        _scores({"p1_managed": 500_000, "p1_toolbox": 50_000}),
        schemas={"p1_managed": {"schema_chars": 120_009},
                 "p1_toolbox": {"schema_chars": 7_030}},
    )
    assert not figure.texts


def test_a_toolless_arm_is_named_on_the_schema_chart():
    figure = plots.schema_size_vs_cost(
        _scores({"p1_managed": 500_000, "p4_bq_direct": 0}),
        schemas={"p1_managed": {"schema_chars": 120_009},
                 "p4_bq_direct": {"tools": 0, "schema_chars": 0}},
    )
    note = " ".join(text.get_text() for text in figure.texts)
    assert "p4_bq_direct" in note and "no tools" in note


# (correct, tokens-per-correct) per tier, read off the M6 capture. Rounded shapes
# would not do: this test only bites at the real geometry, where the top cluster
# sits just under the frame edge instead of in synthetic headroom.
_M6_COST_SHAPE = {
    "p1_managed": ((22, 1689323), (40, 572233)), "p1_toolbox": ((20, 252921), (45, 46428)),
    "p2_managed": ((20, 362823), (44, 56688)), "p2_toolbox": ((19, 481595), (45, 83898)),
    "p3_managed": ((21, 3159221), (45, 626026)), "p3_toolbox": ((20, 583464), (45, 124546)),
    "p1_matched": ((21, 344345), (40, 96193)), "p3_matched": ((21, 777949), (45, 117246)),
    "p4_bq_ca": ((14, 55464), (45, 8807)), "p4_looker_ca": ((9, 182560), (21, 24874)),
}


def test_labels_stay_inside_the_axes():
    # `p2_toolbox t1` shipped drawn across the chart title. It overlapped no other
    # *label*, so the overlap test below passed while the chart was visibly
    # broken: the containment check measured width and not height, and the axes
    # carried no y-margin, so the top cluster had nowhere to put a label but out.
    # Either guard alone fixes it, which is why this asserts the invariant rather
    # than one of them — the failure needs both to be missing.
    scores = {}
    for index, (arm, tiers) in enumerate(_M6_COST_SHAPE.items()):
        for tier, (correct, per_correct) in enumerate(tiers):
            for replicate in range(60):
                score = _score(arm, tier, correct=replicate < correct,
                               tokens=correct * per_correct // 60,
                               index=index * 100 + replicate)
                scores[score.cell_key] = score

    axes = plots.cost_vs_accuracy(scores).axes[0]
    renderer = axes.figure.canvas.get_renderer()
    frame = axes.get_window_extent(renderer)
    escaped = [
        text.get_text() for text in axes.texts
        if not (frame.y0 <= text.get_window_extent(renderer).y0
                and text.get_window_extent(renderer).y1 <= frame.y1
                and frame.x0 <= text.get_window_extent(renderer).x0
                and text.get_window_extent(renderer).x1 <= frame.x1)
    ]
    assert not escaped, f"drawn outside the axes, into the title: {escaped}"


def test_labels_do_not_overlap_each_other():
    # Three arms within a factor of two of each other in both axes: the layout
    # that produced unreadable output before labels were placed by measurement.
    scores = _scores({"p1_toolbox": 50_000, "p2_toolbox": 56_000, "p2_managed": 62_000})
    figure = plots.schema_size_vs_cost(scores, schemas={
        "p1_toolbox": {"schema_chars": 7_030},
        "p2_toolbox": {"schema_chars": 5_602},
        "p2_managed": {"schema_chars": 11_721},
    })
    renderer = figure.canvas.get_renderer()
    boxes = [text.get_window_extent(renderer) for text in figure.axes[0].texts]
    overlaps = [
        (a.get_points().tolist(), b.get_points().tolist())
        for i, a in enumerate(boxes) for b in boxes[i + 1:] if a.overlaps(b)
    ]
    assert not overlaps


# --- rendering a ladder capture -----------------------------------------------


def _ladder_scores():
    """One arm at every rung, accuracy climbing with the rung."""
    out = {}
    for index, tier in enumerate((0, 2, 3, 4, 1)):
        for replicate in range(2):
            score = _score("p1_managed", tier, correct=tier != 0,
                           tokens=1000, index=index * 10 + replicate)
            out[score.cell_key] = score
    return out


def test_the_headline_chart_draws_every_rung_instead_of_raising_on_the_new_ones():
    # TIER_COLOR and TIER_LABEL were two-entry dicts, so a ladder capture took
    # out the chart with a KeyError rather than plotting three-fifths of itself.
    figure = plots.accuracy_by_tier(_ladder_scores())
    labels = [text.get_text() for text in figure.axes[0].get_legend().get_texts()]
    assert len(labels) == 5
    assert labels == sorted(labels, key=lambda text: int(text.split()[1]))
    assert labels[0].startswith("rung 0")
    assert labels[-1].startswith("rung 4")


def test_the_published_two_tier_chart_keeps_its_wording_and_its_geometry():
    # Adding ladder support must not restyle the committed figures. Both the
    # legend text and the bar width are load-bearing: the width expression is
    # `0.76 / len(tiers)`, which is exactly the published 0.38 at two tiers.
    figure = plots.accuracy_by_tier(_scores({"p1_managed": 1000, "p3_toolbox": 2000}))
    labels = [text.get_text() for text in figure.axes[0].get_legend().get_texts()]
    assert labels == ["tier 0 · ungoverned", "tier 1 · governed"]
    assert all(abs(bar.get_width() - 0.38) < 1e-9 for bar in figure.axes[0].patches)


def test_rung_colours_are_distinct_so_five_series_stay_tellable_apart():
    assert len(set(plots.TIER_COLOR[tier] for tier in (0, 2, 3, 4, 1))) == 5


def test_tiers_sort_by_rung_and_not_by_the_integer():
    assert plots._tiers_in(_ladder_scores().values()) == [0, 2, 3, 4, 1]
