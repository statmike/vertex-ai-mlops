"""Platform eval engine, step 3 — cluster failures into patterns (Agent Optimizer).

Evaluation tells you *what* the mean score is; the Agent Optimizer tells you *why*
answers lose. ``client.evals.generate_loss_clusters`` reads the failed-rubric
signals from a rubric-based AutoRater and groups the failures into semantic "loss
patterns" (e.g. "Instruction Following / Over-Punting", "Hallucination") with an
L1/L2 taxonomy and representative examples. That's the actionable end of the
Optimize pillar: each cluster is a candidate instruction fix.

    uv run python optimize/optimize_platform.py

It reuses simulate_platform.py's saved traces (via evaluate_platform.py's flatten
step) so the clustering analyzes the same run you just scored — no second
simulation.

Two hard-won facts drive the shape of this script; both were confirmed live
against the preview service and are the reason it does NOT simply hand it the
EvaluationResult that evaluate_platform.py produces:

1. **Loss clustering only works with the MULTI_TURN_* agentic raters.** Given a
   FINAL_RESPONSE_QUALITY result, ``generate_loss_clusters`` runs the LRO to
   completion and returns an *empty* response — no error, no clusters. Only the
   multi-turn task/tool/trajectory raters carry the failed-rubric signal the
   analysis groups on. We cluster on MULTI_TURN_TASK_SUCCESS.

2. **Those multi-turn raters reject a multi-agent trace** ("does not support
   multiagent evaluation", 400) — and our concierge is a router over three
   specialists (the same limitation evaluate_platform.py documents). So we wrap
   each flattened prompt/response as a **synthetic single-turn AgentData** that
   declares a single agent. That satisfies the multi-turn rater (one turn, one
   agent) *and* clustering's requirement that the EvaluationResult "contain
   AgentData with conversation turns" — the two constraints that otherwise
   contradict each other. Routing correctness across the real topology stays
   covered offline by judge_local.py.

Loss clustering is a **preview** feature served only in the ``global`` region;
this script pins the client there regardless of GOOGLE_CLOUD_LOCATION.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# The rater whose failures we cluster. Loss clustering needs a MULTI_TURN_* rater
# (see module docstring); TASK_SUCCESS is the one most directly tied to "did the
# agent actually do what was asked". The service reports names with a version
# suffix (e.g. "multi_turn_task_success_v1"), so we match by prefix below.
LOSS_METRIC_PREFIX = "multi_turn_task_success"
MAX_CLUSTERS = 5

# A single synthetic agent id for the wrapped traces — one declared agent keeps
# the multi-turn rater from rejecting the case as "multiagent".
SYNTHETIC_AGENT_ID = "agent_concierge"
# Fixed timestamps: the events need valid Timestamps to serialize, but the actual
# values are irrelevant to a single-turn analysis. Using constants keeps the run
# deterministic.
_T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
_T1 = _T0 + datetime.timedelta(seconds=1)


def _resolve_metric_name(result) -> str:
    """Pick the concrete (versioned) rater name to cluster from the result.

    evaluate() reports names like ``multi_turn_task_success_v1``; loss clustering
    must be given the exact name present in the result. Match our target rater by
    prefix, falling back to the first available metric.
    """
    names = [getattr(m, "metric_name", "") for m in getattr(result, "summary_metrics", None) or []]
    for name in names:
        if name.startswith(LOSS_METRIC_PREFIX):
            return name
    if names:
        return names[0]
    return LOSS_METRIC_PREFIX


def _global_client():
    """A client pinned to `global` — where loss clustering is served."""
    import vertexai

    from config import GOOGLE_CLOUD_PROJECT

    if not GOOGLE_CLOUD_PROJECT:
        print("Error: GOOGLE_CLOUD_PROJECT not set.")
        raise SystemExit(1)
    return vertexai.Client(project=GOOGLE_CLOUD_PROJECT, location="global")


def _synthetic_cases(rows: list[dict[str, str]]):
    """Wrap flattened prompt/response rows as single-turn, single-agent EvalCases.

    Each case is one conversation turn — a user event carrying the prompt and a
    model event carrying the agent's final response — under an AgentData that
    declares exactly one agent. This is the shape both the multi-turn rater and
    loss clustering accept (see module docstring).
    """
    from google.genai import types as genai_types
    from vertexai._genai import types as vtypes
    from vertexai._genai.types import evals as evals_types

    cases = []
    agents = {
        SYNTHETIC_AGENT_ID: evals_types.AgentConfig(
            agent_id=SYNTHETIC_AGENT_ID, agent_type="llm"
        )
    }
    for i, row in enumerate(rows):
        events = [
            evals_types.AgentEvent(
                author="user",
                content=genai_types.Content(
                    role="user", parts=[genai_types.Part(text=row["prompt"])]
                ),
                event_time=_T0,
            ),
            evals_types.AgentEvent(
                author=SYNTHETIC_AGENT_ID,
                content=genai_types.Content(
                    role="model", parts=[genai_types.Part(text=row["response"])]
                ),
                event_time=_T1,
            ),
        ]
        agent_data = evals_types.AgentData(
            agents=agents,
            turns=[evals_types.ConversationTurn(turn_index=0, turn_id="t0", events=events)],
        )
        cases.append(vtypes.EvalCase(eval_case_id=f"case_{i}", agent_data=agent_data))
    return cases


def _evaluate_for_clustering(client, rows: list[dict[str, str]]):
    """Score the synthetic single-turn cases with the multi-turn task rater.

    Returns the EvaluationResult whose failed rubrics loss clustering will group.
    """
    from vertexai._genai import types as vtypes

    dataset = vtypes.EvaluationDataset(eval_cases=_synthetic_cases(rows))
    print(f"Scoring {len(rows)} answer(s) with {LOSS_METRIC_PREFIX} for loss analysis...")
    return client.evals.evaluate(
        dataset=dataset, metrics=[vtypes.PrebuiltMetric.MULTI_TURN_TASK_SUCCESS]
    )


def _print_clusters(response, metric_name: str) -> None:
    results = getattr(response, "results", None) or []
    if not results:
        print("No loss clusters returned (too few failures to cluster, or all passed).")
        return
    for analysis in results:
        clusters = getattr(analysis, "clusters", None) or []
        print(f"\n=== {len(clusters)} loss pattern(s) for {metric_name} ===")
        # Biggest clusters first — the failure patterns that cost the most.
        for cluster in sorted(clusters, key=lambda c: getattr(c, "item_count", 0) or 0, reverse=True):
            tax = getattr(cluster, "taxonomy_entry", None)
            # These fields exist on the object but can be None; guard before use.
            l1 = (getattr(tax, "l1_category", None) or "?") if tax else "?"
            l2 = (getattr(tax, "l2_category", None) or "") if tax else ""
            desc = (getattr(tax, "description", None) or "") if tax else ""
            count = getattr(cluster, "item_count", 0) or 0
            label = f"{l1} / {l2}" if l2 else l1
            print(f"\n  [{count:>2}×] {label}")
            if desc:
                print(f"        {desc}")
            examples = getattr(cluster, "examples", None) or []
            for ex in examples[:1]:  # one representative example per cluster
                failed = getattr(ex, "failed_rubrics", None) or []
                if failed:
                    rationale = getattr(failed[0], "classification_rationale", None) or str(failed[0])
                    print(f"        e.g. {str(rationale)[:160]}")


def main() -> None:
    from optimize.evaluate_platform import load_rows

    client = _global_client()

    # Reuse the same flatten path so the clustering analyzes the same answers we
    # score in evaluate_platform.py — just re-scored with the multi-turn rater
    # loss clustering requires.
    rows = load_rows()
    result = _evaluate_for_clustering(client, rows)

    for metric in getattr(result, "summary_metrics", None) or []:
        mean = getattr(metric, "mean_score", None)
        mean_str = f"{mean:.3f}" if isinstance(mean, (int, float)) else str(mean)
        valid = getattr(metric, "num_cases_valid", "?")
        total = getattr(metric, "num_cases_total", "?")
        print(f"  {getattr(metric, 'metric_name', '?')}: mean={mean_str}  ({valid}/{total} scored)")

    metric_name = _resolve_metric_name(result)
    print(f"\nClustering {metric_name} failures into patterns (preview, global region)...")
    try:
        response = client.evals.generate_loss_clusters(
            eval_result=result,
            metric=metric_name,
            config={"max_top_cluster_count": MAX_CLUSTERS},
        )
    except Exception as e:  # noqa: BLE001 — surface a clean message; preview API
        print(f"Loss clustering failed: {e}")
        print("This is a preview feature; confirm it's enabled for your project.")
        raise SystemExit(1) from e

    _print_clusters(response, metric_name)
    print(
        "\nEach pattern is a candidate instruction fix — address the biggest "
        "clusters first, then re-run simulate/evaluate to confirm the lift."
    )


if __name__ == "__main__":
    main()
