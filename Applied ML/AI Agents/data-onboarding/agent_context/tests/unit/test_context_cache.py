"""Tests for the context_cache module."""

import json

from agent_context.context_cache.cache import (
    TableContext,
    _build_brief,
    _entry_name_to_full_id,
    _extract_columns,
    get_all_briefs,
    get_all_detailed,
    get_brief_summary,
    get_detailed_for_tables,
    get_table_columns_from_cache,
    get_table_ids,
    is_cached,
)


class TestEntryNameToFullId:
    def test_standard_path(self):
        name = (
            "projects/my-proj/locations/us/entryGroups/@bigquery/entries/"
            "bigquery.googleapis.com/projects/my-proj/datasets/my_ds/tables/my_tbl"
        )
        assert _entry_name_to_full_id(name) == "my-proj.my_ds.my_tbl"

    def test_invalid_path(self):
        assert _entry_name_to_full_id("invalid/path") is None

    def test_minimal_path(self):
        name = "projects/p/datasets/d/tables/t"
        assert _entry_name_to_full_id(name) == "p.d.t"


class TestBuildBrief:
    def test_strips_data_profile(self):
        entry = {
            "name": "test",
            "description": "A table",
            "table_id": "p.d.t",
            "schema": [
                {
                    "column": "col1",
                    "dataType": "STRING",
                    "description": "A column",
                    "dataProfile": {"nullRatio": 0.1, "distinctValues": 100},
                },
            ],
        }
        brief = _build_brief(entry)
        assert brief["table_id"] == "p.d.t"
        assert len(brief["schema"]) == 1
        assert "dataProfile" not in brief["schema"][0]
        assert brief["schema"][0]["column"] == "col1"

    def test_no_data_profile(self):
        entry = {
            "name": "test",
            "description": "Simple",
            "schema": [{"column": "c", "dataType": "INT64"}],
        }
        brief = _build_brief(entry)
        assert brief["schema"][0]["column"] == "c"


class TestExtractColumns:
    def test_extracts_from_lookup_context_format(self):
        entry = {
            "schema": [
                {"column": "id", "dataType": "INT64", "description": "Primary key"},
                {"column": "name", "dataType": "STRING", "description": ""},
            ],
        }
        cols = _extract_columns(entry)
        assert len(cols) == 2
        assert cols[0] == {"name": "id", "bq_type": "INT64", "description": "Primary key"}
        assert cols[1] == {"name": "name", "bq_type": "STRING", "description": ""}

    def test_empty_schema(self):
        assert _extract_columns({}) == []


class TestCachePublicAPI:
    """Tests for the public API using a manually populated _CACHE."""

    def setup_method(self):
        """Populate _CACHE directly for testing."""
        from agent_context.context_cache import cache

        self._original_cache = cache._CACHE.copy()
        cache._CACHE.clear()

        brief1 = {
            "table_id": "p.d.table1",
            "name": "table1",
            "description": "First table",
            "schema": [
                {"column": "col_a", "dataType": "STRING", "description": "Column A"},
                {"column": "col_b", "dataType": "INT64", "description": "Column B"},
            ],
        }
        detailed1 = {
            **brief1,
            "relationships": {"fk": "p.d.table2.id"},
        }
        cache._CACHE["p.d.table1"] = TableContext(
            full_id="p.d.table1",
            brief=json.dumps(brief1),
            detailed=json.dumps(detailed1),
            columns=[
                {"name": "col_a", "bq_type": "STRING", "description": "Column A"},
                {"name": "col_b", "bq_type": "INT64", "description": "Column B"},
            ],
            description="First table",
        )

        brief2 = {
            "table_id": "p.d.table2",
            "name": "table2",
            "description": "Second table",
            "schema": [{"column": "id", "dataType": "INT64", "description": "PK"}],
        }
        cache._CACHE["p.d.table2"] = TableContext(
            full_id="p.d.table2",
            brief=json.dumps(brief2),
            detailed=json.dumps(brief2),
            columns=[{"name": "id", "bq_type": "INT64", "description": "PK"}],
            description="Second table",
        )

    def teardown_method(self):
        from agent_context.context_cache import cache

        cache._CACHE.clear()
        cache._CACHE.update(self._original_cache)

    def test_get_table_ids(self):
        ids = get_table_ids()
        assert set(ids) == {"p.d.table1", "p.d.table2"}

    def test_is_cached(self):
        assert is_cached("p.d.table1") is True
        assert is_cached("p.d.missing") is False

    def test_get_all_briefs(self):
        briefs = json.loads(get_all_briefs())
        assert len(briefs) == 2
        # No dataProfile in briefs
        for b in briefs:
            for col in b.get("schema", []):
                assert "dataProfile" not in col

    def test_get_all_detailed(self):
        detailed = json.loads(get_all_detailed())
        assert len(detailed) == 2

    def test_get_detailed_for_tables(self):
        result = json.loads(get_detailed_for_tables(["p.d.table1"]))
        assert len(result) == 1
        assert result[0]["table_id"] == "p.d.table1"

    def test_get_detailed_for_missing_table(self):
        result = json.loads(get_detailed_for_tables(["p.d.missing"]))
        assert len(result) == 0

    def test_get_brief_summary(self):
        summary = get_brief_summary()
        assert "table1" in summary
        assert "table2" in summary
        assert "col_a" in summary
        assert "2 columns" in summary

    def test_get_table_columns_from_cache_short_name(self):
        result = get_table_columns_from_cache("table1")
        assert result is not None
        assert result["full_id"] == "p.d.table1"
        assert len(result["columns"]) == 2
        assert result["columns"][0]["name"] == "col_a"

    def test_get_table_columns_from_cache_full_id(self):
        result = get_table_columns_from_cache("p.d.table2")
        assert result is not None
        assert result["full_id"] == "p.d.table2"

    def test_get_table_columns_from_cache_missing(self):
        assert get_table_columns_from_cache("nonexistent") is None
