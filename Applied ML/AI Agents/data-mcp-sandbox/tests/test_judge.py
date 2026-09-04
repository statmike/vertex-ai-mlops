"""Offline guards for the judge. No model calls — these check the prompt contract.

The judge's whole value depends on it not knowing which architecture it is
looking at, and that is a property of a string, so it can be tested for free.
"""

import judge
import mcp_clients


def _rendered():
    return judge.render(
        question="What is our total net revenue, all time?",
        rule="Net Revenue is SUM(txn_amt_x2) and MUST exclude refunded transactions.",
        query="SELECT SUM(txn_amt_x2) FROM t WHERE status_flg = FALSE",
        answer="Net revenue is **251,543.00**.",
    )


def test_judge_prompt_is_blind_to_the_config():
    # A judge told it is looking at "the governed context arm" will find
    # governance in it. §9.3 requires blindness; this is what enforces it.
    prompt = f"{judge.SYSTEM}\n{_rendered()}".lower()
    for key in mcp_clients.CONFIG_KEYS:
        assert key not in prompt
    for leak in ("toolbox", "dataplex", "looker", "managed", "conversational analytics",
                 "tier 0", "tier 1", "path 1", "path 4"):
        assert leak not in prompt, f"prompt leaks {leak!r}"


def test_missing_query_is_labelled_not_blank():
    # An opaque path must read as "did not disclose", not as "ran nothing" — the
    # difference between `unclear` and `invented` in the rubric.
    prompt = judge.render("q", "rule", "", "answer")
    assert judge.NO_QUERY in prompt


def test_prompt_is_bounded():
    # Tool results run to 20k chars. An unbounded prompt would make the judging
    # pass cost more than the sweep it is grading.
    prompt = judge.render("q", "rule", "SELECT 1 " * 5000, "x" * 9000)
    assert len(prompt) < 12_000


def test_rubric_and_schema_agree():
    # A value in the schema enum that the rubric never defines gets returned and
    # then silently means nothing.
    for value in judge.ADHERENCE_VALUES:
        assert value in judge.SYSTEM


def test_reciting_the_rule_is_not_applying_it():
    # The failure mode this instruction exists for: an agent that quotes the
    # governed definition in prose and then sums the decoy column anyway.
    assert "reciting a definition is not applying it" in judge.SYSTEM
