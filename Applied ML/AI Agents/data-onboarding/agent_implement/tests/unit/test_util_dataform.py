"""Tests for Dataform SQLX generation and changelog formatting."""

import json
import os

from agent_implement.tools.util_dataform import (
    create_dataform_project,
    format_changelog_entry,
    generate_sqlx,
)


class TestCreateDataformProject:
    def test_creates_directory_structure(self, tmp_path):
        output_dir = str(tmp_path / "dataform")
        config_path = create_dataform_project(output_dir, "my-project", "my_dataset")

        assert os.path.isfile(config_path)
        assert os.path.isdir(os.path.join(output_dir, "definitions"))

        with open(config_path) as f:
            config = json.load(f)
        assert config["defaultSchema"] == "my_dataset"
        assert config["defaultDatabase"] == "my-project"
        assert config["warehouse"] == "bigquery"


class TestGenerateSqlx:
    def test_basic_sqlx(self):
        columns = [
            {"name": "id", "bq_type": "INT64", "description": "Row identifier"},
            {"name": "name", "bq_type": "STRING", "description": "User name"},
        ]
        result = generate_sqlx("users", columns, "gs://bucket/data.csv", "User data")

        assert "config {" in result
        assert 'type: "table"' in result
        assert "SELECT" in result
        assert "CAST(`id` AS INT64) AS id" in result
        assert "CAST(`name` AS STRING) AS name" in result
        assert 'description: "User data"' in result

    def test_with_partition_and_cluster(self):
        columns = [
            {"name": "created_at", "bq_type": "TIMESTAMP", "description": "Created time"},
            {"name": "region", "bq_type": "STRING", "description": "Region"},
        ]
        result = generate_sqlx(
            "events",
            columns,
            "gs://bucket/events.csv",
            partition_by={"column": "created_at", "type": "DAY"},
            cluster_by=["region"],
        )

        assert "partitionBy" in result
        assert "clusterBy" in result

    def test_column_descriptions_in_config(self):
        columns = [
            {"name": "val", "bq_type": "FLOAT64", "description": "A numeric value"},
        ]
        result = generate_sqlx("data", columns, "gs://bucket/data.csv")
        assert "A numeric value" in result

    def test_source_name_aliasing(self):
        columns = [
            {"name": "user_name", "source_name": "UserName", "bq_type": "STRING", "description": ""},
        ]
        result = generate_sqlx("t", columns, "gs://bucket/t.csv")
        assert "CAST(`UserName` AS STRING) AS user_name" in result


class TestFormatChangelogEntry:
    def test_basic_entry(self):
        result = format_changelog_entry(
            tables=["users", "orders"],
            action="created",
        )
        assert "Tables created" in result
        assert "`users`" in result
        assert "`orders`" in result

    def test_with_decisions_and_notes(self):
        result = format_changelog_entry(
            tables=["events"],
            action="updated",
            decisions=["Added timestamp partitioning"],
            notes=["Source had 5% null rate in email column"],
        )
        assert "Schema Decisions" in result
        assert "timestamp partitioning" in result
        assert "Notes" in result
        assert "null rate" in result
