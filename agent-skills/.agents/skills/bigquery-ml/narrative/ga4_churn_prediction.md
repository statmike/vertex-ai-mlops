# GA4 Churn Prediction — BigQuery ML

Define churn from **real first-party engagement behavior** — a Google Analytics 4 event export — rather than order history. Engineer features from each user's first 7 days of activity, label churn from a real observed 30-day forward window, train a classifier, and identify the real drivers. A genuine complement to `workflows/churn_retention` (`workflows/churn_retention/`)'s order-lapse-based churn definition: same business question, a completely different dataset and signal.

**Models used:** `BOOSTED_TREE_CLASSIFIER`
**Functions used:** `ML.EVALUATE`, `ML.CONFUSION_MATRIX`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, `ML.EXPLAIN_PREDICT`

`BOOSTED_TREE_CLASSIFIER`'s own mechanics are already covered in depth in `models/boosted_tree_classifier` (`models/boosted_tree_classifier/`) and not repeated here — **this workflow's real content is the cohort/label definition, behavioral feature engineering, and honest evaluation.**

**Data:** [`bigquery-public-data.ga4_obfuscated_sample_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — a real GA4 export from the Google Merchandise Store, 2020-11-01 through 2021-01-31 (92 days).

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (BOOSTED_TREE_CLASSIFIER) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-boosted-tree) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No connection needed.

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

---
## Step 1 — Cohort + feature window (first 7 days) + label window (next 30 days)

**Cohort:** users whose first-ever event falls between `2020-11-01` and `2020-12-24` — chosen so every cohort member's 30-day label window (`first_date + 7` through `first_date + 36`) completes on or before `2021-01-31`, the last day in the dataset. **Feature window:** each user's first 7 days of activity. **Label window:** the following 30 days — a user with no events in that window is labeled `churned = TRUE`.

This is real observed history end-to-end (the dataset is a static historical export), not a simulated forward projection — a genuine backtest.

```python
query = """
CREATE OR REPLACE TABLE `{project}.{dataset}.ga4_churn_prediction_features` AS
WITH events AS (
  SELECT
    user_pseudo_id,
    PARSE_DATE('%Y%m%d', event_date) AS event_date,
    event_name,
    device.category AS device_category,
    geo.country AS country,
    traffic_source.medium AS traffic_medium,
    (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec') AS engagement_time_msec
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
),
first_visit AS (
  SELECT user_pseudo_id, MIN(event_date) AS first_date
  FROM events
  GROUP BY user_pseudo_id
  HAVING first_date BETWEEN '2020-11-01' AND '2020-12-24'
),
feature_window AS (
  SELECT e.*, f.first_date
  FROM events e
  JOIN first_visit f USING (user_pseudo_id)
  WHERE e.event_date BETWEEN f.first_date AND DATE_ADD(f.first_date, INTERVAL 6 DAY)
),
label_window AS (
  SELECT DISTINCT e.user_pseudo_id
  FROM events e
  JOIN first_visit f USING (user_pseudo_id)
  WHERE e.event_date BETWEEN DATE_ADD(f.first_date, INTERVAL 7 DAY) AND DATE_ADD(f.first_date, INTERVAL 36 DAY)
)
SELECT
  fw.user_pseudo_id,
  ANY_VALUE(fw.device_category) AS device_category,
  ANY_VALUE(fw.country) AS country,
  ANY_VALUE(fw.traffic_medium) AS traffic_medium,
  COUNT(*) AS n_events,
  COUNT(DISTINCT fw.event_date) AS n_active_days,
  COUNTIF(fw.event_name = 'page_view') AS n_page_view,
  COUNTIF(fw.event_name = 'view_item') AS n_view_item,
  COUNTIF(fw.event_name = 'add_to_cart') AS n_add_to_cart,
  COUNTIF(fw.event_name = 'begin_checkout') AS n_begin_checkout,
  COUNTIF(fw.event_name = 'session_start') AS n_sessions,
  COUNTIF(fw.event_name = 'purchase') > 0 AS did_purchase,
  IFNULL(SUM(fw.engagement_time_msec), 0) AS total_engagement_time_msec,
  lw.user_pseudo_id IS NULL AS churned
FROM feature_window fw
LEFT JOIN label_window lw USING (user_pseudo_id)
GROUP BY fw.user_pseudo_id, lw.user_pseudo_id
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()

query = f"""
SELECT
  COUNTIF(churned) AS n_churned,
  COUNTIF(NOT churned) AS n_retained,
  ROUND(AVG(CAST(churned AS INT64)), 3) AS churn_rate
FROM `{PROJECT_ID}.{DATASET_ID}.ga4_churn_prediction_features`
"""
client.query(query).to_dataframe()
```

**94.3% of the cohort churned** — an even more extreme imbalance than `churn_retention`'s 91.2%. Most first-time visitors to the Google Merchandise Store never come back within 30 days, regardless of what they did in their first week.

---
## Step 2 — Baseline: `BOOSTED_TREE_CLASSIFIER` on behavioral counts alone

With a 94% base churn rate, a model that always predicts "churned" gets 94% accuracy while being completely useless. **`auto_class_weights = TRUE`** forces the model to actually learn the minority (retained) class.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.ga4_churn_prediction_baseline`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['churned'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart,
       n_begin_checkout, n_sessions, did_purchase, churned
FROM `{project}.{dataset}.ga4_churn_prediction_features`
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model ga4_churn_prediction_baseline created')
```

```python
query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.ga4_churn_prediction_baseline`)"
client.query(query).to_dataframe()
```

**`roc_auc` ≈ 0.74** — already far stronger than `churn_retention`'s RFM baseline (`roc_auc` ≈ 0.53). First-week engagement behavior is a much more individually-informative churn signal than a snapshot of past order history alone.

---
## Step 3 — Richer feature engineering: + device/geo/traffic/engagement time

Add device category, country, traffic medium, and total engagement time from the same first-7-days window — signals the behavioral counts alone can't see.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.ga4_churn_prediction_model`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['churned'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart,
       n_begin_checkout, n_sessions, did_purchase, device_category, country,
       traffic_medium, total_engagement_time_msec, churned
FROM `{project}.{dataset}.ga4_churn_prediction_features`
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model ga4_churn_prediction_model created')
```

```python
query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.ga4_churn_prediction_model`)"
client.query(query).to_dataframe()
```

**Honest finding — the mirror image of `churn_retention`'s:** there, richer features improved the fixed-threshold metrics (accuracy/recall/F1) while `roc_auc` barely moved. Here, **`roc_auc` improves meaningfully (0.744 → 0.771)** while accuracy, recall, and F1 all move slightly the *other* way (0.731→0.718, 0.733→0.717, 0.837→0.827). Device/geo/traffic/engagement-time features shift the model's overall *ranking* of churners above non-churners (what `roc_auc` measures) without improving how many of those rankings land on the correct side of the default 0.5 cutoff. Neither metric is "wrong" here — they answer different questions, and a real deployment would tune the decision threshold rather than read fixed-cutoff metrics at face value.

> `BOOSTED_TREE_CLASSIFIER` training carries a small amount of run-to-run variation even with identical data and options — exact figures may drift slightly on a rerun, but the direction and rough size of the contrast with `churn_retention` is the durable finding.

```python
query = f"SELECT * FROM ML.CONFUSION_MATRIX(MODEL `{PROJECT_ID}.{DATASET_ID}.ga4_churn_prediction_model`)"
client.query(query).to_dataframe()
```

---
## Step 4 — `ML.GLOBAL_EXPLAIN` + `ML.FEATURE_IMPORTANCE`: what actually drives the model

`ML.GLOBAL_EXPLAIN` requires `enable_global_explain = TRUE` at training time (set above). Full mechanics of both functions are covered in `models/boosted_tree_classifier` (`models/boosted_tree_classifier/`) — here we just read the result.

```python
query = f"SELECT * FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.ga4_churn_prediction_model`) ORDER BY attribution DESC"
client.query(query).to_dataframe()
```

**`n_events` dominates** (attribution ≈ 0.22 — three times the next feature, `n_sessions` ≈ 0.074). **`did_purchase` has attribution ≈ 0.0**: once `n_events`/`n_active_days`/`n_sessions` are in the model, whether a user purchased in week 1 adds no independent signal — its information is fully subsumed by the broader activity-volume features.

```python
query = f"SELECT * FROM ML.FEATURE_IMPORTANCE(MODEL `{PROJECT_ID}.{DATASET_ID}.ga4_churn_prediction_model`) ORDER BY importance_gain DESC"
client.query(query).to_dataframe()
```

Unlike `churn_retention` (where `ML.GLOBAL_EXPLAIN` and `ML.FEATURE_IMPORTANCE` rankings diverged sharply), here the two **mostly agree** — `n_events`, `n_active_days`, `n_sessions` top both lists, and `did_purchase` is last in both (`importance_weight = 0`: the tree never once splits on it).

---
## Step 5 — `ML.EXPLAIN_PREDICT`: per-user driver attribution

Global importance says what matters *on average*; `ML.EXPLAIN_PREDICT` says what mattered for *this specific user* — the level of detail an actual retention campaign would act on.

```python
query = f"""
SELECT
  predicted_churned,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.ga4_churn_prediction_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ga4_churn_prediction_features` LIMIT 5),
  STRUCT(3 AS top_k_features)
)
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Tie back to `churn_retention`: does early purchase behavior protect against churn here the way order frequency didn\'t there?

```python
query = f"""
SELECT
  did_purchase,
  COUNT(*) AS n_users,
  ROUND(AVG(CAST(churned AS INT64)), 3) AS churn_rate
FROM `{PROJECT_ID}.{DATASET_ID}.ga4_churn_prediction_features`
GROUP BY did_purchase
ORDER BY did_purchase
"""
client.query(query).to_dataframe()
```

**A genuinely different, stronger finding than `churn_retention`'s:** users who purchase in their first week churn at **73.2%**; users who don\'t churn at **94.6%** — a 21-point gap. Contrast with `churn_retention`'s finding that 2+ orders barely reduced churn risk (91.6% vs. 90.0%, a 1.6-point gap): early purchase *intent* is a much stronger churn signal here than repeat-purchase *history* was there. Two genuinely different datasets and two genuinely different (and both honest) answers to a similar-sounding question — not a contradiction, a reminder that "does loyalty reduce churn" depends entirely on what signal is available and what churn window is being predicted.

---
## Related content

- `models/boosted_tree_classifier` (`models/boosted_tree_classifier/`) — the algorithm mechanics in depth: `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, exporting/visualizing a tree, the `TRANSFORM` clause.
- `workflows/churn_retention` (`workflows/churn_retention/`) — the complementary order-lapse-based churn technique, and the contrasting finding referenced in Step 6.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT * FROM ML.GLOBAL_EXPLAIN(MODEL `statmike-mlops-349915.bq_ml.ga4_churn_prediction_model`)
ORDER BY attribution DESC
```

---
## Examples — BigFrames

`bigframes.ml.ensemble.XGBClassifier` maps to `BOOSTED_TREE_CLASSIFIER` (already verified in `models/boosted_tree_classifier/`).

```python
import bigframes.pandas as bpd
from bigframes.ml.ensemble import XGBClassifier

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

df = bpd.read_gbq(f"SELECT n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart, n_begin_checkout, n_sessions, did_purchase, device_category, country, traffic_medium, total_engagement_time_msec, churned FROM `{PROJECT_ID}.{DATASET_ID}.ga4_churn_prediction_features`")
X = df.drop(columns=['churned'])
y = df['churned']

model = XGBClassifier()
model.fit(X, y)
model.predict(X).peek()
```
