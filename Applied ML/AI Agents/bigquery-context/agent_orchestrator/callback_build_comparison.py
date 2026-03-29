"""Callback: assemble discovery results from state for the compare agent.

Runs as ``before_agent_callback`` on the compare agent. Reads all
nomination and reranker result state keys from the five approaches,
formats a structured summary with a cross-approach comparison table,
and stores it in ``state["discovery_summary"]``. Returns ``None`` so
the LLM still runs and reasons over the injected data.
"""

import json

from google.adk.agents.callback_context import CallbackContext

from reranker.util_rerank import _normalize_table_id
from schemas import RerankerResponse

APPROACHES = [
    ("bq_tools", "1: BQ Tools"),
    ("dataplex_search", "2: Search"),
    ("dataplex_context", "3: Context"),
    ("context_prefilter", "4: Pre-Filter"),
    ("semantic_context", "5: Semantic"),
]


def _format_summary(state: dict) -> str:
    """Build a structured comparison summary from session state."""
    sections = []

    # --- Parse all reranker results ---
    parsed_results: dict[str, RerankerResponse | None] = {}
    for key, _ in APPROACHES:
        raw = state.get(f"reranker_result_{key}", "")
        if raw:
            try:
                parsed_results[key] = RerankerResponse.model_validate(json.loads(raw))
            except (json.JSONDecodeError, Exception):
                parsed_results[key] = None
        else:
            parsed_results[key] = None

    # --- Build cross-approach comparison table ---
    # Collect all unique tables from nominations and reranker results
    all_tables: set[str] = set()
    nominations_by_approach: dict[str, set[str]] = {}
    ranks_by_approach: dict[str, dict[str, tuple[int, float]]] = {}  # key → {table: (rank, conf)}

    for key, _ in APPROACHES:
        # Nominations
        nominated = state.get(f"nominated_tables_{key}", [])
        nominations_by_approach[key] = {_normalize_table_id(t) for t in nominated}
        all_tables.update(nominations_by_approach[key])

        # Reranker results
        ranks_by_approach[key] = {}
        result = parsed_results.get(key)
        if result:
            for t in result.ranked_tables:
                norm_id = _normalize_table_id(t.table_id)
                ranks_by_approach[key][norm_id] = (t.rank, t.confidence)
                all_tables.add(norm_id)

    # Sort tables by how many approaches ranked them (most consensus first)
    def sort_key(table_id):
        ranked_count = sum(
            1 for key, _ in APPROACHES if table_id in ranks_by_approach[key]
        )
        best_conf = max(
            (ranks_by_approach[key].get(table_id, (99, 0.0))[1] for key, _ in APPROACHES),
            default=0.0,
        )
        return (-ranked_count, -best_conf, table_id)

    sorted_tables = sorted(all_tables, key=sort_key)

    # Shorten table names for readability (drop project prefix)
    def short_name(full_id: str) -> str:
        parts = full_id.split(".")
        if len(parts) == 3:
            return f"{parts[1]}.{parts[2]}"
        return full_id

    # Build the cross-approach table
    sections.append("## Cross-Approach Comparison")
    sections.append("")
    header = "| Table |"
    sep = "|---|"
    for _, label in APPROACHES:
        header += f" {label} |"
        sep += "---|"
    sections.append(header)
    sections.append(sep)

    for table_id in sorted_tables:
        row = f"| `{short_name(table_id)}` |"
        for key, _ in APPROACHES:
            nominated = table_id in nominations_by_approach[key]
            ranked = ranks_by_approach[key].get(table_id)
            if ranked:
                rank, conf = ranked
                row += f" #{rank} ({conf:.2f}) |"
            elif nominated:
                row += " nominated |"
            else:
                row += " — |"
        sections.append(row)

    sections.append("")
    sections.append(
        "_Cells show reranker rank and confidence if ranked, "
        "'nominated' if sent to reranker but not ranked, "
        "or '—' if not discovered by that approach._"
    )
    sections.append("")

    # --- Per-approach reranker detail ---
    sections.append("## Per-Approach Reranker Detail")
    sections.append("")

    for key, label in APPROACHES:
        result = parsed_results.get(key)
        if not result:
            sections.append(f"### Approach {label}")
            sections.append("_(no reranker result)_")
            sections.append("")
            continue

        sections.append(f"### Approach {label}")

        if not result.ranked_tables:
            sections.append(f"No relevant tables found. Notes: {result.notes}")
            sections.append("")
            continue

        sections.append(
            "| Rank | Table | Confidence | Key Columns | SQL Hints |"
        )
        sections.append("|---|---|---|---|---|")
        for t in result.ranked_tables:
            norm_id = _normalize_table_id(t.table_id)
            cols = ", ".join(
                f"`{c.name}` ({c.data_type})" for c in t.key_columns
            ) if t.key_columns else ""
            sections.append(
                f"| {t.rank} | `{short_name(norm_id)}` | {t.confidence:.2f} "
                f"| {cols} | {t.sql_hints} |"
            )

        if result.notes:
            sections.append(f"\n**Notes:** {result.notes}")
        sections.append("")

    return "\n".join(sections)


async def build_comparison(callback_context: CallbackContext):
    """Assemble discovery results into state for LLM comparison.

    Reads all nomination and reranker state keys, formats a structured
    summary with cross-approach comparison table, stores it in
    ``state["discovery_summary"]``, and returns ``None`` so the LLM
    runs with the data injected via ``{discovery_summary}`` in the
    instruction.
    """
    summary = _format_summary(callback_context.state)
    callback_context.state["discovery_summary"] = summary
    return None
