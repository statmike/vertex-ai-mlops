"""Tests for pandas→BQ type mapping and design utilities."""

from agent_design.tools.util_bq_types import (
    pandas_dtype_to_bq,
    sanitize_column_name,
    suggest_clustering,
    suggest_partitioning,
)


class TestPandasDtypeToBq:
    def test_int64(self):
        assert pandas_dtype_to_bq("int64") == "INT64"

    def test_float64(self):
        assert pandas_dtype_to_bq("float64") == "FLOAT64"

    def test_object_to_string(self):
        assert pandas_dtype_to_bq("object") == "STRING"

    def test_bool(self):
        assert pandas_dtype_to_bq("bool") == "BOOL"

    def test_datetime(self):
        assert pandas_dtype_to_bq("datetime64[ns]") == "TIMESTAMP"

    def test_unknown_defaults_to_string(self):
        assert pandas_dtype_to_bq("weird_type") == "STRING"

    def test_category_override_datetime(self):
        assert pandas_dtype_to_bq("object", "datetime_candidate") == "TIMESTAMP"

    def test_category_override_boolean(self):
        assert pandas_dtype_to_bq("object", "boolean") == "BOOL"


class TestSanitizeColumnName:
    def test_simple(self):
        assert sanitize_column_name("column_name") == "column_name"

    def test_camel_case(self):
        assert sanitize_column_name("columnName") == "column_name"

    def test_spaces(self):
        assert sanitize_column_name("Column Name") == "column_name"

    def test_special_chars(self):
        assert sanitize_column_name("col@#$name") == "col_name"

    def test_leading_digit(self):
        assert sanitize_column_name("1st_col") == "_1st_col"

    def test_empty(self):
        assert sanitize_column_name("") == "unnamed"

    def test_multiple_underscores(self):
        assert sanitize_column_name("a___b") == "a_b"


class TestSuggestPartitioning:
    def test_date_column(self):
        columns = [
            {"name": "created_date", "dtype": "object", "category": "datetime_candidate"},
            {"name": "value", "dtype": "float64", "category": "numeric"},
        ]
        result = suggest_partitioning(columns)
        assert result is not None
        assert result["column"] == "created_date"

    def test_no_date_columns(self):
        columns = [
            {"name": "name", "dtype": "object", "category": "text"},
            {"name": "value", "dtype": "float64", "category": "numeric"},
        ]
        result = suggest_partitioning(columns)
        assert result is None


class TestSuggestClustering:
    def test_categorical_columns(self):
        columns = [
            {"name": "category", "dtype": "object", "category": "categorical", "unique_pct": 5},
            {"name": "id", "dtype": "int64", "category": "numeric", "unique_pct": 100},
            {"name": "status", "dtype": "object", "category": "categorical", "unique_pct": 2},
        ]
        result = suggest_clustering(columns)
        assert len(result) >= 1
        assert "category" in result

    def test_max_four(self):
        columns = [
            {"name": f"cat_{i}", "dtype": "object", "category": "categorical", "unique_pct": 10}
            for i in range(10)
        ]
        result = suggest_clustering(columns)
        assert len(result) <= 4
