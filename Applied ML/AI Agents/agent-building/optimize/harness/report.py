"""Render scored runs into a Markdown report — pure string building, no I/O."""

from __future__ import annotations

from .scoring import ScoredRun, aggregate


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def render_report(runs: list[ScoredRun], title: str = "Local Evaluation Report") -> str:
    """Build a Markdown report: summary table + per-scenario detail."""
    summary = aggregate(runs)

    lines = [f"# {title}", ""]
    lines += [
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Scenarios | {summary['total']} |",
        f"| Routing accuracy | {_pct(summary['routing_accuracy'])} |",
        f"| Answer pass rate (score ≥ 4) | {_pct(summary['answer_pass_rate'])} |",
        f"| Avg answer score (1-5) | {summary['avg_answer_score']:.2f} |",
        "",
        "## Per-scenario",
        "",
        "| Scenario | Expected | Routed to | Route | Score | Notes |",
        "|---|---|---|:--:|:--:|---|",
    ]

    for r in runs:
        route_mark = "✅" if r.routing_correct else "❌"
        routed = r.routed_to or "—"
        note = r.error or r.reasoning
        note = note.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {r.scenario_id} | {r.expected_agent} | {routed} | "
            f"{route_mark} | {r.answer_score} | {note} |"
        )

    lines.append("")
    return "\n".join(lines)
