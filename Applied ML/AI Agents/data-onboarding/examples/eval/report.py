"""Generate markdown reports from evaluation results.

Produces the Results section for example documentation, showing the
selected best answer with timing comparisons and judge verdicts.
"""

from __future__ import annotations

import re

from .schemas import EvalResult, RunResult

# Agent flow descriptions by persona
PERSONA_FLOWS = {
    "Data Analyst": "`agent_chat` → `agent_context` (callback: rerank) → `agent_convo` (conversational_chat)",
    "Data Engineer": "`agent_chat` → `agent_engineer` (meta_chat)",
    "Catalog Explorer": "`agent_chat` → `agent_catalog` (search_context / get_table_columns)",
}


def _format_timing_table(result: RunResult) -> str:
    """Build a markdown timing table from a run result."""
    if not result.timing:
        return ""

    lines = ["| Step | Agent | Action | Time |", "|------|-------|--------|------|"]
    step = 0

    for entry in result.timing:
        action = entry.action
        if action.startswith("call:"):
            step += 1
            action_text = f"`{action.replace('call: ', '')}`"
            if entry.transfer_to:
                action_text += f" → transfer to {entry.transfer_to}"
            lines.append(f"| {step} | {entry.agent} | {action_text} | {entry.elapsed}s |")

    lines.append(f"| | | **Total** | **{result.total_time_s}s** |")
    return "\n".join(lines)


def _format_mode_comparison(eval_result: EvalResult) -> str:
    """Build a mode comparison table for Data Analyst / Data Engineer questions."""
    if not eval_result.thinking_result or not eval_result.fast_result:
        return ""

    v = eval_result.verdict
    if not v:
        return ""

    ts = v.thinking_score
    fs = v.fast_score

    lines = [
        "| Metric | Thinking | Fast |",
        "|--------|----------|------|",
        f"| **Time** | {eval_result.thinking_result.total_time_s}s | {eval_result.fast_result.total_time_s}s |",
        f"| Groundedness | {ts.groundedness:.2f} | {fs.groundedness:.2f} |",
        f"| Accuracy | {ts.accuracy:.2f} | {fs.accuracy:.2f} |",
        f"| Completeness | {ts.completeness:.2f} | {fs.completeness:.2f} |",
        f"| **Selected** | {'**Winner**' if v.winner == 'thinking' else ''} | {'**Winner**' if v.winner == 'fast' else ''} |",
    ]

    if v.winner == "tie":
        lines[-1] = f"| **Selected** | **Tie** | **Tie** |"

    return "\n".join(lines)


def _extract_reranker_info(result: RunResult) -> str:
    """Extract a summary of what the reranker found."""
    summary = result.reranker_summary
    if not summary:
        return ""

    lines = []
    match = re.search(r"Found \*\*(\d+)\*\* relevant table\(s\)", summary)
    if match:
        count = match.group(1)
        tables = re.findall(
            r"`([^`]+)`\*\* — confidence: (\d+\.\d+)\n> (.+?)(?:\n|$)",
            summary,
        )
        if tables:
            parts = []
            for table_id, conf, _reason in tables:
                short_name = table_id.split(".")[-1] if "." in table_id else table_id
                parts.append(f"`{short_name}` ({conf})")
            lines.append(f"**Reranker:** {count} table(s) — {', '.join(parts)}")
        else:
            lines.append(f"**Reranker:** {count} table(s)")

    return "\n".join(lines)


def build_results_markdown(results: list[EvalResult]) -> str:
    """Build the full Results section markdown from evaluation results."""
    lines = ["## Results", ""]

    # Summary table
    lines.append("### Evaluation Summary")
    lines.append("")
    lines.append("Each Data Analyst and Data Engineer question was run with both "
                 "**Thinking** and **Fast** modes of the Conversational Analytics API. "
                 "An LLM judge (Gemini) evaluated both answers on groundedness, accuracy, "
                 "and completeness, then selected the better answer. Catalog Explorer "
                 "questions use AI.SEARCH (no thinking mode).")
    lines.append("")

    # Aggregate stats
    judged = [r for r in results if r.verdict]
    if judged:
        thinking_wins = sum(1 for r in judged if r.verdict.winner == "thinking")
        fast_wins = sum(1 for r in judged if r.verdict.winner == "fast")
        ties = sum(1 for r in judged if r.verdict.winner == "tie")

        avg_thinking_time = sum(r.thinking_result.total_time_s for r in judged if r.thinking_result) / len(judged)
        avg_fast_time = sum(r.fast_result.total_time_s for r in judged if r.fast_result) / len(judged)

        lines.append(f"| | Thinking | Fast | Tie |")
        lines.append(f"|---|----------|------|-----|")
        lines.append(f"| **Wins** | {thinking_wins} | {fast_wins} | {ties} |")
        lines.append(f"| **Avg time** | {avg_thinking_time:.1f}s | {avg_fast_time:.1f}s | |")
        lines.append("")

    # Group by persona
    personas: dict[str, list[EvalResult]] = {}
    for r in results:
        personas.setdefault(r.persona, []).append(r)

    for persona in ["Data Analyst", "Data Engineer", "Catalog Explorer"]:
        if persona not in personas:
            continue

        lines.append(f"### {persona}")
        lines.append("")

        for result in personas[persona]:
            qid = result.id
            question = result.question
            anchor = qid

            lines.append(f'<a id="{anchor}"></a>')
            q_num = qid.split("-")[-1].upper()
            lines.append(f"#### {q_num}: {question}")
            lines.append("")

            # Flow
            flow = PERSONA_FLOWS.get(persona, "")
            if flow:
                lines.append(f"**Flow:** {flow}")
                lines.append("")

            # Get the selected result for timing/answer
            selected = (
                result.single_result
                or (result.thinking_result if result.selected_mode == "thinking" else result.fast_result)
                or result.thinking_result
                or result.fast_result
            )

            if not selected:
                lines.append("*No result available.*")
                lines.append("")
                continue

            # Mode comparison (for judged questions)
            comparison = _format_mode_comparison(result)
            if comparison:
                lines.append(f"**Mode:** {result.selected_mode.upper()} selected")
                lines.append("")
                lines.append("<details>")
                lines.append("<summary>Mode comparison</summary>")
                lines.append("")
                lines.append(comparison)
                lines.append("")
                if result.verdict:
                    lines.append(f"> {result.verdict.reasoning}")
                lines.append("")
                lines.append("</details>")
                lines.append("")

            # Timing table
            timing_table = _format_timing_table(selected)
            if timing_table:
                lines.append(timing_table)
                lines.append("")

            # Reranker info (Data Analyst only)
            if persona == "Data Analyst":
                reranker = _extract_reranker_info(selected)
                if reranker:
                    lines.append(reranker)
                    lines.append("")

            # Answer
            lines.append("**Answer:**")
            lines.append("")
            answer = result.selected_answer or selected.final_answer
            if not answer:
                error = selected.error
                if error:
                    lines.append(f"**Error:** {error}")
                else:
                    lines.append("*No answer received.*")
            else:
                lines.append(answer)
            lines.append("")

    return "\n".join(lines)
