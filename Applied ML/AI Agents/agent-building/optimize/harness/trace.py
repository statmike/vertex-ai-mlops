"""Turn a stream of ADK events into a compact, judgeable trace.

The local runner yields ``google.adk.events.Event`` objects. For scoring we only
need three things per scenario: which specialist got the question (routing), the
final text answer, and the tools that fired (trajectory). This module distills
exactly that — as plain functions over duck-typed events so it's testable with
lightweight fakes, no runner required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunTrace:
    """Everything the judge needs about one scenario run."""

    routed_to: str | None = None  # specialist the router transferred to
    final_answer: str = ""
    tools_called: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.final_answer)


def _iter_parts(event: Any):
    """Yield content parts of an event, tolerating missing attrs."""
    content = getattr(event, "content", None)
    parts = getattr(content, "parts", None) if content else None
    return parts or []


def extract_trace(events: list[Any]) -> RunTrace:
    """Reduce ADK events to a RunTrace.

    Routing is read from ``event.actions.transfer_to_agent`` (the concierge's
    delegation). The final answer is the last non-user text part. Tool calls are
    collected in order for trajectory scoring.
    """
    trace = RunTrace()

    for event in events:
        actions = getattr(event, "actions", None)
        transfer = getattr(actions, "transfer_to_agent", None) if actions else None
        # First transfer is the router's routing decision; ignore later ones.
        if transfer and trace.routed_to is None:
            trace.routed_to = transfer

        for part in _iter_parts(event):
            call = getattr(part, "function_call", None)
            if call and getattr(call, "name", None):
                trace.tools_called.append(call.name)

    # Final answer: last text part authored by a non-user (specialist or router).
    for event in reversed(events):
        if getattr(event, "author", None) == "user":
            continue
        for part in _iter_parts(event):
            text = getattr(part, "text", None)
            if text:
                trace.final_answer = text
                return trace

    return trace
