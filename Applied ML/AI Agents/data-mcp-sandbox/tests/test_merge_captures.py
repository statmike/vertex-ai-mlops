"""Offline guards on combining two sweeps into one capture.

A merge writes over the file every published number is computed from, and every
way it can go wrong is silent: a dropped cell shrinks a denominator, a duplicate
key replaces a recorded failure with a success, and a flattened header attributes
one run's model or tier fence to cells it never touched. None of those raise on
their own, so they are asserted here rather than noticed in a report diff.
"""

import pytest

import traces


def _header(**overrides):
    base = {
        "started": "2026-09-05T02:07:23+00:00",
        "git_commit": "834421c3",
        "project": "example-project",
        "agent_model": "gemini-3.7-flash",
        "model_location": "global",
        "temperature": 0.0,
        "toolbox_version": "1.10.0",
        "use_tier_sa": True,
        "runs": 5,
        "tiers": [0, 1],
        "configs": ["p1_managed"],
        "question_ids": ["direct-q1"],
        "total_cells": 10,
        "tool_schemas": {"p1_managed": {"tools": 5, "schema_chars": 120009}},
        "quality_scans": True,
    }
    base.update(overrides)
    return base


def _cell(key, config="p1_managed"):
    return traces.Cell(
        cell_key=key, question_id="direct-q1", category="direct",
        question="how many?", config=config, tier=0, run=1, answer="5",
    )


def test_arms_and_schemas_union_while_cells_add_up():
    header = traces.merge_headers([
        _header(),
        _header(git_commit="b987b497", configs=["p4_bq_direct"], total_cells=240,
                started="2026-09-07T14:26:18+00:00",
                tool_schemas={"p4_bq_direct": {"tools": 0, "schema_chars": 0}}),
    ])
    assert header["configs"] == ["p1_managed", "p4_bq_direct"]
    assert set(header["tool_schemas"]) == {"p1_managed", "p4_bq_direct"}
    assert header["total_cells"] == 250
    # The earliest start, not the last write: the capture's window has to cover
    # every cell in it or cost attribution would query a window missing half of them.
    assert header["started"] == "2026-09-05T02:07:23+00:00"


def test_a_merged_capture_names_every_commit_and_claims_none_as_its_own():
    header = traces.merge_headers([
        _header(), _header(git_commit="b987b497", configs=["p4_bq_direct"]),
    ])
    # The whole point: no single `git_commit` survives to be read as if it
    # produced all the cells.
    assert "git_commit" not in header
    assert [run["git_commit"] for run in header["merged_from"]] == ["834421c3", "b987b497"]
    assert [run["configs"] for run in header["merged_from"]] == [["p1_managed"], ["p4_bq_direct"]]


@pytest.mark.parametrize(
    "field,value",
    [
        ("agent_model", "gemini-3.7-pro"),
        ("temperature", 0.7),
        ("use_tier_sa", False),
        ("runs", 3),
        ("tiers", [0]),
        ("question_ids", ["direct-q2"]),
        ("project", "other-project"),
        ("toolbox_version", "1.9.0"),
        ("model_location", "us-central1"),
    ],
)
def test_captures_that_measured_different_things_refuse_to_merge(field, value):
    with pytest.raises(ValueError, match=field):
        traces.merge_headers([
            _header(), _header(configs=["p4_bq_direct"], **{field: value}),
        ])


def test_a_field_added_after_a_capture_was_taken_does_not_block_the_merge():
    # The published capture predates `ca_thinking_mode`, `ca_model` and
    # `tier_semantics`, so its header omits them while every run since writes
    # them empty. Read as a disagreement, that would make the one capture every
    # headline number comes from permanently unextendable — the guard refusing
    # the exact merge the fields were added to make safe.
    header = traces.merge_headers([
        _header(),
        _header(git_commit="b987b497", configs=["p4_bq_direct"],
                ca_thinking_mode="", ca_model="", tier_semantics=""),
    ])
    assert header["configs"] == ["p1_managed", "p4_bq_direct"]


def test_the_same_arm_twice_is_refused_rather_than_concatenated():
    # Two runs of one arm would double its cell count and halve every rate
    # computed as a fraction of it.
    with pytest.raises(ValueError, match="p1_managed"):
        traces.merge_headers([_header(), _header(git_commit="b987b497")])


def test_scan_state_moves_per_run_instead_of_blocking_the_merge():
    # Unlike the fields above, this one legitimately differs and the difference
    # is worth publishing: it changes what `lookup_context` returns on Path 3
    # tier 1 and nothing else, so a Path 4 run taken after the scans were
    # provisioned is still comparable to a Path 1-3 run taken before.
    header = traces.merge_headers([
        _header(quality_scans=None),
        _header(git_commit="b987b497", configs=["p4_bq_direct"], quality_scans=True),
    ])
    assert "quality_scans" not in header, "one state must not stand in for both runs"
    assert [run["quality_scans"] for run in header["merged_from"]] == [None, True]


def test_runs_that_agree_on_scans_still_say_so_once():
    header = traces.merge_headers([
        _header(), _header(git_commit="b987b497", configs=["p4_bq_direct"]),
    ])
    assert header["quality_scans"] is True


def test_a_single_header_merges_to_itself_unchanged():
    # `merged_from` must not appear on an ordinary capture, or every report
    # would start claiming to be a merge of one.
    header = traces.merge_headers([_header()])
    assert header == _header()


def _goldens(active_users):
    return {"0": {"active_user_count": {"key": "active_user_count", "value": active_users,
                                        "trap_value": None, "tolerance": 0.005, "trap_name": ""}}}


def test_each_run_keeps_the_oracle_that_was_true_when_it_ran():
    # Four of this corpus's goldens are trailing windows over data anchored at
    # build time, so the right answer moves with the calendar. Carrying the base
    # run's oracle onto a later run's cells grades correct answers as wrong.
    header = traces.merge_headers([
        _header(goldens=_goldens(2671.0)),
        _header(git_commit="b987b497", configs=["p4_bq_direct"], goldens=_goldens(2786.0)),
    ])
    assert "goldens" not in header, "a merged capture must not have one oracle for all arms"
    by_cell = traces.goldens_by_cell(
        header, [("p1_managed", "direct-q1"), ("p4_bq_direct", "direct-q1")]
    )
    assert by_cell[("p1_managed", "direct-q1")]["0"]["active_user_count"]["value"] == 2671.0
    assert by_cell[("p4_bq_direct", "direct-q1")]["0"]["active_user_count"]["value"] == 2786.0


def test_a_run_that_froze_no_oracle_is_absent_rather_than_empty():
    # The scorer refuses these by name. An empty dict would read as "frozen,
    # nothing in it" and score every cell against no golden at all.
    header = traces.merge_headers([
        _header(goldens=_goldens(2671.0)),
        _header(git_commit="b987b497", configs=["p4_bq_direct"]),
    ])
    assert "goldens" not in header["merged_from"][1]
    asked = [("p1_managed", "direct-q1"), ("p4_bq_direct", "direct-q1")]
    assert set(traces.goldens_by_cell(header, asked)) == {("p1_managed", "direct-q1")}


def test_an_unmerged_capture_answers_with_its_one_oracle_for_every_cell():
    header = _header(configs=["p1_managed", "p1_toolbox"], goldens=_goldens(2671.0))
    asked = [("p1_managed", "direct-q1"), ("p1_toolbox", "direct-q1")]
    by_cell = traces.goldens_by_cell(header, asked)
    assert set(by_cell) == set(asked)
    assert by_cell[("p1_toolbox", "direct-q1")] == _goldens(2671.0)


def test_a_capture_with_no_frozen_oracle_says_so_rather_than_guessing():
    assert traces.goldens_by_cell(_header(), [("p1_managed", "direct-q1")]) == {}
    assert traces.goldens_by_cell({}, [("p1_managed", "direct-q1")]) == {}


def test_an_added_question_reaches_arms_already_captured():
    # The anchored re-issues: same twelve arms, three questions the first sweep
    # never asked. Refusing this would leave the fix publishable only as a
    # sibling file, outside the factorial every headline number is computed over.
    header = traces.merge_headers([
        _header(configs=["p1_managed", "p1_toolbox"], total_cells=20),
        _header(git_commit="b987b497", configs=["p1_managed", "p1_toolbox"],
                question_ids=["direct-q1a"], total_cells=20),
    ])
    assert header["configs"] == ["p1_managed", "p1_toolbox"]
    assert header["question_ids"] == ["direct-q1", "direct-q1a"]
    assert header["total_cells"] == 40


def test_the_same_arm_and_question_twice_is_still_refused():
    with pytest.raises(ValueError, match="direct-q1"):
        traces.merge_headers([
            _header(question_ids=["direct-q1", "direct-q2"]),
            _header(git_commit="b987b497", question_ids=["direct-q1"]),
        ])


def test_runs_that_leave_a_hole_in_the_grid_refuse_to_merge():
    # One arm asked q1, a different arm asked q2. Nothing collides, and the
    # union looks like a 2x2 factorial holding two cells. Half of every
    # arm-vs-arm comparison drawn from it would be against a cell that does not
    # exist.
    with pytest.raises(ValueError, match="question_ids"):
        traces.merge_headers([
            _header(),
            _header(git_commit="b987b497", configs=["p4_bq_direct"],
                    question_ids=["direct-q2"]),
        ])


def test_a_run_that_added_questions_grades_only_the_questions_it_asked():
    # `battery.freeze_oracle` freezes all fifteen goldens however few questions
    # the run asked, so the second block below holds a drifted `active_user_count`
    # for a question it never put to an agent. Keying on (arm, question) is what
    # keeps that value unreachable.
    header = traces.merge_headers([
        _header(goldens=_goldens(2671.0)),
        _header(git_commit="b987b497", question_ids=["direct-q1a"],
                goldens=_goldens(2786.0)),
    ])
    by_cell = traces.goldens_by_cell(
        header, [("p1_managed", "direct-q1"), ("p1_managed", "direct-q1a")]
    )
    assert by_cell[("p1_managed", "direct-q1")]["0"]["active_user_count"]["value"] == 2671.0
    assert by_cell[("p1_managed", "direct-q1a")]["0"]["active_user_count"]["value"] == 2786.0


def test_a_merge_written_before_question_ids_were_recorded_still_resolves():
    # Arms could not overlap then, so one run's block covered every question its
    # arms were asked. Dropping to no coverage at all would unscore a published
    # capture on read.
    header = traces.merge_headers([
        _header(goldens=_goldens(2671.0)),
        _header(git_commit="b987b497", configs=["p4_bq_direct"], goldens=_goldens(2786.0)),
    ])
    for run in header["merged_from"]:
        del run["question_ids"]
    by_cell = traces.goldens_by_cell(header, [("p4_bq_direct", "direct-q1")])
    assert by_cell[("p4_bq_direct", "direct-q1")]["0"]["active_user_count"]["value"] == 2786.0


def test_merging_into_a_capture_that_is_already_a_merge_keeps_every_oracle():
    # The published capture is itself two sweeps under two oracles. Treated as
    # one run it would arrive carrying no `goldens` at all — a merged header
    # deliberately has none — and every cell in it would come out ungradeable.
    base = traces.merge_headers([
        _header(goldens=_goldens(2671.0)),
        _header(git_commit="b987b497", configs=["p4_bq_direct"], goldens=_goldens(2786.0)),
    ])
    header = traces.merge_headers([
        base,
        _header(git_commit="c111", configs=["p1_managed", "p4_bq_direct"],
                question_ids=["direct-q1a"], total_cells=20, goldens=_goldens(2804.0)),
    ])
    assert [run["git_commit"] for run in header["merged_from"]] == [
        "834421c3", "b987b497", "c111",
    ]
    assert all(run.get("goldens") for run in header["merged_from"])
    by_cell = traces.goldens_by_cell(header, [
        ("p1_managed", "direct-q1"), ("p4_bq_direct", "direct-q1"),
        ("p1_managed", "direct-q1a"), ("p4_bq_direct", "direct-q1a"),
    ])
    reading = {pair: block["0"]["active_user_count"]["value"] for pair, block in by_cell.items()}
    assert reading == {
        ("p1_managed", "direct-q1"): 2671.0,
        ("p4_bq_direct", "direct-q1"): 2786.0,
        ("p1_managed", "direct-q1a"): 2804.0,
        ("p4_bq_direct", "direct-q1a"): 2804.0,
    }


def test_a_capture_that_does_not_say_what_it_asked_refuses_to_merge():
    with pytest.raises(ValueError, match="question_ids"):
        traces.merge_headers([
            _header(), _header(configs=["p4_bq_direct"], question_ids=[]),
        ])


def test_every_cell_survives_the_merge():
    merged = traces.merge_cells([
        {"a": _cell("a"), "b": _cell("b")},
        {"c": _cell("c", "p4_bq_direct")},
    ])
    assert sorted(merged) == ["a", "b", "c"]
    assert merged["c"].config == "p4_bq_direct"


def test_a_repeated_cell_key_is_refused_rather_than_overwritten():
    # Last-write-wins here would let a re-run quietly replace a captured
    # failure, which is the one observation this project never discards.
    with pytest.raises(ValueError, match="resume"):
        traces.merge_cells([{"a": _cell("a")}, {"a": _cell("a")}])
