import io
import logging

import pandas as pd
from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_acquire.tools.util_gcs import download_bytes

logger = logging.getLogger(__name__)


async def analyze_columns(
    gcs_path: str,
    extension: str,
    tool_context: tools.ToolContext,
) -> str:
    """
    Perform detailed column analysis on a data file.

    Goes beyond basic schema inference to analyze value distributions,
    detect date/time patterns, identify categorical vs continuous columns,
    and flag potential data quality issues.

    Args:
        gcs_path: The GCS path of the data file.
        extension: The file extension.
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A detailed column analysis report, or an error message.
    """
    try:
        data = download_bytes(gcs_path)
        filename = gcs_path.split("/")[-1]

        # Read into DataFrame
        if extension in ("csv", "tsv"):
            sep = "\t" if extension == "tsv" else ","
            df = pd.read_csv(io.BytesIO(data), sep=sep, low_memory=False)
        elif extension in ("json", "jsonl"):
            import json as json_mod

            text = data.decode("utf-8", errors="replace")
            lines = text.strip().split("\n")
            if len(lines) > 1:
                records = [json_mod.loads(line) for line in lines if line.strip()]
                df = pd.DataFrame(records)
            else:
                parsed = json_mod.loads(text)
                df = pd.DataFrame(parsed if isinstance(parsed, list) else [parsed])
        elif extension in ("xlsx", "xls"):
            df = pd.read_excel(io.BytesIO(data))
        elif extension == "parquet":
            df = pd.read_parquet(io.BytesIO(data))
        else:
            return f"Cannot analyze columns for .{extension} files."

        result = f"Column analysis for {filename}:\n"
        result += f"  Total rows: {len(df)}, Total columns: {len(df.columns)}\n\n"

        analysis = {}
        for col in df.columns:
            series = df[col]

            # nunique / value_counts fail on columns with unhashable types
            # (e.g. lists from json_normalize). Fall back gracefully.
            try:
                nunique = int(series.nunique())
            except TypeError:
                nunique = -1
            unique_pct = round(float(nunique) / max(len(series), 1) * 100, 1) if nunique >= 0 else 0.0

            col_analysis = {
                "dtype": str(series.dtype),
                "null_count": int(series.isna().sum()),
                "null_pct": round(float(series.isna().mean()) * 100, 1),
                "unique_count": max(nunique, 0),
                "unique_pct": unique_pct,
            }

            # Detect column category
            if series.dtype in ("int64", "float64"):
                col_analysis["category"] = "numeric"
                non_null = series.dropna()
                if len(non_null) > 0:
                    col_analysis["min"] = float(non_null.min())
                    col_analysis["max"] = float(non_null.max())
                    col_analysis["mean"] = round(float(non_null.mean()), 4)
            elif series.dtype == "bool":
                col_analysis["category"] = "boolean"
            elif series.dtype == "object":
                if nunique < 0:
                    col_analysis["category"] = "complex"
                else:
                    sample = series.dropna().head(20)
                    try:
                        pd.to_datetime(sample)
                        col_analysis["category"] = "datetime_candidate"
                    except (ValueError, TypeError):
                        if unique_pct < 5:
                            col_analysis["category"] = "categorical"
                            try:
                                col_analysis["top_values"] = (
                                    series.value_counts().head(10).to_dict()
                                )
                            except TypeError:
                                pass
                        else:
                            col_analysis["category"] = "text"
            else:
                col_analysis["category"] = str(series.dtype)

            analysis[str(col)] = col_analysis

            result += f"  {col}:\n"
            result += f"    type: {col_analysis['dtype']} ({col_analysis.get('category', '?')})\n"
            result += f"    nulls: {col_analysis['null_pct']}%, unique: {col_analysis['unique_pct']}%\n"
            if "min" in col_analysis:
                result += f"    range: [{col_analysis['min']}, {col_analysis['max']}]\n"
            if "top_values" in col_analysis:
                top = list(col_analysis["top_values"].items())[:5]
                result += f"    top values: {dict(top)}\n"

        # Store analysis
        schemas = dict(tool_context.state.get("schemas_analyzed", {}))
        if gcs_path in schemas:
            schemas[gcs_path]["column_analysis"] = analysis
        else:
            schemas[gcs_path] = {"filename": filename, "column_analysis": analysis}
        tool_context.state["schemas_analyzed"] = schemas

        return result

    except Exception as e:
        return log_tool_error("analyze_columns", e)
