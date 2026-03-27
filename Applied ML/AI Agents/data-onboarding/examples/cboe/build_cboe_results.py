"""Build the Results section of cboe.md from collected question results.

Run from the data-onboarding project root:

    uv run python examples/cboe/build_cboe_results.py           # preview to stdout
    uv run python examples/cboe/build_cboe_results.py --write    # update cboe.md in place

Reads examples/cboe/results/cboe_results.json and generates markdown for each
completed question. When --write is used, replaces everything after the
"## Results" header in examples/cboe/cboe.md.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Ensure the project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

RESULTS_FILE = Path(__file__).parent / "results" / "cboe_results.json"
CBOE_MD = Path(__file__).parent / "cboe.md"

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
    prev_elapsed = 0.0

    for entry in timing:
        action = entry.get("action", "")
        agent = entry.get("agent", "")
        elapsed = entry.get("elapsed", 0)
        transfer = entry.get("transfer_to", "")

        if action.startswith("call:"):
            step += 1
            action_text = f"`{action.replace('call: ', '')}`"
            if transfer:
                action_text += f" → transfer to {transfer}"
            lines.append(f"| {step} | {agent} | {action_text} | {elapsed}s |")
        elif action.startswith("text:") and not action.startswith("text: "):
            # Final text output — skip internal
            pass

    lines.append(f"| | | **Total** | **{result.get('total_time_s', 0)}s** |")
    return "\n".join(lines)


def extract_reranker_info(result: dict) -> str:
    """Extract a summary of what the reranker found."""
    summary = result.get("reranker_summary", "")
    if not summary:
        return ""

    # Parse the reranker markdown to get table count and names
    lines = []
    # Look for "Found **N** relevant table(s)"
    match = re.search(r"Found \*\*(\d+)\*\* relevant table\(s\)", summary)
    if match:
        count = match.group(1)
        # Extract table IDs and confidence scores
        tables = re.findall(
            r"`([^`]+)`\*\* — confidence: (\d+\.\d+)\n> (.+?)(?:\n|$)",
            summary,
        )
        if tables:
            parts = []
            for table_id, conf, reason in tables:
                short_name = table_id.split(".")[-1] if "." in table_id else table_id
                parts.append(f"`{short_name}` ({conf})")
            lines.append(f"**Reranker result:** {count} table(s) — {', '.join(parts)}")
            # Add first table's reasoning
            if tables[0][2]:
                lines.append(f'> "{tables[0][2]}"')
        else:
            lines.append(f"**Reranker result:** {count} table(s)")

    return "\n".join(lines)


def format_answer(result: dict) -> str:
    """Format the final answer as markdown."""
    answer = result.get("final_answer", "")
    if not answer:
        error = result.get("error", "")
        if error:
            return f"**Error:** {error}"
        return "*No answer received.*"

    # Check if answer contains a data table (lines with aligned columns)
    has_data_table = bool(re.search(r"^\s+\S+\s{2,}\S+", answer, re.MULTILINE))

    if has_data_table:
        # Wrap data sections in code blocks for readability
        parts = answer.split("\n\n")
        formatted = []
        in_data = False
        for part in parts:
            stripped = part.strip()
            if stripped.startswith("## Data retrieved") or stripped.startswith("## SQL generated"):
                in_data = True
                formatted.append(stripped)
                continue
            if in_data and re.search(r"^\s+\S+\s{2,}\S+", part, re.MULTILINE):
                formatted.append(f"```\n{part}\n```")
                in_data = False
            elif stripped.startswith("### ") or stripped.startswith("## "):
                in_data = False
                formatted.append(stripped)
            else:
                in_data = False
                formatted.append(part)
        return "\n\n".join(formatted)

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

            # Reranker info (Data Analyst only)
            if persona == "Data Analyst":
                reranker = extract_reranker_info(result)
                if reranker:
                    lines.append(reranker)
                    lines.append("")

            # Answer
            lines.append("**Answer:**")
            lines.append("")
            lines.append(format_answer(result))
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Build cboe.md Results section")
    parser.add_argument("--write", action="store_true", help="Update cboe.md in place")
    parser.add_argument("--results", type=str, default=str(RESULTS_FILE))
    args = parser.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        print(f"No results file found at {results_path}")
        print("Run: uv run python examples/cboe/run_cboe_questions.py")
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

    # Update cboe.md — replace everything after "## Results" or append
    cboe_text = CBOE_MD.read_text()

    # Find "## Results" marker
    marker = "\n## Results"
    marker_pos = cboe_text.find(marker)

    if marker_pos >= 0:
        # Replace from marker to end
        new_text = cboe_text[:marker_pos] + "\n" + results_md + "\n"
    else:
        # Append after a separator
        new_text = cboe_text.rstrip() + "\n\n---\n\n" + results_md + "\n"

    CBOE_MD.write_text(new_text)
    print(f"Updated {CBOE_MD}")


if __name__ == "__main__":
    main()
