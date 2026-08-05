"""Format Conversational Analytics API stream responses into plain text.

Trimmed from the documented helper set
(https://cloud.google.com/gemini/docs/conversational-analytics-api/build-agent-sdk):
this agent surfaces the natural-language answer and small result tables, and
leaves chart rendering out to keep the demo lightweight.
"""

import pandas as pd


def handle_text_response(resp) -> str:
    """Join the text parts of a natural-language answer."""
    return "\n".join(getattr(resp, "parts", []))


def handle_data_response(resp) -> str:
    """Render a retrieved result set as a small text table (result branch only)."""
    if "result" not in resp:
        return ""
    fields = [field.name for field in resp.result.schema.fields]
    columns: dict[str, list] = {f: [] for f in fields}
    for row in resp.result.data:
        for f in fields:
            columns[f].append(row[f])
    return "Data retrieved:\n" + pd.DataFrame(columns).to_string(index=False)
