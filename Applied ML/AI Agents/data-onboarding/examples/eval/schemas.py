"""Pydantic models for the evaluation framework.

Structured outputs for the LLM judge and evaluation results.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# --- LLM Judge structured output ---


class AnswerScore(BaseModel):
    """Evaluation scores for a single answer."""

    groundedness: float = Field(
        description="0.0-1.0: Does the answer reference specific data values, "
        "table names, column names, or SQL results? Higher = more grounded in actual data."
    )
    accuracy: float = Field(
        description="0.0-1.0: Is the answer factually correct based on the data "
        "and question context? Higher = more accurate."
    )
    completeness: float = Field(
        description="0.0-1.0: Does the answer fully address all parts of the "
        "question? Higher = more complete."
    )


class JudgeVerdict(BaseModel):
    """LLM judge verdict comparing two answers to the same question."""

    winner: Literal["thinking", "fast", "tie"] = Field(
        description="Which answer is better overall: 'thinking', 'fast', or 'tie' if equivalent."
    )
    reasoning: str = Field(
        description="Brief explanation of why the winner was chosen (2-3 sentences)."
    )
    thinking_score: AnswerScore = Field(
        description="Scores for the THINKING mode answer."
    )
    fast_score: AnswerScore = Field(
        description="Scores for the FAST mode answer."
    )


# --- Evaluation result records ---


class TimingEntry(BaseModel):
    """A single step in the agent execution trace."""

    elapsed: float
    agent: str
    action: str = ""
    transfer_to: str = ""


class RunResult(BaseModel):
    """Result from running a single question with a specific thinking mode."""

    mode: Literal["thinking", "fast", "single"]
    total_time_s: float
    final_answer: str
    tool_response: str = ""
    reranker_summary: str = ""
    timing: list[TimingEntry] = Field(default_factory=list)
    event_count: int = 0
    error: str = ""


class EvalResult(BaseModel):
    """Full evaluation result for a single question."""

    id: str
    persona: str
    question: str
    thinking_result: RunResult | None = None
    fast_result: RunResult | None = None
    single_result: RunResult | None = None
    verdict: JudgeVerdict | None = None
    selected_mode: str = ""
    selected_answer: str = ""
    selected_time_s: float = 0.0
