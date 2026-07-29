# Churn / Retention — BigQuery ML

Define churn from **real order-history gaps** — not a synthetic label — then engineer features, train a classifier, evaluate it honestly, and identify the real drivers. Reuses `workflows/customer_segmentation` (`workflows/customer_segmentation/`)'s dataset for narrative continuity: same customers, same time window, a related business question.

**Models used:** `BOOSTED_TREE_CLASSIFIER`
**Functions used:** `ML.EVALUATE`, `ML.CONFUSION_MATRIX`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`, `ML.EXPLAIN_PREDICT`

`BOOSTED_TREE_CLASSIFIER`'s own mechanics (confusion matrix, ROC curve, `TRANSFORM`, exporting/visualizing a tree) are already covered in depth in `models/boosted_tree_classifier` (`models/boosted_tree_classifier/`) and not repeated here — **this workflow's real content is the label definition, feature engineering, and honest evaluation.**

**Data:** [`bigquery-public-data.thelook_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) (`orders`, `order_items`, `users`).

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
## Step 1 — Define churn from a fixed feature cutoff + forward label window

**Feature cutoff:** `2024-01-01` (matches `workflows/customer_segmentation` (`customer_segmentation`)). **Label window:** the following 180 days (through `2024-06-29`). A customer who ordered *before* the cutoff but placed **no order in the label window** is labeled `churned = TRUE`.

Both dates are far enough in the past (this notebook is being run well after `2024-06-29`) that this is **real observed history**, not a simulated forward projection — a genuine backtest, not a synthetic label.

```python
query = """
CREATE OR REPLACE TABLE `{project}.{dataset}.churn_retention_features` AS
WITH order_value AS (
  SELECT order_id, user_id, SUM(sale_price) AS order_total,
         COUNT(DISTINCT product_id) AS n_products,
         MAX(CASE WHEN returned_at IS NOT NULL THEN 1 ELSE 0 END) AS had_return
  FROM `bigquery-public-data.thelook_ecommerce.order_items`
  GROUP BY order_id, user_id
),
rfm AS (
  SELECT
    o.user_id,
    DATE_DIFF(DATE '2024-01-01', MAX(DATE(o.created_at)), DAY) AS recency_days,
    COUNT(DISTINCT o.order_id) AS frequency,
    SUM(ov.order_total) AS monetary,
    SUM(ov.order_total) / COUNT(DISTINCT o.order_id) AS avg_order_value,
    SUM(ov.n_products) AS distinct_products,
    AVG(ov.had_return) AS return_rate
  FROM `bigquery-public-data.thelook_ecommerce.orders` o
  JOIN order_value ov USING (order_id, user_id)
  WHERE o.created_at < '2024-01-01'
  GROUP BY o.user_id
),
future_activity AS (
  SELECT DISTINCT user_id
  FROM `bigquery-public-data.thelook_ecommerce.orders`
  WHERE created_at >= '2024-01-01' AND created_at < '2024-06-29'
)
SELECT
  r.*, u.age, u.gender, u.traffic_source,
  DATE_DIFF(DATE '2024-01-01', DATE(u.created_at), DAY) AS tenure_days,
  fa.user_id IS NULL AS churned
FROM rfm r
JOIN `bigquery-public-data.thelook_ecommerce.users` u ON r.user_id = u.id
LEFT JOIN future_activity fa USING (user_id)
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()

query = f"""
SELECT
  COUNTIF(churned) AS n_churned,
  COUNTIF(NOT churned) AS n_retained,
  ROUND(AVG(CAST(churned AS INT64)), 3) AS churn_rate
FROM `{PROJECT_ID}.{DATASET_ID}.churn_retention_features`
"""
client.query(query).to_dataframe()
```

**91.2% of customers churned.** The extreme imbalance is itself a real finding for this dataset: most customers never place a second order at all, regardless of any feature — consistent with the ~1.3 orders/customer average already seen in `customer_segmentation`.

---
## Step 2 — Baseline: `BOOSTED_TREE_CLASSIFIER` on RFM features alone

With a 91% base churn rate, a model that always predicts "churned" gets 91% accuracy while being completely useless. **`auto_class_weights = TRUE`** forces the model to actually learn the minority (retained) class instead of exploiting the imbalance.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.churn_retention_baseline`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['churned'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT recency_days, frequency, monetary, churned
FROM `{project}.{dataset}.churn_retention_features`
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model churn_retention_baseline created')
```

```python
query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.churn_retention_baseline`)"
client.query(query).to_dataframe()
```

**`roc_auc` ≈ 0.53 — barely above random (0.5).** Recency/frequency/monetary from a single snapshot do not meaningfully separate churners from retained customers in this dataset. Precision looks deceptively high (~0.92) only because the model is right whenever it (correctly, and often) predicts the majority class.

---
## Step 3 — Richer feature engineering: behavior + demographics

Add average order value, distinct products purchased, return rate (from `order_items`), and account age plus demographics (from `users`) — signals a bare RFM table can't see.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.churn_retention_model`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['churned'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT',
  enable_global_explain = TRUE
) AS
SELECT recency_days, frequency, monetary, avg_order_value, distinct_products,
       return_rate, age, gender, traffic_source, tenure_days, churned
FROM `{project}.{dataset}.churn_retention_features`
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model churn_retention_model created')
```

```python
query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.churn_retention_model`)"
client.query(query).to_dataframe()
```

**Honest finding, worth stating plainly rather than glossing over:** accuracy (0.49 → 0.60), recall (0.48 → 0.61), and F1 (0.64 → 0.73) all improve meaningfully with the richer feature set — but **`roc_auc` barely moves (0.531 → 0.544)**. This isn't a contradiction: `roc_auc` measures the model's *ranking* quality across every possible probability threshold, while accuracy/recall/F1 are all read off a single fixed 0.5 cutoff. Richer features can shift *where* predicted probabilities land relative to 0.5 — improving the fixed-threshold metrics — without meaningfully improving how well the model *ranks* churners above non-churners overall, which is what `roc_auc` captures. No single metric tells the whole story here. The practical takeaway: this synthetic e-commerce generator simply does not encode a strong *individual-level* churn signal in transaction history alone. A real production churn model would typically need richer behavioral signal — browsing/session data, email engagement, support tickets — than a transaction log by itself provides.

`ML.CONFUSION_MATRIX` on the richer model shows exactly how that 0.605 recall breaks down: of 5,056 real churners, it correctly flags 3,059 (the `expected_label=true, TRUE` cell) and misses 1,997 — recall on the **churned** class (`TRUE`), matching `ML.EVALUATE`'s figure exactly. The 234 false positives on the retained class are the real cost of that improved catch rate.

```python
query = f"SELECT * FROM ML.CONFUSION_MATRIX(MODEL `{PROJECT_ID}.{DATASET_ID}.churn_retention_model`)"
client.query(query).to_dataframe()
```

---
## Step 4 — `ML.GLOBAL_EXPLAIN` + `ML.FEATURE_IMPORTANCE`: what actually drives the model

`ML.GLOBAL_EXPLAIN` requires `enable_global_explain = TRUE` at training time (set above). Full mechanics of both functions are covered in `models/boosted_tree_classifier` (`models/boosted_tree_classifier/`) — here we just read the result.

```python
query = f"SELECT * FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJECT_ID}.{DATASET_ID}.churn_retention_model`) ORDER BY attribution DESC"
client.query(query).to_dataframe()
```

**`tenure_days` (how long someone has been a customer) is the single dominant driver** — more important than any of the three original RFM features. `frequency` is second.

```python
query = f"SELECT * FROM ML.FEATURE_IMPORTANCE(MODEL `{PROJECT_ID}.{DATASET_ID}.churn_retention_model`) ORDER BY importance_gain DESC"
client.query(query).to_dataframe()
```

`ML.FEATURE_IMPORTANCE`'s ranking (by `importance_gain`, the average loss reduction the feature contributes when it's used to split) doesn't match `ML.GLOBAL_EXPLAIN`'s ranking (by Shapley-style `attribution`) — `return_rate` jumps from 8th-of-9 by attribution to 3rd by gain, while `recency_days` drops from 3rd to 5th. These measure genuinely different things: `importance_gain` reflects how useful a feature is *when the tree chooses to split on it* (a feature used rarely but decisively, like `return_rate` at only `importance_weight=4`, can still have high average gain), while `attribution` reflects the feature's typical contribution *across all predictions*, split frequency included. Neither ranking is "more correct" — they answer different questions ("how much does this feature matter each time it's used?" vs. "how much does this feature matter on average across customers?").

---
## Step 5 — `ML.EXPLAIN_PREDICT`: per-customer driver attribution

Global importance says what matters *on average*; `ML.EXPLAIN_PREDICT` says what mattered for *this specific customer* — the level of detail an actual retention campaign would act on.

```python
query = f"""
SELECT
  predicted_churned,
  top_feature_attributions
FROM ML.EXPLAIN_PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.churn_retention_model`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.churn_retention_features` LIMIT 5),
  STRUCT(3 AS top_k_features)
)
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Tie back to `customer_segmentation`: does loyalty actually reduce churn risk?

`workflows/customer_segmentation` (`customer_segmentation`)'s KMEANS segments are driven jointly by recency, frequency, *and* monetary value — there's no single hard cutoff separating them. As a simple proxy for its "loyal regulars"/"champions" segments (both averaging 2+ orders) vs. its "recent, low-value" and "lapsed" segments (both averaging 1 order), split customers by order count alone: does 2+ orders actually predict lower churn?

```python
query = f"""
SELECT
  CASE WHEN frequency = 1 THEN '1 order' ELSE '2+ orders' END AS frequency_group,
  COUNT(*) AS n_customers,
  ROUND(AVG(CAST(churned AS INT64)), 3) AS churn_rate
FROM `{PROJECT_ID}.{DATASET_ID}.churn_retention_features`
GROUP BY frequency_group
ORDER BY frequency_group
"""
client.query(query).to_dataframe()
```

**A genuinely useful, slightly deflating finding:** 1-order customers churn at 91.6%; repeat customers (2+ orders) still churn at 90.0% — barely lower. In this dataset, having already placed a second order does **not** meaningfully protect against churn. This helps explain why the classifier's `roc_auc` stays low even with richer features: the signal genuinely is weak, not just poorly engineered.

---
## Related content

- `models/boosted_tree_classifier` (`models/boosted_tree_classifier/`) — the algorithm mechanics in depth: `ML.CONFUSION_MATRIX`, `ML.ROC_CURVE`, exporting/visualizing a tree, the `TRANSFORM` clause.
- `workflows/customer_segmentation` (`workflows/customer_segmentation/`) — the shared dataset and RFM feature engineering this workflow builds on.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT * FROM ML.GLOBAL_EXPLAIN(MODEL `statmike-mlops-349915.bq_ml.churn_retention_model`)
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

df = bpd.read_gbq(f"SELECT recency_days, frequency, monetary, avg_order_value, distinct_products, return_rate, age, gender, traffic_source, tenure_days, churned FROM `{PROJECT_ID}.{DATASET_ID}.churn_retention_features`")
X = df.drop(columns=['churned'])
y = df['churned']

model = XGBClassifier()
model.fit(X, y)
model.predict(X).peek()
```
