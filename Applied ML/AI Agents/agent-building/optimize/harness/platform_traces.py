"""Flatten simulated multi-agent traces into scorable prompt/response rows.

Shared by the platform scripts (evaluate_platform.py, optimize_platform.py) and
unit-tested offline. The managed multi-turn trace raters reject a multi-agent
system (see evaluate_platform.py), so we reduce each simulated conversation to a
plain ``prompt`` + final ``response`` and score *that*. This module is the pure,
cloud-free core of that reduction.
"""

from __future__ import annotations

from typing import Any


def final_response(agent_data: Any) -> str:
    """Pull the agent's final answer text out of a simulated trace.

    A trace is ``agent_data.turns[].events[]``; the answer is the last non-user,
    model-authored text event. Returns "" when the run errored (the A2A discovery
    scenario can fail under the simulator).
    """
    if not isinstance(agent_data, dict):
        return ""
    text = ""
    for turn in agent_data.get("turns", []) or []:
        for event in turn.get("events", []) or []:
            content = event.get("content") or {}
            is_model = content.get("role") == "model" or event.get("author") not in (None, "user")
            if not is_model:
                continue
            parts = content.get("parts") or []
            joined = " ".join(p.get("text", "") for p in parts if p.get("text"))
            if joined.strip():
                text = joined
    return text


def is_incomplete(agent_data: Any) -> bool:
    """True when the simulator couldn't complete the scenario.

    A failed run carries only an ``error`` key (and no ``agents`` topology), so
    scoring it would penalize the agent for an infrastructure failure, not a bad
    answer. Callers skip these.
    """
    return isinstance(agent_data, dict) and "error" in agent_data and "agents" not in agent_data


def flatten_records(records: list[dict]) -> tuple[list[dict[str, str]], int]:
    """Reduce saved trace records to ``[{prompt, response}]`` rows.

    Returns the rows plus a count of scenarios skipped as incomplete.
    """
    rows: list[dict[str, str]] = []
    skipped = 0
    for record in records:
        agent_data = record.get("agent_data")
        if is_incomplete(agent_data):
            skipped += 1
            continue
        rows.append(
            {
                "prompt": record.get("starting_prompt", ""),
                "response": final_response(agent_data),
            }
        )
    return rows, skipped
