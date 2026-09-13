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


def test_an_unscoreable_question_leaves_the_rate_alone_rather_than_scoring_zero():
    # The third exception in this module's docstring. `correct` is still computed
    # and still on the Score — a reader can inspect it — but `graded` is what
    # every rate divides by, so the cell neither helps nor hurts an arm.
    graded = scoring.Score(
        cell_key="a", config="p1_managed", tier=1, question_id="q1",
        category="direct", answered=True, correct=True,
    )
    ungraded = scoring.Score(
        cell_key="b", config="p1_managed", tier=1, question_id="semantic-q2",
        category="semantic-ambiguity", answered=True, correct=False, scoreable=False,
    )
    assert scoring.graded([graded, ungraded]) == [graded]
    # Not deleted, not blanked. The disagreement is still on the record.
    assert ungraded.correct is False


def test_an_unscoreable_cell_is_never_an_application_loss():
    # An agent can acquire the Active rule, apply it exactly, anchor the window
    # to the data's last timestamp instead of to now, and disagree with the
    # oracle. Charging that to "acquired the rule and misapplied it" reports our
    # corpus's defect as the agent's.
    score = scoring.Score(
        cell_key="a", config="p1_managed", tier=1, question_id="governed-q1",
        category="governed-logic", answered=True, correct=False, scoreable=False,
        acquisition_observable=True, rules_required=["active"], rules_acquired=["active"],
    )
    assert score.acquired
    assert not score.application_loss


def test_arm_equivalence_counts_verdicts_over_gradeable_pairs_only():
    # Two arms that both got an anchor-ambiguous question "wrong" agree, and that
    # agreement is about the coin landing the same way twice. Counted, it inflates
    # `same verdict` — the one column a procurement decision reads.
    cells, scores = {}, {}
    for index, (question, scoreable) in enumerate(
        [("q1", True), ("q2", True), ("semantic-q2", False)]
    ):
        for config_key, correct in (("p1_managed", index == 0), ("p1_toolbox", False)):
            key = traces.cell_key(question, config_key, 1, 1)
            cells[key] = traces.Cell(
                cell_key=key, question_id=question, category="direct", question="?",
                config=config_key, tier=1, run=1, answer="42",
            )
            scores[key] = scoring.Score(
                cell_key=key, config=config_key, tier=1, question_id=question,
                category="direct", answered=True, correct=correct, scoreable=scoreable,
            )

    result = scoring.compare_arms(cells, scores, "p1_managed", "p1_toolbox")
    assert result.pairs == 3
    assert result.graded_pairs == 2
    # One of the two gradeable questions agrees. Over three pairs it would read 67%.
    assert result.fraction("same_verdict") == 0.5
    # Sequence and value stay on all three: those are observed, not arbitrated.
    assert result.fraction("same_sequence") == 1.0


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


# --- the 0/n scan -------------------------------------------------------------


def _zero_scores(
    question: str, tier: int, arms: list[str], values: list[float],
    correct_arms: tuple[str, ...] = (), trap_value: float | None = None,
    runs: int = 5,
):
    """One (question, tier) block: `arms` each answering its value `runs` times."""
    scores = []
    for config_key, value in zip(arms, values, strict=True):
        for run in range(1, runs + 1):
            scores.append(scoring.Score(
                cell_key=traces.cell_key(question, config_key, tier, run),
                config=config_key, tier=tier, question_id=question,
                category="governed-logic", answered=True, value=value,
                correct=config_key in correct_arms,
                sprang_trap=trap_value is not None and value == trap_value,
                trap_known=trap_value is not None,
            ))
    return scores


def test_arms_agreeing_on_one_wrong_number_is_read_as_a_grading_mismatch():
    # The signature that cost this project a retracted headline: every arm 0/n,
    # every arm on the same number, and only the oracle dissenting.
    scans = scoring.zero_scan(_zero_scores(
        "governed-q1", 1, ["p1_managed", "p2_toolbox", "p3_toolbox", "p3_managed"],
        [2804, 2804, 2699, 2804], trap_value=3520,
    ))
    assert [scan.suspect for scan in scans] == [True]
    assert scans[0].shutouts == 4
    assert scans[0].clusters == 2  # the two defensible window anchors
    assert scans[0].modal_value == 2804


def test_arms_converging_on_the_trap_value_is_the_corpus_working():
    # Tier 0 is *supposed* to shut every arm out on a governed question. Flagging
    # that would report the experiment's central finding as a bug in the rubric.
    scans = scoring.zero_scan(_zero_scores(
        "governed-q1", 0, ["p1_managed", "p2_toolbox", "p3_toolbox", "p3_managed"],
        [3520, 3520, 3520, 2699], trap_value=3520,
    ))
    assert [scan.suspect for scan in scans] == [False]
    assert scans[0].by_design


def test_varied_wrong_answers_are_ordinary_failure_not_a_shared_cause():
    scans = scoring.zero_scan(_zero_scores(
        "trap-q2", 0, ["p1_managed", "p2_toolbox", "p3_toolbox", "p3_managed"],
        [776, 25, 1250, 99], trap_value=3520,
    ))
    assert [scan.suspect for scan in scans] == [False]
    assert scans[0].clusters == 4


def test_a_shutout_is_flagged_even_when_other_arms_scored_normally():
    # The real defect did not shut out the whole factorial: the two direct arms
    # were merged in under a second oracle and graded fine, while ten arms went
    # 0/n. A check that only fired on a unanimous zero would have stayed silent.
    scans = scoring.zero_scan(_zero_scores(
        "governed-q1", 1,
        ["p1_managed", "p2_toolbox", "p3_toolbox", "p4_bq_direct"],
        [2804, 2804, 2804, 2718], correct_arms=("p4_bq_direct",), trap_value=3520,
    ))
    assert [scan.suspect for scan in scans] == [True]
    assert scans[0].shutouts == 3
    assert scans[0].arms == 4


def test_a_missing_trap_value_is_reported_as_the_missing_trap_and_not_as_a_bad_golden():
    # `null_revenue_count` had no `trap_sql`, so seven arms profiling the column
    # *named* revenue and reporting 0 looked like ordinary wrongness. The two
    # repairs are different, so the diagnosis has to distinguish them.
    scans = scoring.zero_scan(_zero_scores(
        "metadata-q1", 0, ["p1_managed", "p2_toolbox", "p3_toolbox"], [0, 0, 0],
    ))
    assert scans[0].suspect
    assert not scans[0].trap_known
    assert "no trap value" in scans[0].reason


def test_too_few_arms_or_one_replicate_is_not_a_shutout():
    # An arm with n=1 is 0/1 half the time on anything hard.
    single = _zero_scores(
        "governed-q1", 1, ["p1_managed", "p2_toolbox", "p3_toolbox"],
        [2804, 2804, 2804], runs=1,
    )
    assert scoring.zero_scan(single) == []
    two_arms = _zero_scores("governed-q1", 1, ["p1_managed", "p2_toolbox"], [2804, 2804])
    assert scoring.zero_scan(two_arms) == []


def test_the_scan_never_looks_at_a_question_the_rubric_already_excluded():
    # Otherwise every capture taken before the anchored questions existed would
    # re-flag the three known-unscoreable ones forever.
    scores = _zero_scores(
        "semantic-q2", 1, ["p1_managed", "p2_toolbox", "p3_toolbox"], [2804, 2804, 2804],
    )
    for score in scores:
        score.scoreable = False
    assert scoring.zero_scan(scores) == []
