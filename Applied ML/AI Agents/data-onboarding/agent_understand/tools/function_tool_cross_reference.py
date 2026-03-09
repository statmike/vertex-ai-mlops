import json
import logging

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error

from .util_gemini import generate_content

logger = logging.getLogger(__name__)


async def cross_reference(
    tool_context: tools.ToolContext,
) -> str:
    """
    Cross-reference data file schemas with context documents using Gemini.

    Takes the column names and types from analyzed schemas, and the content
    from context documents, then uses an LLM to generate meaningful column
    descriptions and identify relationships.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        Cross-reference results with column descriptions, or an error message.
    """
    try:
        schemas = tool_context.state.get("schemas_analyzed", {})
        contexts = tool_context.state.get("context_documents", {})

        if not schemas:
            return "No schemas to cross-reference. Run read_data_file and analyze_columns first."

        # Build prompt with schema info and context
        schema_summary = ""
        for path, schema in schemas.items():
            schema_summary += f"\n### File: {schema.get('filename', path)}\n"
            if "columns" in schema:
                for col in schema["columns"]:
                    schema_summary += (
                        f"  - {col['name']} ({col['dtype']}): "
                        f"{col['unique_count']} unique, "
                        f"{col['null_pct']}% null, "
                        f"samples: {col['sample_values'][:3]}\n"
                    )
            elif "column_analysis" in schema:
                for col_name, info in schema["column_analysis"].items():
                    schema_summary += (
                        f"  - {col_name} ({info['dtype']}, {info.get('category', '?')}): "
                        f"{info['unique_count']} unique, {info['null_pct']}% null\n"
                    )

        context_summary = ""
        for path, ctx in contexts.items():
            context_summary += (
                f"\n### Context: {ctx.get('filename', path)}\n"
                f"{ctx.get('content', '')[:5000]}\n"
            )

        if not context_summary:
            context_summary = "(No context documents available)"

        prompt = f"""You are analyzing data files being onboarded into BigQuery.
Given the data file schemas and any available context documents, provide:
1. A meaningful description for each column based on the context
2. Suggested BigQuery-friendly column names (snake_case)
3. Any relationships between columns or files
4. Potential data quality concerns

Return your analysis as JSON with this structure:
{{
  "files": {{
    "<filename>": {{
      "description": "table description",
      "columns": {{
        "<column_name>": {{
          "description": "what this column represents",
          "suggested_bq_name": "snake_case_name",
          "suggested_bq_type": "STRING|INT64|FLOAT64|TIMESTAMP|DATE|BOOL|JSON",
          "notes": "any concerns or observations"
        }}
      }}
    }}
  }},
  "relationships": ["description of any relationships found"],
  "quality_concerns": ["any data quality issues"]
}}

## Data File Schemas:
{schema_summary}

## Context Documents:
{context_summary}
"""

        response = await generate_content(
            contents=[prompt],
            tool_context=tool_context,
            tool_name="cross_reference",
        )

        response_text = response.text or ""

        # Parse JSON response
        # Strip markdown fences if present
        clean = response_text.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            clean = "\n".join(lines)

        try:
            insights = json.loads(clean)
        except json.JSONDecodeError:
            insights = {"raw_analysis": response_text}

        tool_context.state["context_insights"] = insights

        # Format readable summary
        result = "Cross-reference analysis complete.\n\n"
        if "files" in insights:
            for fname, finfo in insights["files"].items():
                result += f"### {fname}\n"
                result += f"Description: {finfo.get('description', 'N/A')}\n"
                if "columns" in finfo:
                    for cname, cinfo in finfo["columns"].items():
                        result += (
                            f"  {cname} → {cinfo.get('suggested_bq_name', cname)} "
                            f"({cinfo.get('suggested_bq_type', '?')}): "
                            f"{cinfo.get('description', 'N/A')}\n"
                        )
                result += "\n"

        if "relationships" in insights:
            result += "Relationships:\n"
            for r in insights["relationships"]:
                result += f"  - {r}\n"

        if "quality_concerns" in insights:
            result += "Quality concerns:\n"
            for q in insights["quality_concerns"]:
                result += f"  - {q}\n"

        return result

    except Exception as e:
        return log_tool_error("cross_reference", e)
