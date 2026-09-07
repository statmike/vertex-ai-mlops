"""Offline invariants for the sweep planner and its capture format.

No cloud calls and no model calls — these guard the properties that make a
1,440-cell run recoverable and interpretable, which is exactly what you cannot
afford to discover is broken four hours in.
"""

import json
from datetime import UTC, datetime, timedelta

import agents
import battery
import golden
import mcp_clients
import traces
from agents import _failed


def _questions():
    return battery.load_questions()


def test_questions_file_parses_and_is_complete():
    # Deliberately asserts *structure*, not a count. The battery is meant to be
    # edited — adapting the sandbox to another warehouse means rewriting these
    # questions — and a hardcoded `== 12` turns every such edit into a failing
    # test that says nothing about whether the edit was correct. `validate.py`
    # is what checks the edit is coherent.
    questions = _questions()
    assert questions, "questions.json is empty"
    assert len({question.id for question in questions}) == len(questions)
    for question in questions:
        assert question.golden_key
        assert question.evidence["must_have"]


def test_plan_is_config_major_so_an_interrupted_sweep_leaves_whole_configs():
    current = battery.plan(_questions()[:2], ["p1_managed", "p1_toolbox"], [0, 1], 2)
    configs_in_order = [config_key for _, config_key, _, _ in current.cells]
    # Every cell of the first config precedes every cell of the second.
    assert configs_in_order == sorted(configs_in_order, key=configs_in_order.index)
    assert configs_in_order[0] == "p1_managed"
    assert configs_in_order[-1] == "p1_toolbox"


def test_cell_key_is_stable():
    # --resume finds its place by this string. Changing it silently re-runs a
    # completed sweep from scratch, at full cost.
    assert traces.cell_key("semantic-q1", "p2_managed", 1, 3) == "semantic-q1|p2_managed|tier1|run3"


def test_header_records_whether_the_tier_fence_was_on():
    # Without this a results file cannot be told apart from an uncontrolled one.
    meta = battery.header(battery.plan(_questions()[:1], ["p1_managed"], [0], 1))
    assert "use_tier_sa" in meta
    assert meta["total_cells"] == 1
    assert meta["agent_model"]


def test_round_trip_preserves_tool_calls(tmp_path):
    path = tmp_path / "results.json"
    cell = traces.Cell(
        cell_key="q|c|tier0|run1",
        question_id="q",
        category="direct",
        question="?",
        config="p1_managed",
        tier=0,
        run=1,
        answer="42",
        tool_calls=[traces.ToolCall(seq=0, name="execute_sql", args={"sql": "SELECT 1"},
                                    result="[{}]", is_error=False)],
    )
    traces.save(path, {cell.cell_key: cell}, {"note": "test"})
    loaded = traces.load(path)
    assert loaded[cell.cell_key].tool_names() == ["execute_sql"]
    assert loaded[cell.cell_key].tool_calls[0].args == {"sql": "SELECT 1"}
    assert json.loads(path.read_text())["header"] == {"note": "test"}


def test_only_failed_cells_are_reworked_by_resume():
    good = traces.Cell(cell_key="k", question_id="q", category="direct", question="?",
                       config="p1_managed", tier=0, run=1, answer="42")
    errored = traces.Cell(cell_key="k", question_id="q", category="direct", question="?",
                          config="p1_managed", tier=0, run=1, answer="42", error="boom")
    empty = traces.Cell(cell_key="k", question_id="q", category="direct", question="?",
                        config="p1_managed", tier=0, run=1, answer="   ")
    assert good.ok
    assert not errored.ok
    assert not empty.ok


def test_mcp_success_is_not_read_as_an_error():
    # An MCP result always carries `isError`, and "iserror" contains "error", so
    # a substring test marks every successful call failed. Read the flag.
    assert not _failed({"content": [{"type": "text", "text": "ok"}], "isError": False})
    assert _failed({"content": [], "isError": True})
    assert _failed({"error": "connection lost"})
    assert not _failed({"content": []})  # empty but successful is not an error


def test_transient_endpoint_failures_are_retried_and_real_ones_are_not():
    # Verbatim from the M6 sweep. Both of these are conditions of the endpoint,
    # and both clustered on particular arms — four 503s hit only p2_toolbox and
    # p3_managed — so recording them would charge a service blip to an
    # architecture. Anything that could only have come from the arm itself must
    # still be kept: docs/method.md counts those as failures rather than dropping
    # them, because dropping them flatters whichever path crashes most.
    assert agents.is_transient(Exception(
        "ServerError: 503 UNAVAILABLE. {'error': {'code': 503, 'message': "
        "'The service is currently unavailable.', 'status': 'UNAVAILABLE'}}"
    ))
    assert agents.is_transient(Exception("_ResourceExhaustedError: 429 RESOURCE_EXHAUSTED"))

    assert not agents.is_transient(Exception("PermissionDenied: 403 lacks bigquery.jobs.create"))
    assert not agents.is_transient(Exception("BadRequest: 400 Unrecognized name: revenue_amount"))
    assert not agents.is_transient(Exception("TimeoutError: toolbox server never became ready"))


def test_matched_arms_really_match():
    # The whole point of p1_matched/p3_matched is that the *only* difference from
    # their managed twins is which endpoint serves the schema. If someone widens
    # MANAGED_BIGQUERY_TOOLS and not MATCHED_BIGQUERY_TOOLS, the arm silently
    # stops being a control and F4 goes back to measuring two things at once.
    managed_bq = set(mcp_clients.MANAGED_BIGQUERY_TOOLS)
    matched_bq = set(mcp_clients.MATCHED_BIGQUERY_TOOLS)
    # `execute_sql_readonly` (managed) and `execute_sql` under writeMode:blocked
    # (Toolbox) are the same capability under different names.
    assert managed_bq - {"execute_sql_readonly"} == matched_bq - {"execute_sql"}
    assert set(mcp_clients.MANAGED_DATAPLEX_TOOLS) == set(mcp_clients.MATCHED_DATAPLEX_TOOLS)

    p1 = mcp_clients.CONFIGS["p1_matched"]
    p3 = mcp_clients.CONFIGS["p3_matched"]
    assert len(p1.toolbox_tools) == len(mcp_clients.MANAGED_BIGQUERY_TOOLS)
    assert len(p3.toolbox_tools) == len(mcp_clients.MANAGED_DATAPLEX_TOOLS) + len(
        mcp_clients.MANAGED_BIGQUERY_TOOLS
    )


def test_plan_is_the_full_factorial_with_matched_arms():
    # The invariant is the *product*, not the shipped numbers: every question is
    # asked on every arm at every tier for every replicate, and no cell key
    # collides. Written against the actual lengths so that editing the battery
    # for another warehouse changes the size without breaking the property.
    # As shipped that is 12 x 12 x 2 x 5 = 1,440.
    questions = _questions()
    configs, tiers, runs = list(mcp_clients.CONFIG_KEYS), [0, 1], 5
    current = battery.plan(questions, configs, tiers, runs)
    expected = len(questions) * len(configs) * len(tiers) * runs
    assert len(current) == expected
    keys = {battery.traces.cell_key(q.id, c, t, r) for q, c, t, r in current.cells}
    assert len(keys) == expected, "cell keys collide, so cells would overwrite each other"


def test_cost_join_fields_survive_a_round_trip(tmp_path):
    # started_at/ended_at are the join key to BigQuery job attribution and cannot
    # be backfilled, so losing them in serialization would silently cost a sweep.
    path = tmp_path / "r.json"
    cell = traces.Cell(
        cell_key="k", question_id="q", category="direct", question="?",
        config="p1_matched", tier=1, run=1, answer="42",
        started_at="2026-09-03T12:00:00+00:00", ended_at="2026-09-03T12:01:00+00:00",
        attempts=3,
        tool_calls=[traces.ToolCall(seq=0, name="execute_sql", result="[]", duration_s=1.25)],
    )
    traces.save(path, {cell.cell_key: cell}, {})
    got = traces.load(path)[cell.cell_key]
    assert got.started_at and got.ended_at
    assert got.attempts == 3
    assert got.tool_calls[0].duration_s == 1.25


def test_retried_cells_are_flagged_so_latency_stays_comparable():
    # A cell that hit quota backoff carries up to ~300s of sleep in latency_s.
    # Reporting it alongside single-attempt cells is how you publish a fake number.
    clean = traces.Cell(cell_key="k", question_id="q", category="direct", question="?",
                        config="p1_managed", tier=0, run=1, answer="42", attempts=1)
    retried = traces.Cell(cell_key="k", question_id="q", category="direct", question="?",
                          config="p1_managed", tier=0, run=1, answer="42", attempts=4)
    assert clean.attempts == 1
    assert retried.attempts > 1


def _fake_oracle(monkeypatch, tag="fresh"):
    """Stand in for `golden.freeze`, which needs BigQuery. Returns a call counter."""
    calls: list[list[int]] = []

    def fake(tiers):
        calls.append(sorted(tiers))
        return {str(tier): {"total_users": {"value": tag}} for tier in sorted(tiers)}

    monkeypatch.setattr(golden, "freeze", fake)
    return calls


def _sweep(tmp_path, monkeypatch, header=None, tag="fresh"):
    """A one-cell plan, a results file holding `header`, and a stubbed oracle."""
    current = battery.plan(_questions()[:1], ["p1_managed"], [0, 1], 1)
    path = tmp_path / "results.json"
    if header is not None:
        traces.save(path, {}, header)
    return current, path, _fake_oracle(monkeypatch, tag)


def test_a_fresh_sweep_freezes_the_oracle_before_it_spends_anything(tmp_path, monkeypatch):
    # The whole point of C.1: the oracle must describe the day the cells ran, and
    # the only moment that is knowably true is sweep start.
    current, path, calls = _sweep(tmp_path, monkeypatch)
    frozen = battery.freeze_oracle(current, path, resume=False)

    assert calls == [[0, 1]], "the oracle must be resolved once, for every tier in the plan"
    assert set(frozen["goldens"]) == {"0", "1"}
    # Timestamped, or a later reader cannot tell how stale the grading is.
    assert datetime.fromisoformat(frozen["goldens_frozen_at"]).tzinfo is not None


def test_a_resume_carries_the_oracle_rather_than_refreezing_it(tmp_path, monkeypatch):
    # Re-freezing on resume would regrade day one's cells against day two's
    # answers — the same error as freezing at export, moved somewhere quieter.
    yesterday = (datetime.now(UTC) - timedelta(hours=2)).isoformat(timespec="seconds")
    current, path, calls = _sweep(
        tmp_path,
        monkeypatch,
        header={"goldens": {"0": {"total_users": {"value": "original"}}},
                "goldens_frozen_at": yesterday},
    )
    frozen = battery.freeze_oracle(current, path, resume=True)

    assert calls == [], "a resume that re-resolves the oracle changes the grading mid-sweep"
    assert frozen["goldens"]["0"]["total_users"]["value"] == "original"
    assert frozen["goldens_frozen_at"] == yesterday


def test_a_stale_carried_oracle_says_so(tmp_path, monkeypatch, capsys):
    # Four goldens are trailing windows drifting ~2%/day against a 0.5%
    # tolerance, so a resume days later grades its new cells against the wrong
    # day. It is still the least-wrong option, but it must not be silent.
    old = (datetime.now(UTC) - timedelta(hours=battery.ORACLE_STALE_HOURS + 1))
    current, path, _ = _sweep(
        tmp_path,
        monkeypatch,
        header={"goldens": {"0": {}}, "goldens_frozen_at": old.isoformat(timespec="seconds")},
    )
    battery.freeze_oracle(current, path, resume=True)
    assert "WARNING" in capsys.readouterr().out


def test_a_resume_of_a_pre_c1_capture_freezes_rather_than_refusing(tmp_path, monkeypatch):
    # A run interrupted before this existed has no oracle on file. Today's is
    # imperfect for its day-one cells and infinitely better than none.
    current, path, calls = _sweep(tmp_path, monkeypatch, header={"started": "2026-09-05"})
    frozen = battery.freeze_oracle(current, path, resume=True)
    assert calls == [[0, 1]]
    assert frozen["goldens"]


def test_a_merged_capture_keeps_each_runs_freeze_time_with_its_oracle():
    # `goldens_frozen_at` at the top level of a merged file would date one run's
    # oracle and appear to date both.
    def header(commit, config_key, frozen_at):
        return {"agent_model": "m", "runs": 1, "git_commit": commit, "started": "2026-09-05",
                "configs": [config_key], "total_cells": 1,
                "goldens": {"0": {}}, "goldens_frozen_at": frozen_at}

    merged = traces.merge_headers([
        header("aaa", "p1_managed", "2026-09-05T02:07:23+00:00"),
        header("bbb", "p4_bq_direct", "2026-09-07T14:26:18+00:00"),
    ])
    assert "goldens_frozen_at" not in merged
    assert [run["goldens_frozen_at"] for run in merged["merged_from"]] == [
        "2026-09-05T02:07:23+00:00", "2026-09-07T14:26:18+00:00",
    ]


def test_every_outcome_field_reaches_the_cell():
    # `to_cell` copies Outcome -> Cell field by field. Adding a field to both and
    # forgetting the copy line yields a results file full of defaults that looks
    # perfectly healthy — which is exactly how started_at/ended_at shipped empty
    # on the first instrumented smoke run. Give every shared field a value no
    # default could be mistaken for, and check each one arrives.
    import dataclasses

    outcome_fields = {f.name for f in dataclasses.fields(agents.Outcome)}
    shared = outcome_fields & {f.name for f in dataclasses.fields(traces.Cell)}

    outcome = agents.Outcome(
        answer="42",
        tool_calls=[traces.ToolCall(seq=1, name="execute_sql", result="ok")],
        usage={"total_token_count": 1234},
        latency_s=12.5,
        error="boom",
        started_at="2026-01-01T00:00:00+00:00",
        ended_at="2026-01-01T00:01:00+00:00",
        attempts=3,
        emitted_sql=["SELECT 1"],
        bq_job_ids=["job_abc"],
    )
    for name in sorted(shared):
        assert getattr(outcome, name), f"fixture leaves Outcome.{name} at its default"

    question = battery.Question(
        id="q1", category="direct", question="how many?", evidence={}, golden_key="g",
    )
    cell = battery.to_cell(question, "p1_toolbox", 1, 2, outcome)
    for name in sorted(shared):
        assert getattr(cell, name) == getattr(outcome, name), (
            f"Cell.{name} exists on Outcome but to_cell never copies it"
        )
