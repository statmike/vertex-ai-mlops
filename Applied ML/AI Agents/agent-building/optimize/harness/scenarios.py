"""The shared evaluation set — one source of truth for both engines.

Each scenario pairs a user question with ground truth: which specialist *should*
handle it (routing correctness) and a short reference of what a good answer looks
like (grounding for the judge). ``scenarios.json`` sits beside this module so the
platform and local engines score the exact same cases.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# The three specialists the concierge routes to. A scenario's expected_agent must
# be one of these (validated on load) so a typo can't silently pass every run.
VALID_AGENTS = frozenset({"agent_catalog", "agent_analytics", "agent_discovery"})

SCENARIOS_PATH = Path(__file__).resolve().parent / "scenarios.json"


@dataclass(frozen=True)
class Scenario:
    """One evaluation case."""

    id: str
    question: str
    expected_agent: str  # which specialist should handle it
    reference: str  # what a correct answer covers (judge grounding)


def load_scenarios(path: Path | None = None) -> list[Scenario]:
    """Load and validate scenarios from JSON.

    Raises ValueError on a malformed file so a broken eval set fails loudly
    rather than silently evaluating nothing.
    """
    path = path or SCENARIOS_PATH
    raw = json.loads(path.read_text())
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{path} must contain a non-empty JSON array of scenarios.")

    scenarios = []
    seen_ids = set()
    for i, item in enumerate(raw):
        missing = {"id", "question", "expected_agent", "reference"} - item.keys()
        if missing:
            raise ValueError(f"Scenario #{i} is missing keys: {sorted(missing)}")
        if item["id"] in seen_ids:
            raise ValueError(f"Duplicate scenario id: {item['id']!r}")
        if item["expected_agent"] not in VALID_AGENTS:
            raise ValueError(
                f"Scenario {item['id']!r} has unknown expected_agent "
                f"{item['expected_agent']!r}; must be one of {sorted(VALID_AGENTS)}"
            )
        seen_ids.add(item["id"])
        scenarios.append(
            Scenario(
                id=item["id"],
                question=item["question"],
                expected_agent=item["expected_agent"],
                reference=item["reference"],
            )
        )
    return scenarios
