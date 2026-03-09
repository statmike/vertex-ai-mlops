"""Multi-format file readers for data and context files."""

import io
import json
import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Maximum rows to read for schema inference
MAX_SAMPLE_ROWS = 500


def read_csv(data: bytes, filename: str = "") -> dict:
    """Read CSV/TSV file and return schema + sample data."""
    sep = "\t" if filename.endswith((".tsv", ".TSV")) else ","
    df = pd.read_csv(io.BytesIO(data), sep=sep, nrows=MAX_SAMPLE_ROWS, low_memory=False)
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
    """Read Excel file and return schema + sample data."""
    df = pd.read_excel(io.BytesIO(data), nrows=MAX_SAMPLE_ROWS)
    return _dataframe_to_summary(df, filename)


def read_parquet(data: bytes, filename: str = "") -> dict:
    """Read Parquet file and return schema + sample data."""
    df = pd.read_parquet(io.BytesIO(data))
    if len(df) > MAX_SAMPLE_ROWS:
        df = df.head(MAX_SAMPLE_ROWS)
    return _dataframe_to_summary(df, filename)


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
    """Convert a pandas DataFrame to a summary dict for the agent."""
    columns = []
    for col in df.columns:
        col_info = {
            "name": str(col),
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isna().sum()),
            "null_pct": round(float(df[col].isna().mean()) * 100, 1),
            "unique_count": int(df[col].nunique()),
            "sample_values": [
                str(v) for v in df[col].dropna().head(5).tolist()
            ],
        }
        columns.append(col_info)

    return {
        "filename": filename,
        "type": "tabular",
        "rows": len(df),
        "columns": columns,
        "column_names": list(df.columns),
    }
