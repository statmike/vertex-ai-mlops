# Feature Store Workflow — What Point-in-Time Correctness Is Actually Worth

Every training row in a supervised model is a claim: *given what we knew at this moment, this is what happened next.* Building the feature side of that claim with a plain `GROUP BY` over the entity's whole history quietly breaks it — the features then describe a future the label has already happened in. This is **label leakage**, and it is the most common way a model that looks excellent offline turns out to be worthless in production.

This notebook does not argue that. It measures it, twice, on the same data and the same split:

- **Arm A — the tempting mistake.** Aggregate each customer's full order history with `GROUP BY user_id`, join it to every training row.
- **Arm B — point-in-time correct.** Retrieve each customer's feature vector as of *that specific order's* timestamp with `functions/feature_store` (`ML.ENTITY_FEATURES_AT_TIME`).

Then it asks the question that actually matters, which is not "which offline number is bigger": **what does the leaky model do when production hands it the only features it can really have?**

**The prediction problem.** One training row per order. Features as of the instant that order was placed. Label: *did this customer place another order within 90 days?*

**What this notebook establishes, all measured here:**

1. The two arms produce a large `roc_auc` gap — and the larger number is the wrong one.
2. The gap has a specific, exhibitable cause: the leaky feature *contains* the label. Measured as a correlation, as a group-mean difference, and as the model's own dominant weight.
3. Fed point-in-time features at serving time, the leaky model's advantage **evaporates entirely** — it lands where the honest model already was.
4. The honest model sits near chance, which is a real property of this dataset independently confirmed by `workflows/churn_retention` (`workflows/churn_retention/`) (`roc_auc` 0.531 → 0.544). That makes the leaky arm's headline number *entirely* manufactured — there is no real signal for it to have been an exaggeration of.
5. The identical feature-assembly logic serves the online vector with `ML.FEATURES_AT_TIME` — offline/online parity with no feature store to operate.

**Data:** [`bigquery-public-data.thelook_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-data/thelook-ecommerce).

**Related content:** `functions/feature_store` (`functions/feature_store/`) covers the two retrieval functions in detail — the table shapes, the arguments, and the failure modes. Read it first if the calls here look unfamiliar. `workflows/churn_retention` (`workflows/churn_retention/`) predicts a different label on the same orders; `workflows/cross_validation` (`workflows/cross_validation/`) uses the same deterministic hash-split idiom.

**References:** `reference/model-free-functions.md` (Full reference) | [`ML.ENTITY_FEATURES_AT_TIME`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-entity-feature-time) | [`ML.FEATURES_AT_TIME`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature-time) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No connection needed — everything runs inside BigQuery.

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

dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
dataset = bigquery.Dataset(dataset_ref)
dataset.location = LOCATION
client.create_dataset(dataset, exists_ok=True)
print(f'Dataset {PROJECT_ID}.{DATASET_ID} ready')

%load_ext bigquery_magics
```

Two settings that make the comparison trustworthy rather than merely plausible.

**A fixed cutoff.** `thelook_ecommerce` is a rolling dataset whose newest rows advance with the calendar, so every window below is pinned to fixed dates.

**The query cache turned off for every evaluation.** BigQuery's result cache keys on the query text, and `CREATE OR REPLACE MODEL` does not change the text of the `ML.EVALUATE` that follows it — so re-running this notebook can serve you the *previous* run's metrics for a model that has since been retrained. This bit during the build of this very notebook: after a retrain that had genuinely changed both arms, each one reported its *previous* run's `roc_auc` to four decimals — a stale pair of numbers that looked entirely plausible. It is documented with `ML.EVALUATE` in the `reference/model-lifecycle-functions.md#mlevaluate` (lifecycle-function reference) and worth defending against by default.

```python
CUTOFF     = '2024-01-01'  # feature history is built strictly before this instant
TRAIN_FROM = '2022-01-01'  # first order eligible to become a training row
TRAIN_TO   = '2023-09-30'  # last one, leaving room for its full 90-day label window
LABEL_DAYS = 90

# Never serve a cached ML.EVALUATE after CREATE OR REPLACE MODEL
NO_CACHE = bigquery.QueryJobConfig(use_query_cache=False)

def q(sql, no_cache=False):
    return client.query(sql, job_config=NO_CACHE if no_cache else None).to_dataframe()
```

---
## Step 1 — The label, and a split that both arms must share

One row per order placed in the training window. The label looks forward 90 days from that order and asks whether the same customer came back.

The split is a deterministic hash of `order_id`, not a random draw. That matters more than it usually does here: the two arms are separate `CREATE MODEL` statements, and if each drew its own random split the metric gap would be confounded by the split difference. A hash split guarantees both arms see byte-identical train and eval row sets, so the only thing that differs between them is how the features were built.

```python
client.query(f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.fsw_labeled` AS
WITH o AS (
  SELECT order_id, CAST(user_id AS STRING) AS entity_id, created_at
  FROM `bigquery-public-data.thelook_ecommerce.orders`
)
SELECT a.order_id,
       a.entity_id,
       a.created_at AS time,
       IF(EXISTS(SELECT 1 FROM o b
                 WHERE b.entity_id = a.entity_id
                   AND b.created_at >  a.created_at
                   AND b.created_at <= TIMESTAMP_ADD(a.created_at, INTERVAL {LABEL_DAYS} DAY)),
          1, 0) AS reordered_90d,
       MOD(ABS(FARM_FINGERPRINT(CAST(a.order_id AS STRING))), 10) >= 8 AS is_eval
FROM o a
WHERE a.created_at BETWEEN TIMESTAMP '{TRAIN_FROM}' AND TIMESTAMP '{TRAIN_TO}'
""").result()

q(f"""
SELECT COUNT(*) AS training_rows,
       COUNT(DISTINCT entity_id) AS customers,
       ROUND(AVG(reordered_90d), 4) AS base_rate,
       COUNTIF(NOT is_eval) AS train_rows,
       COUNTIF(is_eval) AS eval_rows
FROM `{PROJECT_ID}.{DATASET_ID}.fsw_labeled`
""")
```

An imbalanced binary problem with a low single-digit base rate — realistic for repeat purchase, and worth remembering when reading `roc_auc` later, since it is the metric least distorted by imbalance.

---
## Step 2 — One feature history, built once, used by both arms

The feature table below is the shared substrate. Each row records what became true about a customer at one instant, and nothing about any later instant — the running aggregates use `ROWS UNBOUNDED PRECEDING` over an ordering by event time, so no row can see its own future.

It is deliberately **sparse**: order events carry the purchase features, shipment and delivery events carry the fulfilment features, and each row is NULL everywhere it has nothing to say. That is the shape `functions/feature_store` (`functions/feature_store/`) works through in detail, and the reason `ignore_feature_nulls => TRUE` appears on every retrieval in this notebook.

Note that this table is *not* where the leakage comes from. Both arms read the same history. The leakage is introduced by *how it is queried*, which is the point.

```python
client.query(f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.fsw_history` AS
WITH ord AS (
  SELECT o.order_id, CAST(o.user_id AS STRING) AS entity_id,
         o.created_at, o.shipped_at, o.delivered_at, o.num_of_item,
         SUM(oi.sale_price) AS order_value
  FROM `bigquery-public-data.thelook_ecommerce.orders` o
  JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi USING (order_id)
  WHERE o.created_at < TIMESTAMP '{CUTOFF}'
  GROUP BY 1, 2, 3, 4, 5, 6
),
events AS (
  SELECT entity_id, created_at AS feature_timestamp,
         COUNT(*)               OVER w AS lifetime_orders,
         ROUND(SUM(order_value) OVER w, 2) AS lifetime_spend,
         ROUND(AVG(order_value) OVER w, 2) AS avg_order_value,
         SUM(num_of_item)       OVER w AS lifetime_items,
         TIMESTAMP_DIFF(created_at, LAG(created_at) OVER p, DAY) AS days_since_prev_order,
         CAST(NULL AS FLOAT64) AS last_ship_lag_h,
         CAST(NULL AS FLOAT64) AS last_delivery_lag_h
  FROM ord
  WINDOW w AS (PARTITION BY entity_id ORDER BY created_at ROWS UNBOUNDED PRECEDING),
         p AS (PARTITION BY entity_id ORDER BY created_at)
  UNION ALL
  SELECT entity_id, shipped_at, NULL, NULL, NULL, NULL, NULL,
         ROUND(TIMESTAMP_DIFF(shipped_at, created_at, MINUTE) / 60, 2), NULL
  FROM ord WHERE shipped_at IS NOT NULL
  UNION ALL
  SELECT entity_id, delivered_at, NULL, NULL, NULL, NULL, NULL, NULL,
         ROUND(TIMESTAMP_DIFF(delivered_at, shipped_at, MINUTE) / 60, 2)
  FROM ord WHERE delivered_at IS NOT NULL
)
SELECT entity_id, feature_timestamp,
       MAX(lifetime_orders)       AS lifetime_orders,
       MAX(lifetime_spend)        AS lifetime_spend,
       MAX(avg_order_value)       AS avg_order_value,
       MAX(lifetime_items)        AS lifetime_items,
       MAX(days_since_prev_order) AS days_since_prev_order,
       MAX(last_ship_lag_h)       AS last_ship_lag_h,
       MAX(last_delivery_lag_h)   AS last_delivery_lag_h
FROM events
GROUP BY entity_id, feature_timestamp
""").result()

q(f"""
SELECT COUNT(*) AS history_rows, COUNT(DISTINCT entity_id) AS customers,
       MIN(feature_timestamp) AS earliest, MAX(feature_timestamp) AS latest
FROM `{PROJECT_ID}.{DATASET_ID}.fsw_history`
""")
```

---
## Step 3 — Arm A: the tempting mistake

Here is the query almost everyone writes first. It is short, it reads naturally, and there is nothing in it that looks like a bug:

```sql
SELECT entity_id, MAX(lifetime_orders) AS lifetime_orders, ...
FROM feature_history
GROUP BY entity_id          -- <-- no time bound anywhere
```

One row per customer, summarizing *everything ever known about them*, joined onto every training row. The training row for an order placed in March 2022 receives features computed from orders placed in 2023.

```python
client.query(f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.fsw_arm_leaky` AS
WITH all_history AS (
  SELECT entity_id,
         MAX(lifetime_orders)       AS lifetime_orders,
         MAX(lifetime_spend)        AS lifetime_spend,
         AVG(avg_order_value)       AS avg_order_value,
         MAX(lifetime_items)        AS lifetime_items,
         AVG(days_since_prev_order) AS days_since_prev_order,
         AVG(last_ship_lag_h)       AS last_ship_lag_h,
         AVG(last_delivery_lag_h)   AS last_delivery_lag_h
  FROM `{PROJECT_ID}.{DATASET_ID}.fsw_history`
  GROUP BY entity_id
)
SELECT l.order_id, l.is_eval, l.reordered_90d, h.* EXCEPT (entity_id)
FROM `{PROJECT_ID}.{DATASET_ID}.fsw_labeled` l
JOIN all_history h USING (entity_id)
""").result()

q(f"SELECT COUNT(*) AS rows_built FROM `{PROJECT_ID}.{DATASET_ID}.fsw_arm_leaky`")
```

---
## Step 4 — Arm B: point-in-time correct

Same history, same training rows, same feature names. The difference is that the retrieval is anchored to each order's own timestamp, which is what the entity table's `time` column supplies.

Two mechanics from `functions/feature_store` (`functions/feature_store/`) apply directly and are easy to get wrong:

- The entity table's **extra columns are dropped** — only `entity_id` and the requested time come back. The label is an extra column, so it has to be joined back on, here using `(entity_id, feature_timestamp)` since the function returns the requested instant in `feature_timestamp`.
- The join is an **inner** join. Any order whose customer has no feature row at or before that instant would silently vanish. The row count below is the check, not a formality.

One production constraint that does not bite at this scale but will at yours: the entity time relation is documented as capped at **100 MB**. That is `entity_id` plus `time` and nothing else, so it goes a long way — but a training set of tens of millions of labeled events will exceed it, and the fix is to partition the build by time window or entity range and `UNION ALL` the pieces.

```python
client.query(f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.fsw_arm_correct` AS
SELECT l.order_id, l.is_eval, l.reordered_90d,
       f.lifetime_orders, f.lifetime_spend, f.avg_order_value, f.lifetime_items,
       f.days_since_prev_order, f.last_ship_lag_h, f.last_delivery_lag_h
FROM ML.ENTITY_FEATURES_AT_TIME(
       TABLE `{PROJECT_ID}.{DATASET_ID}.fsw_history`,
       (SELECT entity_id, time FROM `{PROJECT_ID}.{DATASET_ID}.fsw_labeled`),
       num_rows => 1, ignore_feature_nulls => TRUE) f
JOIN `{PROJECT_ID}.{DATASET_ID}.fsw_labeled` l
  ON l.entity_id = f.entity_id AND l.time = f.feature_timestamp
""").result()

q(f"""
SELECT (SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.fsw_labeled`)     AS labeled_rows,
       (SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.fsw_arm_correct`) AS arm_b_rows,
       (SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.fsw_arm_leaky`)   AS arm_a_rows
""")
```

All three equal, so no rows were lost and the two arms are genuinely row-for-row comparable. That equality is a property of this construction — the history was built from the same orders, so every order's customer necessarily has a feature row at that exact instant — and not something the function guarantees in general.

Before training, look at what actually differs between the two feature tables for the same customer.

```python
q(f"""
SELECT 'Arm A — all-history (leaky)' AS arm, ROUND(AVG(lifetime_orders), 3) AS mean_lifetime_orders,
       ROUND(AVG(lifetime_spend), 2) AS mean_lifetime_spend
FROM `{PROJECT_ID}.{DATASET_ID}.fsw_arm_leaky`
UNION ALL
SELECT 'Arm B — as-of the order (correct)', ROUND(AVG(lifetime_orders), 3), ROUND(AVG(lifetime_spend), 2)
FROM `{PROJECT_ID}.{DATASET_ID}.fsw_arm_correct`
ORDER BY arm
""")
```

Arm A's customers look busier and richer than Arm B's, on identical rows. Nothing was fabricated — those orders are real. They just had not happened yet at the moment each training row is supposed to describe.

---
## Step 5 — Train both arms, identically

`data_split_method='NO_SPLIT'` on the pre-filtered training rows, so BigQuery ML does no splitting of its own and the hash split from Step 1 is the only one in play. Evaluation is then an explicit call against the held-out table.

```python
for arm in ['correct', 'leaky']:
    client.query(f"""
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.fsw_model_{arm}`
    OPTIONS(model_type='LOGISTIC_REG',
            input_label_cols=['reordered_90d'],
            data_split_method='NO_SPLIT',
            enable_global_explain=FALSE) AS
    SELECT * EXCEPT (order_id, is_eval)
    FROM `{PROJECT_ID}.{DATASET_ID}.fsw_arm_{arm}`
    WHERE NOT is_eval
    """).result()
    print(f'Trained fsw_model_{arm}')
```

---
## Step 6 — The measured gap

Each model scored on its own held-out rows — which is exactly the number that would be reported in a model card or a launch review.

```python
q(f"""
SELECT 'Arm A — all-history (leaky)' AS arm,
       ROUND(roc_auc, 4) AS roc_auc, ROUND(log_loss, 4) AS log_loss
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.fsw_model_leaky`,
                 (SELECT * EXCEPT (order_id, is_eval)
                  FROM `{PROJECT_ID}.{DATASET_ID}.fsw_arm_leaky` WHERE is_eval))
UNION ALL
SELECT 'Arm B — as-of the order (correct)',
       ROUND(roc_auc, 4), ROUND(log_loss, 4)
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.fsw_model_correct`,
                 (SELECT * EXCEPT (order_id, is_eval)
                  FROM `{PROJECT_ID}.{DATASET_ID}.fsw_arm_correct` WHERE is_eval))
ORDER BY arm
""", no_cache=True)
```

A very large gap, in the direction that gets a model shipped. Arm A would sail through review; Arm B looks like a failed project. Every instinct trained on offline metrics says Arm A is the better model.

It is not a better model. It is the same model, given the answer.

---
## Step 7 — Where that number came from

The mechanism is worth exhibiting rather than asserting, because "leakage" is otherwise an accusation you cannot check. Take the single feature `lifetime_orders` and compare its two versions against the label.

```python
q(f"""
SELECT 'Arm A — all-history (leaky)' AS feature_version,
       ROUND(CORR(lifetime_orders, reordered_90d), 4) AS corr_with_label,
       ROUND(AVG(IF(reordered_90d = 1, lifetime_orders, NULL)), 2) AS mean_if_reordered,
       ROUND(AVG(IF(reordered_90d = 0, lifetime_orders, NULL)), 2) AS mean_if_not
FROM `{PROJECT_ID}.{DATASET_ID}.fsw_arm_leaky`
UNION ALL
SELECT 'Arm B — as-of the order (correct)',
       ROUND(CORR(lifetime_orders, reordered_90d), 4),
       ROUND(AVG(IF(reordered_90d = 1, lifetime_orders, NULL)), 2),
       ROUND(AVG(IF(reordered_90d = 0, lifetime_orders, NULL)), 2)
FROM `{PROJECT_ID}.{DATASET_ID}.fsw_arm_correct`
ORDER BY feature_version
""", no_cache=True)
```

There it is, in one line. Measured **as of the order**, a customer's order count tells you essentially nothing about whether they will come back — the two group means are barely apart and the correlation rounds to near zero. Measured **over all history**, reorderers have a visibly higher total order count.

Of course they do. If a customer reordered within 90 days, that reorder is one of the orders being counted. The all-history feature does not *predict* the label, it *contains* it. And a linear model is very good at finding that.

```python
q(f"""
SELECT processed_input AS feature, ROUND(weight, 4) AS weight
FROM ML.WEIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.fsw_model_leaky`)
ORDER BY ABS(weight) DESC
""", no_cache=True)
```

The model agrees. Setting the intercept aside, `lifetime_orders` carries a weight an order of magnitude above every other feature — it learned to read the answer and largely ignored the rest of the vector.

---
## Step 8 — What production actually does to the leaky model

This is the step that turns the previous ones from a methodological point into a cost.

At serving time there is no "all history." A customer's future orders have not happened. The only feature vector that can exist is the point-in-time one — so the model trained on Arm A features will be scored on Arm B features whether anyone planned for that or not.

Simulate exactly that: same leaky model, same eval rows, features rebuilt as-of.

```python
q(f"""
SELECT 'Arm A model, leaky features (the offline claim)' AS scenario,
       ROUND(roc_auc, 4) AS roc_auc
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.fsw_model_leaky`,
                 (SELECT * EXCEPT (order_id, is_eval)
                  FROM `{PROJECT_ID}.{DATASET_ID}.fsw_arm_leaky` WHERE is_eval))
UNION ALL
SELECT 'Arm A model, as-of features (production reality)',
       ROUND(roc_auc, 4)
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.fsw_model_leaky`,
                 (SELECT * EXCEPT (order_id, is_eval)
                  FROM `{PROJECT_ID}.{DATASET_ID}.fsw_arm_correct` WHERE is_eval))
UNION ALL
SELECT 'Arm B model, as-of features (honest all along)',
       ROUND(roc_auc, 4)
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.fsw_model_correct`,
                 (SELECT * EXCEPT (order_id, is_eval)
                  FROM `{PROJECT_ID}.{DATASET_ID}.fsw_arm_correct` WHERE is_eval))
ORDER BY roc_auc DESC
""", no_cache=True)
```

The leaky model's advantage does not shrink. It **disappears**, landing essentially where the honest model already was — because the feature it was relying on no longer contains anything.

That is the real cost of leakage, and it is not the inflated metric. It is that the inflated metric bought nothing: months of work, a model card, a launch decision, and a production system whose measured quality is the same as the model that looked like a failure. The honest arm was never worse. It was the only one reporting the truth.

**On the honest arm being near chance.** It is worth resisting the urge to rescue that number. Repeat purchase in this dataset is close to unpredictable from order history, which `workflows/churn_retention` (`workflows/churn_retention/`) independently found while predicting a different label on these same orders (`roc_auc` 0.531 → 0.544 even after substantially enriching the features). That agreement makes this demonstration cleaner rather than weaker: with no real signal available, **every point of the leaky arm's advantage is manufactured**, and none of it can be argued to be an exaggeration of something genuine.

---
## Step 9 — Serving: the same features, one call, no feature store

The offline/online parity problem is that training-time and serving-time features are usually assembled by two different pieces of code, which drift apart. Here they are two calls to the same family, against the same table, with the same arguments.

Training asked for a different instant per row, so it used `ML.ENTITY_FEATURES_AT_TIME`. Serving asks for one instant shared by everyone — *now* — so it uses `ML.FEATURES_AT_TIME`. Nothing else changes, including `ignore_feature_nulls => TRUE`, which is required by the sparse shape of the history in both cases.

```python
client.query(f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.fsw_serving` AS
SELECT * FROM ML.FEATURES_AT_TIME(
  TABLE `{PROJECT_ID}.{DATASET_ID}.fsw_history`,
  time => TIMESTAMP '{CUTOFF}', num_rows => 1, ignore_feature_nulls => TRUE)
""").result()

q(f"""
SELECT COUNT(*) AS customers_served,
       COUNTIF(lifetime_orders IS NULL) AS missing_order_count
FROM `{PROJECT_ID}.{DATASET_ID}.fsw_serving`
""")
```

Column-for-column, this is the vector the model was trained on. Score it with the honest model.

```python
q(f"""
SELECT entity_id, lifetime_orders, lifetime_spend,
       ROUND(predicted_reordered_90d_probs[OFFSET(0)].prob, 4) AS p_reorder
FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.fsw_model_correct`,
                TABLE `{PROJECT_ID}.{DATASET_ID}.fsw_serving`)
ORDER BY p_reorder DESC
LIMIT 10
""", no_cache=True)
```

That is the whole serving path: a feature history table, one function call, and `ML.PREDICT`. No feature store to provision, no online store to keep in sync, no separate serving code to drift.

The honest caveat, given Step 8: this model's ranking is close to uninformative on this dataset, so the ordering above should not be read as a targeting list. What the step demonstrates is the *mechanism* — that the same feature definitions reach training and serving without being written twice, which is the property a feature store exists to provide and the one worth keeping when you do not have one.
