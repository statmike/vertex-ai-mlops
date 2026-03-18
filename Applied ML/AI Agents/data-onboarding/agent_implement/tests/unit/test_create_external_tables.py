"""Tests for create_external_tables tool."""

from agent_implement.tools.util_sql import GCS_FORMAT_MAP
from agent_orchestrator.config import DATA_FILE_EXTENSIONS


class TestGcsFormatMap:
    def test_format_map_covers_data_extensions(self):
        """Every DATA_FILE_EXTENSION except xlsx/xls/xml should be in GCS_FORMAT_MAP."""
        unsupported = {"xlsx", "xls", "xml"}
        for ext in DATA_FILE_EXTENSIONS:
            if ext in unsupported:
                assert ext not in GCS_FORMAT_MAP
            else:
                assert ext in GCS_FORMAT_MAP, f"Missing GCS_FORMAT_MAP entry for '.{ext}'"

    def test_csv_config(self):
        fmt, opts = GCS_FORMAT_MAP["csv"]
        assert fmt == "CSV"
        assert opts["skip_leading_rows"] == 1

    def test_tsv_config(self):
        fmt, opts = GCS_FORMAT_MAP["tsv"]
        assert fmt == "CSV"
        assert opts["skip_leading_rows"] == 1
        assert opts["field_delimiter"] == "\t"

    def test_parquet_config(self):
        fmt, opts = GCS_FORMAT_MAP["parquet"]
        assert fmt == "PARQUET"
        assert opts == {}

    def test_json_config(self):
        fmt, opts = GCS_FORMAT_MAP["json"]
        assert fmt == "NEWLINE_DELIMITED_JSON"

    def test_unsupported_format_not_in_map(self):
        assert "xlsx" not in GCS_FORMAT_MAP
        assert "xls" not in GCS_FORMAT_MAP
        assert "xml" not in GCS_FORMAT_MAP
