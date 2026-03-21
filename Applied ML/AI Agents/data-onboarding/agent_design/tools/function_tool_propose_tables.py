import logging
import re

from google.adk import tools

from agent_acquire.tools.util_common import log_tool_error
from agent_orchestrator.config import BQ_BRONZE_DATASET, GOOGLE_CLOUD_PROJECT

from .util_bq_types import (
    pandas_dtype_to_bq,
    sanitize_column_name,
    suggest_clustering,
    suggest_partitioning,
)

logger = logging.getLogger(__name__)

# Regex to strip trailing date patterns from base filenames for grouping.
# Matches _YYYY-MM-DD, _YYYY_MM_DD, _YYYYMMDD at end of string.
_DATE_SUFFIX_RE = re.compile(
    r"[_\-](\d{4})[_\-](\d{2})[_\-](\d{2})$"
    r"|[_\-](\d{8})$"
)


def _group_key(filename: str) -> str:
    """Extract a table group key from a filename.

    Strips the file extension and any trailing date suffix, then lowercases.
    E.g. ``IPSF_FULL_2025-01-01.parquet`` -> ``ipsf_full``.
    """
    base = filename.rsplit(".", 1)[0] if "." in filename else filename
    base = _DATE_SUFFIX_RE.sub("", base)
    return sanitize_column_name(base)


def _columns_compatible(col_sets: list[set[str]]) -> bool:
    """Check whether column name sets are identical (case-insensitive)."""
    if not col_sets:
        return True
    first = col_sets[0]
    return all(s == first for s in col_sets[1:])


def _find_shared_keys(cols_a: list[dict], cols_b: list[dict]) -> list[str]:
    """Find columns that share the same name and BQ type between two tables."""
    map_a = {c["name"]: c.get("bq_type", "STRING") for c in cols_a}
    shared = []
    for col in cols_b:
        name = col["name"]
        bq_type = col.get("bq_type", "STRING")
        if name in map_a and map_a[name] == bq_type:
            shared.append(name)
    return shared


def _detect_relationships(proposals: dict) -> None:
    """Detect inter-table relationships and add ``related_tables`` to each proposal.

    Detects:
      - **Snapshot (_lro)**: ``foo_lro`` is a snapshot of ``foo``.
      - **Containment (_full)**: ``foo_full`` contains ``foo_bar`` if
        ``foo_bar``'s columns are a subset of ``foo_full``'s columns.

    Also computes ``shared_keys`` (columns with matching name + BQ type)
    for every related pair.
    """
    names = set(proposals.keys())

    # Initialize related_tables for every proposal
    for prop in proposals.values():
        prop.setdefault("related_tables", {})

    # --- Snapshot detection: _lro suffix ---
    for name in names:
        if name.endswith("_lro"):
            base_name = name[:-4]  # strip _lro
            if base_name in names:
                lro_cols = proposals[name].get("enriched_columns", proposals[name].get("columns", []))
                base_cols = proposals[base_name].get("enriched_columns", proposals[base_name].get("columns", []))
                shared = _find_shared_keys(lro_cols, base_cols)

                proposals[name]["related_tables"]["snapshot_of"] = base_name
                if shared:
                    proposals[name]["related_tables"]["shared_keys"] = shared

                proposals[base_name]["related_tables"].setdefault("has_snapshot", [])
                if isinstance(proposals[base_name]["related_tables"]["has_snapshot"], str):
                    proposals[base_name]["related_tables"]["has_snapshot"] = [
                        proposals[base_name]["related_tables"]["has_snapshot"]
                    ]
                proposals[base_name]["related_tables"]["has_snapshot"].append(name)

    # --- Containment detection: _full suffix ---
    for name in names:
        if not name.endswith("_full"):
            continue

        prefix = name[:-5]  # strip _full
        full_cols = proposals[name].get("enriched_columns", proposals[name].get("columns", []))
        full_col_names = {c["name"] for c in full_cols}

        if not full_col_names:
            continue

        contained = []
        for other_name in names:
            if other_name == name:
                continue
            # Must share the same prefix
            if not other_name.startswith(prefix + "_") and other_name != prefix:
                continue
            # Skip _lro tables (they're snapshots, not contained)
            if other_name.endswith("_lro"):
                continue

            other_cols = proposals[other_name].get(
                "enriched_columns", proposals[other_name].get("columns", [])
            )
            other_col_names = {c["name"] for c in other_cols}

            if not other_col_names:
                continue

            # Containment: other table's columns are a subset of _full
            if other_col_names.issubset(full_col_names):
                contained.append(other_name)
                shared = _find_shared_keys(full_cols, other_cols)
                proposals[other_name]["related_tables"]["contained_by"] = name
                if shared:
                    proposals[other_name]["related_tables"].setdefault("shared_keys", shared)

        if contained:
            proposals[name]["related_tables"]["contains"] = sorted(contained)


async def propose_tables(
    tool_context: tools.ToolContext,
) -> str:
    """
    Propose BigQuery table structures based on analyzed schemas and context insights.

    Groups related files (e.g. quarterly snapshots) into a single table,
    verifies schema compatibility within each group, maps pandas dtypes to
    BigQuery types, enriches columns with context-insight descriptions, and
    suggests partitioning and clustering.

    Args:
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A summary of proposed tables, or an error message.
    """
    try:
        schemas = tool_context.state.get("schemas_analyzed", {})
        insights = tool_context.state.get("context_insights", {})

        if not schemas:
            return "No schemas to design tables from. Run the understand phase first."

        bronze_dataset = tool_context.state.get("bq_bronze_dataset", BQ_BRONZE_DATASET)

        # Collect context-insight column metadata (descriptions, type overrides)
        file_insights = insights.get("files", {}) if isinstance(insights, dict) else {}
        insight_columns: dict[str, dict] = {}
        for _fname, finfo in file_insights.items():
            if isinstance(finfo, dict) and "columns" in finfo:
                insight_columns.update(finfo["columns"])

        # --- Step 1: Group files by naming pattern ---
        groups: dict[str, list[tuple[str, dict]]] = {}
        for path, schema in schemas.items():
            filename = schema.get("filename", path.split("/")[-1])
            key = _group_key(filename)
            groups.setdefault(key, []).append((path, schema))

        proposals = {}

        for group_name, members in groups.items():
            # --- Step 2: Verify schema compatibility ---
            col_name_sets = []
            for _path, schema in members:
                names = set()
                if "columns" in schema:
                    names = {c["name"].lower() for c in schema["columns"]}
                elif "column_analysis" in schema:
                    names = {n.lower() for n in schema["column_analysis"]}
                col_name_sets.append(names)

            if not _columns_compatible(col_name_sets):
                logger.warning(
                    "Schema mismatch in group '%s' — columns differ across files. "
                    "Using first file's schema.", group_name,
                )

            # Use the first file's schema as the representative
            rep_path, rep_schema = members[0]
            rep_filename = rep_schema.get("filename", rep_path.split("/")[-1])

            # Gather all source paths and filenames
            source_paths = [p for p, _ in members]
            source_files = [
                s.get("filename", p.split("/")[-1]) for p, s in members
            ]

            # Sum row counts across group — prefer total_rows (from parquet metadata)
            total_row_count = 0
            for _path, schema in members:
                total_row_count += schema.get("total_rows", schema.get("rows", 0))

            # Table-level description from insights
            rep_file_info = file_insights.get(rep_filename, {})
            table_description = rep_file_info.get(
                "description", f"Data from {group_name}"
            )

            full_table_id = f"{GOOGLE_CLOUD_PROJECT}.{bronze_dataset}.{group_name}"

            # --- Step 3: Enrich columns ---
            raw_columns = []
            if "columns" in rep_schema:
                for col in rep_schema["columns"]:
                    raw_columns.append({
                        "source_name": col["name"],
                        "name": sanitize_column_name(col["name"]),
                        "dtype": col["dtype"],
                        "category": col.get("category", ""),
                    })
            elif "column_analysis" in rep_schema:
                for col_name, info in rep_schema["column_analysis"].items():
                    raw_columns.append({
                        "source_name": col_name,
                        "name": sanitize_column_name(col_name),
                        "dtype": info["dtype"],
                        "category": info.get("category", ""),
                    })

            enriched_columns = []
            for col in raw_columns:
                source_name = col["source_name"]
                dtype = col.get("dtype", "object")
                category = col.get("category", "")

                # Map pandas dtype → BQ type
                bq_type = pandas_dtype_to_bq(dtype, category)

                # Apply context-insight overrides
                col_insight = insight_columns.get(source_name, {})
                if col_insight.get("suggested_bq_type"):
                    bq_type = col_insight["suggested_bq_type"]

                description = col_insight.get("description", "")

                # Apply column name from context (critical for headerless CSVs)
                col_name = col["name"]
                if col_insight.get("suggested_bq_name"):
                    col_name = sanitize_column_name(col_insight["suggested_bq_name"])

                enriched_col = {
                    "name": col_name,
                    "source_name": source_name,
                    "bq_type": bq_type,
                    "description": description,
                    "mode": "NULLABLE",
                    "notes": col_insight.get("notes", ""),
                }

                # Carry attribution for inspectable metadata
                if col_insight.get("attributed_to"):
                    enriched_col["attributed_to"] = col_insight["attributed_to"]

                enriched_columns.append(enriched_col)

            # Deduplicate enriched column names (cross-reference can map
            # multiple generic columns to the same suggested name).
            seen_names: dict[str, int] = {}
            for ec in enriched_columns:
                n = ec["name"]
                if n in seen_names:
                    seen_names[n] += 1
                    ec["name"] = f"{n}_{seen_names[n]}"
                else:
                    seen_names[n] = 0

            # --- Step 4: Partitioning & clustering ---
            partition_by = suggest_partitioning(raw_columns)
            cluster_by = suggest_clustering(raw_columns)

            # Remap partition/cluster column references to enriched names.
            # suggested_bq_name may have renamed columns; the DDL must use
            # the enriched names since the SELECT aliases use them.
            name_remap = {}
            for raw, enriched in zip(raw_columns, enriched_columns):
                if raw["name"] != enriched["name"]:
                    name_remap[raw["name"]] = enriched["name"]
            if name_remap:
                if partition_by and partition_by["column"] in name_remap:
                    partition_by = dict(partition_by)
                    partition_by["column"] = name_remap[partition_by["column"]]
                cluster_by = [name_remap.get(c, c) for c in cluster_by]

            # Carry headerless flag for downstream (e.g. external table creation)
            is_headerless = rep_schema.get("headerless", False)

            proposal = {
                "table_name": group_name,
                "full_table_id": full_table_id,
                "description": table_description,
                "source_files": source_files,
                "source_paths": source_paths,
                # Keep singular fields for backward compatibility
                "source_file": source_files[0] if source_files else "",
                "source_path": source_paths[0] if source_paths else "",
                "row_count": total_row_count,
                "columns": raw_columns,
                "enriched_columns": enriched_columns,
                "partition_by": partition_by,
                "cluster_by": cluster_by,
            }
            if is_headerless:
                proposal["headerless"] = True

            proposals[group_name] = proposal

        # --- Step 5: Detect inter-table relationships ---
        _detect_relationships(proposals)

        tool_context.state["proposed_tables"] = proposals

        # Format summary
        result = f"Proposed {len(proposals)} table(s) from {len(schemas)} file(s):\n\n"
        for _name, prop in proposals.items():
            n_files = len(prop.get("source_files", []))
            result += (
                f"### {prop['full_table_id']}\n"
                f"  Description: {prop['description']}\n"
                f"  Source files: {n_files}\n"
                f"  Row count: {prop['row_count']}\n"
                f"  Columns: {len(prop.get('enriched_columns', []))}\n"
            )
            if prop.get("partition_by"):
                result += f"  Partition: BY {prop['partition_by']['type']}({prop['partition_by']['column']})\n"
            if prop.get("cluster_by"):
                result += f"  Cluster: BY {', '.join(prop['cluster_by'])}\n"
            if prop.get("related_tables"):
                for rel_type, rel_val in prop["related_tables"].items():
                    result += f"  Relationship: {rel_type} → {rel_val}\n"
            result += "\n"

        return result

    except Exception as e:
        return log_tool_error("propose_tables", e)
