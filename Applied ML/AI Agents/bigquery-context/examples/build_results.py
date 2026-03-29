"""Build results markdown from collected question results.

Run from the bigquery-context project root:

    uv run python examples/build_results.py              # preview to stdout
    uv run python examples/build_results.py --write      # write examples/results.md

Reads examples/results/results.json and generates a markdown report with
cross-approach comparison tables, accuracy scores, and timing breakdowns.
"""

import argparse
import json
from pathlib import Path

RESULTS_FILE = Path(__file__).parent / "results" / "results.json"
OUTPUT_MD = Path(__file__).parent / "results.md"

APPROACHES = [
    ("bq_tools", "1: BQ Tools"),
    ("dataplex_search", "2: Search"),
    ("dataplex_context", "3: Context"),
    ("context_prefilter", "4: PreFilter"),
    ("semantic_context", "5: Semantic"),
]


def _short_table(full_id: str) -> str:
    parts = full_id.split(".")
    return f"{parts[-2]}.{parts[-1]}" if len(parts) >= 2 else full_id


def _very_short_table(full_id: str) -> str:
    return full_id.rsplit(".", 1)[-1]


def build_summary_table(results: list[dict]) -> str:
    """Build the top-level summary table across all questions."""
    lines = ["## Summary", ""]

    # Per-approach aggregates
    approach_keys = [k for k, _ in APPROACHES]
    approach_labels = [l for _, l in APPROACHES]

    header = f"| Metric | " + " | ".join(approach_labels) + " |"
    sep = "|---|" + "|".join("---" for _ in APPROACHES) + "|"
    lines.extend([header, sep])

    # Recall (found expected tables)
    recalls = []
    for key in approach_keys:
        scores = [
            r["approaches"][key]["recall"]
            for r in results
            if key in r.get("approaches", {})
        ]
        avg = sum(scores) / len(scores) if scores else 0
        recalls.append(f"{avg:.0%}")
    lines.append(f"| **Avg Recall** | " + " | ".join(recalls) + " |")

    # Precision
    precisions = []
    for key in approach_keys:
        scores = [
            r["approaches"][key]["precision"]
            for r in results
            if key in r.get("approaches", {})
        ]
        avg = sum(scores) / len(scores) if scores else 0
        precisions.append(f"{avg:.0%}")
    lines.append(f"| **Avg Precision** | " + " | ".join(precisions) + " |")

    # Perfect recall (found all expected tables)
    perfects = []
    for key in approach_keys:
        count = sum(
            1
            for r in results
            if key in r.get("approaches", {})
            and r["approaches"][key]["recall"] == 1.0
        )
        perfects.append(f"{count}/{len(results)}")
    lines.append(
        f"| **Perfect Recall** | " + " | ".join(perfects) + " |"
    )

    # Avg tables ranked
    avg_ranked = []
    for key in approach_keys:
        counts = [
            r["approaches"][key]["ranked_count"]
            for r in results
            if key in r.get("approaches", {})
        ]
        avg = sum(counts) / len(counts) if counts else 0
        avg_ranked.append(f"{avg:.1f}")
    lines.append(
        f"| **Avg Tables Ranked** | " + " | ".join(avg_ranked) + " |"
    )

    # Avg completion time (when approach finished, relative to question start)
    avg_times = []
    for key in approach_keys:
        times = [
            r["approaches"][key].get("completed_s", 0)
            for r in results
            if key in r.get("approaches", {})
        ]
        avg = sum(times) / len(times) if times else 0
        avg_times.append(f"{avg:.1f}s")
    lines.append(
        f"| **Avg Completed** | " + " | ".join(avg_times) + " |"
    )

    # Total time
    total_times = [r.get("total_time_s", 0) for r in results]
    avg_total = sum(total_times) / len(total_times) if total_times else 0
    lines.append("")
    lines.append(
        f"**Avg total time per question:** {avg_total:.1f}s "
        f"(orchestrator runs all 5 in parallel + compare agent)"
    )

    return "\n".join(lines)


def build_question_detail(result: dict) -> str:
    """Build the detail section for a single question."""
    lines = []
    qid = result["id"]
    question = result["question"]
    expected = result.get("expected_tables", [])
    category = result.get("category", "")
    total_time = result.get("total_time_s", 0)

    lines.append(f"### {qid}: {question}")
    lines.append("")
    lines.append(
        f"**Category:** {category} | "
        f"**Expected:** {', '.join(f'`{t}`' for t in expected)} | "
        f"**Total time:** {total_time}s"
    )
    lines.append("")

    if result.get("error"):
        lines.append(f"**Error:** {result['error']}")
        lines.append("")
        return "\n".join(lines)

    approaches = result.get("approaches", {})
    if not approaches:
        lines.append("*No approach results.*")
        return "\n".join(lines)

    # Cross-approach comparison table
    approach_keys = [k for k, _ in APPROACHES]
    approach_labels = [l for _, l in APPROACHES]

    # Collect all tables
    all_tables = set()
    for key in approach_keys:
        a = approaches.get(key, {})
        for t in a.get("nominated", []):
            all_tables.add(_short_table(t))
        for t in a.get("ranked_tables", []):
            all_tables.add(_short_table(t["table_id"]))

    # Sort: expected first, then by consensus
    expected_short = {_very_short_table(t) for t in expected}

    def sort_key(tid):
        is_expected = 1 if _very_short_table(tid) in expected_short else 0
        ranked_count = sum(
            1
            for key in approach_keys
            if any(
                _short_table(t["table_id"]) == tid
                for t in approaches.get(key, {}).get("ranked_tables", [])
            )
        )
        return (-is_expected, -ranked_count, tid)

    sorted_tables = sorted(all_tables, key=sort_key)

    header = "| Table | " + " | ".join(approach_labels) + " | Expected |"
    sep = "|---|" + "---|" * len(APPROACHES) + "---|"
    lines.extend([header, sep])

    for tid in sorted_tables:
        is_exp = "yes" if _very_short_table(tid) in expected_short else ""
        cols = []
        for key in approach_keys:
            a = approaches.get(key, {})
            nominated_short = {_short_table(t) for t in a.get("nominated", [])}
            ranked = next(
                (
                    t
                    for t in a.get("ranked_tables", [])
                    if _short_table(t["table_id"]) == tid
                ),
                None,
            )
            if ranked:
                cols.append(f"#{ranked['rank']} ({ranked['confidence']:.2f})")
            elif tid in nominated_short:
                cols.append("nominated")
            else:
                cols.append("—")
        row = f"| `{tid.split('.')[-1]}` | " + " | ".join(cols) + f" | {is_exp} |"
        lines.append(row)

    lines.append("")

    # Accuracy row
    accuracy_cols = []
    for key in approach_keys:
        a = approaches.get(key, {})
        recall = a.get("recall", 0)
        missed = a.get("missed", [])
        if recall == 1.0:
            accuracy_cols.append("all found")
        elif missed:
            accuracy_cols.append(f"missed: {', '.join(f'`{m}`' for m in missed)}")
        else:
            accuracy_cols.append(f"recall={recall:.0%}")

    lines.append(
        "| **Accuracy** | " + " | ".join(accuracy_cols) + " | |"
    )
    lines.append("")

    # Timing row
    timing_cols = []
    for key in approach_keys:
        a = approaches.get(key, {})
        completed = a.get("completed_s", 0)
        evts = a.get("event_count", 0)
        timing_cols.append(f"{completed}s ({evts} evts)")
    lines.append(
        "| **Timing** | " + " | ".join(timing_cols) + " | |"
    )
    lines.append("")

    return "\n".join(lines)


def build_results_markdown(results: list[dict]) -> str:
    """Build the full results markdown report."""
    lines = [
        "# BigQuery Context — Example Results",
        "",
        "Auto-generated by `run_questions.py` → `build_results.py`.",
        "",
        f"**Questions:** {len(results)} | "
        f"**Approaches per question:** 5 (parallel) + compare agent",
        "",
    ]

    # Summary table
    lines.append(build_summary_table(results))
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-question detail grouped by category
    lines.append("## Per-Question Detail")
    lines.append("")

    categories = [
        ("single-table", "Single-Table Questions"),
        ("multi-table-same-dataset", "Multi-Table (Same Dataset)"),
        ("multi-table-cross-dataset", "Multi-Table (Cross-Dataset)"),
    ]

    for cat_key, cat_label in categories:
        cat_results = [r for r in results if r.get("category") == cat_key]
        if not cat_results:
            continue

        lines.append(f"### {cat_label}")
        lines.append("")

        for result in cat_results:
            lines.append(build_question_detail(result))
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Build results markdown from collected results"
    )
    parser.add_argument(
        "--write", action="store_true", help="Write to results.md"
    )
    parser.add_argument(
        "--results", type=str, default=str(RESULTS_FILE),
        help="Input results JSON file",
    )
    parser.add_argument(
        "--output", type=str, default=str(OUTPUT_MD),
        help="Output markdown file",
    )
    args = parser.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        print(f"No results file found at {results_path}")
        print("Run: uv run python examples/run_questions.py")
        return

    with open(results_path) as f:
        results = json.load(f)

    completed = [r for r in results if r.get("approaches") or r.get("error")]
    print(f"Found {len(completed)}/{len(results)} completed results")

    report = build_results_markdown(completed)

    if not args.write:
        print()
        print(report)
        return

    output_path = Path(args.output)
    output_path.write_text(report + "\n")
    print(f"Written to {output_path}")


if __name__ == "__main__":
    main()
