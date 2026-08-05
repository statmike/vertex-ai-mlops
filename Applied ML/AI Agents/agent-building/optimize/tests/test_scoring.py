"""Tests for judge parsing, scoring, and aggregation."""

from optimize.harness import aggregate, parse_judge_output
from optimize.harness.scenarios import Scenario
from optimize.harness.scoring import ScoredRun, score_run
from optimize.harness.trace import RunTrace


def test_parse_clean_json():
    score, reasoning = parse_judge_output('{"score": 5, "reasoning": "spot on"}')
    assert score == 5
    assert reasoning == "spot on"


def test_parse_with_code_fence_and_prose():
    text = 'Here is my verdict:\n```json\n{"score": 4, "reasoning": "good"}\n```'
    score, reasoning = parse_judge_output(text)
    assert score == 4
    assert reasoning == "good"


def test_parse_clamps_out_of_range():
    assert parse_judge_output('{"score": 9}')[0] == 5
    assert parse_judge_output('{"score": 0}')[0] == 1


def test_parse_garbage_fails_closed():
    # Unparseable => treated as the worst score, never a crash or silent pass.
    assert parse_judge_output("not json at all")[0] == 1
    assert parse_judge_output('{"score": "high"}')[0] == 1


def test_routing_and_pass_flags():
    scen = Scenario("t", "q", "agent_catalog", "ref")
    good = score_run(scen, RunTrace(routed_to="agent_catalog"), 4, "ok")
    assert good.routing_correct
    assert good.answer_pass

    bad_route = score_run(scen, RunTrace(routed_to="agent_analytics"), 5, "ok")
    assert not bad_route.routing_correct

    low_score = score_run(scen, RunTrace(routed_to="agent_catalog"), 3, "meh")
    assert not low_score.answer_pass


def test_error_run_never_passes():
    scen = Scenario("t", "q", "agent_catalog", "ref")
    errored = score_run(scen, RunTrace(error="boom"), 5, "n/a")
    assert not errored.answer_pass


def test_aggregate_rates():
    runs = [
        ScoredRun("a", "agent_catalog", "agent_catalog", 5, ""),
        ScoredRun("b", "agent_analytics", "agent_catalog", 4, ""),  # wrong route, good answer
        ScoredRun("c", "agent_discovery", "agent_discovery", 2, ""),  # right route, bad answer
    ]
    agg = aggregate(runs)
    assert agg["total"] == 3
    assert abs(agg["routing_accuracy"] - 2 / 3) < 1e-9
    assert abs(agg["answer_pass_rate"] - 2 / 3) < 1e-9
    assert abs(agg["avg_answer_score"] - 11 / 3) < 1e-9


def test_aggregate_empty_is_zero_not_crash():
    agg = aggregate([])
    assert agg == {
        "total": 0,
        "routing_accuracy": 0.0,
        "answer_pass_rate": 0.0,
        "avg_answer_score": 0.0,
    }
