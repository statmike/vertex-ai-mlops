"""Build enriched Context for the Conversational Analytics API from reranker output.

Maps reranker structured data to the API's Context proto fields:
- Per-table schema overrides with column descriptions and types
- Schema relationships from join suggestions
- Glossary terms from domain-specific column descriptions
- Enhanced system instruction with per-table SQL guidance
"""

import logging

logger = logging.getLogger(__name__)


def build_enriched_context(
    reranker_result: dict,
    table_docs: list[dict] | None = None,
    system_instruction: str = "",
) -> dict:
    """Build an enriched Context dict from reranker output.

    The returned dict can be passed to ``ParseDict()`` to create a
    ``geminidataanalytics.Context`` proto.

    Args:
        reranker_result: The reranker response dict (from ``RerankerResponse.model_dump()``).
        table_docs: Optional list of table documentation dicts with
            ``full_table_id`` and ``columns`` keys.
        system_instruction: Base system instruction to enhance.

    Returns:
        Dict suitable for ``ParseDict`` into a Context proto, with keys:
        ``system_instruction``, ``datasource_references``, ``options``,
        ``schema_relationships``, ``glossary_terms``.
    """
    ranked_tables = reranker_result.get("ranked_tables", [])
    if not ranked_tables:
        return {}

    # Build table references with schema overrides
    table_references = []
    sql_hints_parts = []
    schema_relationships = []
    glossary_terms = set()

    for rt in ranked_tables:
        table_id = rt.get("table_id", "")
        parts = table_id.split(".")
        if len(parts) != 3:
            continue

        project_id, dataset_id, table_name = parts

        # Build schema fields from key_columns
        fields = []
        for col in rt.get("key_columns", []):
            field = {
                "name": col.get("name", ""),
                "type": col.get("data_type", "STRING"),
            }
            desc = col.get("description", "")
            if desc:
                field["description"] = desc
                # Extract potential glossary terms from descriptions
                # (short, capitalized phrases that look like domain terms)
                _extract_glossary_terms(desc, glossary_terms)
            fields.append(field)

        table_ref = {
            "project_id": project_id,
            "dataset_id": dataset_id,
            "table_id": table_name,
        }

        # Add schema override if we have column info
        if fields:
            table_ref["schema"] = {"fields": fields}
            table_desc = rt.get("table_description", "")
            if table_desc:
                table_ref["schema"]["description"] = table_desc

        table_references.append(table_ref)

        # Collect SQL hints
        hints = rt.get("sql_hints", "")
        if hints:
            sql_hints_parts.append(f"For `{table_id}`: {hints}")

        # Build schema relationships from join suggestions
        for js in rt.get("join_suggestions", []):
            target = js.get("target_table", "")
            target_parts = target.split(".")
            if len(target_parts) != 3:
                continue

            rel = {
                "source_table": {
                    "project_id": project_id,
                    "dataset_id": dataset_id,
                    "table_id": table_name,
                },
                "target_table": {
                    "project_id": target_parts[0],
                    "dataset_id": target_parts[1],
                    "table_id": target_parts[2],
                },
                "join_keys": js.get("join_keys", []),
                "relationship": js.get("relationship", ""),
            }
            schema_relationships.append(rel)

    # Build enhanced system instruction
    enhanced_instruction = system_instruction or (
        "Help users explore, analyze, and give detailed reports "
        "for the provided data sources."
    )
    if sql_hints_parts:
        enhanced_instruction += "\n\nSQL Guidance from context analysis:\n"
        enhanced_instruction += "\n".join(f"- {h}" for h in sql_hints_parts)

    # Build the Context dict
    context = {
        "system_instruction": enhanced_instruction,
        "datasource_references": {
            "bq": {"table_references": table_references},
        },
        "options": {"analysis": {"python": {"enabled": True}}},
    }

    if schema_relationships:
        context["schema_relationships"] = schema_relationships

    if glossary_terms:
        context["glossary_terms"] = [
            {"term": term} for term in sorted(glossary_terms)
        ]

    return context


def _extract_glossary_terms(description: str, terms: set) -> None:
    """Extract potential domain-specific glossary terms from a description.

    Looks for short capitalized phrases or acronyms that might be
    domain-specific terminology worth adding to the glossary.

    Args:
        description: Column or table description text.
        terms: Set to add discovered terms to (modified in-place).
    """
    import re

    # Find all-caps acronyms (2-6 chars) like VIX, FIPS, CBOE
    for match in re.finditer(r'\b([A-Z]{2,6})\b', description):
        term = match.group(1)
        # Skip common English words that happen to be caps
        if term not in {"THE", "AND", "FOR", "NOT", "BUT", "ALL", "ANY", "ARE", "WAS", "HAS"}:
            terms.add(term)
