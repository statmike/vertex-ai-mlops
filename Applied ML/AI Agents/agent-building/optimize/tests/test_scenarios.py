"""Tests for scenario loading + validation."""

import json

import pytest

from optimize.harness import load_scenarios
from optimize.harness.scenarios import VALID_AGENTS


def test_bundled_scenarios_load_and_are_valid():
    scenarios = load_scenarios()
    assert len(scenarios) >= 6
    # Every modality is represented, so the eval exercises all three specialists.
    covered = {s.expected_agent for s in scenarios}
    assert covered == VALID_AGENTS


def test_duplicate_ids_rejected(tmp_path):
    path = tmp_path / "s.json"
    path.write_text(
        json.dumps(
            [
                {"id": "x", "question": "q", "expected_agent": "agent_catalog", "reference": "r"},
                {
                    "id": "x",
                    "question": "q2",
                    "expected_agent": "agent_analytics",
                    "reference": "r",
                },
            ]
        )
    )
    with pytest.raises(ValueError, match="Duplicate"):
        load_scenarios(path)


def test_unknown_agent_rejected(tmp_path):
    path = tmp_path / "s.json"
    path.write_text(
        json.dumps(
            [
                {"id": "x", "question": "q", "expected_agent": "agent_typo", "reference": "r"},
            ]
        )
    )
    with pytest.raises(ValueError, match="unknown expected_agent"):
        load_scenarios(path)


def test_empty_file_rejected(tmp_path):
    path = tmp_path / "s.json"
    path.write_text("[]")
    with pytest.raises(ValueError, match="non-empty"):
        load_scenarios(path)
