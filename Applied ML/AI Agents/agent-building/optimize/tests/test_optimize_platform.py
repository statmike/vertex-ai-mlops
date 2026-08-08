"""Offline tests for the Agent Optimizer (loss clustering) helpers.

The cloud calls live in functions that import vertexai lazily; the pure pieces —
metric-name resolution, synthetic-case construction, cluster printing — are
tested here without touching the service.
"""

from types import SimpleNamespace

from optimize import optimize_platform as op


def _result_with_metrics(*names):
    metrics = [SimpleNamespace(metric_name=n) for n in names]
    return SimpleNamespace(summary_metrics=metrics)


def test_resolve_metric_prefers_task_success_prefix():
    result = _result_with_metrics("general_quality_v1", "multi_turn_task_success_v1")
    assert op._resolve_metric_name(result) == "multi_turn_task_success_v1"


def test_resolve_metric_falls_back_to_first():
    result = _result_with_metrics("some_other_metric_v2")
    assert op._resolve_metric_name(result) == "some_other_metric_v2"


def test_resolve_metric_handles_empty():
    assert op._resolve_metric_name(_result_with_metrics()) == op.LOSS_METRIC_PREFIX


def test_synthetic_cases_are_single_turn_single_agent():
    rows = [{"prompt": "q1", "response": "a1"}, {"prompt": "q2", "response": "a2"}]
    cases = op._synthetic_cases(rows)
    assert len(cases) == 2

    ad = cases[0].agent_data
    # Exactly one declared agent — this is what keeps the multi-turn rater from
    # rejecting the case as multiagent.
    assert list(ad.agents) == [op.SYNTHETIC_AGENT_ID]
    # Exactly one turn, with a user event then a model event.
    assert len(ad.turns) == 1
    events = ad.turns[0].events
    assert [e.author for e in events] == ["user", op.SYNTHETIC_AGENT_ID]
    assert events[0].content.parts[0].text == "q1"
    assert events[1].content.parts[0].text == "a1"
    # Every event carries a timestamp (required for the case to serialize).
    assert all(e.event_time is not None for e in events)


def test_print_clusters_handles_none_taxonomy_fields(capsys):
    # The SDK leaves l2_category / description as None on some entries; the
    # printer must not slice None.
    tax = SimpleNamespace(l1_category="Instruction Following", l2_category=None, description=None)
    cluster = SimpleNamespace(taxonomy_entry=tax, item_count=3, examples=[])
    response = SimpleNamespace(results=[SimpleNamespace(clusters=[cluster])])

    op._print_clusters(response, "multi_turn_task_success_v1")
    out = capsys.readouterr().out
    assert "Instruction Following" in out
    assert "3×" in out


def test_print_clusters_reports_no_clusters(capsys):
    op._print_clusters(SimpleNamespace(results=[]), "multi_turn_task_success_v1")
    assert "No loss clusters" in capsys.readouterr().out
