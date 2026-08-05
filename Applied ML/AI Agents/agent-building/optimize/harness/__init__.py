"""Reusable, unit-tested logic for the local eval harness.

Kept separate from the CLI scripts so the parts that don't need cloud — trace
extraction, judge-output parsing, scoring math, and report rendering — can be
tested fully offline.
"""

from .observability import agent_activity_sql, event_summary_sql
from .report import render_report
from .scenarios import Scenario, load_scenarios
from .scoring import ScoredRun, aggregate, parse_judge_output
from .trace import RunTrace, extract_trace

__all__ = [
    "RunTrace",
    "ScoredRun",
    "Scenario",
    "agent_activity_sql",
    "aggregate",
    "event_summary_sql",
    "extract_trace",
    "load_scenarios",
    "parse_judge_output",
    "render_report",
]
