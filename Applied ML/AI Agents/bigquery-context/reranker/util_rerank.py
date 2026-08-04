"""Utility for calling Gemini with structured output to produce a ranked table list."""

import json
import re

from google import genai
from google.genai import types

from config import GOOGLE_CLOUD_PROJECT, TOOL_MODEL, TOOL_MODEL_LOCATION
from schemas import RerankerResponse


def _normalize_table_id(raw_id: str) -> str:
    """Normalize a table ID to project.dataset.table format.

    Handles variants the reranker sometimes produces from Dataplex paths:
      - "project.dataset.table" → keep as-is
      - "projects.project.datasets.dataset.tables.table" → strip path components
      - "projects.project.datasets.dataset.table" → strip partial path
    """
    return re.sub(
        r"^projects[./]([^./]+)[./](?:datasets[./])?([^./]+)[./](?:tables[./])?([^./]+)$",
        r"\1.\2.\3",
        raw_id,
    )


RERANKER_SYSTEM_PROMPT = """\
You are a BigQuery table relevance ranker. Given a user's question and metadata
about candidate BigQuery tables, you rank the tables by relevance.

For each table, evaluate:
1. How directly the table's columns and description answer the question
2. Which specific columns would be used in a SQL query to answer it
3. Whether joins to other candidate tables would help
4. What SQL patterns (WHERE filters, GROUP BY, aggregations) would be needed

Some candidate metadata comes from the Knowledge Catalog context capsule and may
include richer signals — use them when present:
- `frequent_joins` (or join hints): real observed join relationships. Prefer
  these when proposing join_suggestions rather than guessing join keys.
- glossary terms / `related_terms` / `business_descriptions`: business meaning of
  columns. Use them to disambiguate columns and improve reasoning.
- `guidelines`: authored NL→SQL guidance for the table. Fold applicable
  guidance directly into sql_hints.

Return ALL tables with confidence >= 0.5, ranked by relevance (most relevant
first). Do not omit borderline tables — include anything that could
plausibly help answer the question, even indirectly (e.g., a population
table needed for a per-capita calculation). Set confidence scores honestly:
0.9+ for highly relevant, 0.5-0.8 for partially relevant. Only exclude
tables below 0.5 confidence.

For table_id, always use the standard BigQuery fully-qualified format:
`project.dataset.table` (e.g., `my-project.my_dataset.my_table`).
Extract the project, dataset, and table name from whatever identifier
format appears in the metadata.

For key_columns, identify the most important columns for answering the question
and flag which are useful for filtering vs aggregation.

For sql_hints, provide concrete SQL guidance like:
- "Filter on weather_date for time-based questions"
- "GROUP BY subscriber_type to compare rider categories"
- "JOIN to stations table on start_station_id = station_id"
"""


_genai_client = None


# ---------------------------------------------------------------------------
# Reranker token-usage accounting (exact, for the benchmark cost metric).
#
# ``call_reranker`` invokes Gemini directly (not as an ADK tool), so its
# ``usage_metadata`` never reaches the ADK event stream. We record it here in a
# process-local accumulator the benchmark harness resets before each isolated
# approach-run and reads afterwards. Runs are sequential (one approach at a
# time), so a plain module global is sufficient and exact.
# ---------------------------------------------------------------------------
_USAGE_LOG: list[dict] = []


def reset_usage() -> None:
    """Clear the reranker usage accumulator (call before an isolated run)."""
    _USAGE_LOG.clear()


def get_usage() -> dict:
    """Return aggregated reranker token usage since the last ``reset_usage``.

    Returns a dict with ``prompt_tokens``, ``output_tokens``, ``total_tokens``,
    and ``calls`` (number of reranker Gemini invocations).
    """
    return {
        "prompt_tokens": sum(u["prompt_tokens"] for u in _USAGE_LOG),
        "output_tokens": sum(u["output_tokens"] for u in _USAGE_LOG),
        "total_tokens": sum(u["total_tokens"] for u in _USAGE_LOG),
        "calls": len(_USAGE_LOG),
    }


def _record_usage(response) -> None:
    """Append one Gemini response's token usage to the accumulator."""
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return
    _USAGE_LOG.append(
        {
            "prompt_tokens": getattr(usage, "prompt_token_count", 0) or 0,
            "output_tokens": getattr(usage, "candidates_token_count", 0) or 0,
            "total_tokens": getattr(usage, "total_token_count", 0) or 0,
        }
    )


def _get_client() -> genai.Client:
    """Return a cached genai Client."""
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(
            vertexai=True,
            project=GOOGLE_CLOUD_PROJECT,
            location=TOOL_MODEL_LOCATION or "us-central1",
        )
    return _genai_client


def call_reranker(
    question: str,
    candidate_metadata: str,
    discovery_method: str,
    top_k: int,
) -> RerankerResponse:
    """Call Gemini with structured output to rank candidate tables.

    Args:
        question: The user's original question.
        candidate_metadata: String containing table metadata (schemas,
            descriptions, profiles, etc.) from the discovery approach.
        discovery_method: Which approach produced the candidates
            ("bq_tools", "kc_search", "kc_context", "context_prefilter",
            "semantic_context").
        top_k: Maximum number of tables to return.

    Returns:
        RerankerResponse with ranked tables.
    """
    client = _get_client()

    user_prompt = f"""\
## User Question
{question}

## Discovery Method
{discovery_method}

## Ranking Instructions
Return ALL tables with confidence >= 0.5 (up to {top_k} maximum).
Do not drop borderline tables — if a table could contribute to answering
the question (even as a supporting join), include it.

## Candidate Table Metadata
{candidate_metadata}
"""

    response = client.models.generate_content(
        model=TOOL_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=RERANKER_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=RerankerResponse.model_json_schema(),
            temperature=0.0,
        ),
    )

    _record_usage(response)

    result = RerankerResponse.model_validate(json.loads(response.text))

    # Normalize table IDs — the reranker sometimes picks up Dataplex path
    # format from the metadata (e.g., "projects.proj.datasets.ds.tables.tbl")
    for t in result.ranked_tables:
        t.table_id = _normalize_table_id(t.table_id)

    return result


def format_reranker_markdown(result: RerankerResponse, label: str) -> str:
    """Format a RerankerResponse as readable markdown for agent output.

    Args:
        result: The reranker result to format.
        label: Approach label, e.g. "Approach 2: Knowledge Catalog Search".
    """
    lines = [f"**[{label}]**", ""]

    if not result.ranked_tables:
        lines.append(result.notes or "No relevant tables found.")
        return "\n".join(lines)

    lines.append(f"Found **{len(result.ranked_tables)}** relevant table(s):")
    lines.append("")

    for t in result.ranked_tables:
        lines.append(f"**#{t.rank}. `{t.table_id}`** — confidence: {t.confidence:.2f}")
        lines.append(f"> {t.reasoning}")
        if t.key_columns:
            col_strs = []
            for c in t.key_columns:
                tags = []
                if c.useful_for_filtering:
                    tags.append("filter")
                if c.useful_for_aggregation:
                    tags.append("aggregate")
                if c.is_key:
                    tags.append("key")
                tag_str = f" ({', '.join(tags)})" if tags else ""
                col_strs.append(f"`{c.name}` {c.data_type}{tag_str}")
            lines.append(f"- **Key columns:** {', '.join(col_strs)}")
        if t.sql_hints:
            lines.append(f"- **SQL hints:** {t.sql_hints}")
        if t.join_suggestions:
            for j in t.join_suggestions:
                lines.append(
                    f"- **Join:** → `{j.target_table}` "
                    f"ON {', '.join(j.join_keys)} ({j.relationship})"
                )
        lines.append("")

    if result.notes:
        lines.append(f"**Notes:** {result.notes}")

    return "\n".join(lines)
