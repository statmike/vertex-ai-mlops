"""Platform eval engine, step 2 — score the simulated traces with AutoRaters.

Feeds the traces from simulate_platform.py to the managed evaluation service's
prebuilt AutoRaters, then prints the summary metrics.

    uv run python optimize/evaluate_platform.py

This is the platform counterpart to judge_local.py: managed AutoRaters instead of
our own LLM-judge prompt.

**Multi-agent caveat (why we flatten first).** The concierge is a *router over
three specialists*. The managed multi-turn raters that read the raw agent trace —
MULTI_TURN_TASK_SUCCESS, MULTI_TURN_TOOL_USE_QUALITY, MULTI_TURN_TRAJECTORY_QUALITY
— currently reject a multi-agent trace outright ("does not support multiagent
evaluation", HTTP 400). So instead of handing the raters the multi-agent
``agent_data`` topology, we flatten each simulated conversation to a plain
``prompt`` + final ``response`` and score *that* with the final-response raters,
which judge answer text and don't care how many agents produced it. (Routing
correctness across the whole system is still covered offline by judge_local.py.)
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


def _client():
    import vertexai

    from config import GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROJECT

    if not GOOGLE_CLOUD_PROJECT:
        print("Error: GOOGLE_CLOUD_PROJECT not set.")
        raise SystemExit(1)
    return vertexai.Client(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)


def _final_response(agent_data: dict) -> str:
    """Pull the agent's final answer text out of a simulated trace.

    A trace is ``agent_data.turns[].events[]``; the answer is the last non-user,
    model-authored text event. Returns "" when the run errored (the A2A discovery
    scenario can fail under the simulator — see simulate_platform.py).
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


def main() -> None:
    import pandas as pd
    from vertexai._genai.types import EvaluationDataset, PrebuiltMetric

    if not TRACES_PATH.exists():
        print(f"No traces at {TRACES_PATH}. Run: uv run python optimize/simulate_platform.py")
        raise SystemExit(1)

    client = _client()

    # Flatten the multi-agent traces to prompt + final response (see module
    # docstring). Skip cases the simulator couldn't complete (agent_data carries
    # only an "error" key), so a failed A2A hop doesn't score as an empty answer.
    saved = json.loads(TRACES_PATH.read_text())
    rows = []
    skipped = 0
    for record in saved["eval_dataset_records"]:
        agent_data = record.get("agent_data")
        if isinstance(agent_data, dict) and "error" in agent_data and "agents" not in agent_data:
            skipped += 1
            continue
        rows.append(
            {
                "prompt": record.get("starting_prompt", ""),
                "response": _final_response(agent_data),
            }
        )
    if skipped:
        print(f"Skipping {skipped} scenario(s) the simulator could not complete.")
    if not rows:
        print("No completed scenarios to evaluate.")
        raise SystemExit(1)

    dataset = EvaluationDataset(eval_dataset_df=pd.DataFrame(rows))

    # Final-response raters (reference-free): overall answer quality, and the
    # general-quality rubric. Both judge the answer text, so they work on a
    # multi-agent system where the trajectory raters do not.
    metrics = [
        PrebuiltMetric.FINAL_RESPONSE_QUALITY,
        PrebuiltMetric.GENERAL_QUALITY,
    ]

    print(f"Evaluating {len(rows)} simulated answer(s) with managed AutoRaters...")
    result = client.evals.evaluate(dataset=dataset, metrics=metrics)

    print("\n=== Platform evaluation summary ===")
    for metric in getattr(result, "summary_metrics", None) or []:
        name = getattr(metric, "metric_name", "?")
        mean = getattr(metric, "mean_score", None)
        valid = getattr(metric, "num_cases_valid", "?")
        total = getattr(metric, "num_cases_total", "?")
        mean_str = f"{mean:.3f}" if isinstance(mean, (int, float)) else str(mean)
        print(f"  {name}: mean={mean_str}  ({valid}/{total} cases scored)")
    print(
        "\nInspect full results in the Cloud Console (Gen AI evaluation), or use "
        "client.evals.generate_loss_clusters(...) to group failures."
    )


if __name__ == "__main__":
    main()
