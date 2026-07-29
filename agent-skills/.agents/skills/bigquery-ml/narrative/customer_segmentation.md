# Customer Segmentation — BigQuery ML

Segment customers into actionable business groups using **RFM (Recency/Frequency/Monetary)** features engineered from raw order history, then `KMEANS` clustering. Contrast with `models/kmeans` (`models/kmeans/`)'s `penguins` mechanism demo: this is the real business-clustering version, on real e-commerce order data, with a genuine "what do we do about each segment" payoff.

**Models used:** `KMEANS`
**Functions used:** `ML.STANDARD_SCALER`, `ML.EVALUATE`, `ML.CENTROIDS`, `ML.PREDICT`

**This workflow's real content is feature engineering**, same spirit as `workflows/regression_based_forecasting` (`workflows/regression_based_forecasting/`): turning raw `(user, order, order_item)` rows into one row per customer with three engineered signals — how recently they last ordered, how often they order, and how much they spend. `KMEANS`'s own mechanics (training, `ML.EVALUATE`, non-determinism, tuning `num_clusters`) are already covered in depth in `models/kmeans/` and not repeated here.

**Data:** [`bigquery-public-data.thelook_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) (`orders`, `order_items`) — real e-commerce order history. Analysis uses a **fixed cutoff date (`2024-01-01`)** rather than `CURRENT_DATE()`, so results don't silently shift every time this notebook is re-run in the future.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (KMEANS) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-kmeans) | `setup` (Setup guide)

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
## Step 1 — RFM feature engineering from raw order history

For every customer with at least one order before the analysis cutoff: **Recency** (days since their most recent order), **Frequency** (distinct order count), **Monetary** (total amount spent across all their order line items).

```python
query = """
CREATE OR REPLACE TABLE `{project}.{dataset}.customer_segmentation_rfm` AS
WITH order_value AS (
  SELECT order_id, user_id, SUM(sale_price) AS order_total
  FROM `bigquery-public-data.thelook_ecommerce.order_items`
  GROUP BY order_id, user_id
)
SELECT
  o.user_id,
  DATE_DIFF(DATE '2024-01-01', MAX(DATE(o.created_at)), DAY) AS recency_days,
  COUNT(DISTINCT o.order_id) AS frequency,
  SUM(ov.order_total) AS monetary
FROM `bigquery-public-data.thelook_ecommerce.orders` o
JOIN order_value ov USING (order_id, user_id)
WHERE o.created_at < '2024-01-01'
GROUP BY o.user_id
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()

query = f"SELECT COUNT(*) AS n_customers, ROUND(AVG(recency_days)) AS avg_recency, ROUND(AVG(frequency),2) AS avg_frequency, ROUND(AVG(monetary),2) AS avg_monetary FROM `{PROJECT_ID}.{DATASET_ID}.customer_segmentation_rfm`"
client.query(query).to_dataframe()
```

~27,700 customers, averaging ~1.3 orders each — most customers in this dataset order rarely, exactly the kind of pattern RFM segmentation is meant to surface (a single average hides very different customer types).

---
## Step 2 — `KMEANS` on standardized RFM features

`ML.STANDARD_SCALER` first — `monetary` ranges into the thousands while `frequency` tops out in single digits; without scaling, `monetary` alone would dominate every distance calculation.

> **GOTCHA (caught during pre-validation, not shown as a demonstrated mistake here):** `user_id` must **not** appear in the training query/`TRANSFORM` — it would become a raw, unscaled feature and badly distort clustering (an arbitrary large integer, treated as if it were a meaningful numeric signal). Keep training to feature columns only; join `user_id` back afterward via `ML.PREDICT`.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.customer_segmentation_kmeans`
TRANSFORM(
  ML.STANDARD_SCALER(recency_days) OVER() AS recency_scaled,
  ML.STANDARD_SCALER(frequency) OVER() AS frequency_scaled,
  ML.STANDARD_SCALER(monetary) OVER() AS monetary_scaled
)
OPTIONS(model_type = 'KMEANS', num_clusters = 4, kmeans_init_method = 'KMEANS++') AS
SELECT recency_days, frequency, monetary
FROM `{project}.{dataset}.customer_segmentation_rfm`
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model customer_segmentation_kmeans created')
```

---
## Step 3 — `ML.EVALUATE` + `ML.CENTROIDS`: inspect the fitted segments

> **Reminder from `models/kmeans/`: `KMEANS` retraining is genuinely non-deterministic**, even with `KMEANS++` initialization — exact centroid numbering and `davies_bouldin_index` will vary slightly run to run. The segment *shapes* below are the real, reproducible finding; the specific numbers are illustrative of one run.

```python
query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.customer_segmentation_kmeans`)"
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT centroid_id, feature, ROUND(numerical_value, 3) AS numerical_value
FROM ML.CENTROIDS(MODEL `{PROJECT_ID}.{DATASET_ID}.customer_segmentation_kmeans`)
ORDER BY centroid_id, feature
"""
client.query(query).to_dataframe()
```

---
## Step 4 — `ML.PREDICT` on the full customer base, real segment profiles

Join `user_id` back in here (not during training) and aggregate each segment's actual (unscaled) recency/frequency/monetary averages — the numbers a business stakeholder actually cares about.

```python
query = f"""
SELECT
  CENTROID_ID,
  COUNT(*) AS n_customers,
  ROUND(AVG(recency_days)) AS avg_recency_days,
  ROUND(AVG(frequency), 2) AS avg_frequency,
  ROUND(AVG(monetary), 2) AS avg_monetary
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.customer_segmentation_kmeans`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.customer_segmentation_rfm`
)
GROUP BY CENTROID_ID
ORDER BY CENTROID_ID
"""
segment_profiles = client.query(query).to_dataframe()
segment_profiles
```

**Four genuinely interpretable segments, confirmed across multiple independent retrains** (`KMEANS` centroid IDs reshuffle every retrain — the table above will very likely NOT match these ID numbers if you re-run this notebook. Identify each segment by its **characteristics** in your own table above, not by centroid ID):
- The segment with the **highest average spend** — in this run, ~$460, ~5% of customers, decent frequency (~2.2 orders) — **Champions**: most valuable, worth retention investment.
- The segment with **high order frequency but moderate spend** — in this run, ~2.2 orders, ~$141 avg, ~17% of customers, good recency — **Loyal regulars**: repeat buyers, worth nurturing toward Champion status.
- The **majority** segment with **the best recency but only 1 order and the lowest spend** — in this run, ~52% of customers, ~$77 avg — **Recent, low-value**: bought once, recently, but haven't shown a repeat pattern yet.
- The segment with **by far the worst recency** (over 2.5 years) alongside low frequency/spend — in this run, ~26% of customers, ~$85 avg — **Lapsed / lost**: hasn't purchased in years, the clearest re-engagement-or-write-off decision of the four.

This same shape — one small high-value segment, one frequent-but-moderate-spend segment, one large recent-low-value majority, and one long-lapsed segment — has now been observed across three independent retrainings, even though the specific centroid ID attached to each has been different every time.

---
## Step 5 — Visualize the segments

Recency vs. monetary, colored by segment. `frequency` is deliberately not used as a plot axis here — it only takes small integer values (mostly 1-4 orders) in this dataset, so a scatter plot against it renders as thin vertical stripes rather than a useful 2D view; its role in the segmentation is already captured numerically in Step 4's aggregated table.

```python
import matplotlib.pyplot as plt

query = f"""
SELECT CENTROID_ID, recency_days, frequency, monetary
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.customer_segmentation_kmeans`,
  TABLE `{PROJECT_ID}.{DATASET_ID}.customer_segmentation_rfm`
)
"""
df = client.query(query).to_dataframe()

cluster_colors = {1: '#4285F4', 2: '#EA4335', 3: '#34A853', 4: '#FBBC05'}

fig, ax = plt.subplots(figsize=(7, 6))
for centroid_id in sorted(df['CENTROID_ID'].unique()):
    subset = df[df['CENTROID_ID'] == centroid_id]
    ax.scatter(
        subset['recency_days'], subset['monetary'],
        c=cluster_colors.get(centroid_id, '#999999'),
        alpha=0.4, s=20, label=f'Segment {centroid_id} (n={len(subset)})'
    )
ax.set_xlabel('Recency (days since last order)')
ax.set_ylabel('Monetary (total spend, $)')
ax.set_title('Customer segments: recency vs. monetary')
ax.legend()
plt.show()
```

---
## Related content

- `models/kmeans` (`models/kmeans/`) — the `KMEANS` algorithm mechanics in depth: tuning `num_clusters`, the verified non-determinism finding, `ML.DETECT_ANOMALIES` on cluster distance.
- `functions/scalers` (`functions/scalers/`) — `ML.STANDARD_SCALER` and its siblings in full depth.
- `workflows/churn_retention` (`workflows/churn_retention/`) — reuses this same customer base to ask a related question: which customers are likely to churn, and does churn risk correlate with these segments?

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT centroid_id, feature, ROUND(numerical_value, 3) AS numerical_value
FROM ML.CENTROIDS(MODEL `statmike-mlops-349915.bq_ml.customer_segmentation_kmeans`)
ORDER BY centroid_id, feature
```

---
## Examples — BigFrames

`bigframes.ml.cluster.KMeans` is a real first-class wrapper (already verified in `models/kmeans/`).

```python
import bigframes.pandas as bpd
from bigframes.ml.cluster import KMeans
from bigframes.ml.preprocessing import StandardScaler
from bigframes.ml.pipeline import Pipeline

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

df = bpd.read_gbq(f"SELECT recency_days, frequency, monetary FROM `{PROJECT_ID}.{DATASET_ID}.customer_segmentation_rfm`")

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('kmeans', KMeans(n_clusters=4)),
])
pipeline.fit(df)
pipeline.predict(df).peek()
```
