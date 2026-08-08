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
``prompt`` + final ``response`` (see harness/platform_traces.py) and score *that*
with the final-response raters, which judge answer text and don't care how many
agents produced it. (Routing correctness across the whole system is still covered
offline by judge_local.py.)

The evaluation step is exposed as :func:`run_evaluation` so optimize_platform.py
can reuse the exact same dataset + raters to then cluster the failures.
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


def load_rows() -> list[dict[str, str]]:
    """Load the saved traces and flatten them to scorable prompt/response rows."""
    from optimize.harness.platform_traces import flatten_records

    if not TRACES_PATH.exists():
        print(f"No traces at {TRACES_PATH}. Run: uv run python optimize/simulate_platform.py")
        raise SystemExit(1)

    saved = json.loads(TRACES_PATH.read_text())
    rows, skipped = flatten_records(saved["eval_dataset_records"])
    if skipped:
        print(f"Skipping {skipped} scenario(s) the simulator could not complete.")
    if not rows:
        print("No completed scenarios to evaluate.")
        raise SystemExit(1)
    return rows


def run_evaluation(client, rows: list[dict[str, str]]):
    """Score the flattened rows with the managed final-response raters.

    Returns the EvaluationResult so callers (optimize_platform.py) can feed it to
    loss clustering without re-running the evaluation.
    """
    import pandas as pd
    from vertexai._genai.types import EvaluationDataset, PrebuiltMetric

    dataset = EvaluationDataset(eval_dataset_df=pd.DataFrame(rows))

    # Final-response raters (reference-free): overall answer quality, and the
    # general-quality rubric. Both judge the answer text, so they work on a
    # multi-agent system where the trajectory raters do not.
    metrics = [
        PrebuiltMetric.FINAL_RESPONSE_QUALITY,
        PrebuiltMetric.GENERAL_QUALITY,
    ]

    print(f"Evaluating {len(rows)} simulated answer(s) with managed AutoRaters...")
    return client.evals.evaluate(dataset=dataset, metrics=metrics)


def print_summary(result) -> None:
    print("\n=== Platform evaluation summary ===")
    for metric in getattr(result, "summary_metrics", None) or []:
        name = getattr(metric, "metric_name", "?")
        mean = getattr(metric, "mean_score", None)
        valid = getattr(metric, "num_cases_valid", "?")
        total = getattr(metric, "num_cases_total", "?")
        mean_str = f"{mean:.3f}" if isinstance(mean, (int, float)) else str(mean)
        print(f"  {name}: mean={mean_str}  ({valid}/{total} cases scored)")


def main() -> None:
    client = _client()
    rows = load_rows()
    result = run_evaluation(client, rows)
    print_summary(result)
    print(
        "\nInspect full results in the Cloud Console (Gen AI evaluation), or run "
        "optimize/optimize_platform.py to cluster the failures into patterns."
    )


if __name__ == "__main__":
    main()
