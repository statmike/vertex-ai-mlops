"""Offline tests for the platform-trace flattening harness."""

from optimize.harness.platform_traces import (
    final_response,
    flatten_records,
    is_incomplete,
)


def _agent_data_with(*texts, roles=None):
    """Build an agent_data dict with a single turn of model text events."""
    roles = roles or ["model"] * len(texts)
    events = [
        {"content": {"role": role, "parts": [{"text": t}]}}
        for t, role in zip(texts, roles, strict=True)
    ]
    return {"agents": {}, "turns": [{"events": events}]}


def test_final_response_takes_last_model_text():
    data = _agent_data_with("first", "final")
    assert final_response(data) == "final"


def test_final_response_ignores_user_events():
    data = {
        "turns": [
            {
                "events": [
                    {"content": {"role": "user", "parts": [{"text": "question"}]}},
                    {"content": {"role": "model", "parts": [{"text": "answer"}]}},
                ]
            }
        ]
    }
    assert final_response(data) == "answer"


def test_final_response_handles_non_dict():
    assert final_response(None) == ""
    assert final_response("error") == ""


def test_is_incomplete_detects_error_only_traces():
    assert is_incomplete({"error": "boom"}) is True
    # An errored-but-still-multi-agent trace is not "incomplete" for our purposes.
    assert is_incomplete({"error": "boom", "agents": {}}) is False
    assert is_incomplete(_agent_data_with("ok")) is False


def test_flatten_records_skips_incomplete_and_maps_rows():
    records = [
        {"starting_prompt": "q1", "agent_data": _agent_data_with("a1")},
        {"starting_prompt": "q2", "agent_data": {"error": "boom"}},  # skipped
        {"starting_prompt": "q3", "agent_data": _agent_data_with("draft", "a3")},
    ]
    rows, skipped = flatten_records(records)
    assert skipped == 1
    assert rows == [
        {"prompt": "q1", "response": "a1"},
        {"prompt": "q3", "response": "a3"},
    ]
