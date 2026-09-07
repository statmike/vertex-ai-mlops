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
        ("quality_scans", False),
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


def test_the_same_arm_twice_is_refused_rather_than_concatenated():
    # Two runs of one arm would double its cell count and halve every rate
    # computed as a fraction of it.
    with pytest.raises(ValueError, match="p1_managed"):
        traces.merge_headers([_header(), _header(git_commit="b987b497")])


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
    by_config = traces.goldens_by_config(header, ["p1_managed", "p4_bq_direct"])
    assert by_config["p1_managed"]["0"]["active_user_count"]["value"] == 2671.0
    assert by_config["p4_bq_direct"]["0"]["active_user_count"]["value"] == 2786.0


def test_a_run_that_froze_no_oracle_is_absent_rather_than_empty():
    # The scorer refuses these by name. An empty dict would read as "frozen,
    # nothing in it" and score every cell against no golden at all.
    header = traces.merge_headers([
        _header(goldens=_goldens(2671.0)),
        _header(git_commit="b987b497", configs=["p4_bq_direct"]),
    ])
    assert "goldens" not in header["merged_from"][1]
    asked = ["p1_managed", "p4_bq_direct"]
    assert set(traces.goldens_by_config(header, asked)) == {"p1_managed"}


def test_an_unmerged_capture_answers_with_its_one_oracle_for_every_arm():
    header = _header(configs=["p1_managed", "p1_toolbox"], goldens=_goldens(2671.0))
    by_config = traces.goldens_by_config(header, ["p1_managed", "p1_toolbox"])
    assert set(by_config) == {"p1_managed", "p1_toolbox"}
    assert by_config["p1_toolbox"] == _goldens(2671.0)


def test_a_capture_with_no_frozen_oracle_says_so_rather_than_guessing():
    assert traces.goldens_by_config(_header(), ["p1_managed"]) == {}
    assert traces.goldens_by_config({}, ["p1_managed"]) == {}


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
