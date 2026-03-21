"""Pandas dtype to BigQuery type mapping and table design utilities."""

# Pandas dtype → BigQuery type mapping
DTYPE_TO_BQ = {
    "int64": "INT64",
    "int32": "INT64",
    "int16": "INT64",
    "int8": "INT64",
    "Int64": "INT64",
    "Int32": "INT64",
    "Int16": "INT64",
    "Int8": "INT64",
    "float64": "FLOAT64",
    "float32": "FLOAT64",
    "Float64": "FLOAT64",
    "Float32": "FLOAT64",
    "bool": "BOOL",
    "boolean": "BOOL",
    "object": "STRING",
    "string": "STRING",
    "datetime64[ns]": "TIMESTAMP",
    "datetime64[ns, UTC]": "TIMESTAMP",
    "date": "DATE",
    "timedelta64[ns]": "STRING",
    "category": "STRING",
}

# Category-based type suggestions (from analyze_columns output)
CATEGORY_TO_BQ = {
    "numeric": None,  # Use dtype mapping
    "boolean": "BOOL",
    "datetime_candidate": "TIMESTAMP",
    "time_candidate": "TIME",
    "categorical": "STRING",
    "text": "STRING",
}


def pandas_dtype_to_bq(dtype: str, category: str | None = None) -> str:
    """Map a pandas dtype string to a BigQuery type.

    Args:
        dtype: Pandas dtype string (e.g., 'int64', 'object').
        category: Optional category from column analysis.

    Returns:
        BigQuery type string.
    """
    # Category overrides for detected patterns
    if category and category in CATEGORY_TO_BQ:
        bq_type = CATEGORY_TO_BQ[category]
        if bq_type:
            return bq_type

    return DTYPE_TO_BQ.get(dtype, "STRING")


def suggest_partitioning(columns: list[dict]) -> dict | None:
    """Suggest a partitioning column based on column analysis.

    Looks for date/timestamp columns. Prefers columns with 'date' or 'time' in the name.

    Args:
        columns: List of column dicts with 'name', 'dtype', and optionally 'category'.

    Returns:
        Dict with 'column' and 'type', or None if no good candidate.
    """
    candidates = []
    for col in columns:
        category = col.get("category", "")
        dtype = col.get("dtype", "")
        name = col.get("name", "").lower()

        if category == "datetime_candidate" or "datetime" in dtype:
            priority = 0 if any(k in name for k in ("date", "time", "created", "updated")) else 1
            candidates.append((priority, col["name"]))

    if candidates:
        candidates.sort()
        return {"column": candidates[0][1], "type": "MONTH"}

    return None


def suggest_clustering(columns: list[dict], max_columns: int = 4) -> list[str]:
    """Suggest clustering columns based on column analysis.

    Prefers categorical columns with moderate cardinality, and ID columns.

    Args:
        columns: List of column dicts.
        max_columns: Maximum number of clustering columns (BQ limit is 4).

    Returns:
        List of column names to cluster by.
    """
    # BQ does not allow floating-point types in CLUSTER BY
    float_dtypes = {"float64", "float32", "Float64", "Float32"}
    float_categories = {"numeric"}  # numeric category often maps to FLOAT64

    candidates = []
    for col in columns:
        name = col.get("name", "").lower()
        category = col.get("category", "")
        dtype = col.get("dtype", "")
        unique_pct = col.get("unique_pct", 100)

        # Skip float columns — they cannot be used for clustering
        if dtype in float_dtypes:
            continue
        if category in float_categories and dtype not in ("int64", "int32", "Int64", "Int32"):
            continue

        score = 0
        if category == "categorical":
            score += 3
        if any(k in name for k in ("id", "type", "status", "category", "region", "country")):
            score += 2
        if 0.1 < unique_pct < 50:
            score += 1

        if score > 0:
            candidates.append((score, col["name"]))

    candidates.sort(reverse=True)
    return [name for _, name in candidates[:max_columns]]


def sanitize_column_name(name: str) -> str:
    """Convert a column name to a BQ-friendly snake_case name."""
    import re

    # Replace common separators with underscore
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    # Convert camelCase to snake_case
    clean = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", clean)
    # Collapse multiple underscores
    clean = re.sub(r"_+", "_", clean)
    # Strip leading/trailing underscores
    clean = clean.strip("_").lower()
    # Ensure it starts with a letter or underscore
    if clean and clean[0].isdigit():
        clean = f"_{clean}"
    return clean or "unnamed"
