"""Local LLM-judge scoring: build the prompt, parse the verdict, aggregate.

The judge model is only called from ``judge_local.py``; everything here is pure so
it can be unit-tested offline. Two signals per scenario:

    routing_correct — did the router send it to the expected specialist?
                      (deterministic, computed here — no model needed)
    answer_score    — 1-5 quality of the final answer vs. the reference
                      (from the judge model's JSON verdict)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .scenarios import Scenario
from .trace import RunTrace

# Judge output must be JSON; we defensively strip prose/code fences around it.
_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)

JUDGE_SYSTEM_INSTRUCTION = (
    "You are a strict evaluator of a retail assistant's answers. Score how well "
    "the answer satisfies the reference, penalizing hallucination and vagueness. "
    "Respond with ONLY a JSON object, no prose."
)


def build_judge_prompt(scenario: Scenario, trace: RunTrace) -> str:
    """Prompt asking the judge to score one answer against its reference."""
    return (
        f"User question:\n{scenario.question}\n\n"
        f"Reference (what a correct answer covers):\n{scenario.reference}\n\n"
        f"Assistant's final answer:\n{trace.final_answer or '(no answer)'}\n\n"
        "Return JSON exactly like:\n"
        '{"score": <integer 1-5>, "reasoning": "<one sentence>"}\n'
        "5 = fully correct and grounded; 1 = wrong, empty, or hallucinated."
    )


def parse_judge_output(text: str) -> tuple[int, str]:
    """Extract (score, reasoning) from a judge response.

    Tolerates code fences and surrounding prose. Clamps score to 1-5. Falls back
    to (1, ...) on unparseable output so a judge glitch reads as a failure, never
    a crash or a silent pass.
    """
    match = _JSON_OBJECT.search(text or "")
    if not match:
        return 1, "unparseable judge output"
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return 1, "invalid judge JSON"

    raw = data.get("score", 1)
    try:
        score = int(raw)
    except (TypeError, ValueError):
        score = 1
    score = max(1, min(5, score))
    reasoning = str(data.get("reasoning", "")).strip() or "(no reasoning given)"
    return score, reasoning


@dataclass
class ScoredRun:
    """A scenario's full result: routing + answer quality."""

    scenario_id: str
    expected_agent: str
    routed_to: str | None
    answer_score: int  # 1-5
    reasoning: str
    error: str | None = None

    @property
    def routing_correct(self) -> bool:
        return self.routed_to == self.expected_agent

    @property
    def answer_pass(self) -> bool:
        # 4+ is the pass bar for a 1-5 quality scale.
        return self.error is None and self.answer_score >= 4


def score_run(scenario: Scenario, trace: RunTrace, score: int, reasoning: str) -> ScoredRun:
    """Combine a scenario, its trace, and the judge verdict into a ScoredRun."""
    return ScoredRun(
        scenario_id=scenario.id,
        expected_agent=scenario.expected_agent,
        routed_to=trace.routed_to,
        answer_score=score,
        reasoning=reasoning,
        error=trace.error,
    )


def aggregate(runs: list[ScoredRun]) -> dict:
    """Summary metrics across all scored runs.

    Rates are fractions in [0, 1]; ``0`` denominators yield ``0.0`` (an empty run
    is a failed run, not a divide-by-zero).
    """
    total = len(runs)
    if total == 0:
        return {
            "total": 0,
            "routing_accuracy": 0.0,
            "answer_pass_rate": 0.0,
            "avg_answer_score": 0.0,
        }

    routing_ok = sum(1 for r in runs if r.routing_correct)
    answer_ok = sum(1 for r in runs if r.answer_pass)
    score_sum = sum(r.answer_score for r in runs)
    return {
        "total": total,
        "routing_accuracy": routing_ok / total,
        "answer_pass_rate": answer_ok / total,
        "avg_answer_score": score_sum / total,
    }
