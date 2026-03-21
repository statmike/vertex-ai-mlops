"""Tests for config constants, RESOURCE_PREFIX derivation, and overrides."""

import importlib

import agent_orchestrator.config as cfg
from agent_orchestrator.config import (
    ACQUIRE_FILE_EXTENSIONS,
    BQ_ANALYTICS_DATASET,
    BQ_ANALYTICS_TABLE,
    BQ_BRONZE_DATASET,
    BQ_META_DATASET,
    CONTEXT_FILE_EXTENSIONS,
    CRAWL_MAX_DEPTH,
    CRAWL_MAX_FILES,
    DATA_FILE_EXTENSIONS,
    GCS_STAGING_ROOT,
    OUTPUT_DIR,
    RESOURCE_PREFIX,
    TOOL_MODEL,
    extract_domain_slug,
    get_bronze_dataset,
    get_staging_dataset,
)


class TestConfigDefaults:
    """Verify config constants have sensible defaults."""

    def test_tool_model_has_default(self):
        assert isinstance(TOOL_MODEL, str)
        assert len(TOOL_MODEL) > 0

    def test_bq_datasets(self):
        assert BQ_BRONZE_DATASET == "data_onboarding_bronze"
        assert BQ_META_DATASET == "data_onboarding_meta"

    def test_bq_analytics(self):
        assert BQ_ANALYTICS_DATASET == "data_onboarding_adk"
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

    def test_output_dir(self):
        assert OUTPUT_DIR == "./output"

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
        monkeypatch.delenv("BQ_META_DATASET", raising=False)
        monkeypatch.delenv("BQ_ANALYTICS_DATASET", raising=False)
        monkeypatch.delenv("GCS_STAGING_ROOT", raising=False)
        importlib.reload(cfg)
        assert cfg.RESOURCE_PREFIX == "my_project"
        assert cfg.BQ_BRONZE_DATASET == "my_project_bronze"
        assert cfg.BQ_META_DATASET == "my_project_meta"
        assert cfg.BQ_ANALYTICS_DATASET == "my_project_adk"
        assert cfg.GCS_STAGING_ROOT == "applied-ml/ai-agents/my-project"

    def test_individual_override_wins(self, monkeypatch):
        monkeypatch.setenv("RESOURCE_PREFIX", "my_project")
        monkeypatch.setenv("BQ_BRONZE_DATASET", "custom_bronze")
        monkeypatch.delenv("BQ_META_DATASET", raising=False)
        monkeypatch.delenv("BQ_ANALYTICS_DATASET", raising=False)
        monkeypatch.delenv("GCS_STAGING_ROOT", raising=False)
        importlib.reload(cfg)
        assert cfg.BQ_BRONZE_DATASET == "custom_bronze"
        # Others still derive from prefix
        assert cfg.BQ_META_DATASET == "my_project_meta"

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


class TestDomainSlug:
    """Verify domain slug extraction and domain-scoped dataset naming."""

    def test_strips_data_subdomain(self):
        assert extract_domain_slug("https://data.cms.gov/provider-data") == "cms_gov"

    def test_strips_www_subdomain(self):
        assert extract_domain_slug("https://www.census.gov/data") == "census_gov"

    def test_strips_api_subdomain(self):
        assert extract_domain_slug("https://api.example.com/v1") == "example_com"

    def test_plain_domain(self):
        assert extract_domain_slug("https://example.com/data") == "example_com"

    def test_empty_url(self):
        assert extract_domain_slug("") == ""

    def test_non_url(self):
        assert extract_domain_slug("gs://bucket/path") == ""

    def test_get_bronze_dataset_with_slug(self):
        # Use cfg.* to avoid stale imports after reload in earlier tests
        result = cfg.get_bronze_dataset("cms_gov")
        assert result == f"{cfg.RESOURCE_PREFIX}_cms_gov_bronze"

    def test_get_bronze_dataset_without_slug(self):
        result = cfg.get_bronze_dataset("")
        assert result == cfg.BQ_BRONZE_DATASET

    def test_get_bronze_dataset_no_arg(self):
        result = cfg.get_bronze_dataset()
        assert result == cfg.BQ_BRONZE_DATASET

    def test_get_staging_dataset_with_slug(self):
        result = cfg.get_staging_dataset("cms_gov")
        assert result == f"{cfg.RESOURCE_PREFIX}_cms_gov_staging"

    def test_get_staging_dataset_no_slug(self):
        result = cfg.get_staging_dataset()
        assert result == f"{cfg.RESOURCE_PREFIX}_staging"
