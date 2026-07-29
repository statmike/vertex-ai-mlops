# Data Quality / Model Monitoring — BigQuery ML Model-Free Functions

Five functions for training/serving **skew** and data **drift** monitoring, plus descriptive-statistics helpers. **Basic tier:** `ML.DESCRIBE_DATA`, `ML.VALIDATE_DATA_SKEW`, `ML.VALIDATE_DATA_DRIFT` (tabular output, `is_anomaly` flags). **Advanced/TFDV-compatible tier:** `ML.TFDV_DESCRIBE`, `ML.TFDV_VALIDATE` (emit/consume a TensorFlow `DatasetFeatureStatisticsList` proto as JSON, for interop with the `tensorflow-data-validation` library). None require a connection.

> **Not the same as `ML.DETECT_ANOMALIES`.** This notebook is about **dataset-level** distribution shift — comparing whole datasets or time windows to each other, or to a model's stored training statistics. `ML.DETECT_ANOMALIES` (already covered in `models/kmeans` (K-Means), `models/pca` (PCA), `models/autoencoder` (Autoencoder), `models/arima_plus` (ARIMA_PLUS), `models/arima_plus_xreg` (ARIMA_PLUS_XREG)) is about **row-level** outliers within one dataset. Similar name, different concept — easy to conflate.

**When to use these:**
- `ML.DESCRIBE_DATA` — profile a dataset before/after training, or before formal skew/drift checks.
- `ML.VALIDATE_DATA_SKEW` — catch serving inputs that have drifted from what a model was actually trained on, using the model's own stored training statistics (no need to keep the original training data around).
- `ML.VALIDATE_DATA_DRIFT` — compare any two datasets/time windows directly (e.g. this week vs. last week of serving data).
- `ML.TFDV_DESCRIBE`/`ML.TFDV_VALIDATE` — the same ideas, TFDV-proto-compatible, for teams already using `tensorflow-data-validation` in a TFX pipeline.

**Data:** [`bigquery-public-data.ml_datasets.census_adult_income`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — same dataset as `models/logistic_regression` (Logistic Regression).

**Related production content:** `MLOps/Model%20Monitoring/bqml-model-monitoring-tutorial.ipynb` (`MLOps/Model Monitoring/bqml-model-monitoring-tutorial.ipynb`) and `model_monitoring_job.sql` show the full production pattern — a scheduled retrain/alert loop and real `tfdv.visualize_statistics()`/`display_anomalies()` rendering. This notebook stays focused on the 5 functions' mechanics in isolation.

**References:** `RESOURCES.md` (Full reference) | [Model monitoring overview](https://cloud.google.com/bigquery/docs/model-monitoring-overview) | `setup` (Setup guide)

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
## Step 1 — Train a small scratch model

`ML.VALIDATE_DATA_SKEW` needs a real model with stored training statistics to compare against — train one small `LOGISTIC_REG`, same recipe as `models/logistic_regression` (`models/logistic_regression/`).

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.data_quality_scratch_model`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  data_split_method = 'RANDOM',
  data_split_eval_fraction = 0.2
) AS
SELECT age, workclass, education, education_num, marital_status, occupation,
       relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model data_quality_scratch_model created')
```

---
## Step 2 — `ML.DESCRIBE_DATA`: descriptive statistics, numeric and categorical

The first step of any monitoring workflow — profile a dataset before doing anything else. `top_k` controls how many top categorical values are returned; `num_quantiles` controls numeric quantile granularity.

```python
query = """
SELECT name, num_rows, min, max, mean, stddev, median, quantiles
FROM ML.DESCRIBE_DATA(
  TABLE `bigquery-public-data.ml_datasets.census_adult_income`,
  STRUCT(3 AS top_k, 4 AS num_quantiles)
)
WHERE name IN ('age', 'capital_gain')
"""
client.query(query).to_dataframe()
```

Categorical columns populate `unique`/`top_values` instead of the numeric stats columns:

```python
query = """
SELECT name, unique, top_values, num_nulls
FROM ML.DESCRIBE_DATA(
  TABLE `bigquery-public-data.ml_datasets.census_adult_income`,
  STRUCT(3 AS top_k, 4 AS num_quantiles)
)
WHERE name IN ('workclass', 'income_bracket')
"""
client.query(query).to_dataframe()
```

---
## Step 3 — MAJOR GOTCHA (verified live): naive `LIMIT` sampling looks like severe skew

`ML.VALIDATE_DATA_SKEW` compares new (serving) data against the **training statistics stored inside the model** — no need to keep the original training data around. It's genuinely sensitive: the public `census_adult_income` table is **not** randomly ordered, so grabbing "the first N rows" with `LIMIT` (no `ORDER BY`) silently returns a non-representative slice.

```python
query = """
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_SKEW(
  MODEL `{project}.{dataset}.data_quality_scratch_model`,
  (SELECT age, workclass, education, education_num, marital_status, occupation,
          relationship, race, sex, hours_per_week, native_country
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   LIMIT 5000)
)
ORDER BY is_anomaly DESC, input
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).to_dataframe()
```

**Verified:** `education_num` flags `is_anomaly=TRUE` with a Jensen-Shannon divergence of ~0.65 (threshold 0.3) — despite being drawn from the **exact same table** the model trained on. This is a sampling bug, not a real serving-data problem: `LIMIT` without `ORDER BY` isn't a random sample.

**Fix:** sample randomly instead of grabbing "the first N rows":

```python
query = """
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_SKEW(
  MODEL `{project}.{dataset}.data_quality_scratch_model`,
  (SELECT age, workclass, education, education_num, marital_status, occupation,
          relationship, race, sex, hours_per_week, native_country
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE RAND() < 0.15)
)
ORDER BY is_anomaly DESC, input
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).to_dataframe()
```

**Verified:** every column's divergence drops to near-zero, correctly reporting no skew — confirming the earlier alarm was purely a sampling artifact. **Lesson: how you sample your comparison data matters as much as the function call itself** — a naive `LIMIT` can manufacture a false skew alarm just as easily as it can hide a real one.

---
## Step 4 — `ML.VALIDATE_DATA_DRIFT`: real drift between two genuinely different populations

Unlike `ML.VALIDATE_DATA_SKEW`, this compares **two arbitrary datasets** directly — no model or stored training stats needed (the `MODEL` argument is optional, only adding a Vertex AI visualization link). Compare a random sample of the whole population against a real subgroup — incorporated self-employed workers — to show a genuine, explainable drift signal, not a sampling bug.

```python
query = """
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE RAND() < 0.3),
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT(0.1 AS numerical_default_threshold)
)
"""
client.query(query).to_dataframe()
```

**Verified:** `education_num` flags real drift (Jensen-Shannon divergence ~0.18, above the 0.1 threshold) — incorporated self-employed workers skew toward more education than the general population. A genuine, explainable finding this time, not a sampling artifact.

### `categorical_metric_type`: the metric choice genuinely changes which features get flagged

So far every categorical column has used the default `L_INFTY`. Compare against `JENSEN_SHANNON_DIVERGENCE` on the same categorical columns, same threshold, same two populations.

```python
query = """
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT sex, relationship, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE RAND() < 0.3),
  (SELECT sex, relationship, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT(0.05 AS categorical_default_threshold)
)
ORDER BY input
"""
client.query(query).to_dataframe()
```

```python
query = """
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT sex, relationship, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE RAND() < 0.3),
  (SELECT sex, relationship, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT(0.05 AS categorical_default_threshold, 'JENSEN_SHANNON_DIVERGENCE' AS categorical_metric_type)
)
ORDER BY input
"""
client.query(query).to_dataframe()
```

**Verified: the metric choice changes which features get flagged, at the identical threshold.** Under `L_INFTY`, all three columns (`race`, `relationship`, `sex`) exceed 0.05 and are flagged `is_anomaly=TRUE`. Under `JENSEN_SHANNON_DIVERGENCE`, `race` and `sex` drop below 0.05 and are no longer flagged — only `relationship` remains an anomaly under both metrics. `L_INFTY` (the maximum single-category proportion difference) and Jensen-Shannon divergence (a distribution-wide difference) measure genuinely different things, so switching one for the other on a real dataset can silently change your alerting behavior — not just a documentation footnote.

### `thresholds`: per-column overrides

Override the threshold for one specific column (`race`) while every other column keeps the `categorical_default_threshold`/`numerical_default_threshold`.

```python
query = """
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT age, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE RAND() < 0.3),
  (SELECT age, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT([('race', 0.01)] AS thresholds)
)
ORDER BY input
"""
client.query(query).to_dataframe()
```

**Verified:** `race`'s override (`threshold=0.01`) flags it `is_anomaly=TRUE` even though its actual divergence (~0.08) would pass comfortably under the `categorical_default_threshold=0.3` that `age` still uses. Useful for tightening (or loosening) sensitivity on specific business-critical columns without changing the default for everything else.

---
## Step 5 — `ML.TFDV_DESCRIBE` + `ML.TFDV_VALIDATE`: the TFDV-proto tier

Same ideas as Steps 2-4, but emitting/consuming a TensorFlow Data Validation `DatasetFeatureStatisticsList` proto (JSON) instead of tabular rows — for teams already using `tensorflow-data-validation` in a TFX pipeline. `ML.TFDV_DESCRIBE` behaves like `tfdv.generate_statistics_from_csv`.

```python
query = """
SELECT dataset_feature_statistics_list
FROM ML.TFDV_DESCRIBE(
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE RAND() < 0.05)
)
"""
df = client.query(query).to_dataframe()
print(df['dataset_feature_statistics_list'].iloc[0][:500], '...')
```

`ML.TFDV_VALIDATE` compares two such protos and returns a TFDV `Anomalies` proto — the TFDV-native equivalent of Step 4's drift check above, same `education_num` signal, different (proto) representation:

```python
query = """
WITH base AS (
  SELECT dataset_feature_statistics_list AS stats
  FROM ML.TFDV_DESCRIBE(
    (SELECT age, education_num, hours_per_week
     FROM `bigquery-public-data.ml_datasets.census_adult_income`
     WHERE RAND() < 0.3)
  )
),
compare AS (
  SELECT dataset_feature_statistics_list AS stats
  FROM ML.TFDV_DESCRIBE(
    (SELECT age, education_num, hours_per_week
     FROM `bigquery-public-data.ml_datasets.census_adult_income`
     WHERE workclass = ' Self-emp-inc')
  )
)
SELECT ML.TFDV_VALIDATE(base.stats, compare.stats, 'DRIFT') AS anomalies
FROM base, compare
"""
df = client.query(query).to_dataframe()

import json
anomalies = json.loads(df['anomalies'].iloc[0])
print(json.dumps(anomalies['drift_skew_info'], indent=2))
```

The `ML.TFDV_DESCRIBE` proto above is truncated for readability (it's a full per-column statistics dump); the `ML.TFDV_VALIDATE` output above is parsed and printed in full — confirming the same `education_num` divergence (~0.18) found by `ML.VALIDATE_DATA_DRIFT` in Step 4, just expressed as a TFDV `drift_skew_info` measurement instead of a tabular row. In a full TFDV Python environment, `json_format.ParseDict` + `tfdv.visualize_statistics()`/`tfdv.display_anomalies()` render both as the familiar TFDV facets/anomaly widgets. See `MLOps/Model%20Monitoring/bqml-model-monitoring-tutorial.ipynb` (`MLOps/Model Monitoring/bqml-model-monitoring-tutorial.ipynb`) for that full rendering.

### `ML.TFDV_VALIDATE`'s `'SKEW'` mode: the TFDV-native equivalent of Step 3's skew check

The prior `ML.TFDV_VALIDATE` call used `'DRIFT'` mode. `'SKEW'` mode is semantically the training-vs-serving comparison — the TFDV-proto counterpart to `ML.VALIDATE_DATA_SKEW`, comparing stats from a "training" sample against a "serving" sample (here, both built manually via `ML.TFDV_DESCRIBE`, since this function works on any two proto statistics regardless of source).

```python
query = """
WITH training_stats AS (
  SELECT dataset_feature_statistics_list AS stats
  FROM ML.TFDV_DESCRIBE(
    (SELECT age, education_num, hours_per_week
     FROM `bigquery-public-data.ml_datasets.census_adult_income`
     WHERE RAND() < 0.3)
  )
),
serving_stats AS (
  SELECT dataset_feature_statistics_list AS stats
  FROM ML.TFDV_DESCRIBE(
    (SELECT age, education_num, hours_per_week
     FROM `bigquery-public-data.ml_datasets.census_adult_income`
     WHERE workclass = ' Self-emp-inc')
  )
)
SELECT ML.TFDV_VALIDATE(training_stats.stats, serving_stats.stats, 'SKEW') AS anomalies
FROM training_stats, serving_stats
"""
df = client.query(query).to_dataframe()

import json
anomalies = json.loads(df['anomalies'].iloc[0])
print(json.dumps(anomalies['drift_skew_info'], indent=2))
```

**Verified:** the output structure is identical to `'DRIFT'` mode (same `drift_skew_info` array, same `skew_measurements`/divergence values) — `education_num` again shows the ~0.18 divergence. `'SKEW'` vs `'DRIFT'` mode changes the *baseline schema*'s comparator type (`skew_comparator` vs `drift_comparator`) and semantic framing (training-vs-serving vs. two arbitrary windows), not the underlying computation — consistent with `ML.VALIDATE_DATA_SKEW`/`ML.VALIDATE_DATA_DRIFT` sharing the same output schema in the tabular tier above.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT name, num_rows, min, max, mean, stddev
FROM ML.DESCRIBE_DATA(
  TABLE `bigquery-public-data.ml_datasets.census_adult_income`,
  STRUCT(3 AS top_k, 4 AS num_quantiles)
)
WHERE name = 'hours_per_week'
```

---
## Examples — BigFrames

There is **no** direct BigFrames equivalent for any of these five — `bigframes.pandas.DataFrame.describe()` gives comparable (but not identical) profiling to `ML.DESCRIBE_DATA`; there's nothing built in for skew/drift/TFDV.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

df = bpd.read_gbq(
    "SELECT age, hours_per_week FROM `bigquery-public-data.ml_datasets.census_adult_income`"
)
df.describe()
```
