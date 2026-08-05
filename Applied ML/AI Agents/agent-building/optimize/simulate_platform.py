"""Platform eval engine, step 1 — simulate multi-turn conversations.

Uses the managed Gen AI Evaluation & Simulation API to synthesize user scenarios
from the concierge's own definition, then runs a **simulated user** against the
agent to capture behavior traces. Traces are saved for evaluate_platform.py.

    uv run python optimize/simulate_platform.py

This is the platform counterpart to run_local.py: instead of our own runner + a
hand-written scenario file, the service drives the conversation. It's a preview
feature; see the README for docs links.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = Path(__file__).resolve().parent / "results"
TRACES_PATH = RESULTS_DIR / "platform_traces.json"

# How many scenarios to synthesize and how many turns the simulated user takes.
SCENARIO_COUNT = 6
MAX_TURNS = 4

GENERATION_INSTRUCTION = (
    "Generate realistic questions a shopper, merchant, or analyst would ask "
    "theLook's retail concierge: policy/how-to questions answerable from "
    "documents, quantitative questions about sales and orders, and questions "
    "about what data or tables exist. Keep each scenario to a single clear goal."
)


def _client():
    import vertexai

    from config import GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROJECT

    if not GOOGLE_CLOUD_PROJECT:
        print("Error: GOOGLE_CLOUD_PROJECT not set.")
        raise SystemExit(1)
    return vertexai.Client(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)


def _agent_info():
    """Describe the agent under test for scenario generation."""
    from vertexai._genai.types.evals import AgentInfo

    from agent_concierge.agent import root_agent

    return AgentInfo(name=root_agent.name, root_agent_id=root_agent.name)


def main() -> None:
    from agent_concierge.agent import root_agent

    client = _client()

    print(f"Generating {SCENARIO_COUNT} conversation scenarios...")
    scenarios = client.evals.generate_conversation_scenarios(
        agent_info=_agent_info(),
        config={"count": SCENARIO_COUNT, "generation_instruction": GENERATION_INSTRUCTION},
    )

    print(f"Running inference with a simulated user (max {MAX_TURNS} turns)...")
    traces = client.evals.run_inference(
        agent=root_agent,
        src=scenarios,
        config={"user_simulator_config": {"max_turn": MAX_TURNS}},
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # EvaluationDataset is serializable via its dict form; persist for evaluate step.
    payload = traces.model_dump() if hasattr(traces, "model_dump") else traces
    TRACES_PATH.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(f"\nWrote simulated traces to {TRACES_PATH.relative_to(PROJECT_ROOT)}")
    print("Next: uv run python optimize/evaluate_platform.py")


if __name__ == "__main__":
    main()
