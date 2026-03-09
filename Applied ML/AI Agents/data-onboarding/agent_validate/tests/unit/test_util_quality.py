"""Tests for validation utility functions.

These test the pure logic functions. BQ query functions are tested
via integration tests since they require a live BQ connection.
"""


class TestQualityUtilsImport:
    """Verify the module imports without error."""

    def test_module_imports(self):
        from agent_validate.tools import util_quality

        assert hasattr(util_quality, "get_table_row_count")
        assert hasattr(util_quality, "get_column_null_rates")
        assert hasattr(util_quality, "get_column_types")
        assert hasattr(util_quality, "check_lineage_exists")

    def test_get_bq_client_function_exists(self):
        from agent_validate.tools.util_quality import get_bq_client

        assert callable(get_bq_client)

    def test_row_count_returns_none_without_project(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "")
        import importlib

        import agent_validate.tools.util_quality as mod

        importlib.reload(mod)
        # Should return None when project not set
        result = mod.get_table_row_count("nonexistent")
        assert result is None

    def test_column_types_returns_empty_without_project(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "")
        import importlib

        import agent_validate.tools.util_quality as mod

        importlib.reload(mod)
        result = mod.get_column_types("nonexistent")
        assert result == {}

    def test_null_rates_returns_empty_without_project(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "")
        import importlib

        import agent_validate.tools.util_quality as mod

        importlib.reload(mod)
        result = mod.get_column_null_rates("nonexistent")
        assert result == {}

    def test_lineage_returns_false_without_project(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "")
        import importlib

        import agent_validate.tools.util_quality as mod

        importlib.reload(mod)
        result = mod.check_lineage_exists("src", "tbl")
        assert result is False
