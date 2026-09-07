"""Offline invariants for cross-capture comparison (Amendment C.0).

The comparator's job is mostly to *refuse*, so most of these assert that it
does. A comparator that happily subtracts two captures taken on different
Toolbox versions is worse than no comparator, because its output looks like a
result.
"""

import compare
import scoring
import traces


def _header(**overrides):
    """A header agreeing on everything in MUST_AGREE unless told otherwise."""
    base = {
        "project": "example-project",
        "agent_model": "gemini-3.7-flash",
        "model_location": "global",
        "temperature": 0.0,
        "toolbox_version": "v1.10.0",
        "use_tier_sa": True,
        "runs": 5,
        "tiers": [0, 1],
        "question_ids": ["q1", "q2"],
    }
    return {**base, **overrides}


def _score(key, config, tier, correct):
    return scoring.Score(
        cell_key=key, config=config, tier=tier, question_id=key.split("|")[0],
        category="direct", correct=correct, answered=True,
    )


def _scores(spec):
    """spec: {(question, config, tier, run): correct} -> keyed Score dict."""
    out = {}
    for (question, config_key, tier, run), correct in spec.items():
        key = traces.cell_key(question, config_key, tier, run)
        out[key] = _score(key, config_key, tier, correct)
    return out


# --- align ---------------------------------------------------------------------


def test_the_declared_axis_may_differ_and_nothing_else_may():
    alignment = compare.align(
        [_header(), _header(agent_model="other-model")], axes=("agent_model",)
    )
    assert alignment.ok
    assert alignment.varied["agent_model"] == ["gemini-3.7-flash", "other-model"]
    assert not alignment.conflicts


def test_a_bumped_toolbox_makes_two_captures_incomparable():
    # The pin-freeze rule in C.7 is enforced here, not by discipline. A Toolbox
    # bump changes the tool inventory, so a delta across it is unattributable.
    alignment = compare.align(
        [_header(), _header(agent_model="other-model", toolbox_version="v1.11.0")],
        axes=("agent_model",),
    )
    assert not alignment.ok
    assert "toolbox_version" in alignment.conflicts
    assert "agent_model" not in alignment.conflicts


def test_an_axis_that_did_not_actually_vary_is_flagged_not_passed():
    # Comparing a capture to itself yields all-zero deltas, which read as
    # "the model made no difference" rather than "no model change was measured".
    alignment = compare.align([_header(), _header()], axes=("agent_model",))
    assert not alignment.ok
    assert alignment.inert == ("agent_model",)
    assert not alignment.conflicts


def test_tier_order_is_not_a_difference():
    # `tiers` is a list, and [1, 0] measured the same thing as [0, 1].
    alignment = compare.align(
        [_header(tiers=[0, 1]), _header(tiers=[1, 0], agent_model="other")],
        axes=("agent_model",),
    )
    assert "tiers" not in alignment.conflicts


def test_a_ladder_capture_aligns_against_the_published_one_on_tiers():
    # C.2's replication check: the ladder holds five rungs, the published
    # capture two, and everything else is frozen.
    alignment = compare.align(
        [_header(), _header(tiers=[0, 2, 3, 4, 1])], axes=("tiers",)
    )
    assert alignment.ok
    assert "tiers" in alignment.varied


def test_differing_replicate_counts_are_declarable_rather_than_fatal():
    # C.3 runs n=3 against a published n=5. Rates stay comparable; precision
    # does not, which is why `runs` has to be declared out loud.
    axes = ("agent_model", "runs")
    assert compare.align([_header(), _header(agent_model="other", runs=3)], axes=axes).ok


# --- deltas --------------------------------------------------------------------


def test_only_cells_present_in_both_captures_are_differenced():
    a = _scores({("q1", "p1_managed", 1, 1): True, ("q1", "p1_managed", 1, 2): True})
    b = _scores({("q1", "p1_managed", 1, 1): False})
    result = compare.deltas(a, b)

    entry = result.entries[0]
    assert entry.pairs == 1, "run 2 exists only in A and must not enter the denominator"
    assert entry.correct_a == 1
    assert entry.correct_b == 0
    assert result.unpaired_a == 1
    assert result.unpaired_b == 0


def test_an_arm_present_in_only_one_capture_is_named():
    a = _scores({("q1", "p1_managed", 1, 1): True})
    b = _scores({("q1", "p3_managed", 1, 1): True})
    result = compare.deltas(a, b)
    assert result.only_in_a == ("p1_managed",)
    assert result.only_in_b == ("p3_managed",)
    assert not result.entries


def test_a_delta_inside_the_noise_floor_is_not_resolved():
    # 200 paired cells, one flip: 0.5 points, under the measured 1-point floor.
    a = _scores({("q1", "p1_managed", 1, run): True for run in range(200)})
    b = _scores({("q1", "p1_managed", 1, run): run != 0 for run in range(200)})
    entry = compare.deltas(a, b).entries[0]
    assert entry.points == -0.5
    assert not entry.resolved


# --- rank stability ------------------------------------------------------------


def _delta(config_key, accuracy_a, accuracy_b, pairs=100):
    return compare.Delta(
        config=config_key, tier=1, pairs=pairs,
        correct_a=round(accuracy_a * pairs), correct_b=round(accuracy_b * pairs),
    )


def test_a_preserved_ordering_is_concordant():
    entries = [_delta("p1", 0.50, 0.30), _delta("p3", 0.80, 0.60)]
    check = compare.rank_stability(entries)[0]
    assert (check.concordant, check.discordant, check.unresolved) == (1, 0, 0)
    assert check.tau == 1.0


def test_a_reversed_ordering_is_named_not_just_counted():
    entries = [_delta("p1", 0.50, 0.80), _delta("p3", 0.80, 0.50)]
    check = compare.rank_stability(entries)[0]
    assert check.discordant == 1
    assert check.inversions == [("p1", "p3")]
    assert check.tau == -1.0


def test_arms_separated_by_less_than_the_floor_are_unresolved_not_ordered():
    # Half a point apart in A. Calling that an ordering and then calling its
    # reversal an inversion manufactures a finding out of resampling noise.
    entries = [_delta("p1", 0.500, 0.30), _delta("p3", 0.505, 0.60)]
    check = compare.rank_stability(entries)[0]
    assert (check.concordant, check.discordant, check.unresolved) == (0, 0, 1)
    assert check.tau is None, "tau over zero resolved pairs must not report agreement"


def test_unresolved_pairs_never_inflate_tau():
    # One real inversion plus two pairs nothing separates. Counting the
    # unresolved pairs as concordant would report +0.33 — stability, from noise.
    entries = [_delta("a", 0.50, 0.80), _delta("b", 0.80, 0.50), _delta("c", 0.801, 0.801)]
    check = compare.rank_stability(entries)[0]
    assert check.unresolved == 2
    assert check.tau == -1.0


# --- rendering -----------------------------------------------------------------


def test_a_refusal_renders_instead_of_the_numbers():
    # The failure mode this guards: printing a conflict warning above a table of
    # deltas, which readers take as the result with a caveat attached.
    alignment = compare.align(
        [_header(), _header(agent_model="other", toolbox_version="v1.11.0")],
        axes=("agent_model",),
    )
    text = compare.render(alignment, compare.Deltas(), [], ("base", "new"))
    assert "Not comparable" in text
    assert "toolbox_version" in text
    assert "Accuracy delta" not in text


def test_an_inert_axis_withholds_the_numbers_too():
    # Same reason as a conflict: every delta would be zero by construction, and
    # a table under a warning banner gets quoted as "the model made no
    # difference" rather than "no model change was measured".
    alignment = compare.align([_header(), _header()], axes=("agent_model",))
    a = _scores({("q1", "p1_managed", 1, 1): True})
    result = compare.deltas(a, dict(a))
    text = compare.render(alignment, result, compare.rank_stability(result.entries),
                          ("base", "same"))
    assert "Axis did not vary" in text
    assert "Accuracy delta" not in text
    assert "Rank stability" not in text


def test_every_cell_pairing_is_stated_even_when_nothing_was_dropped():
    a = _scores({("q1", "p1_managed", 1, 1): True})
    result = compare.deltas(a, dict(a))
    alignment = compare.align([_header(), _header(agent_model="other")], ("agent_model",))
    text = compare.render(alignment, result, compare.rank_stability(result.entries),
                          ("base", "new"))
    assert "Every cell paired." in text
