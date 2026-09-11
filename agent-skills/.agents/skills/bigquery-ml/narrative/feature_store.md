# Point-in-Time Feature Retrieval — `ML.FEATURES_AT_TIME` and `ML.ENTITY_FEATURES_AT_TIME`

Two model-free table-valued functions that answer *"what did we know about this entity at this moment?"* — the question a feature store exists to answer. **`ML.FEATURES_AT_TIME`** retrieves each entity's feature vector as of one shared timestamp: the online-serving shape. **`ML.ENTITY_FEATURES_AT_TIME`** retrieves each entity's vector as of *its own* timestamp: the training-set shape, and the thing that prevents label leakage. Neither trains anything, neither needs a connection, and neither creates a model object. There is no feature store to provision — the feature table is an ordinary BigQuery table.

**The thesis of this notebook: the shape of your feature table decides which arguments you need, and getting that backwards is silent.** The same argument — `ignore_feature_nulls` — is *mandatory* on one table shape and *actively harmful* on another, with no error either way. So this notebook builds the three table shapes a feature history actually takes in practice (**dense**, **sparse**, and **EAV**), then runs the same function against each and measures what changes.

**What this notebook establishes, all measured here rather than quoted:**

1. The default call is *exactly* a `QUALIFY ROW_NUMBER()` window — proven equal in both directions, so you always know what you are getting.
2. Hand-writing that same window is easy to get silently wrong: one alias-shadowing slip returns the wrong "latest" row for **roughly half** of all entities, with no error.
3. On a **sparse** history the default call is nearly useless — **17,440 of 26,979** entities come back with a NULL order count they do not actually have.
4. `ignore_feature_nulls => TRUE` repairs exactly that, assembling one vector from **three different source rows**. This is the argument's design purpose, not a workaround.
5. On a **dense** table the same flag fabricates data: **1,572** entities get a delivery duration for an order that was never delivered.
6. **EAV** storage pivots back to sparse and round-trips through the function to an identical answer.
7. `num_rows > 1` returns the N latest rows but stamps them all with the *requested* time — erasing the only column that could tell them apart.
8. `ML.ENTITY_FEATURES_AT_TIME` is an **inner** join, and it drops extra entity-table columns — including your label.

**Data:** [`bigquery-public-data.thelook_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-data/thelook-ecommerce) — real order/shipment/delivery event timestamps, which is what makes a genuinely sparse feature history possible without inventing one.

**Related content:** `workflows/feature_store` (`workflows/feature_store/`) puts these two functions to work end to end and measures what leakage actually costs. `functions/feature_engineering` (`functions/feature_engineering/`) is where the feature *values* come from; this notebook is about retrieving them at the right moment.

**References:** `reference/model-free-functions.md` (Full reference) | [`ML.FEATURES_AT_TIME`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature-time) | [`ML.ENTITY_FEATURES_AT_TIME`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-entity-feature-time) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No connection needed — both functions run entirely inside BigQuery.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
```

### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.

```python
from google.cloud import bigquery
import pandas as pd

client = bigquery.Client(project=PROJECT_ID)
pd.set_option('display.max_colwidth', None)

# Create the shared dataset (idempotent)
dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
dataset = bigquery.Dataset(dataset_ref)
dataset.location = LOCATION
client.create_dataset(dataset, exists_ok=True)
print(f'Dataset {PROJECT_ID}.{DATASET_ID} ready')

# Register %%bigquery cell magic (auto-loaded in Colab, needed elsewhere)
%load_ext bigquery_magics
```

Everything below is built as of a fixed cutoff. `thelook_ecommerce` is a rolling dataset whose latest rows advance with the calendar, so pinning a cutoff is what makes the numbers in this notebook reproducible.

```python
CUTOFF = '2024-01-01'  # fixed as-of instant; all feature history is built strictly before this
```

---
## Step 1 — The contract: two columns, exactly named, exactly typed

`ML.FEATURES_AT_TIME` has one hard requirement and it is not negotiable. The feature table must contain:

| column | type | meaning |
|---|---|---|
| `entity_id` | `STRING` | who the feature row is about |
| `feature_timestamp` | `TIMESTAMP` | when the feature values became true |

Every *other* column is treated as a feature. The names are fixed — not configurable — so most real tables need a rename on the way in. They are, however, **case-insensitive**: `Entity_ID` and `Feature_TimeStamp` are accepted, and the original casing comes back in the output. The *types* are not negotiable either way. The signature:

```sql
ML.FEATURES_AT_TIME(
  {TABLE table_name | (query)},
  [, time => TIMESTAMP]
  [, num_rows => INT64]
  [, ignore_feature_nulls => BOOL]
)
```

The three named arguments are all optional. `time` defaults to the current timestamp, `num_rows` to **1**, and `ignore_feature_nulls` to `FALSE`. Note that `time` takes a single timestamp, not a list — passing an array fails with `Unable to coerce type ARRAY<TIMESTAMP> to expected type TIMESTAMP`. The three violations of the contract below are worth seeing as real errors rather than as a warning in prose.

```python
def try_query(sql, label):
    """Run a query that is expected to fail and print the error BigQuery actually returns."""
    try:
        client.query(sql).result()
        print(f'{label}: unexpectedly succeeded')
    except Exception as e:
        msg = '\n  '.join(str(e).split('\n')[:2])
        print(f'{label}:\n  {msg}\n')

# entity_id must be STRING, not the INT64 that user_id naturally is
try_query("""
SELECT * FROM ML.FEATURES_AT_TIME(
  (SELECT 1 AS entity_id, CURRENT_TIMESTAMP() AS feature_timestamp, 1.0 AS f),
  time => CURRENT_TIMESTAMP())
""", 'entity_id as INT64')

# feature_timestamp must be TIMESTAMP, not DATE
try_query("""
SELECT * FROM ML.FEATURES_AT_TIME(
  (SELECT '1' AS entity_id, CURRENT_DATE() AS feature_timestamp, 1.0 AS f),
  time => CURRENT_TIMESTAMP())
""", 'feature_timestamp as DATE')

# and the columns have to be there at all
try_query("""
SELECT * FROM ML.FEATURES_AT_TIME(
  (SELECT '1' AS entity_id, 1.0 AS f),
  time => CURRENT_TIMESTAMP())
""", 'no feature_timestamp column')
```

All three fail at query-planning time, which is the good outcome — you cannot accidentally run a point-in-time join against a table that does not have a point in time. `user_id` in `thelook_ecommerce` is an `INT64`, so `CAST(user_id AS STRING) AS entity_id` is mandatory for everything that follows, and a `DATE` partition column will not stand in for `feature_timestamp`.

---
## Step 2 — Three shapes a feature history actually takes

Before running the function it is worth being precise about what it is running *against*, because that is what decides the arguments. A feature history is stored in one of three shapes.

| shape | one row is… | NULL means | typical source |
|---|---|---|---|
| **Dense** | a complete observation of an entity at a moment | *genuinely unknown or not applicable* | a snapshot job, a nightly rollup |
| **Sparse** | one *update* to some subset of features | *this update did not touch that feature* | event streams landing at different cadences |
| **EAV** | a single `(entity, time, feature name, value)` observation | *(absent rows, not NULLs)* | generic feature-logging infrastructure |

That middle column is the whole notebook. On a **sparse** table a NULL is an artifact of how the row was written and should be looked through. On a **dense** table a NULL is a fact and must be preserved. `ignore_feature_nulls` is the switch between those two readings, and nothing in the data tells BigQuery which one you meant.

`thelook_ecommerce` gives us all three honestly, because an order emits events at genuinely different times: it is *created*, later *shipped*, later still *delivered*. Each event knows something the others do not.

```python
# Shared source: one row per order, with its three event timestamps and its value
ORDERS_CTE = f"""
WITH ord AS (
  SELECT o.order_id,
         CAST(o.user_id AS STRING) AS entity_id,
         o.created_at, o.shipped_at, o.delivered_at, o.status, o.num_of_item,
         SUM(oi.sale_price) AS order_value
  FROM `bigquery-public-data.thelook_ecommerce.orders` o
  JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi USING (order_id)
  WHERE o.created_at < TIMESTAMP '{CUTOFF}'
  GROUP BY 1, 2, 3, 4, 5, 6, 7
)
"""
print(ORDERS_CTE)
```

### 2a — The sparse shape

Three event streams, one entity, one table. An order-created row knows the running order count and spend; it knows nothing about shipping. A ship row knows only the ship lag. A delivery row knows only the delivery lag. Every other column on that row is NULL — not because the value is unknown, but because *that event was not about that feature*.

One housekeeping step is worth doing deliberately rather than discovering later: the final `GROUP BY` collapses any events that landed on the same entity at the same instant. `feature_timestamp` is how these functions decide what "most recent" means, so duplicate entity-instants make that ordering ambiguous and the tie gets broken arbitrarily — a small, silent source of run-to-run variation. Making the pair unique on write removes the question.

```python
sql = ORDERS_CTE + """
, events AS (
  SELECT entity_id, created_at AS feature_timestamp,
         COUNT(*)                        OVER w AS lifetime_orders,
         ROUND(SUM(order_value)          OVER w, 2) AS lifetime_spend,
         CAST(NULL AS FLOAT64) AS last_ship_lag_h,
         CAST(NULL AS FLOAT64) AS last_delivery_lag_h
  FROM ord
  WINDOW w AS (PARTITION BY entity_id ORDER BY created_at ROWS UNBOUNDED PRECEDING)
  UNION ALL
  SELECT entity_id, shipped_at, NULL, NULL,
         ROUND(TIMESTAMP_DIFF(shipped_at, created_at, MINUTE) / 60, 2), NULL
  FROM ord WHERE shipped_at IS NOT NULL
  UNION ALL
  SELECT entity_id, delivered_at, NULL, NULL, NULL,
         ROUND(TIMESTAMP_DIFF(delivered_at, shipped_at, MINUTE) / 60, 2)
  FROM ord WHERE delivered_at IS NOT NULL
)
-- Collapse any events that landed on the same entity at the same instant, so
-- every (entity_id, feature_timestamp) pair is unique. Without this, "the most
-- recent row" is ambiguous and the retrieval breaks the tie arbitrarily.
SELECT entity_id, feature_timestamp,
       MAX(lifetime_orders)     AS lifetime_orders,
       MAX(lifetime_spend)      AS lifetime_spend,
       MAX(last_ship_lag_h)     AS last_ship_lag_h,
       MAX(last_delivery_lag_h) AS last_delivery_lag_h
FROM events
GROUP BY entity_id, feature_timestamp
"""
client.query(f'CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.fs_sparse` AS {sql}').result()

client.query(f"""
SELECT COUNT(*) AS rows_total,
       COUNT(DISTINCT entity_id) AS entities,
       COUNTIF(lifetime_orders     IS NULL) AS null_lifetime_orders,
       COUNTIF(last_ship_lag_h     IS NULL) AS null_ship_lag,
       COUNTIF(last_delivery_lag_h IS NULL) AS null_delivery_lag
FROM `{PROJECT_ID}.{DATASET_ID}.fs_sparse`
""").to_dataframe()
```

Most cells in this table are NULL, and that is correct — it is the normal state of a feature history assembled from independent event streams. Here is one entity's full history, which is the object every later step operates on.

```python
client.query(f"""
SELECT feature_timestamp, lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
FROM `{PROJECT_ID}.{DATASET_ID}.fs_sparse`
WHERE entity_id = '10000'
ORDER BY feature_timestamp
""").to_dataframe()
```

Six rows across four years, and **no single row describes this customer**. The order count lives on one row, the ship lag on another, the delivery lag on a third. Remember this table — Step 6 reassembles it.

### 2b — The dense shape

One row per order, every column populated from that order's own record. `days_to_deliver` is the interesting one: it is NULL for orders that were cancelled, are still processing, or have shipped but not arrived. That NULL is a **fact about the order**, not a gap in the feed.

```python
sql = ORDERS_CTE + """
SELECT entity_id, created_at AS feature_timestamp,
       num_of_item AS items_in_order,
       status      AS order_status,
       ROUND(TIMESTAMP_DIFF(delivered_at, created_at, MINUTE) / 24 / 60, 2) AS days_to_deliver
FROM ord
"""
client.query(f'CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.fs_dense` AS {sql}').result()

client.query(f"""
SELECT COUNT(*) AS rows_total,
       COUNT(DISTINCT entity_id) AS entities,
       COUNTIF(items_in_order  IS NULL) AS null_items,
       COUNTIF(order_status    IS NULL) AS null_status,
       COUNTIF(days_to_deliver IS NULL) AS null_days_to_deliver
FROM `{PROJECT_ID}.{DATASET_ID}.fs_dense`
""").to_dataframe()
```

### 2c — The EAV shape

Entity–Attribute–Value: one row per *observation*. Generic feature-logging systems land here because a new feature needs no schema change — it is just a new value of `feature_name`. The value column is a `STRUCT` with one field per type, of which exactly one is populated. Note what happens to the NULLs: they simply are not written.

```python
sql = f"""
SELECT entity_id AS entity_key, feature_timestamp, feature_name,
       STRUCT(CAST(NULL AS STRING) AS string_value,
              CAST(v AS INT64)     AS int_value,
              CAST(NULL AS FLOAT64) AS float_value,
              CAST(NULL AS BOOL)   AS bool_value) AS feature_value
FROM `{PROJECT_ID}.{DATASET_ID}.fs_sparse`
UNPIVOT (v FOR feature_name IN (lifetime_orders))
UNION ALL
SELECT entity_id, feature_timestamp, feature_name,
       STRUCT(NULL, NULL, CAST(v AS FLOAT64), NULL)
FROM `{PROJECT_ID}.{DATASET_ID}.fs_sparse`
UNPIVOT (v FOR feature_name IN (lifetime_spend, last_ship_lag_h, last_delivery_lag_h))
"""
client.query(f'CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.fs_eav` AS {sql}').result()

client.query(f"""
SELECT feature_name, COUNT(*) AS observations
FROM `{PROJECT_ID}.{DATASET_ID}.fs_eav`
GROUP BY feature_name ORDER BY feature_name
""").to_dataframe()
```

`UNPIVOT` drops NULLs, so EAV stores only what was actually observed — that is the shape's entire appeal, and why `last_delivery_lag_h` has far fewer rows than `lifetime_orders`. It is also why EAV cannot be handed to `ML.FEATURES_AT_TIME` directly: the function needs one column per feature. Step 8 pivots it back.

---
## Step 3 — The default call, and exactly what it equals

Start with the simplest possible invocation against the dense table: one shared timestamp, default everything.

```python
client.query(f"""
SELECT *
FROM ML.FEATURES_AT_TIME(
  TABLE `{PROJECT_ID}.{DATASET_ID}.fs_dense`,
  time => TIMESTAMP '{CUTOFF}')
WHERE entity_id IN ('10000', '10001', '10002')
ORDER BY entity_id
""").to_dataframe()
```

One row per entity, holding that entity's most recent observation at or before `time`. One thing in that output is worth naming now because it surprises people later: `feature_timestamp` is **the time you asked for**, not the time the source row was written. The provenance of the values is discarded, uniformly, on every row.

Rather than describe the retrieval logic, prove it. The claim is that the default call is exactly `QUALIFY ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY feature_timestamp DESC) = 1`. `EXCEPT DISTINCT` in both directions is the test — two empty results mean the sets are identical.

```python
client.query(f"""
WITH fn AS (
  SELECT entity_id, feature_timestamp, items_in_order, order_status, days_to_deliver
  FROM ML.FEATURES_AT_TIME(TABLE `{PROJECT_ID}.{DATASET_ID}.fs_dense`,
                           time => TIMESTAMP '{CUTOFF}', num_rows => 1)
),
latest AS (
  SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.fs_dense`
  WHERE feature_timestamp <= TIMESTAMP '{CUTOFF}'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY feature_timestamp DESC) = 1
),
hand AS (
  SELECT entity_id, TIMESTAMP '{CUTOFF}' AS feature_timestamp,
         items_in_order, order_status, days_to_deliver
  FROM latest
)
SELECT (SELECT COUNT(*) FROM (SELECT * FROM fn   EXCEPT DISTINCT SELECT * FROM hand)) AS in_function_not_hand,
       (SELECT COUNT(*) FROM (SELECT * FROM hand EXCEPT DISTINCT SELECT * FROM fn))   AS in_hand_not_function
""").to_dataframe()
```

Zero and zero. The function is not doing anything you could not write yourself, and knowing precisely what it equals is what lets you reason about the rest of this notebook.

So why use it? Partly brevity — but mostly because the hand-written version has a trap in it.

---
## Step 4 — Why the hand-written window is worth avoiding

The `hand` CTE above is deliberately written in two steps: pick the latest row, *then* overwrite `feature_timestamp` with the requested time. Collapsing those into one `SELECT` is the obvious simplification, and it is wrong.

BigQuery resolves `QUALIFY` **after** the `SELECT` list, so a select-list alias is visible to it. Aliasing a constant as `feature_timestamp` means the window's `ORDER BY feature_timestamp DESC` no longer orders by the column — it orders by the constant. Every row ties, and `ROW_NUMBER()` picks arbitrarily. No error, no warning.

```python
client.query(f"""
WITH fn AS (
  SELECT entity_id, lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
  FROM ML.FEATURES_AT_TIME(TABLE `{PROJECT_ID}.{DATASET_ID}.fs_sparse`,
                           time => TIMESTAMP '{CUTOFF}', num_rows => 1)
),
shadowed AS (
  -- the alias below shadows the source column inside QUALIFY
  SELECT entity_id, TIMESTAMP '{CUTOFF}' AS feature_timestamp,
         lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
  FROM `{PROJECT_ID}.{DATASET_ID}.fs_sparse`
  WHERE feature_timestamp <= TIMESTAMP '{CUTOFF}'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY feature_timestamp DESC) = 1
)
SELECT COUNT(*) AS entities_compared,
       COUNTIF(f.lifetime_orders IS DISTINCT FROM s.lifetime_orders
            OR f.lifetime_spend  IS DISTINCT FROM s.lifetime_spend
            OR f.last_ship_lag_h IS DISTINCT FROM s.last_ship_lag_h
            OR f.last_delivery_lag_h IS DISTINCT FROM s.last_delivery_lag_h) AS entities_disagreeing
FROM fn f JOIN (SELECT * EXCEPT (feature_timestamp) FROM shadowed) s USING (entity_id)
""").to_dataframe()
```

Roughly **46% of entities** get a different — and wrong — feature vector, from a query that runs cleanly and looks entirely reasonable on inspection.

The exact count moves between runs, and that is the tell rather than a nuisance: with every row tied on a constant, `ROW_NUMBER()` has no defined winner, so which wrong row you get is not stable. A query whose output changes when nothing about the data changed is one of the few leakage-adjacent bugs that announces itself — if you happen to run it twice. The function has no select list to shadow anything with, so it cannot be broken this way, and that is a better argument for using it than brevity.

---
## Step 5 — The default call on a sparse history: correct, and nearly useless

Everything above ran against the dense table, where "the latest row" is a complete observation. Run the identical call against the sparse table and the same logic produces something you cannot model on.

```python
client.query(f"""
SELECT COUNT(*) AS entities,
       COUNTIF(lifetime_orders     IS NULL) AS null_lifetime_orders,
       COUNTIF(last_ship_lag_h     IS NULL) AS null_ship_lag,
       COUNTIF(last_delivery_lag_h IS NULL) AS null_delivery_lag
FROM ML.FEATURES_AT_TIME(
  TABLE `{PROJECT_ID}.{DATASET_ID}.fs_sparse`,
  time => TIMESTAMP '{CUTOFF}', num_rows => 1)
""").to_dataframe()
```

Nearly two thirds of these customers appear to have **no order count at all**, and every one of them has ordered — that is where the rows came from. The retrieval is doing exactly what Step 3 proved it does: returning the single most recent row. It is just that on a sparse history the most recent row is usually a shipment or a delivery, and those rows know nothing about order counts.

This is the failure mode worth internalizing: it is not an error, the row counts are right, and the output looks like a legitimate feature vector full of missing data. A model trained on it would conclude that most customers are new.

---
## Step 6 — `ignore_feature_nulls => TRUE`: the sparse-shape reassembler

Flip one argument. Per feature column, the function now walks back to the most recent row where *that column* is non-NULL, independently of the others.

```python
client.query(f"""
SELECT COUNT(*) AS entities,
       COUNTIF(lifetime_orders     IS NULL) AS null_lifetime_orders,
       COUNTIF(last_ship_lag_h     IS NULL) AS null_ship_lag,
       COUNTIF(last_delivery_lag_h IS NULL) AS null_delivery_lag
FROM ML.FEATURES_AT_TIME(
  TABLE `{PROJECT_ID}.{DATASET_ID}.fs_sparse`,
  time => TIMESTAMP '{CUTOFF}', num_rows => 1, ignore_feature_nulls => TRUE)
""").to_dataframe()
```

`lifetime_orders` goes to **zero** NULLs. The remaining gaps are honest ones: those customers genuinely never had an order ship, or never had one delivered, before the cutoff. The shape artifact is gone and the real absences survive — which is precisely the distinction Step 2's table set up.

The single-entity trace is what makes the mechanism concrete. This is the same customer whose six-row history appeared in Step 2a.

```python
client.query(f"""
SELECT 'history' AS source, CAST(feature_timestamp AS STRING) AS ts,
       lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
FROM `{PROJECT_ID}.{DATASET_ID}.fs_sparse`
WHERE entity_id = '10000' AND feature_timestamp < TIMESTAMP '{CUTOFF}'
UNION ALL
SELECT 'default', CAST(feature_timestamp AS STRING),
       lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
FROM ML.FEATURES_AT_TIME(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.fs_sparse` WHERE entity_id = '10000'),
  time => TIMESTAMP '{CUTOFF}', num_rows => 1)
UNION ALL
SELECT 'ignore_feature_nulls', CAST(feature_timestamp AS STRING),
       lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
FROM ML.FEATURES_AT_TIME(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.fs_sparse` WHERE entity_id = '10000'),
  time => TIMESTAMP '{CUTOFF}', num_rows => 1, ignore_feature_nulls => TRUE)
ORDER BY source, ts
""").to_dataframe()
```

Read the last two rows against the six above them. The **default** row takes everything from the 2021-12-12 delivery event and reports a customer with no orders and no spend. The **`ignore_feature_nulls`** row takes `lifetime_orders` and `lifetime_spend` from 2021-12-07, `last_ship_lag_h` from 2021-12-08, and `last_delivery_lag_h` from 2021-12-12 — **three different source rows, assembled into one vector that exists in no row of the table**.

That is worth stating plainly, because it is usually presented as a hazard: the function returns a row that never existed. On a sparse history that is not a hazard, it is the entire point. Reassembling the current state from updates that arrived at different times is the job. Which is also why the flag is dangerous somewhere else.

---
## Step 7 — The same flag on a dense table fabricates data

Run `ignore_feature_nulls => TRUE` against the dense table, where a NULL `days_to_deliver` means *this order was not delivered*. The function has no way to know that, so it does what it was told: it reaches back to an earlier order that was.

```python
client.query(f"""
WITH d AS (
  SELECT * FROM ML.FEATURES_AT_TIME(TABLE `{PROJECT_ID}.{DATASET_ID}.fs_dense`,
                                    time => TIMESTAMP '{CUTOFF}', num_rows => 1)
),
g AS (
  SELECT * FROM ML.FEATURES_AT_TIME(TABLE `{PROJECT_ID}.{DATASET_ID}.fs_dense`,
                                    time => TIMESTAMP '{CUTOFF}', num_rows => 1,
                                    ignore_feature_nulls => TRUE)
)
SELECT d.order_status AS latest_order_status,
       COUNT(*) AS entities,
       COUNTIF(d.days_to_deliver IS NULL) AS null_with_default,
       COUNTIF(g.days_to_deliver IS NULL) AS null_with_ignore_nulls,
       COUNTIF(d.days_to_deliver IS NULL AND g.days_to_deliver IS NOT NULL) AS fabricated
FROM d JOIN g USING (entity_id)
GROUP BY latest_order_status ORDER BY latest_order_status
""").to_dataframe()
```

Add up the `fabricated` column: **1,572 customers** are now reported with a delivery duration for an order that was cancelled, is still processing, or has shipped but not arrived. Every one of those numbers is a real measurement — of a *different, earlier order*. Nothing in the output marks them, and `Complete` and `Returned` rows are untouched, so a spot check of a few rows will very likely look fine.

Set the two results side by side, because they are the same function call:

| feature table | `ignore_feature_nulls => TRUE` does | verdict |
|---|---|---|
| **sparse** (Step 6) | repairs 17,440 entities whose order count was a storage artifact | **required** |
| **dense** (Step 7) | invents a delivery time for 1,572 undelivered orders | **harmful** |

Neither call errors. Neither output looks wrong. The only thing that decides which one you got is a property of your table that BigQuery cannot see — so it has to be something you know before you write the call.

---
## Step 8 — EAV: pivot back, then retrieve

`ML.FEATURES_AT_TIME` requires one column per feature, so an EAV table has to be pivoted on the way in. The conditional-aggregate idiom does it in one pass, selecting the `feature_value` struct field that matches each feature's type.

Because EAV omits unobserved values entirely, the pivot reproduces the sparse shape exactly — including its NULLs — so it needs `ignore_feature_nulls => TRUE` for the same reason Step 6 did.

```python
client.query(f"""
SELECT COUNT(*) AS entities,
       COUNTIF(lifetime_orders     IS NULL) AS null_lifetime_orders,
       COUNTIF(last_delivery_lag_h IS NULL) AS null_delivery_lag
FROM ML.FEATURES_AT_TIME(
  (SELECT entity_key AS entity_id, feature_timestamp,
          MAX(IF(feature_name = 'lifetime_orders',     feature_value.int_value,   NULL)) AS lifetime_orders,
          MAX(IF(feature_name = 'lifetime_spend',      feature_value.float_value, NULL)) AS lifetime_spend,
          MAX(IF(feature_name = 'last_ship_lag_h',     feature_value.float_value, NULL)) AS last_ship_lag_h,
          MAX(IF(feature_name = 'last_delivery_lag_h', feature_value.float_value, NULL)) AS last_delivery_lag_h
   FROM `{PROJECT_ID}.{DATASET_ID}.fs_eav`
   GROUP BY entity_id, feature_timestamp),
  time => TIMESTAMP '{CUTOFF}', num_rows => 1, ignore_feature_nulls => TRUE)
""").to_dataframe()
```

Identical to Step 6's result — same entity count, same zero, same residual delivery gaps. The round trip holds, which is the practical reassurance an EAV feature log needs: the storage shape is a storage decision and does not change the answer.

The cost is in the pivot, not the retrieval. Every feature must be named twice — once in the `IF`, once in the struct field — so adding a feature that needed no schema change on write does need a query change on read. That is the trade EAV makes.

---
## Step 9 — Two properties of the output that break downstream SQL

### `num_rows` returns more history, and erases which is which

`num_rows` defaults to 1. Raising it returns up to N of the most recent rows per entity.

```python
rows = []
for n in [1, 2, 3]:
    df = client.query(f"""
    SELECT {n} AS num_rows_arg, COUNT(*) AS rows_returned, COUNT(DISTINCT entity_id) AS entities
    FROM ML.FEATURES_AT_TIME(TABLE `{PROJECT_ID}.{DATASET_ID}.fs_sparse`,
                             time => TIMESTAMP '{CUTOFF}', num_rows => {n})
    """).to_dataframe()
    rows.append(df)
pd.concat(rows, ignore_index=True)
```

```python
client.query(f"""
SELECT entity_id, feature_timestamp, lifetime_orders, last_ship_lag_h, last_delivery_lag_h
FROM ML.FEATURES_AT_TIME(
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.fs_sparse` WHERE entity_id = '10000'),
  time => TIMESTAMP '{CUTOFF}', num_rows => 3)
""").to_dataframe()
```

Three rows, and **all three carry the same `feature_timestamp`** — the requested time. The source timestamps that distinguish them are gone, and no other column recovers them. So `num_rows > 1` supports aggregating over recent history (an average of the last three ship lags) but cannot support sequencing it, because there is nothing left to `ORDER BY`. If you need the ordering, keep a copy of the event time as an ordinary feature column, where it will survive.

### Column order *is* preserved

Worth checking rather than assuming, since a reordered output would quietly break any positional consumer downstream.

```python
src = [f.name for f in client.get_table(f'{PROJECT_ID}.{DATASET_ID}.fs_sparse').schema]
out = [f.name for f in client.query(f"""
SELECT * FROM ML.FEATURES_AT_TIME(TABLE `{PROJECT_ID}.{DATASET_ID}.fs_sparse`,
                                  time => TIMESTAMP '{CUTOFF}') LIMIT 0
""").result().schema]
pd.DataFrame({'source_table': src, 'function_output': out})
```

Identical, column for column. `SELECT *` into a positional consumer — `EXCEPT DISTINCT`, `UNION ALL`, `INSERT INTO ... SELECT *` — lines up correctly.

One caveat on how you *inspect* that, because it is an easy way to convince yourself otherwise: several clients sort field names when rendering a row as JSON, including the `bq` command-line tool's `--format=json`. Read the order off the schema, as the cell above does, not off a serialized row.

---
## Step 10 — `ML.ENTITY_FEATURES_AT_TIME`: a different timestamp per entity

Everything so far used one shared `time`, which is the online-serving question: *what does every entity look like right now?* Training asks a different question, one label at a time: *what did this entity look like at the moment its label was determined?* Those moments differ per row, so a single `time` cannot express them.

```sql
ML.ENTITY_FEATURES_AT_TIME(
  {TABLE feature_table | (query)},
  {TABLE entity_table  | (query)}
  [, num_rows => INT64]
  [, ignore_feature_nulls => BOOL]
)
```

The second table supplies the per-entity instants and needs two columns: `entity_id` (`STRING`) and **`time`** (`TIMESTAMP`) — note that it is `time` here, not `feature_timestamp`. There is no `time` argument, because the entity table *is* the time argument.

```python
# Ask for each customer's state at the moment of each of their orders in H2 2023
client.query(f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.fs_entities` AS
SELECT CAST(user_id AS STRING) AS entity_id,
       created_at AS time,
       order_id,
       status AS order_status
FROM `bigquery-public-data.thelook_ecommerce.orders`
WHERE created_at BETWEEN TIMESTAMP '2023-06-01' AND TIMESTAMP '2023-12-31'
""").result()

client.query(f"""
SELECT *
FROM ML.ENTITY_FEATURES_AT_TIME(
  TABLE `{PROJECT_ID}.{DATASET_ID}.fs_sparse`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.fs_entities`,
  num_rows => 1, ignore_feature_nulls => TRUE)
ORDER BY entity_id, feature_timestamp
LIMIT 5
""").to_dataframe()
```

Two things to notice in that output, both of which cost real time if discovered later.

`feature_timestamp` here holds the *requested* instant from the entity table — the same substitution `ML.FEATURES_AT_TIME` makes. And `order_id` and `order_status` are **gone**. The entity table's extra columns are not carried through; only `entity_id` and the requested time survive. Since the label is exactly such a column, it has to be joined back on.

```python
client.query(f"""
SELECT (SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.fs_entities`) AS requests,
       (SELECT COUNT(*) FROM ML.ENTITY_FEATURES_AT_TIME(
          TABLE `{PROJECT_ID}.{DATASET_ID}.fs_sparse`,
          TABLE `{PROJECT_ID}.{DATASET_ID}.fs_entities`,
          num_rows => 1, ignore_feature_nulls => TRUE)) AS returned
""").to_dataframe()
```

Equal here — every order's customer necessarily has a feature row at that order's own timestamp, since the history was built from those same orders. That equality is a property of this construction, not a guarantee of the function.

### It is an inner join, and the rows it drops are the ones you care about

Ask for features *before* each customer's first order and the requests simply disappear.

```python
client.query(f"""
WITH cold AS (
  SELECT entity_id, TIMESTAMP_SUB(MIN(feature_timestamp), INTERVAL 1 DAY) AS time
  FROM `{PROJECT_ID}.{DATASET_ID}.fs_sparse`
  GROUP BY entity_id
)
SELECT (SELECT COUNT(*) FROM cold) AS requests,
       (SELECT COUNT(*) FROM ML.ENTITY_FEATURES_AT_TIME(
          TABLE `{PROJECT_ID}.{DATASET_ID}.fs_sparse`,
          (SELECT * FROM cold),
          num_rows => 1, ignore_feature_nulls => TRUE)) AS returned
""").to_dataframe()
```

Every request returns nothing. An entity with no feature history at or before its requested instant is **omitted**, not returned with NULL features — so the output is silently smaller than the input.

That matters because the dropped rows are not a random sample. They are precisely the cold-start cases: new customers, newly launched products, the first weeks of any entity's life. Dropping them makes a training set look cleaner and a model look better while removing the population the model will most often be asked about in production. If you need those rows, `LEFT JOIN` the entity table back onto the function's output and decide explicitly what a missing vector means.

---
## The same query with `%%bigquery` magics

The `%%bigquery` cell magic runs SQL directly and assigns the result to a pandas DataFrame — convenient for interactive work. Note that the magic does not interpolate Python variables into the SQL, so the identifiers are written out in full.

```sql
%%bigquery serving_vectors --project statmike-mlops-349915
SELECT entity_id, lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
FROM ML.FEATURES_AT_TIME(
  TABLE `statmike-mlops-349915.bq_ml.fs_sparse`,
  time => TIMESTAMP '2024-01-01',
  num_rows => 1,
  ignore_feature_nulls => TRUE)
ORDER BY lifetime_spend DESC
LIMIT 10
```

```python
serving_vectors
```

---
## The same query with BigFrames

[BigQuery DataFrames](https://cloud.google.com/bigquery/docs/bigquery-dataframes-introduction) offers a pandas-shaped API that compiles to BigQuery SQL. There is no BigFrames wrapper for these two table-valued functions, so the function call itself goes through `read_gbq` — after which the result is an ordinary lazy BigFrames DataFrame.

```python
import bigframes.pandas as bpd

bpd.close_session()
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

vectors = bpd.read_gbq(f"""
SELECT entity_id, lifetime_orders, lifetime_spend, last_ship_lag_h, last_delivery_lag_h
FROM ML.FEATURES_AT_TIME(
  TABLE `{PROJECT_ID}.{DATASET_ID}.fs_sparse`,
  time => TIMESTAMP '{CUTOFF}', num_rows => 1, ignore_feature_nulls => TRUE)
""")

print(f'{vectors.shape[0]:,} serving vectors, {vectors.shape[1]} columns')
vectors[['lifetime_orders', 'lifetime_spend']].describe().to_pandas()
```
