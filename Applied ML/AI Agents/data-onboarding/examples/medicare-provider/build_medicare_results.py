"""Build the Results section of readme.md from collected question results.

Run from the data-onboarding project root:

    uv run python examples/medicare-provider/build_medicare_results.py           # preview to stdout
    uv run python examples/medicare-provider/build_medicare_results.py --write   # update readme.md in place

Reads examples/medicare-provider/results/medicare_results.json and generates
markdown for each completed question. When --write is used, replaces everything
after the "## Results" header in examples/medicare-provider/readme.md.
"""

import argparse
import json
import re
from pathlib import Path

RESULTS_FILE = Path(__file__).parent / "results" / "medicare_results.json"
README_MD = Path(__file__).parent / "readme.md"

# Agent flow descriptions by persona
PERSONA_FLOWS = {
    "Data Analyst": "`agent_chat` → `agent_context` (callback: rerank) → `agent_convo` (conversational_chat)",
    "Data Engineer": "`agent_chat` → `agent_engineer` (meta_chat)",
    "Catalog Explorer": "`agent_chat` → `agent_catalog` (search_context / get_table_columns)",
}


def format_timing_table(result: dict) -> str:
    """Build a markdown timing table from the timing breakdown."""
    timing = result.get("timing", [])
    if not timing:
        return ""

    lines = ["| Step | Agent | Action | Time |", "|------|-------|--------|------|"]
    step = 0

    for entry in timing:
        action = entry.get("action", "")
        agent = entry.get("agent", "")
        elapsed = entry.get("elapsed", 0)

        if action.startswith("call:"):
            step += 1
            action_text = f"`{action.replace('call: ', '')}`"
            lines.append(f"| {step} | {agent} | {action_text} | {elapsed}s |")

    lines.append(f"| | | **Total** | **{result.get('total_time_s', 0)}s** |")
    return "\n".join(lines)


def format_answer(result: dict) -> str:
    """Format the final answer as markdown."""
    answer = result.get("final_answer", "")
    if not answer:
        error = result.get("error", "")
        if error:
            return f"**Error:** {error}"
        return "*No answer received.*"
    return answer


def build_results_markdown(results: list[dict]) -> str:
    """Build the full Results section markdown."""
    lines = ["## Results", ""]

    # Group by persona
    personas = {}
    for r in results:
        persona = r.get("persona", "Unknown")
        personas.setdefault(persona, []).append(r)

    for persona in ["Data Analyst", "Data Engineer", "Catalog Explorer"]:
        if persona not in personas:
            continue

        lines.append(f"### {persona}")
        lines.append("")

        for result in personas[persona]:
            qid = result["id"]
            question = result["question"]
            anchor = qid

            lines.append(f'<a id="{anchor}"></a>')
            lines.append(f"#### {qid.split('-')[-1].upper()}: {question}")
            lines.append("")

            # Flow
            flow = PERSONA_FLOWS.get(persona, "")
            if flow:
                lines.append(f"**Flow:** {flow}")
                lines.append("")

            # Timing table
            timing_table = format_timing_table(result)
            if timing_table:
                lines.append(timing_table)
                lines.append("")

            # Answer
            lines.append("**Answer:**")
            lines.append("")
            lines.append(format_answer(result))
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Build readme.md Results section")
    parser.add_argument("--write", action="store_true", help="Update readme.md in place")
    parser.add_argument("--results", type=str, default=str(RESULTS_FILE))
    args = parser.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        print(f"No results file found at {results_path}")
        print("Run: uv run python examples/medicare-provider/run_medicare_questions.py")
        return

    with open(results_path) as f:
        results = json.load(f)

    completed = [r for r in results if r.get("final_answer") or r.get("error")]
    print(f"Found {len(completed)}/{len(results)} completed results")

    results_md = build_results_markdown(completed)

    if not args.write:
        print()
        print(results_md)
        return

    # Update readme.md — replace everything after "## Results" or append
    readme_text = README_MD.read_text()

    marker = "\n## Results"
    marker_pos = readme_text.find(marker)

    if marker_pos >= 0:
        new_text = readme_text[:marker_pos] + "\n" + results_md + "\n"
    else:
        new_text = readme_text.rstrip() + "\n\n---\n\n" + results_md + "\n"

    README_MD.write_text(new_text)
    print(f"Updated {README_MD}")


if __name__ == "__main__":
    main()
