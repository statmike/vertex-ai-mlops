# Anomaly / Fraud Detection — BigQuery ML

The real ground-truth validation the 5 existing `ML.DETECT_ANOMALIES` demos — `models/kmeans` (`models/kmeans/`), `models/pca` (`models/pca/`), `models/autoencoder` (`models/autoencoder/`), `models/arima_plus` (`models/arima_plus/`), `models/arima_plus_xreg` (`models/arima_plus_xreg/`) — all lack: a dataset with **genuine labeled fraud**. Train unsupervised detection on features only (no label), score it, and measure real precision/recall against the truth — then contrast with a supervised classifier trained *with* the label.

**Models used:** `PCA`, `AUTOENCODER`, `BOOSTED_TREE_CLASSIFIER`
**Functions used:** `ML.DETECT_ANOMALIES`, `ML.EVALUATE`

> **GOTCHA — distinct from `functions/data_quality` (`functions/data_quality/`):** this is **row-level** anomaly detection within one dataset (is *this transaction* unusual?). `ML.VALIDATE_DATA_SKEW`/`ML.VALIDATE_DATA_DRIFT` are **dataset-level** distribution comparisons (has *the whole dataset* shifted?). Different concept, similar-sounding name.

`ML.DETECT_ANOMALIES`'s basic mechanics (the required 3-argument form, `contamination`) are already covered in the 5 notebooks above and not repeated here — **this workflow's real content is the honest precision/recall measurement against real labels.**

**Data:** [`bigquery-public-data.ml_datasets.ulb_fraud_detection`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — the classic ULB/Kaggle credit-card-fraud dataset: 284,807 transactions, 492 real fraud cases (0.17%), features `Time`, `V1`-`V28` (already PCA-anonymized by the original data providers), `Amount`.

**References:** `RESOURCES.md` (Full reference) | [ML.DETECT_ANOMALIES docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-detect-anomalies) | `setup` (Setup guide)

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
## Step 0 — How rare is fraud, really?

Confirm the class imbalance directly from the data before doing anything else.

```python
query = """
SELECT Class, COUNT(*) AS n, ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 4) AS pct
FROM `bigquery-public-data.ml_datasets.ulb_fraud_detection`
GROUP BY Class
"""
client.query(query).to_dataframe()
```

**492 fraud cases out of 284,807 transactions — 0.17%.** Any evaluation of this problem has to be precision/recall based; accuracy alone is meaningless (predicting "never fraud" gets 99.83% accuracy while catching nothing).

---
## Step 1 — Unsupervised: `PCA` trained on features only (no `Class` label)

The whole point of unsupervised detection: train without ever seeing which transactions are fraud.

> **MAJOR GOTCHA (verified live — a genuinely new finding):** training with `pca_explained_variance_ratio` (a variable component *count*, chosen to hit a variance target) produced wildly different `ML.DETECT_ANOMALIES` results across otherwise-identical retrainings of the exact same `CREATE OR REPLACE MODEL` statement — true-positive counts of 3, 235, and 279 (out of 492 real frauds) across three separate runs — **even though `ML.EVALUATE`'s `total_explained_variance_ratio` stayed bit-for-bit stable (~0.95473) every time.** Near-threshold eigenvalues can flip which exact components get retained between runs, which swings per-row reconstruction error dramatically even though the aggregate variance captured looks identical. This refines `RESOURCES.md` (`RESOURCES.md`)'s "PCA is fully deterministic" claim — true for `ML.EVALUATE`'s own metric, not necessarily true for downstream anomaly scores. **Fix: use a fixed `num_principal_components` instead** — substantially more stable across retrainings (verified: independent runs landed in a TP=114-132 range).

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.anomaly_fraud_pca`
OPTIONS(
  model_type = 'PCA',
  num_principal_components = 10,
  scale_features = TRUE
) AS
SELECT * EXCEPT(Class)
FROM `bigquery-public-data.ml_datasets.ulb_fraud_detection`
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model anomaly_fraud_pca created')
```

Score with the **true fraud rate as `contamination`** — an "oracle" choice. In a real scenario you wouldn't know this in advance, but using it here isolates the method's ceiling performance from the separate problem of guessing a good `contamination` value. `Class` is not a training feature, but passes through the scoring query unused — the same passthrough behavior `ML.PREDICT` has.

```python
query = f"""
SELECT is_anomaly, Class, COUNT(*) AS n
FROM ML.DETECT_ANOMALIES(
  MODEL `{PROJECT_ID}.{DATASET_ID}.anomaly_fraud_pca`,
  STRUCT(0.001727 AS contamination),
  (SELECT * FROM `bigquery-public-data.ml_datasets.ulb_fraud_detection`)
)
GROUP BY is_anomaly, Class
ORDER BY is_anomaly DESC, Class
"""
client.query(query).to_dataframe()
```

**Verified (`num_principal_components=10`, across independent runs): precision ~20-24%, recall ~23-27%.** Modest but real signal — and far more reproducible than the `pca_explained_variance_ratio` mode above.

---
## Step 2 — Unsupervised: `AUTOENCODER` — does a nonlinear method do better?

Same features, same `contamination`, a fundamentally different (nonlinear) reconstruction method.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.anomaly_fraud_autoencoder`
OPTIONS(
  model_type = 'AUTOENCODER',
  hidden_units = [16, 8, 16],
  activation_fn = 'RELU',
  batch_size = 512,
  max_iterations = 10
) AS
SELECT * EXCEPT(Class)
FROM `bigquery-public-data.ml_datasets.ulb_fraud_detection`
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model anomaly_fraud_autoencoder created')
```

```python
query = f"""
SELECT is_anomaly, Class, COUNT(*) AS n
FROM ML.DETECT_ANOMALIES(
  MODEL `{PROJECT_ID}.{DATASET_ID}.anomaly_fraud_autoencoder`,
  STRUCT(0.001727 AS contamination),
  (SELECT * FROM `bigquery-public-data.ml_datasets.ulb_fraud_detection`)
)
GROUP BY is_anomaly, Class
ORDER BY is_anomaly DESC, Class
"""
client.query(query).to_dataframe()
```

**Verified: precision ~23-26%, recall ~27-29% — comparable to PCA's stabilized result, not dramatically better.** On this already-decorrelated feature set (`V1`-`V28` are themselves PCA outputs from the original data providers), the nonlinear autoencoder doesn't show an obvious edge over well-configured `PCA`. (`AUTOENCODER` retraining is itself non-deterministic — see `models/autoencoder` (`models/autoencoder/`) — same caveat as `PCA` above.) Both unsupervised methods catch well under a third of real fraud — this is the honest ceiling for *unsupervised* detection on this dataset.

---
## Step 3 — Supervised: `BOOSTED_TREE_CLASSIFIER` trained *with* the `Class` label

What changes when the model is allowed to learn directly from confirmed fraud/not-fraud examples? `auto_class_weights = TRUE` corrects for the same extreme imbalance seen in Step 0.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.anomaly_fraud_supervised`
OPTIONS(
  model_type = 'BOOSTED_TREE_CLASSIFIER',
  input_label_cols = ['Class'],
  auto_class_weights = TRUE,
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT *
FROM `bigquery-public-data.ml_datasets.ulb_fraud_detection`
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model anomaly_fraud_supervised created')
```

```python
query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.anomaly_fraud_supervised`)"
client.query(query).to_dataframe()
```

**Verified (on the automatic held-out eval split): precision ~27%, recall ~87%, `roc_auc` ~0.97.**

**Honest comparison note:** this is evaluated on a held-out split (~15 real fraud cases — `ML.CONFUSION_MATRIX` shows TP=13, FN=2), while Steps 1-2 scored the *full* dataset (unsupervised methods have no train/test split concern since they never see labels at all) — the populations aren't identically sized, so treat this as directional rather than a precise apples-to-apples ratio. The takeaway is still large and clear: **recall roughly triples (29% → 87%)** when the model can train directly on the exact fraud pattern it's trying to catch, at a similar precision. This is the real, quantified answer to "what does having labels buy you" — the entire premise this workflow exists to test.

---
## Related content

- `functions/data_quality` (`functions/data_quality/`) — the dataset-level counterpart: `ML.VALIDATE_DATA_SKEW`/`ML.VALIDATE_DATA_DRIFT` ask "has the whole dataset shifted?" rather than "is this one row unusual?"
- `models/pca` (`models/pca/`), `models/autoencoder` (`models/autoencoder/`), `models/kmeans` (`models/kmeans/`) — `ML.DETECT_ANOMALIES` mechanics in depth (the 3-argument requirement, `contamination`, per-row reconstruction loss).
- `models/arima_plus` (`models/arima_plus/`), `models/arima_plus_xreg` (`models/arima_plus_xreg/`) — the time-series form of `ML.DETECT_ANOMALIES`, where the input-data argument is optional.
- `models/boosted_tree_classifier` (`models/boosted_tree_classifier/`) — full `BOOSTED_TREE_CLASSIFIER` mechanics.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT *
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.anomaly_fraud_supervised`)
```
