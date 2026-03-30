"""Utility for calling Gemini with structured output to produce a ranked table list.

Supports a two-pass reranking strategy:
  Pass 1 (shortlist): compact summaries for ALL tables → top K candidates.
  Pass 2 (detail): full metadata for top K only → final ranked output.
"""

import json
import logging
import re

from google import genai
from google.genai import types

from agent_context.schemas import RerankerResponse, ShortlistResponse
from agent_orchestrator.config import GOOGLE_CLOUD_PROJECT, TOOL_MODEL, TOOL_MODEL_LOCATION

logger = logging.getLogger(__name__)


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

Return tables ranked by relevance (most relevant first). Only include tables
that are genuinely relevant — do not pad the list. Set confidence scores
honestly: 0.9+ for highly relevant, 0.5-0.8 for partially relevant,
below 0.5 for tangentially relevant.

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

SHORTLIST_SYSTEM_PROMPT = """\
You are a BigQuery table relevance screener. Given a user's question and a
compact catalog of available tables, identify which tables are potentially
relevant to answering the question.

For each relevant table, provide:
- table_id: the fully-qualified BigQuery reference (project.dataset.table)
- confidence: 0.0 to 1.0 (how likely this table helps answer the question)
- reason: a brief 1-sentence explanation

Include any table that might be relevant — it's better to include a
borderline table than to miss one. Sort by confidence descending.
"""


def _get_client() -> genai.Client:
    return genai.Client(
        vertexai=True,
        project=GOOGLE_CLOUD_PROJECT,
        location=TOOL_MODEL_LOCATION or "us-central1",
    )


def call_reranker(
    question: str,
    candidate_metadata: str,
    top_k: int = 10,
) -> RerankerResponse:
    """Call Gemini with structured output to rank candidate tables.

    Args:
        question: The user's original question.
        candidate_metadata: String containing table metadata (schemas,
            descriptions, profiles, etc.) from discovery.
        top_k: Maximum number of tables to return.

    Returns:
        RerankerResponse with ranked tables.
    """
    client = _get_client()

    user_prompt = f"""\
## User Question
{question}

## Discovery Method
table_documentation

## Top K
Return at most {top_k} tables.

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
            temperature=0.1,
        ),
    )

    result = RerankerResponse.model_validate(json.loads(response.text))

    # Normalize table IDs — the reranker sometimes picks up Dataplex path
    # format from the metadata (e.g., "projects.proj.datasets.ds.tables.tbl")
    for t in result.ranked_tables:
        t.table_id = _normalize_table_id(t.table_id)

    return result


def _shortlist_pass(
    question: str,
    catalog_summary: str,
    top_k: int = 10,
) -> ShortlistResponse:
    """Pass 1 — screen all tables using compact summaries.

    Args:
        question: The user's question.
        catalog_summary: Compact catalog text (table names, column names,
            1-line descriptions). Typically ~100 tokens per table.
        top_k: Maximum tables to shortlist.

    Returns:
        ShortlistResponse with candidate table IDs and confidence scores.
    """
    client = _get_client()

    user_prompt = f"""\
## User Question
{question}

## Return at most {top_k} tables.

## Available Tables
{catalog_summary}
"""

    response = client.models.generate_content(
        model=TOOL_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SHORTLIST_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ShortlistResponse.model_json_schema(),
            temperature=0.1,
        ),
    )

    return ShortlistResponse.model_validate(json.loads(response.text))


def _detail_pass(
    question: str,
    candidate_metadata: str,
    top_k: int = 10,
) -> RerankerResponse:
    """Pass 2 — rank shortlisted tables using full metadata.

    Args:
        question: The user's question.
        candidate_metadata: Full metadata for shortlisted tables only.
        top_k: Maximum tables to return.

    Returns:
        RerankerResponse with detailed rankings.
    """
    return call_reranker(question, candidate_metadata, top_k)


def _build_detail_metadata(
    shortlisted_ids: list[str],
    catalog_data: dict[str, dict],
) -> str:
    """Build a detailed metadata text block for shortlisted tables.

    Args:
        shortlisted_ids: Fully-qualified table IDs from the shortlist pass.
        catalog_data: The module-level _catalog_data dict.

    Returns:
        Formatted metadata string with full column details for each table.
    """
    parts = []
    for table_id in shortlisted_ids:
        entry = catalog_data.get(table_id)
        if not entry:
            continue

        parts.append(f"### Table: {entry['table_name']}")
        parts.append(f"  Full reference: `{entry['full_ref']}`")
        parts.append(f"  Dataset: {entry['dataset']}")

        if entry.get("description"):
            parts.append(f"  Description: {entry['description']}")

        columns = entry.get("columns", [])
        if columns:
            parts.append(f"  Columns ({len(columns)}):")
            for col in columns:
                desc = col.get("description", "")
                bq_type = col.get("bq_type", "STRING")
                desc_str = f": {desc[:150]}" if desc else ""
                parts.append(f"    - {col.get('name', '?')} ({bq_type}){desc_str}")

        relationships = entry.get("relationships", {})
        if relationships:
            parts.append("  Relationships:")
            for rel_type, rel_val in relationships.items():
                parts.append(f"    {rel_type}: {rel_val}")

        parts.append("")

    return "\n".join(parts)


def call_reranker_two_pass(
    question: str,
    catalog_summary: str,
    catalog_data: dict[str, dict],
    shortlist_k: int = 10,
    final_k: int = 10,
    min_shortlist: int = 3,
) -> RerankerResponse:
    """Two-pass reranking: shortlist all tables, then detail-rank the top ones.

    Args:
        question: The user's question.
        catalog_summary: Compact catalog text for the shortlist pass.
        catalog_data: Full catalog data dict for the detail pass.
        shortlist_k: Max tables to shortlist in pass 1.
        final_k: Max tables to return in final output.
        min_shortlist: Minimum tables to send to pass 2, even if confidence
            is low. Ensures we don't miss relevant tables.

    Returns:
        RerankerResponse with detailed rankings for the best tables.
    """
    # Pass 1: shortlist
    shortlist = _shortlist_pass(question, catalog_summary, top_k=shortlist_k)

    if not shortlist.shortlisted:
        return RerankerResponse(
            question=question,
            top_k=final_k,
            ranked_tables=[],
            notes="No tables matched in the shortlist pass.",
        )

    # Ensure minimum number of candidates
    candidates = shortlist.shortlisted
    if len(candidates) < min_shortlist:
        # Already fewer than minimum — use all of them
        shortlisted_ids = [c.table_id for c in candidates]
    else:
        # Take those above 0.5 confidence, but ensure at least min_shortlist
        above_threshold = [c for c in candidates if c.confidence > 0.5]
        if len(above_threshold) < min_shortlist:
            shortlisted_ids = [c.table_id for c in candidates[:min_shortlist]]
        else:
            shortlisted_ids = [c.table_id for c in above_threshold]

    logger.info(
        "Shortlist pass: %d/%d tables passed (from %d total catalog entries)",
        len(shortlisted_ids), len(candidates), len(catalog_data),
    )

    # Pass 2: detail rank with full metadata
    detail_metadata = _build_detail_metadata(shortlisted_ids, catalog_data)

    if not detail_metadata.strip():
        return RerankerResponse(
            question=question,
            top_k=final_k,
            ranked_tables=[],
            notes="Shortlisted tables not found in catalog data.",
        )

    return _detail_pass(question, detail_metadata, top_k=final_k)


def format_reranker_markdown(result: RerankerResponse) -> str:
    """Format a RerankerResponse as readable markdown for agent output.

    Args:
        result: The reranker result to format.
    """
    lines = ["**[Reranker Results]**", ""]

    if not result.ranked_tables:
        lines.append(result.notes or "No relevant tables found.")
        return "\n".join(lines)

    lines.append(
        f"Found **{len(result.ranked_tables)}** relevant table(s):"
    )
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
