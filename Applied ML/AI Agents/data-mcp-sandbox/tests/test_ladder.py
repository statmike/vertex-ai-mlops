"""Offline invariants for the governance ladder (Amendment C.2).

The ladder splits governance from one switch into six channels and adds three
tiers between the two published ones. Every failure mode here is quiet: a rung
provisioned with the wrong channels does not raise, it produces a step of zero
that reads as *"this increment of governance does not pay"*. These tests are the
part that fails before the 25.8-hour sweep instead of after it.

`config.LADDER` is read at import time, so ladder-on cases monkeypatch the two
module globals it decides — which is also how `run_battery.py` would see them.
"""

import re
from pathlib import Path

import pytest

import battery
import compare
import config
import traces
import validate


@pytest.fixture
def ladder(monkeypatch):
    """The config as it looks with LADDER=1, without re-importing the world."""
    monkeypatch.setattr(config, "LADDER", True)
    monkeypatch.setattr(config, "TIERS", (0, 1, 2, 3, 4))
    return config


# --- the table itself ------------------------------------------------------------


def test_the_shipped_ladder_is_coherent():
    # `make validate` runs this, and `scripts/setup.py` refuses to provision when
    # it fails. It is the whole reason a typo in RUNG_CHANNELS is a message
    # rather than a flat line in a published chart.
    assert validate.ladder_problems() == []


def test_each_rung_strictly_adds_to_the_one_below():
    carried = [set(config.RUNG_CHANNELS[tier]) for tier in config.RUNG_ORDER]
    for below, above in zip(carried, carried[1:], strict=False):
        assert below < above, "a rung that adds nothing costs 432 cells to measure no step"


def test_the_top_rung_is_exactly_the_published_governed_tier():
    # If rung 4 were anything other than today's tier 1, the ladder's replication
    # check against the published capture would be comparing two different
    # conditions and reporting the difference as drift.
    assert config.RUNG_ORDER[-1] == 1
    assert set(config.RUNG_CHANNELS[1]) == set(config.CHANNELS)
    assert config.RUNG_CHANNELS[0] == ()


def test_the_published_tiers_keep_their_published_rung_positions():
    # 1,440 shipped cells are keyed on tier0/tier1. Moving either one silently
    # re-interprets every one of them.
    assert config.rung_of(0) == 0
    assert config.rung_of(1) == len(config.RUNG_ORDER) - 1


def test_a_rung_that_lost_its_inheritance_is_caught(monkeypatch):
    broken = dict(config.RUNG_CHANNELS)
    broken[3] = ("profiles",)  # dropped `descriptions` from the rung below
    monkeypatch.setattr(config, "RUNG_CHANNELS", broken)
    assert any("must add to tier" in p for p in validate.ladder_problems())


def test_a_mistyped_channel_is_caught_rather_than_provisioning_nothing(monkeypatch):
    broken = dict(config.RUNG_CHANNELS)
    broken[2] = ("descripitons",)
    monkeypatch.setattr(config, "RUNG_CHANNELS", broken)
    assert any("unknown channels" in p for p in validate.ladder_problems())


# --- what gets provisioned where -------------------------------------------------


def test_with_the_ladder_off_every_channel_lands_exactly_where_it_always_did():
    # The old rule was `tier >= 1`. Anything else here changes what `make setup`
    # builds for someone who never enabled the ladder.
    for channel in config.CHANNELS:
        assert config.tiers_with(channel) == (1,), channel


def test_each_channel_reaches_its_own_rungs_and_no_others(ladder):
    assert ladder.tiers_with("descriptions") == (1, 2, 3, 4)
    assert ladder.tiers_with("profiles") == (1, 3, 4)
    assert ladder.tiers_with("rules") == (1, 4)
    assert ladder.tiers_with("glossary") == (1,)
    assert ladder.tiers_with("quality") == (1,)


def test_an_unknown_channel_raises_instead_of_provisioning_nothing():
    # Returning () would provision the rung with nothing, which scores like the
    # rung below and publishes as "this increment does not pay".
    with pytest.raises(ValueError, match="Unknown governance channel"):
        config.tiers_with("descriptons")


def test_teardown_sweeps_tiers_the_current_config_would_not_create():
    # `make teardown` with the ladder off must still delete a ladder run's scans.
    # Deleting only what TIERS names leaves them orphaned and billing under a
    # name nothing left in the config mentions.
    assert set(config.TIERS) <= set(config.PROVISIONABLE_TIERS)
    assert set(config.PROVISIONABLE_TIERS) == set(config.RUNG_ORDER)


# --- Looker is not laddered ------------------------------------------------------


def test_the_ladder_never_reaches_the_shared_looker_instance(ladder):
    # p2_* and p4_looker_ca are excluded from C.2 by design: laddering LookML
    # means semantic-model surgery on an instance this project is a guest on.
    assert ladder.LOOKER_TIERS == (0, 1)


def test_a_rung_asking_for_a_looker_model_is_refused_not_given_tier_ones(ladder):
    # This was `T0 if tier == 0 else T1`, which answers every ladder rung with
    # the fully governed model — rung 2 would score like rung 4 and the ladder
    # would report that profile scans deliver the whole semantic layer.
    for tier in (2, 3, 4):
        with pytest.raises(ValueError, match="no Looker model"):
            ladder.looker_model(tier)
        with pytest.raises(ValueError, match="no Looker model"):
            ladder.looker_connection(tier)


# --- the capture declares its vocabulary -----------------------------------------


def test_a_two_tier_capture_stays_comparable_to_the_published_one():
    # The published capture predates `tier_semantics` entirely. An empty string
    # collapses with its missing value, so the most likely comparison anyone runs
    # — replicate the published sweep, diff it — is not refused by the guard that
    # was added to protect it.
    assert config.tier_semantics() == ""
    published = {"tier_semantics": None}
    fresh = {"tier_semantics": ""}
    assert compare.align([published, fresh], axes=("runs",)).conflicts == {}


def test_a_ladder_capture_says_so(ladder):
    assert ladder.tier_semantics() == "ladder-v1"


def test_tier_semantics_is_guarded_and_recorded():
    assert "tier_semantics" in traces.MUST_AGREE
    plan = battery.plan(battery.load_questions()[:1], ["p1_toolbox"], [0, 1], 1)
    assert "tier_semantics" in battery.header(plan)


def test_two_captures_that_number_tiers_differently_are_refused():
    # Not hypothetical: the whole append-don't-renumber scheme exists because a
    # capture whose `tier1` means something else would pair against ours and
    # report the difference as a finding.
    conflicts = compare.align(
        [{"tier_semantics": "ladder-v1"}, {"tier_semantics": "renumbered-v2"}],
        axes=("runs",),
    ).conflicts
    assert "tier_semantics" in conflicts


# --- enumeration order -----------------------------------------------------------


def test_a_partial_ladder_sweep_leaves_whole_rungs_in_ladder_order(ladder):
    # Cells run tier-major within an arm. In integer order an interruption leaves
    # rung 4 done and the middle of the ladder missing, which is the one shape a
    # partial ladder capture cannot be read from.
    order = [tier for tier in ladder.RUNG_ORDER if tier in ladder.TIERS]
    assert order == [0, 2, 3, 4, 1]

    plan = battery.plan(battery.load_questions()[:1], ["p1_toolbox"], order, 1)
    assert [tier for (_, _, tier, _) in plan.cells] == order


def test_a_renamed_tier_vocabulary_is_caught_before_the_sweep_not_after(monkeypatch):
    # `compare.SEMANTICS_SHARE` lives in another module and is edited separately.
    # A scheme renamed without updating it produces a capture that is refused
    # against the published one — 24 hours after the decision was made.
    monkeypatch.setattr(config, "tier_semantics", lambda: "ladder-v2")
    assert any("SEMANTICS_SHARE" in p for p in validate.ladder_problems())


def test_the_shipped_ladder_vocabulary_can_reach_the_published_capture(ladder):
    # The reason tiers 0 and 1 are never renumbered. If this fails the ladder
    # can still be run, but its rungs 0 and 4 can never be checked against the
    # published tiers 0 and 1, which is the check that makes it internally valid.
    assert compare.shared_tiers(["", ladder.tier_semantics()]) == {0, 1}
    assert validate.ladder_problems() == []


# --- the shell script is joined to the config by string, across languages -------


def _shell_array(name: str) -> list[str]:
    """Read a `NAME=(a b c)` array out of bootstrap_identities.sh.

    Parsed rather than imported because the script is deliberately standalone —
    it creates identities and edits project-level IAM, and its header argues
    that deserves to stay auditable line by line rather than reaching into
    Python for its values. The cost of that choice is a join nothing at runtime
    checks, so it is checked here.
    """
    script = (Path(config.PROJECT_ROOT) / "scripts" / "bootstrap_identities.sh").read_text()
    match = re.search(rf"^{name}=\(([^)]*)\)", script, re.MULTILINE)
    assert match, f"{name} is not a literal array in bootstrap_identities.sh any more"
    return match.group(1).split()


def test_the_bootstrap_script_grants_the_glossary_to_exactly_the_tiers_that_carry_it():
    # Was `tier != 0`, which is the same statement as "carries the glossary"
    # while there are two tiers and wrong once there are five. Measured on a
    # live provision: rungs 1-3 all held mcpSandboxGlossaryReader, so every one
    # of them could read the Net Revenue rule in plain text and the glossary's
    # own step would have measured zero.
    assert [int(t) for t in _shell_array("GLOSSARY_TIERS")] == list(
        config.tiers_with("glossary")
    )


def test_the_bootstrap_script_creates_an_identity_for_every_tier_the_ladder_runs():
    # A rung with no service account falls back to the operator's own ADC, which
    # can read everything. The fence would be missing exactly where the ladder
    # needs it, and the rung would score like the fully governed tier.
    script = (Path(config.PROJECT_ROOT) / "scripts" / "bootstrap_identities.sh").read_text()
    branches = [
        sorted(int(tier) for tier in body.split())
        for body in re.findall(r"^\s*TIERS=\(([^)]*)\)", script, re.MULTILINE)
    ]
    assert sorted(config.PROVISIONABLE_TIERS) in branches, "no LADDER=1 branch covers every rung"
    assert [0, 1] in branches, "the ladder-off branch must still be the two published tiers"
