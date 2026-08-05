"""Platform eval engine, step 2 — score the simulated traces with AutoRaters.

Feeds the traces from simulate_platform.py to the managed evaluation service using
prebuilt **multi-turn** raters (task success + tool-use quality), then prints the
summary metrics.

    uv run python optimize/evaluate_platform.py

This is the platform counterpart to judge_local.py: managed AutoRaters instead of
our own LLM-judge prompt.
"""

from __future__ import annotations

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


def main() -> None:
    from vertexai._genai.types import PrebuiltMetric

    if not TRACES_PATH.exists():
        print(f"No traces at {TRACES_PATH}. Run: uv run python optimize/simulate_platform.py")
        raise SystemExit(1)

    client = _client()

    # Multi-turn raters: did the agent accomplish the task, and use tools well?
    metrics = [
        PrebuiltMetric.MULTI_TURN_TASK_SUCCESS,
        PrebuiltMetric.MULTI_TURN_TOOL_USE_QUALITY,
    ]

    print("Evaluating simulated traces with multi-turn AutoRaters...")
    result = client.evals.evaluate(dataset=str(TRACES_PATH), metrics=metrics)

    print("\n=== Platform evaluation summary ===")
    summary = getattr(result, "summary_metrics", None) or result
    print(summary)
    print(
        "\nInspect full results in the Cloud Console (Gen AI evaluation), or use "
        "client.evals.generate_loss_clusters(...) to group failures."
    )


if __name__ == "__main__":
    main()
