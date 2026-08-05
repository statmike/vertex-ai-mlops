"""Tests for reducing ADK events into a RunTrace.

Events are duck-typed, so we fake them with simple namespaces — no runner needed.
"""

from types import SimpleNamespace

from optimize.harness import extract_trace


def _part(text=None, call_name=None):
    call = SimpleNamespace(name=call_name) if call_name else None
    return SimpleNamespace(text=text, function_call=call)


def _event(author="agent", parts=None, transfer=None):
    content = SimpleNamespace(parts=parts or [])
    actions = SimpleNamespace(transfer_to_agent=transfer)
    return SimpleNamespace(author=author, content=content, actions=actions)


def test_extracts_routing_final_answer_and_tools():
    events = [
        _event(author="user", parts=[_part(text="What's your return window?")]),
        _event(transfer="agent_catalog"),
        _event(parts=[_part(call_name="search_docs")]),
        _event(parts=[_part(text="Our return window is 30 days.")]),
    ]
    trace = extract_trace(events)
    assert trace.routed_to == "agent_catalog"
    assert trace.tools_called == ["search_docs"]
    assert trace.final_answer == "Our return window is 30 days."
    assert trace.ok


def test_first_transfer_wins():
    events = [
        _event(transfer="agent_catalog"),
        _event(transfer="agent_analytics"),
        _event(parts=[_part(text="answer")]),
    ]
    assert extract_trace(events).routed_to == "agent_catalog"


def test_no_answer_is_not_ok():
    events = [_event(transfer="agent_discovery")]
    trace = extract_trace(events)
    assert trace.final_answer == ""
    assert not trace.ok


def test_final_answer_ignores_user_turns():
    events = [
        _event(parts=[_part(text="the real answer")]),
        _event(author="user", parts=[_part(text="a follow-up question")]),
    ]
    assert extract_trace(events).final_answer == "the real answer"
