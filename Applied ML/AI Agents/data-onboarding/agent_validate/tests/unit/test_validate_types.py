"""Tests for type alias normalization in validate_types."""

from agent_validate.tools.function_tool_validate_types import _normalize_bq_type


class TestNormalizeBqType:
    def test_bool_to_boolean(self):
        assert _normalize_bq_type("BOOL") == "BOOLEAN"

    def test_boolean_stays(self):
        assert _normalize_bq_type("BOOLEAN") == "BOOLEAN"

    def test_int64_to_integer(self):
        assert _normalize_bq_type("INT64") == "INTEGER"

    def test_integer_stays(self):
        assert _normalize_bq_type("INTEGER") == "INTEGER"

    def test_float64_to_float(self):
        assert _normalize_bq_type("FLOAT64") == "FLOAT"

    def test_float_stays(self):
        assert _normalize_bq_type("FLOAT") == "FLOAT"

    def test_string_stays(self):
        assert _normalize_bq_type("STRING") == "STRING"

    def test_timestamp_stays(self):
        assert _normalize_bq_type("TIMESTAMP") == "TIMESTAMP"

    def test_date_stays(self):
        assert _normalize_bq_type("DATE") == "DATE"

    def test_case_insensitive(self):
        assert _normalize_bq_type("bool") == "BOOLEAN"
        assert _normalize_bq_type("int64") == "INTEGER"

    def test_unknown_type_passed_through(self):
        assert _normalize_bq_type("STRUCT") == "STRUCT"

    def test_aliases_compare_equal(self):
        assert _normalize_bq_type("BOOL") == _normalize_bq_type("BOOLEAN")
        assert _normalize_bq_type("INT64") == _normalize_bq_type("INTEGER")
        assert _normalize_bq_type("FLOAT64") == _normalize_bq_type("FLOAT")
