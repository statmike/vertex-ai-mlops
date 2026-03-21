"""Tests for the propose_tables tool — file grouping, column enrichment, and relationships."""

from agent_design.tools.function_tool_propose_tables import (
    _columns_compatible,
    _detect_relationships,
    _find_shared_keys,
    _group_key,
)


class TestGroupKey:
    def test_strips_date_suffix_dashes(self):
        assert _group_key("IPSF_FULL_2025-01-01.parquet") == "ipsf_full"

    def test_strips_date_suffix_underscores(self):
        assert _group_key("IPSF_FULL_2025_01_01.parquet") == "ipsf_full"

    def test_strips_yyyymmdd_suffix(self):
        assert _group_key("report_20250101.csv") == "report"

    def test_no_date_suffix(self):
        assert _group_key("lookup_table.csv") == "lookup_table"

    def test_case_insensitive(self):
        k1 = _group_key("IPSF_FULL_2025-01-01.parquet")
        k2 = _group_key("ipsf_full_2025-04-01.parquet")
        assert k1 == k2

    def test_multiple_dates_strips_last(self):
        # Only the trailing date should be stripped
        assert _group_key("data_2024_report_2025-06-01.parquet") == "data_2024_report"

    def test_extension_stripped(self):
        assert _group_key("file.json") == "file"


class TestColumnsCompatible:
    def test_identical_sets(self):
        assert _columns_compatible([{"a", "b"}, {"a", "b"}, {"a", "b"}]) is True

    def test_different_sets(self):
        assert _columns_compatible([{"a", "b"}, {"a", "c"}]) is False

    def test_empty_list(self):
        assert _columns_compatible([]) is True

    def test_single_set(self):
        assert _columns_compatible([{"x", "y"}]) is True


class TestFindSharedKeys:
    def test_matching_columns(self):
        cols_a = [
            {"name": "id", "bq_type": "INT64"},
            {"name": "name", "bq_type": "STRING"},
            {"name": "value", "bq_type": "FLOAT64"},
        ]
        cols_b = [
            {"name": "id", "bq_type": "INT64"},
            {"name": "category", "bq_type": "STRING"},
        ]
        assert _find_shared_keys(cols_a, cols_b) == ["id"]

    def test_type_mismatch(self):
        cols_a = [{"name": "id", "bq_type": "INT64"}]
        cols_b = [{"name": "id", "bq_type": "STRING"}]
        assert _find_shared_keys(cols_a, cols_b) == []

    def test_no_overlap(self):
        cols_a = [{"name": "a", "bq_type": "STRING"}]
        cols_b = [{"name": "b", "bq_type": "STRING"}]
        assert _find_shared_keys(cols_a, cols_b) == []

    def test_multiple_shared(self):
        cols_a = [
            {"name": "provider_ccn", "bq_type": "STRING"},
            {"name": "effective_date", "bq_type": "DATE"},
            {"name": "score", "bq_type": "FLOAT64"},
        ]
        cols_b = [
            {"name": "provider_ccn", "bq_type": "STRING"},
            {"name": "effective_date", "bq_type": "DATE"},
            {"name": "other_field", "bq_type": "STRING"},
        ]
        assert _find_shared_keys(cols_a, cols_b) == ["provider_ccn", "effective_date"]


class TestDetectRelationships:
    """Tests for _detect_relationships — snapshot and containment detection."""

    def _make_proposal(self, name, col_names, col_types=None):
        """Helper to build a minimal proposal dict."""
        if col_types is None:
            col_types = ["STRING"] * len(col_names)
        cols = [{"name": n, "bq_type": t} for n, t in zip(col_names, col_types)]
        return {
            "table_name": name,
            "enriched_columns": cols,
        }

    def test_snapshot_lro_detection(self):
        proposals = {
            "ipsf_hha": self._make_proposal("ipsf_hha", ["id", "name", "value"]),
            "ipsf_hha_lro": self._make_proposal("ipsf_hha_lro", ["id", "name", "value"]),
        }
        _detect_relationships(proposals)

        assert proposals["ipsf_hha_lro"]["related_tables"]["snapshot_of"] == "ipsf_hha"
        assert "ipsf_hha_lro" in proposals["ipsf_hha"]["related_tables"]["has_snapshot"]

    def test_snapshot_shared_keys(self):
        proposals = {
            "ipsf_hha": self._make_proposal(
                "ipsf_hha", ["id", "name"], ["INT64", "STRING"]
            ),
            "ipsf_hha_lro": self._make_proposal(
                "ipsf_hha_lro", ["id", "name"], ["INT64", "STRING"]
            ),
        }
        _detect_relationships(proposals)

        assert "shared_keys" in proposals["ipsf_hha_lro"]["related_tables"]
        assert "id" in proposals["ipsf_hha_lro"]["related_tables"]["shared_keys"]

    def test_containment_full_detection(self):
        # ipsf_full has all columns; ipsf_hha has a subset
        proposals = {
            "ipsf_full": self._make_proposal(
                "ipsf_full", ["id", "name", "score", "extra"]
            ),
            "ipsf_hha": self._make_proposal("ipsf_hha", ["id", "name", "score"]),
            "ipsf_inp": self._make_proposal("ipsf_inp", ["id", "name"]),
        }
        _detect_relationships(proposals)

        assert "contains" in proposals["ipsf_full"]["related_tables"]
        assert "ipsf_hha" in proposals["ipsf_full"]["related_tables"]["contains"]
        assert "ipsf_inp" in proposals["ipsf_full"]["related_tables"]["contains"]
        assert proposals["ipsf_hha"]["related_tables"]["contained_by"] == "ipsf_full"
        assert proposals["ipsf_inp"]["related_tables"]["contained_by"] == "ipsf_full"

    def test_lro_not_counted_as_contained(self):
        proposals = {
            "ipsf_full": self._make_proposal("ipsf_full", ["id", "name"]),
            "ipsf_hha": self._make_proposal("ipsf_hha", ["id", "name"]),
            "ipsf_hha_lro": self._make_proposal("ipsf_hha_lro", ["id", "name"]),
        }
        _detect_relationships(proposals)

        # _lro tables should be detected as snapshots, not contained
        contains = proposals["ipsf_full"]["related_tables"].get("contains", [])
        assert "ipsf_hha_lro" not in contains
        assert "ipsf_hha" in contains

    def test_no_relationships(self):
        proposals = {
            "table_a": self._make_proposal("table_a", ["x", "y"]),
            "table_b": self._make_proposal("table_b", ["a", "b"]),
        }
        _detect_relationships(proposals)

        assert proposals["table_a"]["related_tables"] == {}
        assert proposals["table_b"]["related_tables"] == {}

    def test_non_subset_not_contained(self):
        proposals = {
            "ipsf_full": self._make_proposal("ipsf_full", ["id", "name"]),
            "ipsf_hha": self._make_proposal("ipsf_hha", ["id", "other"]),
        }
        _detect_relationships(proposals)

        # ipsf_hha has "other" which is not in ipsf_full, so not a subset
        assert "contains" not in proposals["ipsf_full"]["related_tables"]

    def test_lro_without_base_no_crash(self):
        proposals = {
            "orphan_lro": self._make_proposal("orphan_lro", ["id"]),
        }
        _detect_relationships(proposals)
        # No base "orphan" table, so no snapshot relationship
        assert proposals["orphan_lro"]["related_tables"] == {}

    def test_multiple_snapshots(self):
        proposals = {
            "report": self._make_proposal("report", ["id", "date"]),
            "report_lro": self._make_proposal("report_lro", ["id", "date"]),
        }
        _detect_relationships(proposals)
        assert proposals["report_lro"]["related_tables"]["snapshot_of"] == "report"
        assert "report_lro" in proposals["report"]["related_tables"]["has_snapshot"]
