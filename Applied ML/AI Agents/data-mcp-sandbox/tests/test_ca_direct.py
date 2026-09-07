"""Offline invariants for the direct-API arms.

No cloud calls: every request here is built and inspected, never sent. What these
guard is the pair of properties the arms exist to provide — that `p4_bq_direct`
and `p4_bq_direct_ctx` differ by exactly one thing, and that the SQL the service
discloses reaches the scorer without disturbing how the published capture scores.
"""

import dataclasses
import json

from google.cloud import geminidataanalytics as gda

import agents
import battery
import ca_direct
import config
import corpus
import mcp_clients
import scoring
import traces

PROJECT = "test-project"


def _request(monkeypatch, config_key, tier):
    # Never let a test read the operator's real project out of .env.
    monkeypatch.setattr(config, "PROJECT_ID", PROJECT)
    return ca_direct.build_request(config_key, tier, "how much net revenue?")


# --- transport is a property of the config, not a special case ----------------


def test_only_the_direct_arms_are_direct():
    direct = [key for key in mcp_clients.CONFIG_KEYS if mcp_clients.is_direct(key)]
    assert direct == ["p4_bq_direct", "p4_bq_direct_ctx"]


def test_an_unknown_config_is_not_direct():
    # `is_direct` is called with a config read off a capture, which may name an
    # arm this checkout no longer has. Returning False sends it down the MCP
    # path, where a missing config already fails loudly.
    assert not mcp_clients.is_direct("p9_invented")


def test_a_direct_arm_records_zero_tools_rather_than_being_dropped():
    # Amendment B.4.5. The schema-size-versus-cost correlation is computed over
    # whatever rows this returns, so omitting an arm silently changes a published
    # result's denominator.
    assert ca_direct.tool_surface("p4_bq_direct") == {"tools": 0, "schema_chars": 0}


def test_an_mcp_arm_cannot_be_assumed_to_have_zero_tools():
    try:
        ca_direct.tool_surface("p1_toolbox")
    except ValueError:
        return
    raise AssertionError("tool_surface silently zeroed an arm that really binds tools")


# --- the two direct arms differ by exactly one thing --------------------------


def test_the_pair_differs_only_in_its_glossary(monkeypatch):
    # This is the whole design of the pair (Amendment B.3): `p4_bq_direct_ctx`
    # isolates the context payload. If the instruction or the datasources drift
    # apart, the arm stops measuring governance and starts measuring prompt.
    plain = _request(monkeypatch, "p4_bq_direct", 1)
    with_ctx = _request(monkeypatch, "p4_bq_direct_ctx", 1)

    assert plain.inline_context.system_instruction == with_ctx.inline_context.system_instruction
    assert (
        plain.inline_context.datasource_references
        == with_ctx.inline_context.datasource_references
    )
    assert list(plain.inline_context.glossary_terms) == []
    assert len(with_ctx.inline_context.glossary_terms) == len(corpus.GLOSSARY_TERMS)


def test_tier_zero_is_ungoverned_even_on_the_context_arm(monkeypatch):
    # Tier 0 is the control. Injecting the glossary there would hand the agent
    # the answer the experiment measures it discovering, and would do it on one
    # arm only — which reads as that arm being good at tier 0.
    request = _request(monkeypatch, "p4_bq_direct_ctx", 0)
    assert list(request.inline_context.glossary_terms) == []


def test_the_glossary_carries_the_rule_text_the_scorer_keys_on(monkeypatch):
    request = _request(monkeypatch, "p4_bq_direct_ctx", 1)
    descriptions = " ".join(t.description for t in request.inline_context.glossary_terms).lower()
    for markers in scoring.GOVERNANCE_MARKERS.values():
        assert any(marker in descriptions for marker in markers)


def test_no_example_query_is_ever_sent(monkeypatch):
    # `ExampleQuery` carries a `sql_query`, and every query we have that is both
    # correct and relevant is the golden oracle's. There is no honest value for
    # that field, so the field stays empty on both arms.
    for key in ("p4_bq_direct", "p4_bq_direct_ctx"):
        request = _request(monkeypatch, key, 1)
        assert list(request.inline_context.example_queries) == []


def test_the_request_names_the_tier_dataset_and_nothing_else(monkeypatch):
    for tier in (0, 1):
        request = _request(monkeypatch, "p4_bq_direct", tier)
        tables = request.inline_context.datasource_references.bq.table_references
        assert {t.dataset_id for t in tables} == {config.tier_dataset(tier)}
        assert {t.table_id for t in tables} == set(corpus.TABLE_NAMES)
        assert {t.project_id for t in tables} == {PROJECT}


def test_the_arm_is_stateless(monkeypatch):
    # One question per cell, no history. A conversation resource would add state
    # to manage without changing what is measured (Amendment B.3, deferred).
    request = _request(monkeypatch, "p4_bq_direct", 1)
    assert gda.ChatRequest.pb(request).WhichOneof("context_provider") == "inline_context"
    assert len(request.messages) == 1


def test_the_instruction_keeps_the_answer_format_the_scorer_needs():
    # `extract_number` reads a plainly-stated number out of prose. An arm that
    # hedges between two candidates parses as whichever came first, so this arm
    # would be scored on its formatting rather than its architecture.
    assert "commit to one" in ca_direct.ANSWER_FORMAT
    # And it must stay governance-free, or the "ungoverned" arm is not.
    lowered = ca_direct.ANSWER_FORMAT.lower()
    for markers in scoring.GOVERNANCE_MARKERS.values():
        assert not any(marker in lowered for marker in markers)


# --- reading the stream -------------------------------------------------------


def _message(system):
    return gda.Message(system_message=system)


def test_disclosed_sql_and_job_id_are_captured():
    # Two messages, not one: `DataMessage.kind` is a oneof, so the SQL and the
    # job that ran it cannot both be set on the same message. A reader building
    # the fixture the other way gets an empty `generated_sql` and no error.
    outcome = agents.Outcome()
    ca_direct._collect(
        _message({"data": {"generated_sql": "SELECT SUM(txn_amt_x2) FROM t"}}), outcome
    )
    ca_direct._collect(
        _message({"data": {"big_query_job": {"project_id": PROJECT, "job_id": "job_abc"}}}),
        outcome,
    )
    assert outcome.emitted_sql == ["SELECT SUM(txn_amt_x2) FROM t"]
    assert outcome.bq_job_ids == ["job_abc"]


def test_a_job_reported_twice_is_counted_once():
    # CA repeats the job on follow-up messages about the same result. Counting it
    # twice would double that cell's BigQuery bytes.
    outcome = agents.Outcome()
    for _ in range(2):
        ca_direct._collect(
            _message({"data": {"big_query_job": {"job_id": "job_abc"}}}), outcome
        )
    assert outcome.bq_job_ids == ["job_abc"]


FINAL = gda.TextMessage.TextType.FINAL_RESPONSE
THOUGHT = gda.TextMessage.TextType.THOUGHT
FOLLOWUP = gda.TextMessage.TextType.FOLLOWUP_QUESTIONS


def test_a_final_response_split_across_messages_is_reassembled():
    outcome = agents.Outcome()
    for chunk in ("The net revenue is", "**1,234.00**."):
        ca_direct._collect(
            _message({"text": {"parts": [chunk], "text_type": FINAL}}), outcome
        )
    assert scoring.extract_number(outcome.answer) == 1234.0


def test_progress_narration_never_reaches_the_answer():
    # Verbatim from the B.6 pre-flight, which is where this was caught. CA
    # narrates its work as THOUGHT and closes with FOLLOWUP_QUESTIONS. An
    # earlier cut concatenated all three, and `extract_number` returned 3.0 off
    # "Retrieved context for 3 tables" on a cell whose answer was 5,000 — every
    # direct cell would have scored against narration, making our parsing bug
    # look like the API being inaccurate.
    outcome = agents.Outcome()
    stream = [
        (THOUGHT, ["Analyzing context", "Retrieved context for 3 tables."]),
        (THOUGHT, ["Running a query", "SELECT COUNT(DISTINCT user_id) FROM t"]),
        (THOUGHT, ["Query execution completed", "Query returned 1 row in 1.12s."]),
        (FINAL, ["There are 5,000 registered users."]),
        (FOLLOWUP, ["How many active users?", "What is the revenue by region?"]),
    ]
    for text_type, parts in stream:
        ca_direct._collect(
            _message({"text": {"parts": parts, "text_type": text_type}}), outcome
        )

    assert outcome.answer == "There are 5,000 registered users."
    assert scoring.extract_number(outcome.answer) == 5000.0
    assert "3 tables" not in outcome.answer
    assert "active users" not in outcome.answer, "follow-up suggestions are not an answer"


def test_an_unlabelled_text_message_is_dropped_rather_than_trusted():
    # Failing loud beats failing silent: an empty answer is already counted as a
    # cell failure, where narration admitted by default parses as a number and
    # looks perfectly healthy.
    outcome = agents.Outcome()
    ca_direct._collect(_message({"text": {"parts": ["Analyzing context"]}}), outcome)
    assert not outcome.answer


def test_a_service_error_is_recorded_not_raised():
    outcome = agents.Outcome()
    ca_direct._collect(_message({"error": {"text": "403 permission denied"}}), outcome)
    assert "403" in outcome.error


# --- the seam into the rest of the harness ------------------------------------


def test_the_battery_routes_direct_arms_away_from_the_adk_loop(monkeypatch):
    # `agents.ask` builds an Agent and a runner. Calling it for a direct arm
    # would try to bind tools that do not exist, hours into a sweep.
    called = []
    monkeypatch.setattr(ca_direct, "ask", _record(called, "direct"))
    monkeypatch.setattr(agents, "ask", _record(called, "mcp"))

    import asyncio

    asyncio.run(battery.ask("p4_bq_direct", 1, "q"))
    asyncio.run(battery.ask("p4_bq_ca", 1, "q"))
    assert called == ["direct", "mcp"]


def _record(sink, label):
    async def _fake(*_args, **_kwargs):
        sink.append(label)
        return agents.Outcome()

    return _fake


def test_disclosed_sql_reaches_the_scorer_and_wins():
    # The point of the arm: evidence recall stops printing `--` on Path 4.
    cell = _cell(emitted_sql=["SELECT SUM(txn_amt_x2), status_flg FROM t"])
    recall, _precision, _decoy = scoring.evidence_scores(
        scoring.evidence_text(cell), {"must_have": ["txn_amt_x2", "status_flg"]}
    )
    assert recall == 1.0


def test_scraping_still_scores_every_arm_that_discloses_nothing():
    # The published capture has no `emitted_sql` anywhere, and re-scoring it must
    # produce the same numbers it produced before this field existed.
    cell = _cell(
        tool_calls=[traces.ToolCall(seq=0, name="execute_sql", args={"sql": "SELECT status_flg"})]
    )
    assert "status_flg" in scoring.evidence_text(cell)


def test_an_undisclosed_direct_cell_is_unmeasured_not_zero():
    # No tool call names CA on a direct arm, so the config is the only signal.
    # Without it this cell scores 0.0 for "skipping the data" it demonstrably read.
    result = scoring.score_cell(_cell(config="p4_bq_direct"), {"must_have": ["status_flg"]}, None)
    assert result.evidence_recall is None
    assert not result.evidence_observable


def _cell(**overrides):
    fields = {
        "cell_key": "k",
        "question_id": "q1",
        "category": "direct",
        "question": "how much?",
        "config": "p4_bq_direct",
        "tier": 1,
        "run": 1,
        "answer": "**1,234.00**",
    }
    fields.update(overrides)
    return traces.Cell(**fields)


def test_a_capture_written_before_these_fields_still_loads(tmp_path):
    # Hard constraint, not a preference (Amendment B.4.2): `results/capture.json.gz`
    # is published, and every field added here must default rather than be required.
    new = {f.name for f in dataclasses.fields(traces.Cell)}
    record = {
        "cell_key": "k", "question_id": "q1", "category": "direct", "question": "?",
        "config": "p1_toolbox", "tier": 1, "run": 1, "answer": "42", "tool_calls": [],
    }
    path = tmp_path / "capture.json"
    path.write_text(json.dumps({"header": {}, "cells": [record]}))

    cells = traces.load(path)
    assert cells["k"].emitted_sql == []
    assert cells["k"].bq_job_ids == []
    assert new - set(record) == {"emitted_sql", "bq_job_ids", "usage", "latency_s", "error",
                                 "started_at", "ended_at", "attempts"}
