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

import base64
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = Path(__file__).resolve().parent / "results"
TRACES_PATH = RESULTS_DIR / "platform_traces.json"


def _jsonable(value):
    """Recursively convert a trace value into JSON that re-validates cleanly.

    Gemini 3 events carry a `thought_signature` as raw ``bytes``. The schema
    evaluate_platform.py reloads with expects those as **base64** — a plain
    ``str(bytes)`` yields a Python repr (``"b'\\x01...'"``) that fails base64
    validation, so every case's agent_data would be dropped and score 0. Encode
    bytes as base64 and recurse through dicts/lists so the round-trip is lossless.
    """
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value

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
    """Describe the agent under test for scenario generation.

    The service needs the whole multi-agent topology, not just the root name: an
    ``agents`` map (root + every delegate, so it can reason about routing) keyed by
    agent id, plus the ``root_agent_id``. ``AgentConfig.from_agent`` derives each
    entry (id, type, description, instruction, tools, sub-agent edges) straight
    from the ADK agent, so this stays in sync with agent_concierge/ automatically.
    """
    from vertexai._genai.types.evals import AgentConfig, AgentInfo

    from agent_concierge.agent import root_agent

    # Walk the tree from the root, collecting one AgentConfig per unique agent.
    agents: dict = {}
    stack = [root_agent]
    while stack:
        agent = stack.pop()
        name = getattr(agent, "name", None)
        if not name or name in agents:
            continue
        agents[name] = AgentConfig.from_agent(agent)
        stack.extend(getattr(agent, "sub_agents", []) or [])

    return AgentInfo(name=root_agent.name, root_agent_id=root_agent.name, agents=agents)


def main() -> None:
    from agent_concierge.agent import root_agent

    client = _client()

    print(f"Generating {SCENARIO_COUNT} conversation scenarios...")
    # The scenario-generation autorater is a preview model served only on the
    # `global` endpoint; our client runs in a region (GOOGLE_CLOUD_LOCATION), so
    # opt in to cross-region routing or the service rejects the request with 400.
    scenarios = client.evals.generate_conversation_scenarios(
        agent_info=_agent_info(),
        config={"count": SCENARIO_COUNT, "generation_instruction": GENERATION_INSTRUCTION},
        allow_cross_region_model=True,
    )

    print(f"Running inference with a simulated user (max {MAX_TURNS} turns)...")
    traces = client.evals.run_inference(
        agent=root_agent,
        src=scenarios,
        config={"user_simulator_config": {"max_turn": MAX_TURNS}},
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # run_inference returns the traces in the EvaluationDataset's `eval_dataset_df`
    # (a pandas DataFrame whose `agent_data` cells are nested dicts). model_dump()
    # would stringify the DataFrame and lose that structure, so persist the frame
    # itself as records JSON (round-trips the nested dicts) alongside the candidate
    # name; evaluate_platform.py rebuilds the dataset from these.
    payload = {
        "candidate_name": traces.candidate_name,
        "eval_dataset_records": _jsonable(traces.eval_dataset_df.to_dict(orient="records")),
    }
    # Use the stdlib encoder (not DataFrame.to_json, whose ujson backend rejects
    # some multi-byte sequences that appear in model/tool output); _jsonable has
    # already base64-encoded the bytes fields, default=str is a last-resort guard.
    TRACES_PATH.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(f"\nWrote {len(payload['eval_dataset_records'])} simulated traces to "
          f"{TRACES_PATH.relative_to(PROJECT_ROOT)}")
    print("Next: uv run python optimize/evaluate_platform.py")


if __name__ == "__main__":
    main()
