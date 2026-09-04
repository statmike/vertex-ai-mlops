"""Provision the BigQuery trap corpus at every governance tier.

Data is generated **server-side and deterministically**: every random-looking
value is a `FARM_FINGERPRINT` of a stable seed string, so a teardown/rebuild
reproduces the same rows. Nothing is generated client-side, so there is no
pandas dependency and no 250k-row upload.

Tier 0 is built first and then copied verbatim into every other tier, which
guarantees the tiers hold byte-identical data. Governance — column descriptions
here, catalog aspects in `catalog_setup` — is the *only* difference between them
(DESIGN.md §6.3).

One deliberate exception to determinism: timestamps are anchored to
`CURRENT_TIMESTAMP()` at build time so "last month" stays meaningful as the
sandbox ages. Golden truth is therefore always recomputed live from these tables
by `golden.py`, never cached.
"""

from google.cloud import bigquery

import config
import corpus

# Tier 0 is the generation source; every other tier is copied from it.
SOURCE_TIER = 0


def _users_sql(dest: str) -> str:
    return f"""
CREATE OR REPLACE TABLE `{dest}` AS
SELECT
  FORMAT('U%05d', i) AS user_id,
  MOD(ABS(FARM_FINGERPRINT(FORMAT('active-%d', i))), 100) < {corpus.PCT_ACTIVE_FLAG} AS is_active,
  DATE_SUB(
    CURRENT_DATE(),
    INTERVAL MOD(ABS(FARM_FINGERPRINT(FORMAT('signup-%d', i))), 1000) DAY
  ) AS signup_date,
  ['North', 'South', 'East', 'West'][
    OFFSET(MOD(ABS(FARM_FINGERPRINT(FORMAT('region-%d', i))), 4))
  ] AS region
FROM UNNEST(GENERATE_ARRAY(1, {corpus.N_USERS})) AS i
"""


def _events_sql(dest: str, users: str) -> str:
    """Clickstream, with the T3 dormancy trap baked in.

    Dormant users get events only *older* than the active window. Non-dormant
    users are guaranteed at least one event inside it (the ``k = 1`` branch) —
    without that guarantee a low-event user could fall outside the window by
    chance and blur the calibrated dormant share.
    """
    dormant_span = corpus.HISTORY_DAYS - corpus.ACTIVE_WINDOW_DAYS - 1
    return f"""
CREATE OR REPLACE TABLE `{dest}` AS
WITH u AS (
  SELECT
    user_id,
    MOD(ABS(FARM_FINGERPRINT(CONCAT('dormant-', user_id))), 100)
      < {corpus.PCT_DORMANT} AS is_dormant,
    MOD(ABS(FARM_FINGERPRINT(CONCAT('nev-', user_id))), 60) + 10 AS n_events
  FROM `{users}`
),
e AS (
  SELECT u.user_id, u.is_dormant, k
  FROM u, UNNEST(GENERATE_ARRAY(1, u.n_events)) AS k
)
SELECT
  FORMAT('E%09d', ROW_NUMBER() OVER (ORDER BY user_id, k)) AS event_id,
  user_id,
  ['page_view', 'click', 'add_to_cart', 'search'][
    OFFSET(MOD(ABS(FARM_FINGERPRINT(CONCAT('etype-', user_id, '-', CAST(k AS STRING)))), 4))
  ] AS event_type,
  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL
    CASE
      WHEN is_dormant THEN {corpus.ACTIVE_WINDOW_DAYS} + 1
        + MOD(ABS(FARM_FINGERPRINT(CONCAT('ets-', user_id, '-', CAST(k AS STRING)))),
              {dormant_span})
      WHEN k = 1 THEN MOD(ABS(FARM_FINGERPRINT(CONCAT('ets1-', user_id))),
                          {corpus.ACTIVE_WINDOW_DAYS})
      ELSE MOD(ABS(FARM_FINGERPRINT(CONCAT('ets-', user_id, '-', CAST(k AS STRING)))),
               {corpus.HISTORY_DAYS})
    END DAY) AS event_ts
FROM e
"""


def _transactions_sql(dest: str, users: str) -> str:
    """Transactions carrying the T1 naming, T2 refund, and T4 null/outlier traps.

    Dormant users transact small and engaged users transact large, so the
    governed "Active" definition (T3) produces a materially different average
    transaction value than the raw ``is_active`` flag.
    """
    return f"""
CREATE OR REPLACE TABLE `{dest}` AS
WITH u AS (
  SELECT
    user_id,
    MOD(ABS(FARM_FINGERPRINT(CONCAT('dormant-', user_id))), 100)
      < {corpus.PCT_DORMANT} AS is_dormant,
    MOD(ABS(FARM_FINGERPRINT(CONCAT('ntxn-', user_id))), 15) + 3 AS n_txn
  FROM `{users}`
),
t AS (
  SELECT u.user_id, u.is_dormant, k, CONCAT(u.user_id, '-', CAST(k AS STRING)) AS seed
  FROM u, UNNEST(GENERATE_ARRAY(1, u.n_txn)) AS k
),
b AS (
  SELECT
    user_id, k, seed,
    CAST(
      CASE
        WHEN is_dormant THEN 5 + MOD(ABS(FARM_FINGERPRINT(CONCAT('amt-', seed))), 30)
        ELSE 40 + MOD(ABS(FARM_FINGERPRINT(CONCAT('amt-', seed))), 160)
      END AS FLOAT64
    ) AS net_base
  FROM t
)
SELECT
  FORMAT('T%09d', ROW_NUMBER() OVER (ORDER BY user_id, k)) AS txn_id,
  user_id,
  CASE
    WHEN MOD(ABS(FARM_FINGERPRINT(CONCAT('null-', seed))), 100) < {corpus.PCT_NULL_REVENUE}
      THEN NULL
    ELSE ROUND(net_base, 2)
  END AS txn_amt_x2,
  CASE
    WHEN MOD(ABS(FARM_FINGERPRINT(CONCAT('outlier-', seed))), 1000)
         < {corpus.OUTLIERS_PER_1000}
      THEN ROUND(net_base * 1000, 2)
    ELSE ROUND(net_base * {corpus.GROSS_MULTIPLIER}, 2)
  END AS revenue_amount,
  MOD(ABS(FARM_FINGERPRINT(CONCAT('refund-', seed))), 100) < {corpus.PCT_REFUNDED}
    AS status_flg,
  TIMESTAMP_SUB(
    CURRENT_TIMESTAMP(),
    INTERVAL MOD(ABS(FARM_FINGERPRINT(CONCAT('tts-', seed))), {corpus.HISTORY_DAYS}) DAY
  ) AS txn_ts
FROM b
"""


# Identical on every tier, and deliberately says nothing about governance.
#
# The dataset description reaches the agent — `lookup_context` returns it under
# `relatedResources`. A tier-specific string like "ungoverned control" would tell
# the model which arm of the experiment it is in, which is a demand
# characteristic, not a governance signal. Tier differences must live in the
# table and column metadata, never in the label on the container.
DATASET_DESCRIPTION = "Data MCP sandbox corpus."


def create_datasets(client: bigquery.Client) -> None:
    """Create one dataset per governance tier (idempotent)."""
    for tier in config.TIERS:
        dataset = bigquery.Dataset(config.dataset_ref(tier))
        dataset.location = config.BQ_LOCATION
        dataset.description = DATASET_DESCRIPTION
        created = client.create_dataset(dataset, exists_ok=True)
        # create_dataset returns an existing dataset untouched, so re-runs need an
        # explicit update to correct a description written by an earlier version.
        if created.description != DATASET_DESCRIPTION:
            created.description = DATASET_DESCRIPTION
            client.update_dataset(created, ["description"])
        print(f"    Dataset ready: {config.tier_dataset(tier)}")
    grant_tier_access(client)


def grant_tier_access(client: bigquery.Client) -> None:
    """Give each tier's service account READER on its own dataset, and only its own.

    This is the load-bearing half of tier isolation. The tier SAs hold no
    project-level data role, so a dataset ACL entry is the *whole* of their data
    access — and because Knowledge Catalog search is ACL-filtered against
    BigQuery, it also decides which catalog entries they can see. Granting tier 0
    a peek at tier 1 here would silently reopen the leak, so every tier's entry
    is removed from every dataset that is not its own.

    Dataset-level IAM is not reachable through `bq add-iam-policy-binding` (that
    covers tables only), so this edits the dataset's `access` list directly.
    """
    if not config.USE_TIER_SA:
        print("    Tier identities: off (USE_TIER_SA=false) — see docs/scoping.md")
        return

    accounts = {tier: config.tier_service_account(tier) for tier in config.TIERS}
    for tier in config.TIERS:
        dataset = client.get_dataset(config.dataset_ref(tier))
        keep = [
            entry
            for entry in dataset.access_entries
            if entry.entity_id not in accounts.values() or entry.entity_id == accounts[tier]
        ]
        if not any(entry.entity_id == accounts[tier] for entry in keep):
            keep.append(
                bigquery.AccessEntry(
                    role="READER", entity_type="userByEmail", entity_id=accounts[tier]
                )
            )
        if keep != list(dataset.access_entries):
            dataset.access_entries = keep
            client.update_dataset(dataset, ["access_entries"])
        print(f"    Reader on {config.tier_dataset(tier)}: {accounts[tier]}")


def generate_source_tier(client: bigquery.Client) -> None:
    """Build the corpus in the source tier. Order matters — users comes first."""
    users = config.table_ref(SOURCE_TIER, corpus.USERS.name)
    statements = [
        (corpus.USERS.name, _users_sql(users)),
        (
            corpus.TRANSACTIONS.name,
            _transactions_sql(config.table_ref(SOURCE_TIER, corpus.TRANSACTIONS.name), users),
        ),
        (
            corpus.RAW_EVENTS.name,
            _events_sql(config.table_ref(SOURCE_TIER, corpus.RAW_EVENTS.name), users),
        ),
    ]
    for name, sql in statements:
        client.query(sql).result()
        print(f"    Built: {config.tier_dataset(SOURCE_TIER)}.{name}")


def copy_to_other_tiers(client: bigquery.Client) -> None:
    """Copy the source tier verbatim into every other tier.

    A plain copy rather than re-running the generator: the generator anchors to
    CURRENT_TIMESTAMP, so re-running it per tier would drift the tiers apart by
    however long the previous tier took to build.
    """
    for tier in config.TIERS:
        if tier == SOURCE_TIER:
            continue
        for table in corpus.TABLE_NAMES:
            job = client.copy_table(
                config.table_ref(SOURCE_TIER, table),
                config.table_ref(tier, table),
                job_config=bigquery.CopyJobConfig(write_disposition="WRITE_TRUNCATE"),
            )
            job.result()
            print(f"    Copied: {config.tier_dataset(tier)}.{table}")


def apply_descriptions(client: bigquery.Client, tier: int) -> None:
    """Publish table and column descriptions. Tier 1+ only — tier 0 stays bare."""
    for table in corpus.CORPUS:
        ref = config.table_ref(tier, table.name)
        obj = client.get_table(ref)
        descriptions = corpus.columns_with_descriptions(table.name)
        obj.schema = [
            field.to_api_repr() | {"description": descriptions.get(field.name, "")}
            for field in obj.schema
        ]
        obj.description = table.description
        client.update_table(obj, ["schema", "description"])
        print(f"    Described: {config.tier_dataset(tier)}.{table.name}")


def strip_descriptions(client: bigquery.Client, tier: int) -> None:
    """Remove all descriptions, so the control tier is genuinely ungoverned.

    Explicit rather than assumed: a copy job carries the source schema across, so
    re-running setup after tier 1 was described would otherwise leak descriptions
    into the control.
    """
    for table in corpus.CORPUS:
        ref = config.table_ref(tier, table.name)
        obj = client.get_table(ref)
        obj.schema = [field.to_api_repr() | {"description": ""} for field in obj.schema]
        obj.description = ""
        client.update_table(obj, ["schema", "description"])
        print(f"    Stripped: {config.tier_dataset(tier)}.{table.name}")


def row_counts(client: bigquery.Client, tier: int) -> dict[str, int]:
    """Row count per table — used by setup to report and by tests to verify."""
    counts = {}
    for table in corpus.TABLE_NAMES:
        sql = f"SELECT COUNT(*) AS n FROM `{config.table_ref(tier, table)}`"
        counts[table] = int(next(iter(client.query(sql).result()))["n"])
    return counts


def verify_traps(client: bigquery.Client, tier: int) -> dict[str, float]:
    """Measure the realized trap calibration.

    The trap percentages are targets applied to a hash, not exact quotas, so the
    realized shares drift a little. Setup prints these; a wildly-off value means
    the generator changed and golden truth should be re-examined.
    """
    txn = config.table_ref(tier, corpus.TRANSACTIONS.name)
    users = config.table_ref(tier, corpus.USERS.name)
    events = config.table_ref(tier, corpus.RAW_EVENTS.name)
    sql = f"""
    SELECT
      (SELECT AVG(CAST(status_flg AS INT64)) FROM `{txn}`) AS pct_refunded,
      (SELECT AVG(CAST(txn_amt_x2 IS NULL AS INT64)) FROM `{txn}`) AS pct_null_revenue,
      (SELECT AVG(CAST(is_active AS INT64)) FROM `{users}`) AS pct_active_flag,
      (
        SELECT AVG(CAST(recent IS NULL AS INT64))
        FROM (
          SELECT u.user_id, MAX(e.event_ts) AS recent
          FROM `{users}` u
          LEFT JOIN `{events}` e
            ON u.user_id = e.user_id
           AND e.event_ts >= TIMESTAMP_SUB(
                 CURRENT_TIMESTAMP(), INTERVAL {corpus.ACTIVE_WINDOW_DAYS} DAY)
          WHERE u.is_active
          GROUP BY u.user_id
        )
      ) AS pct_dormant_among_active
    """
    # Iterating a BigQuery Row yields values, not keys — use .items().
    row = next(iter(client.query(sql).result()))
    return {key: float(value) for key, value in row.items()}
