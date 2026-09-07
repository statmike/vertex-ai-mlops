"""Invariants for the deterministic scorer.

Every test here corresponds to a way the scorer produced a *plausible but false*
number against the real published capture. None of them were caught by the code
running cleanly — each one printed a tidy table with a wrong finding in it.
"""

import scoring
import traces


def _cell(config="p1_managed", tier=1, answer="42", calls=(), error=""):
    return traces.Cell(
        cell_key="k", question_id="q", category="direct", question="?",
        config=config, tier=tier, run=1, answer=answer,
        tool_calls=list(calls), error=error,
    )


def _call(name, args=None, result="", is_error=False, seq=0):
    return traces.ToolCall(
        seq=seq, name=name, args=args or {}, result=result, is_error=is_error
    )


# --- number extraction -------------------------------------------------------


def test_bold_number_wins_over_numbers_in_the_query():
    answer = "Net revenue was **$251,543.00**.\n\n```sql\nSELECT 1 FROM t LIMIT 1000\n```"
    assert scoring.extract_number(answer) == 251543.0


def test_code_fence_numbers_are_never_the_answer():
    # A Path 4 answer really did report `1000` because the row cap appeared in
    # the SQL block before any prose number.
    answer = "```sql\nSELECT COUNT(*) FROM t LIMIT 1000\n```\nThere are 5,000 users."
    assert scoring.extract_number(answer) == 5000.0


def test_no_number_is_none_not_zero():
    assert scoring.extract_number("I could not determine this.") is None
    assert scoring.extract_number("") is None


# --- evidence recovery -------------------------------------------------------


def test_both_sql_argument_names_are_recovered():
    # Toolbox says `sql`, the managed BigQuery endpoint says `query`. Reading only
    # one scored a whole arm at 0.00 recall while it answered 67% correctly.
    toolbox = _cell(calls=[_call("execute_sql", {"sql": "SELECT txn_amt_x2 FROM t"})])
    managed = _cell(calls=[_call("execute_sql_readonly", {"query": "SELECT txn_amt_x2 FROM t"})])
    for cell in (toolbox, managed):
        assert "txn_amt_x2" in scoring.evidence_text(cell)


def test_looker_field_lists_count_as_evidence():
    # Looker MCP takes no SQL — the field list *is* the SELECT clause.
    cell = _cell(calls=[_call("query", {
        "model": "m", "explore": "e", "fields": ["transactions.txn_amt_x2"],
    })])
    recall, _precision, _decoy = scoring.evidence_scores(
        scoring.evidence_text(cell), {"must_have": ["txn_amt_x2"]}
    )
    assert recall == 1.0


def test_the_users_own_question_is_not_evidence():
    # CA's argument is the question text. Scanning it would credit an agent with
    # "queried the users table" for any question containing the word "users".
    cell = _cell(calls=[_call("ask_data_insights", {
        "user_query_with_context": "How many registered users are there?",
    })])
    assert "users" not in scoring.evidence_text(cell).lower()


def test_decoy_does_not_satisfy_a_substring_term():
    # `revenue_amount` contains `revenue`. Treating that as a hit erases the T1 trap.
    recall, precision, decoy = scoring.evidence_scores(
        "SELECT SUM(revenue_amount) FROM t",
        {"must_have": ["txn_amt_x2"], "distractor": ["revenue_amount"]},
    )
    assert recall == 0.0
    assert precision == 0.0
    assert decoy


# --- unmeasured is not zero --------------------------------------------------


def test_opaque_path_reports_evidence_as_unmeasured():
    # CA-for-Looker narrates in prose and never names the field. Scoring that 0.0
    # next to Toolbox's 1.0 would publish "Path 4 ignores the semantic layer".
    cell = _cell(config="p4_looker_ca", calls=[
        _call("looker_conversational_analytics", {"user_query_with_context": "?"},
              result='{"content":[{"text":"I consulted the explore and found the measure."}]}'),
    ])
    score = scoring.score_cell(cell, {"must_have": ["txn_amt_x2"]}, None)
    assert not score.evidence_observable
    assert score.evidence_recall is None


def test_transparent_path_with_no_query_is_a_real_zero_and_says_so():
    cell = _cell(calls=[_call("list_table_ids", {}, result="[]")])
    score = scoring.score_cell(cell, {"must_have": ["txn_amt_x2"]}, None)
    assert score.evidence_observable
    assert score.evidence_recall == 0.0
    assert "no query text recovered" in score.notes


def test_ca_narration_cannot_prove_governance_was_delivered():
    # At tier 0 there is no governed description at all, yet CA confabulated one
    # — and inverted it, calling `txn_amt_x2` the gross list price. That fired the
    # marker on 15 tier-0 cells until CA output was excluded from acquisition.
    hallucinated = '{"text":"txn_amt_x2 is the base gross list price"}'
    cell = _cell(tier=0, config="p1_toolbox", calls=[
        _call("ask_data_insights", {}, result=hallucinated),
    ])
    score = scoring.score_cell(cell, {"must_have": ["txn_amt_x2", "status_flg"]}, None)
    assert not score.acquisition_observable
    assert not score.acquired


def test_acquisition_reads_a_real_description():
    described = "column revenue_amount: MISNAMED. This is the gross list price before discounts."
    cell = _cell(calls=[_call("get_table_info", {}, result=described)])
    score = scoring.score_cell(cell, {"must_have": ["txn_amt_x2", "status_flg"]}, None)
    assert score.acquisition_observable
    assert score.rules_required == ["net-revenue"]
    assert score.acquired


def test_governance_markers_are_in_the_corpus():
    # The markers are literals. If a description is reworded, acquisition silently
    # drops to zero everywhere and reads as an architectural finding.
    for rule, markers in scoring.GOVERNANCE_MARKERS.items():
        text = scoring.corpus_rule_text(rule)
        for marker in markers:
            assert marker in text, f"marker {marker!r} no longer appears in {rule} prose"


# --- containment and failure -------------------------------------------------


def test_ca_reached_from_a_non_path_4_arm_is_flagged():
    # `ask_data_insights` ships inside TOOLBOX_BIGQUERY_TOOLS, so a Path 1 arm can
    # quietly become Path 4 for a cell. It happened on 63% of p1_toolbox tier-0 cells.
    leaked = _cell(config="p1_toolbox", calls=[_call("ask_data_insights", {}, result="{}")])
    native = _cell(config="p4_bq_ca", calls=[_call("ask_data_insights", {}, result="{}")])
    assert scoring.score_cell(leaked, {"must_have": []}, None).ca_leak
    assert not scoring.score_cell(native, {"must_have": []}, None).ca_leak


def test_an_errored_cell_is_scored_as_a_failure_not_skipped():
    score = scoring.score_cell(_cell(error="429 RESOURCE_EXHAUSTED"), {"must_have": []}, None)
    assert not score.answered
    assert not score.correct
    assert score.notes
