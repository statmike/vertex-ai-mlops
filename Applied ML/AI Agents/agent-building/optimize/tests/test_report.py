"""Tests for Markdown report rendering."""

from optimize.harness import render_report
from optimize.harness.scoring import ScoredRun


def test_report_has_summary_and_rows():
    runs = [
        ScoredRun("return_window", "agent_catalog", "agent_catalog", 5, "grounded"),
        ScoredRun("top_sales", "agent_analytics", "agent_catalog", 2, "wrong specialist"),
    ]
    md = render_report(runs, title="Test Report")
    assert "# Test Report" in md
    assert "Routing accuracy | 50%" in md
    assert "return_window" in md
    assert "✅" in md and "❌" in md


def test_report_escapes_pipes_in_notes():
    runs = [ScoredRun("x", "agent_catalog", "agent_catalog", 4, "a | b | c")]
    md = render_report(runs)
    # The pipe inside a note must be escaped so it can't break the table.
    assert "a \\| b \\| c" in md


def test_report_handles_no_route():
    runs = [ScoredRun("x", "agent_catalog", None, 1, "no answer", error="timeout")]
    md = render_report(runs)
    assert "| — |" in md  # missing route rendered as em dash
    assert "timeout" in md  # error shown in place of reasoning
