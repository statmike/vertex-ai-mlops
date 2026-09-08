"""Render the two LookML models from the corpus definition.

LookML cannot be created through an API — it lives in a Git-backed Looker
project — so this module *generates the files* and a human installs them. What
it buys is that the semantic layer cannot drift from `corpus.py`: the governed
Active window, the rule text, and the column list all come from the same place
as the BigQuery corpus and the golden-truth oracle.

The two models are the Looker half of the tier experiment:

- **t0** — raw passthrough. Every column is a dimension; there are **no
  measures**, so a Path 2 agent must assemble revenue itself and can pick the
  wrong column exactly as it would against a bare schema.
- **t1** — semantic. Adds `total_revenue` (net, refunds excluded) and
  `active_user_status` (the governed definition), each carrying the rule text
  as its description.

Type mapping is deliberately narrow: this corpus only uses STRING, FLOAT64,
BOOL, DATE, and TIMESTAMP.
"""

import config
import corpus

LOOKER_TYPES = {
    "STRING": "string",
    "FLOAT64": "number",
    "INT64": "number",
    "BOOL": "yesno",
}

TIME_TYPES = {"TIMESTAMP", "DATE"}

# Looker view name -> corpus table. Views are named for the concept, not the
# physical table, which is the point of a semantic layer (and keeps the T1
# naming trap from leaking into the Explore field names).
VIEW_NAMES = {
    corpus.USERS.name: "users",
    corpus.TRANSACTIONS.name: "transactions",
    corpus.RAW_EVENTS.name: "events",
}

# Every joined view needs a declared primary key or Looker cannot use symmetric
# aggregates, and a summed measure fans out across the join. `user_id` is the key
# of `users` but a foreign key on the other two, so this is per table, not per name.
PRIMARY_KEYS = {
    corpus.USERS.name: "user_id",
    corpus.TRANSACTIONS.name: "txn_id",
    corpus.RAW_EVENTS.name: "event_id",
}


def _dimension(column: corpus.Column, primary_key: str) -> str:
    if column.type in TIME_TYPES:
        timeframes = "[raw, date, week, month, quarter, year]"
        if column.type == "TIMESTAMP":
            timeframes = "[raw, time, date, week, month, quarter, year]"
        name = column.name.removesuffix("_ts").removesuffix("_date")
        return (
            f"  dimension_group: {name} {{\n"
            f"    type: time\n"
            f"    timeframes: {timeframes}\n"
            f'    datatype: {column.type.lower()}\n'
            f"    sql: ${{TABLE}}.{column.name} ;;\n"
            f"  }}\n"
        )
    body = f"  dimension: {column.name} {{\n    type: {LOOKER_TYPES[column.type]}\n"
    if column.name == primary_key:
        body += "    primary_key: yes\n"
    body += f"    sql: ${{TABLE}}.{column.name} ;;\n  }}\n"
    return body


def _view(table: corpus.Table, tier: int) -> str:
    """One view. Descriptions and measures appear at tier 1 only."""
    governed = tier >= 1
    lines = [
        f"view: {VIEW_NAMES[table.name]} {{",
        f"  sql_table_name: `@{{GCP_PROJECT}}.{config.tier_dataset(tier)}.{table.name}` ;;",
        "",
    ]
    if governed:
        lines.insert(2, f'  # {table.description}')

    for column in table.columns:
        block = _dimension(column, PRIMARY_KEYS[table.name])
        if governed:
            escaped = column.description.replace('"', "'")
            block = block.replace(
                "    sql:", f'    description: "{escaped}"\n    sql:', 1
            )
        lines.append(block)

    if governed:
        lines.append(_governed_fields(table, tier))
    lines.append("}")
    return "\n".join(lines)


def _governed_fields(table: corpus.Table, tier: int) -> str:
    """The tier-1-only semantic fields. These are what tier 0 must not have."""
    if table.name == corpus.TRANSACTIONS.name:
        rule = corpus.NET_REVENUE_RULE.replace('"', "'")
        return (
            "  measure: total_revenue {\n"
            "    type: sum\n"
            f'    description: "{rule}"\n'
            "    sql: ${txn_amt_x2} ;;\n"
            '    filters: [status_flg: "no"]\n'
            "    value_format_name: usd\n"
            "  }\n"
        )
    if table.name == corpus.USERS.name:
        rule = corpus.ACTIVE_USER_RULE.replace('"', "'")
        # A correlated subquery rather than a join, so the governed definition
        # is self-contained in the dimension an agent will actually read.
        return (
            "  dimension: active_user_status {\n"
            "    type: string\n"
            f'    description: "{rule}"\n'
            "    sql: CASE WHEN ${TABLE}.is_active AND EXISTS (\n"
            f"           SELECT 1 FROM `@{{GCP_PROJECT}}.{config.tier_dataset(tier)}"
            f".{corpus.RAW_EVENTS.name}` e\n"
            "           WHERE e.user_id = ${TABLE}.user_id\n"
            "             AND e.event_ts >= TIMESTAMP_SUB(\n"
            f"                   CURRENT_TIMESTAMP(), INTERVAL {corpus.ACTIVE_WINDOW_DAYS} DAY)\n"
            "         ) THEN 'Active' ELSE 'Inactive' END ;;\n"
            "  }\n"
        )
    return ""


def _model(tier: int) -> str:
    """The model file: connection, includes, and the single Explore.

    Each tier names its OWN connection. That one line is Path 2's tier fence: the
    connection impersonates `config.tier_service_account(tier)`, so a tier-0 model
    pointed at tier-1 data gets an IAM 403 rather than rows.
    """
    return (
        f'connection: "@{{LOOKER_CONNECTION_T{tier}}}"\n\n'
        f'include: "/{config.looker_model(tier)}/*.view.lkml"\n\n'
        f"explore: {config.LOOKER_EXPLORE} {{\n"
        f'  label: "Transactions (tier {tier})"\n'
        f"  join: {VIEW_NAMES[corpus.USERS.name]} {{\n"
        "    type: left_outer\n"
        "    relationship: many_to_one\n"
        f"    sql_on: ${{{config.LOOKER_EXPLORE}.user_id}} = "
        f"${{{VIEW_NAMES[corpus.USERS.name]}.user_id}} ;;\n"
        "  }\n"
        f"  join: {VIEW_NAMES[corpus.RAW_EVENTS.name]} {{\n"
        "    type: left_outer\n"
        "    relationship: one_to_many\n"
        f"    sql_on: ${{{config.LOOKER_EXPLORE}.user_id}} = "
        f"${{{VIEW_NAMES[corpus.RAW_EVENTS.name]}.user_id}} ;;\n"
        "  }\n"
        "}\n"
    )


def render(tier: int) -> dict[str, str]:
    """Return {relative path: file contents} for one tier's LookML."""
    model = config.looker_model(tier)
    files = {f"{model}.model.lkml": _model(tier)}
    for table in corpus.CORPUS:
        files[f"{model}/{VIEW_NAMES[table.name]}.view.lkml"] = _view(table, tier)
    return files


def render_all() -> dict[str, str]:
    """Every LookML file for every tier, plus the shared manifest."""
    files = {"manifest.lkml": _manifest()}
    for tier in config.LOOKER_TIERS:
        files.update(render(tier))
    return files


def _manifest() -> str:
    """Shared constants. One connection per tier — never a single shared one.

    `scripts/looker_provision.py` creates connections under exactly these names,
    so the manifest ships resolved rather than as a placeholder to hand-edit.
    """
    connections = "\n\n".join(
        f"constant: LOOKER_CONNECTION_T{tier} {{\n"
        f'  value: "{config.looker_connection(tier)}"\n'
        "}"
        for tier in config.LOOKER_TIERS
    )
    return (
        "# Constants referenced by the tier models. Generated — do not hand-edit.\n"
        "constant: GCP_PROJECT {\n"
        f'  value: "{config.PROJECT_ID or "your-project-id"}"\n'
        "}\n\n"
        "# One connection per tier. Each impersonates that tier's service account,\n"
        "# which is what puts Path 2 behind the same IAM fence as every other path.\n"
        f"{connections}\n"
    )
