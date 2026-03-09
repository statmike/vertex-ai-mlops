"""Tests for config constants, RESOURCE_PREFIX derivation, and overrides."""

import importlib

import agent_orchestrator.config as cfg
from agent_orchestrator.config import (
    ACQUIRE_FILE_EXTENSIONS,
    BQ_ANALYTICS_DATASET,
    BQ_ANALYTICS_TABLE,
    BQ_BRONZE_DATASET,
    BQ_BRONZE_META_DATASET,
    CONTEXT_FILE_EXTENSIONS,
    CRAWL_MAX_DEPTH,
    CRAWL_MAX_FILES,
    DATA_FILE_EXTENSIONS,
    DATAFORM_OUTPUT_DIR,
    GCS_STAGING_ROOT,
    RESOURCE_PREFIX,
    TOOL_MODEL,
)


class TestConfigDefaults:
    """Verify config constants have sensible defaults."""

    def test_tool_model_has_default(self):
        assert isinstance(TOOL_MODEL, str)
        assert len(TOOL_MODEL) > 0

    def test_bq_datasets(self):
        assert BQ_BRONZE_DATASET == "data_onboarding_bronze"
        assert BQ_BRONZE_META_DATASET == "data_onboarding_bronze_meta"

    def test_bq_analytics(self):
        assert BQ_ANALYTICS_DATASET == "applied_ml_data_onboarding"
        assert BQ_ANALYTICS_TABLE == "agent_events"

    def test_gcs_staging_root(self):
        assert GCS_STAGING_ROOT == "applied-ml/ai-agents/data-onboarding"

    def test_crawl_defaults(self):
        assert CRAWL_MAX_DEPTH == 1
        assert CRAWL_MAX_FILES == 100

    def test_file_extensions(self):
        assert "csv" in DATA_FILE_EXTENSIONS
        assert "json" in DATA_FILE_EXTENSIONS
        assert "parquet" in DATA_FILE_EXTENSIONS
        assert "pdf" in CONTEXT_FILE_EXTENSIONS
        assert "md" in CONTEXT_FILE_EXTENSIONS
        assert "csv" in ACQUIRE_FILE_EXTENSIONS

    def test_dataform_output_dir(self):
        assert DATAFORM_OUTPUT_DIR == "./output/dataform"

    def test_gcs_bucket_name_strips_prefix(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLOUD_STORAGE_BUCKET", "gs://my-bucket")
        importlib.reload(cfg)
        assert cfg.gcs_bucket_name() == "my-bucket"


class TestResourcePrefix:
    """Verify RESOURCE_PREFIX derivation and individual overrides."""

    def test_default_prefix(self):
        assert RESOURCE_PREFIX == "data_onboarding"

    def test_custom_prefix_derives_all_names(self, monkeypatch):
        monkeypatch.setenv("RESOURCE_PREFIX", "my_project")
        monkeypatch.delenv("BQ_BRONZE_DATASET", raising=False)
        monkeypatch.delenv("BQ_BRONZE_META_DATASET", raising=False)
        monkeypatch.delenv("BQ_ANALYTICS_DATASET", raising=False)
        monkeypatch.delenv("GCS_STAGING_ROOT", raising=False)
        importlib.reload(cfg)
        assert cfg.RESOURCE_PREFIX == "my_project"
        assert cfg.BQ_BRONZE_DATASET == "my_project_bronze"
        assert cfg.BQ_BRONZE_META_DATASET == "my_project_bronze_meta"
        assert cfg.BQ_ANALYTICS_DATASET == "applied_ml_my_project"
        assert cfg.GCS_STAGING_ROOT == "applied-ml/ai-agents/my-project"

    def test_individual_override_wins(self, monkeypatch):
        monkeypatch.setenv("RESOURCE_PREFIX", "my_project")
        monkeypatch.setenv("BQ_BRONZE_DATASET", "custom_bronze")
        monkeypatch.delenv("BQ_BRONZE_META_DATASET", raising=False)
        monkeypatch.delenv("BQ_ANALYTICS_DATASET", raising=False)
        monkeypatch.delenv("GCS_STAGING_ROOT", raising=False)
        importlib.reload(cfg)
        assert cfg.BQ_BRONZE_DATASET == "custom_bronze"
        # Others still derive from prefix
        assert cfg.BQ_BRONZE_META_DATASET == "my_project_bronze_meta"

    def test_gcs_override_wins(self, monkeypatch):
        monkeypatch.setenv("RESOURCE_PREFIX", "my_project")
        monkeypatch.setenv("GCS_STAGING_ROOT", "custom/path")
        importlib.reload(cfg)
        assert cfg.GCS_STAGING_ROOT == "custom/path"

    def test_analytics_override_wins(self, monkeypatch):
        monkeypatch.setenv("RESOURCE_PREFIX", "my_project")
        monkeypatch.setenv("BQ_ANALYTICS_DATASET", "custom_analytics")
        importlib.reload(cfg)
        assert cfg.BQ_ANALYTICS_DATASET == "custom_analytics"
