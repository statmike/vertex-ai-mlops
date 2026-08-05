"""Local judge — score the traces from run_local.py with an LLM judge.

Reads ``results/local_traces.json``, asks a Gemini judge model to rate each final
answer against its scenario reference (1-5), combines that with the deterministic
routing check, and writes both a machine-readable ``results/local_scores.json``
and a human-readable ``results/report.md``.

    uv run python optimize/judge_local.py

Routing correctness needs no model; only answer quality calls the judge.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from optimize.harness import load_scenarios, parse_judge_output, render_report  # noqa: E402
from optimize.harness.scoring import (  # noqa: E402
    JUDGE_SYSTEM_INSTRUCTION,
    build_judge_prompt,
    score_run,
)
from optimize.harness.trace import RunTrace  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
TRACES_PATH = RESULTS_DIR / "local_traces.json"
SCORES_PATH = RESULTS_DIR / "local_scores.json"
REPORT_PATH = RESULTS_DIR / "report.md"


def _judge_model():
    """A Gemini client + model id for judging. Judge with a strong model."""
    from google import genai

    from config import AGENT_MODEL, GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROJECT

    client = genai.Client(
        vertexai=True, project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION
    )
    return client, AGENT_MODEL


def _score_answer(client, model: str, prompt: str) -> tuple[int, str]:
    from google.genai import types

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=JUDGE_SYSTEM_INSTRUCTION,
            temperature=0.0,
        ),
    )
    return parse_judge_output(response.text or "")


def main() -> None:
    if not TRACES_PATH.exists():
        print(f"No traces at {TRACES_PATH}. Run: uv run python optimize/run_local.py")
        raise SystemExit(1)

    scenarios = {s.id: s for s in load_scenarios()}
    records = json.loads(TRACES_PATH.read_text())
    client, model = _judge_model()

    print(f"Judging {len(records)} runs with {model}...\n")
    scored = []
    for rec in records:
        scen = scenarios[rec["scenario_id"]]
        trace = RunTrace(**rec["trace"])

        if trace.error or not trace.final_answer:
            # No answer to judge — record the failure without calling the model.
            run = score_run(scen, trace, 1, trace.error or "no answer produced")
        else:
            score, reasoning = _score_answer(client, model, build_judge_prompt(scen, trace))
            run = score_run(scen, trace, score, reasoning)

        mark = "✅" if run.routing_correct else "❌"
        print(f"  [{run.scenario_id}] route {mark}  answer {run.answer_score}/5")
        scored.append(run)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    SCORES_PATH.write_text(json.dumps([asdict(r) for r in scored], indent=2) + "\n")
    report = render_report(scored, title="Local Evaluation Report (agent-building)")
    REPORT_PATH.write_text(report + "\n")

    print(f"\nWrote scores to {SCORES_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Wrote report to {REPORT_PATH.relative_to(PROJECT_ROOT)}\n")
    print(report)


if __name__ == "__main__":
    main()
