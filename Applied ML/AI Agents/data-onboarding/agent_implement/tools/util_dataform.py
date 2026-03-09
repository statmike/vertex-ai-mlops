"""Dataform SQLX template generation and project structure utilities."""

import datetime
import json
import os


def create_dataform_project(output_dir: str, project_id: str, dataset: str) -> str:
    """Create the Dataform project structure with dataform.json.

    Args:
        output_dir: Directory to create the project in.
        project_id: GCP project ID.
        dataset: Default BigQuery dataset.

    Returns:
        Path to the created dataform.json.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "definitions"), exist_ok=True)

    config = {
        "defaultSchema": dataset,
        "assertionSchema": f"{dataset}_assertions",
        "warehouse": "bigquery",
        "defaultDatabase": project_id,
        "defaultLocation": "US",
    }

    config_path = os.path.join(output_dir, "dataform.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    return config_path


def generate_sqlx(
    table_name: str,
    columns: list[dict],
    source_uri: str,
    description: str = "",
    partition_by: dict | None = None,
    cluster_by: list[str] | None = None,
) -> str:
    """Generate a Dataform SQLX file for a table.

    Args:
        table_name: BQ table name.
        columns: List of column dicts with 'name', 'bq_type', 'description'.
        source_uri: GCS URI of the source file.
        description: Table description.
        partition_by: Optional partition config.
        cluster_by: Optional clustering columns.

    Returns:
        SQLX file content as a string.
    """
    # Build config block
    config_parts = [
        '  type: "table",',
        f'  schema: "{table_name}",',
        f'  description: "{_escape_sqlx(description)}",',
    ]

    if partition_by:
        bq_block = "  bigquery: {\n"
        bq_block += f'    partitionBy: "{partition_by["column"]}",\n'
        if cluster_by:
            cluster_str = ", ".join(f'"{c}"' for c in cluster_by)
            bq_block += f"    clusterBy: [{cluster_str}]\n"
        bq_block += "  },"
        config_parts.append(bq_block)
    elif cluster_by:
        cluster_str = ", ".join(f'"{c}"' for c in cluster_by)
        bq_block = "  bigquery: {\n"
        bq_block += f"    clusterBy: [{cluster_str}]\n"
        bq_block += "  },"
        config_parts.append(bq_block)

    # Column descriptions
    col_descriptions = []
    for col in columns:
        desc = _escape_sqlx(col.get("description", ""))
        col_name = col["name"]
        col_descriptions.append(f'    {col_name}: "{desc}"')

    if col_descriptions:
        config_parts.append(
            '  columns: {\n' + ',\n'.join(col_descriptions) + '\n  }'
        )

    config_block = "config {\n" + "\n".join(config_parts) + "\n}"

    # SQL block
    select_parts = []
    for col in columns:
        bq_type = col.get("bq_type", "STRING")
        source_name = col.get("source_name", col["name"])
        if source_name != col["name"]:
            select_parts.append(f"  CAST(`{source_name}` AS {bq_type}) AS {col['name']}")
        else:
            select_parts.append(f"  CAST(`{col['name']}` AS {bq_type}) AS {col['name']}")

    sql = (
        f"-- Source: {source_uri}\n"
        f"-- Generated: {datetime.date.today().isoformat()}\n\n"
        f"SELECT\n"
        + ",\n".join(select_parts)
        + f"\nFROM\n  `{source_uri}`"
    )

    return f"{config_block}\n\n{sql}\n"


def format_changelog_entry(
    tables: list[str],
    action: str = "created",
    decisions: list[str] | None = None,
    notes: list[str] | None = None,
) -> str:
    """Format a changelog entry in structured markdown.

    Args:
        tables: List of table names affected.
        action: What was done (created, updated, etc.).
        decisions: Schema decision summaries.
        notes: Data quality or other notes.

    Returns:
        Formatted markdown entry.
    """
    today = datetime.date.today().isoformat()
    entry = f"\n## {today} — Tables {action}\n\n"

    entry += "### Tables\n"
    for t in tables:
        entry += f"- `{t}`\n"

    if decisions:
        entry += "\n### Schema Decisions\n"
        for d in decisions:
            entry += f"- {d}\n"

    if notes:
        entry += "\n### Notes\n"
        for n in notes:
            entry += f"- {n}\n"

    return entry


def _escape_sqlx(text: str) -> str:
    """Escape special characters for SQLX string literals."""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
