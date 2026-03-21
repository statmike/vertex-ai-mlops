"""Multi-format file readers for data and context files."""

import io
import json
import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)

# Maximum rows to read for schema inference
MAX_SAMPLE_ROWS = 500


def _looks_headerless(df: pd.DataFrame) -> bool:
    """Heuristic: check if >50% of column names look like data values, not headers.

    Flags columns whose names parse as numbers, dates, or are very long strings
    (likely data values promoted to column names when the file has no header row).
    """
    if len(df.columns) == 0:
        return False
    data_like = 0
    for col_name in df.columns:
        s = str(col_name).strip()
        # Numeric column name
        try:
            float(s)
            data_like += 1
            continue
        except ValueError:
            pass
        # Date-like column name
        try:
            pd.to_datetime(s)
            data_like += 1
            continue
        except (ValueError, TypeError):
            pass
        # Very long string (>40 chars) — likely a data value
        if len(s) > 40:
            data_like += 1
    return data_like / len(df.columns) > 0.5


def read_csv(data: bytes, filename: str = "") -> dict:
    """Read CSV/TSV file and return schema + sample data."""
    sep = "\t" if filename.endswith((".tsv", ".TSV")) else ","
    df = pd.read_csv(io.BytesIO(data), sep=sep, nrows=MAX_SAMPLE_ROWS, low_memory=False)

    if _looks_headerless(df):
        # Save the first row (was misinterpreted as header) then re-read without header
        original_first_row = list(df.columns)
        df = pd.read_csv(
            io.BytesIO(data), sep=sep, header=None,
            nrows=MAX_SAMPLE_ROWS, low_memory=False,
        )
        df.columns = [f"col_{i}" for i in range(len(df.columns))]
        summary = _dataframe_to_summary(df, filename)
        summary["headerless"] = True
        summary["original_first_row"] = [str(v) for v in original_first_row]
        return summary

    return _dataframe_to_summary(df, filename)


def read_json(data: bytes, filename: str = "") -> dict:
    """Read JSON/JSONL file and return schema + sample data."""
    text = data.decode("utf-8", errors="replace")

    # Try JSONL first (one JSON object per line)
    lines = text.strip().split("\n")
    if len(lines) > 1:
        try:
            records = [json.loads(line) for line in lines[:MAX_SAMPLE_ROWS] if line.strip()]
            df = pd.DataFrame(records)
            return _dataframe_to_summary(df, filename)
        except json.JSONDecodeError:
            pass

    # Try as a single JSON document
    parsed = json.loads(text)
    if isinstance(parsed, list):
        df = pd.DataFrame(parsed[:MAX_SAMPLE_ROWS])
        return _dataframe_to_summary(df, filename)
    elif isinstance(parsed, dict):
        # Single object or nested — try to normalize
        df = pd.json_normalize(parsed)
        return _dataframe_to_summary(df, filename)

    return {"filename": filename, "error": "Unsupported JSON structure", "columns": [], "rows": 0}


def read_excel(data: bytes, filename: str = "") -> dict:
    """Read Excel file and return schema + sample data.

    Multi-sheet workbooks return ``type="multi_sheet"`` with per-sheet summaries.
    Single-sheet workbooks (or workbooks with only one non-empty sheet) return
    the same tabular summary as before.
    """
    xls = pd.ExcelFile(io.BytesIO(data))
    sheet_names = xls.sheet_names

    if len(sheet_names) <= 1:
        df = pd.read_excel(xls, sheet_name=0, nrows=MAX_SAMPLE_ROWS)
        return _dataframe_to_summary(df, filename)

    # Multiple sheets — check which ones have data
    sheets_with_data = {}
    for name in sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=name, nrows=MAX_SAMPLE_ROWS)
            if not df.empty:
                sheets_with_data[name] = df
        except Exception:
            continue

    # If only one sheet has data, treat as single-sheet
    if len(sheets_with_data) <= 1:
        name, df = next(iter(sheets_with_data.items())) if sheets_with_data else (sheet_names[0], pd.DataFrame())
        return _dataframe_to_summary(df, filename)

    # Multiple non-empty sheets → return multi_sheet summary
    sheet_summaries = {}
    for name, df in sheets_with_data.items():
        sheet_summaries[name] = _dataframe_to_summary(df, f"{filename}#{name}")

    return {
        "filename": filename,
        "type": "multi_sheet",
        "sheet_names": list(sheets_with_data.keys()),
        "sheets": sheet_summaries,
    }


def read_xml(data: bytes, filename: str = "") -> dict:
    """Read XML file and return schema + sample data.

    Tries progressively specific xpath patterns if the default produces poor
    results (>80% null rate).
    """
    _XPATH_ATTEMPTS = [None, ".//row", ".//record", ".//item", "./*"]

    best_df = None
    best_null_rate = 1.0

    for xpath in _XPATH_ATTEMPTS:
        try:
            kwargs = {"parser": "etree"}
            if xpath is not None:
                kwargs["xpath"] = xpath
            df = pd.read_xml(io.BytesIO(data), **kwargs)
            if df.empty:
                continue
            null_rate = df.isnull().mean().mean()
            if null_rate < best_null_rate:
                best_df = df
                best_null_rate = null_rate
            if null_rate <= 0.8:
                break  # good enough
        except Exception:
            continue

    if best_df is None or best_df.empty:
        return {"filename": filename, "error": "Could not parse XML structure", "columns": [], "rows": 0}

    if len(best_df) > MAX_SAMPLE_ROWS:
        summary = _dataframe_to_summary(best_df.head(MAX_SAMPLE_ROWS), filename)
        summary["total_rows"] = len(best_df)
        return summary
    return _dataframe_to_summary(best_df, filename)


def read_parquet(data: bytes, filename: str = "") -> dict:
    """Read Parquet file and return schema + sample data."""
    import pyarrow.parquet as pq

    buf = io.BytesIO(data)
    pf = pq.ParquetFile(buf)
    total_rows = pf.metadata.num_rows
    buf.seek(0)
    df = pd.read_parquet(buf)
    if len(df) > MAX_SAMPLE_ROWS:
        df = df.head(MAX_SAMPLE_ROWS)
    summary = _dataframe_to_summary(df, filename)
    summary["total_rows"] = total_rows
    return summary


def read_text(data: bytes, filename: str = "") -> dict:
    """Read a text/markdown/context file and return its content."""
    text = data.decode("utf-8", errors="replace")
    return {
        "filename": filename,
        "type": "text",
        "content": text[:50000],  # Cap at 50K chars
        "size_chars": len(text),
        "line_count": text.count("\n") + 1,
    }


def read_file(data: bytes, filename: str, extension: str) -> dict:
    """Route to the appropriate reader based on file extension."""
    readers = {
        "csv": read_csv,
        "tsv": read_csv,
        "json": read_json,
        "jsonl": read_json,
        "xlsx": read_excel,
        "xls": read_excel,
        "xml": read_xml,
        "parquet": read_parquet,
        "txt": read_text,
        "md": read_text,
        "html": read_text,
        "pdf": read_text,  # PDF needs pdfplumber, handled separately
    }

    reader = readers.get(extension)
    if reader:
        try:
            return reader(data, filename)
        except Exception as e:
            logger.warning(f"Failed to read {filename} with {extension} reader: {e}")
            return {"filename": filename, "error": str(e), "columns": [], "rows": 0}

    return {"filename": filename, "error": f"No reader for .{extension}", "columns": [], "rows": 0}


def read_pdf(data: bytes, filename: str = "") -> dict:
    """Read PDF file and extract text content."""
    try:
        import pdfplumber

        pdf = pdfplumber.open(io.BytesIO(data))
        pages = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        pdf.close()

        content = "\n\n---\n\n".join(pages)
        return {
            "filename": filename,
            "type": "text",
            "content": content[:50000],
            "size_chars": len(content),
            "line_count": content.count("\n") + 1,
            "page_count": len(pages),
        }
    except Exception as e:
        logger.warning(f"Failed to read PDF {filename}: {e}")
        return read_text(data, filename)


def _dataframe_to_summary(df: pd.DataFrame, filename: str) -> dict:
    """Convert a pandas DataFrame to a summary dict for the agent.

    Includes column categorization (numeric, boolean, datetime_candidate,
    categorical, text) and enriched statistics so that a separate
    ``analyze_columns`` call is unnecessary.
    """
    columns = []
    for col in df.columns:
        series = df[col]

        # nunique / value_counts fail on columns containing unhashable types
        # (e.g. lists from pd.json_normalize).  Fall back gracefully.
        try:
            nunique = int(series.nunique())
        except TypeError:
            nunique = -1
        unique_pct = round(float(nunique) / max(len(series), 1) * 100, 1) if nunique >= 0 else 0.0

        col_info = {
            "name": str(col),
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "null_pct": round(float(series.isna().mean()) * 100, 1),
            "unique_count": max(nunique, 0),
            "unique_pct": unique_pct,
            "sample_values": [
                str(v) for v in series.dropna().head(5).tolist()
            ],
        }

        # Detect column category
        if series.dtype in ("int64", "float64"):
            col_info["category"] = "numeric"
            non_null = series.dropna()
            if len(non_null) > 0:
                col_info["min"] = float(non_null.min())
                col_info["max"] = float(non_null.max())
                col_info["mean"] = round(float(non_null.mean()), 4)
        elif series.dtype == "bool":
            col_info["category"] = "boolean"
        elif series.dtype == "object" or pd.api.types.is_string_dtype(series):
            # Columns with unhashable values (lists/dicts) — treat as complex
            if nunique < 0:
                col_info["category"] = "complex"
            else:
                sample = series.dropna().head(20)
                try:
                    pd.to_datetime(sample, format="mixed")
                    # Distinguish time-only values (HH:MM or HH:MM:SS) from datetimes
                    if all(
                        re.match(r"^\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?$", str(v).strip())
                        for v in sample
                    ):
                        col_info["category"] = "time_candidate"
                    else:
                        col_info["category"] = "datetime_candidate"
                except (ValueError, TypeError):
                    if unique_pct < 5:
                        col_info["category"] = "categorical"
                        try:
                            col_info["top_values"] = (
                                series.value_counts().head(10).to_dict()
                            )
                        except TypeError:
                            pass
                    else:
                        col_info["category"] = "text"
        else:
            col_info["category"] = str(series.dtype)

        columns.append(col_info)

    return {
        "filename": filename,
        "type": "tabular",
        "rows": len(df),
        "columns": columns,
        "column_names": list(df.columns),
    }
