# Model Monitoring — BigQuery ML Model-Free Functions

Four functions for training/serving **skew** and data **drift** monitoring. **Basic tier:** `ML.VALIDATE_DATA_SKEW`, `ML.VALIDATE_DATA_DRIFT` (tabular output, `is_anomaly` flags). **Advanced/TFDV-compatible tier:** `ML.TFDV_DESCRIBE`, `ML.TFDV_VALIDATE` (emit/consume a TensorFlow `DatasetFeatureStatisticsList` proto as JSON, for interop with the `tensorflow-data-validation` library). None require a connection.

> **Not the same as `ML.DETECT_ANOMALIES`.** This notebook is about **dataset-level** distribution shift — comparing whole datasets or time windows to each other, or to a model's stored training statistics. `ML.DETECT_ANOMALIES` (already covered in `models/kmeans` (K-Means), `models/pca` (PCA), `models/autoencoder` (Autoencoder), `models/arima_plus` (ARIMA_PLUS), `models/arima_plus_xreg` (ARIMA_PLUS_XREG)) is about **row-level** outliers within one dataset. Similar name, different concept — easy to conflate. There is a third question in this family: **window-level** level shifts within one series, which is `functions/time_series` (`functions/time_series/`)'s `ML.DETECT_CHANGE_POINTS`. Whole dataset moved → here; individual row is an outlier → `ML.DETECT_ANOMALIES`; the series stepped to a new level and stayed there → `ML.DETECT_CHANGE_POINTS`.

**What Step 5 establishes, measured here rather than quoted:**

1. The **categorical** metrics are computed on the data. `L_INFTY` and Jensen-Shannon divergence both reproduce by hand, exactly.
2. The **numeric** metric is not. It is computed from a ten-bucket histogram whose edges come from each input's own minimum and maximum — so it can report several times the divergence the values themselves hold.
3. As a direct consequence, **one row can clear a numeric drift alarm**. Shown here with a single row added to a 1,116-row comparison set.

**When to use these:**
- `ML.VALIDATE_DATA_SKEW` — catch serving inputs that have drifted from what a model was actually trained on, using the model's own stored training statistics (no need to keep the original training data around).
- `ML.VALIDATE_DATA_DRIFT` — compare any two datasets/time windows directly (e.g. this week vs. last week of serving data).
- `ML.TFDV_DESCRIBE`/`ML.TFDV_VALIDATE` — the same ideas, TFDV-proto-compatible, for teams already using `tensorflow-data-validation` in a TFX pipeline.

**Data:** [`bigquery-public-data.ml_datasets.census_adult_income`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — same dataset as `models/logistic_regression` (Logistic Regression).

**Profile first.** Every one of these functions answers "has this dataset *changed*." The prior question — what is in this dataset at all — is `functions/exploration` (`functions/exploration/`), where `ML.DESCRIBE_DATA` profiles the columns and `ML.CORRELATION` measures what moves with the target. Profile there, monitor here; the census placeholder that notebook finds (`workclass` reporting `num_nulls = 0` while 1,836 rows hold the string `' ?'`) is exactly the kind of thing a drift check will happily call stable forever.

**Where this sits next to [MLOps/Model Monitoring/](https://github.com/statmike/vertex-ai-mlops/tree/main/MLOps/Model%20Monitoring).** That folder owns the **production loop** — registering a BigQuery ML model to the Vertex AI Model Registry, scheduling the check, alerting on it, and rendering the TFDV protos through `tfdv.visualize_statistics()` / `tfdv.display_anomalies()`. This notebook owns the **four functions' mechanics**: what each argument does, and what the numbers they return are computed from. Its [readme](https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Model%20Monitoring/readme.md) works both metrics through by hand on a three-level toy feature — Step 5 below runs that same arithmetic against the function, on real columns.

Two orchestrations of the drift check as a production loop already live in this project: `pipelines/sql_scripting` (`pipelines/sql_scripting/`) and `pipelines/scheduled_queries` (`pipelines/scheduled_queries/`).

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
CREATE OR REPLACE MODEL `{project}.{dataset}.model_monitoring_scratch_model`
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
print('Model model_monitoring_scratch_model created')
```

---
## Step 2 — MAJOR GOTCHA (verified live): naive `LIMIT` sampling looks like severe skew

`ML.VALIDATE_DATA_SKEW` compares new (serving) data against the **training statistics stored inside the model** — no need to keep the original training data around. It's genuinely sensitive: the public `census_adult_income` table is **not** randomly ordered, so grabbing "the first N rows" with `LIMIT` (no `ORDER BY`) silently returns a non-representative slice.

```python
query = """
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_SKEW(
  MODEL `{project}.{dataset}.model_monitoring_scratch_model`,
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
  MODEL `{project}.{dataset}.model_monitoring_scratch_model`,
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
## Step 3 — `ML.VALIDATE_DATA_DRIFT`: real drift between two genuinely different populations

Unlike `ML.VALIDATE_DATA_SKEW`, this compares **two arbitrary datasets** directly — no model or stored training stats needed (the `MODEL` argument is optional, only adding a Vertex AI visualization link). Compare incorporated self-employed workers against everyone else, to show a genuine, explainable drift signal rather than a sampling bug.

Both populations are `WHERE` clauses on `workclass`, so they are **disjoint and deterministic** — the same two sets of rows on every run. That matters more than it looks: Step 5 recomputes these exact values by hand, and a hand reproduction needs byte-identical inputs, which a `RAND()` sample cannot promise across two queries.

```python
query = """
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass != ' Self-emp-inc'),
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT(0.1 AS numerical_default_threshold)
)
"""
client.query(query).to_dataframe()
```

**Verified:** `education_num` crosses the line (Jensen-Shannon divergence 0.1813, against the 0.1 threshold) — incorporated self-employed workers do skew toward more education than everyone else. `age` and `hours_per_week` differ too, but not by enough to be flagged. A genuine, explainable difference this time, not a sampling artifact.

Hold on to that `education_num` figure. The direction is real; the magnitude is not what it looks like. Step 5 computes the divergence between these two columns of values directly and gets something four and a half times smaller — for a reason that changes how a numeric drift alarm should be read.

### `categorical_metric_type`: the metric choice genuinely changes which features get flagged

So far every categorical column has used the default `L_INFTY`. Compare against `JENSEN_SHANNON_DIVERGENCE` on the same categorical columns, same threshold, same two populations.

```python
query = """
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT sex, relationship, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass != ' Self-emp-inc'),
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
   WHERE workclass != ' Self-emp-inc'),
  (SELECT sex, relationship, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT(0.05 AS categorical_default_threshold, 'JENSEN_SHANNON_DIVERGENCE' AS categorical_metric_type)
)
ORDER BY input
"""
client.query(query).to_dataframe()
```

**Verified: the metric choice changes which features get flagged, at the identical threshold.** Under `L_INFTY` all three columns clear 0.05 and are flagged `is_anomaly=TRUE`. Under `JENSEN_SHANNON_DIVERGENCE` only `relationship` still is — `race` falls to 0.0244, and `sex` lands at 0.0497, under the line by three ten-thousandths on a column whose largest single-category shift is 0.2173.

That near-miss is the lesson rather than a curiosity. `L_INFTY` is the maximum single-category difference, and `sex` has exactly two categories, so its two differences are equal and both maximal. Jensen-Shannon divergence weighs the whole distribution, and a two-category shift of that size is not a large distributional move. The two metrics measure genuinely different things, so swapping one for the other on a live monitor silently redraws the alert boundary — and a column can sit on either side of it.

### `thresholds`: per-column overrides

Override the threshold for one specific column (`race`) while every other column keeps the `categorical_default_threshold`/`numerical_default_threshold`.

```python
query = """
SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT age, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass != ' Self-emp-inc'),
  (SELECT age, race
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT([('race', 0.01)] AS thresholds)
)
ORDER BY input
"""
client.query(query).to_dataframe()
```

**Verified:** `race`'s override (`threshold=0.01`) flags it `is_anomaly=TRUE` even though its `L_INFTY` of 0.0804 would pass comfortably under the default of 0.3 that `age` still uses. Useful for tightening (or loosening) sensitivity on specific business-critical columns without changing the default for everything else.

---
## Step 4 — `ML.TFDV_DESCRIBE` + `ML.TFDV_VALIDATE`: the TFDV-proto tier

Same ideas as Steps 2-3, but emitting/consuming a TensorFlow Data Validation `DatasetFeatureStatisticsList` proto (JSON) instead of tabular rows — for teams already using `tensorflow-data-validation` in a TFX pipeline. `ML.TFDV_DESCRIBE` behaves like `tfdv.generate_statistics_from_csv`.

```python
query = """
SELECT dataset_feature_statistics_list
FROM ML.TFDV_DESCRIBE(
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass != ' Self-emp-inc')
)
"""
df = client.query(query).to_dataframe()
print(df['dataset_feature_statistics_list'].iloc[0][:500], '...')
```

`ML.TFDV_VALIDATE` compares two such protos and returns a TFDV `Anomalies` proto — the TFDV-native equivalent of Step 3's drift check above, same `education_num` signal, different (proto) representation:

```python
query = """
WITH base AS (
  SELECT dataset_feature_statistics_list AS stats
  FROM ML.TFDV_DESCRIBE(
    (SELECT age, education_num, hours_per_week
     FROM `bigquery-public-data.ml_datasets.census_adult_income`
     WHERE workclass != ' Self-emp-inc')
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

The `ML.TFDV_DESCRIBE` proto above is truncated for readability (it's a full per-column statistics dump); the `ML.TFDV_VALIDATE` output above is parsed and printed in full — confirming the same `education_num` divergence (0.1813) found by `ML.VALIDATE_DATA_DRIFT` in Step 3, just expressed as a TFDV `drift_skew_info` measurement instead of a tabular row. In a full TFDV Python environment, `json_format.ParseDict` + `tfdv.visualize_statistics()`/`tfdv.display_anomalies()` render both as the familiar TFDV facets/anomaly widgets. See [MLOps/Model Monitoring/bqml-model-monitoring-tutorial.ipynb](https://github.com/statmike/vertex-ai-mlops/blob/main/MLOps/Model%20Monitoring/bqml-model-monitoring-tutorial.ipynb) for that full rendering.

### `ML.TFDV_VALIDATE`'s `'SKEW'` mode: the TFDV-native equivalent of Step 2's skew check

The prior `ML.TFDV_VALIDATE` call used `'DRIFT'` mode. `'SKEW'` mode is semantically the training-vs-serving comparison — the TFDV-proto counterpart to `ML.VALIDATE_DATA_SKEW`, comparing stats from a "training" sample against a "serving" sample (here, both built manually via `ML.TFDV_DESCRIBE`, since this function works on any two proto statistics regardless of source).

```python
query = """
WITH training_stats AS (
  SELECT dataset_feature_statistics_list AS stats
  FROM ML.TFDV_DESCRIBE(
    (SELECT age, education_num, hours_per_week
     FROM `bigquery-public-data.ml_datasets.census_adult_income`
     WHERE workclass != ' Self-emp-inc')
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

**Verified:** the output structure is identical to `'DRIFT'` mode (same `drift_skew_info` array, same `skew_measurements`/divergence values) — `education_num` again shows the same 0.1813 divergence. `'SKEW'` vs `'DRIFT'` mode changes the *baseline schema*'s comparator type (`skew_comparator` vs `drift_comparator`) and semantic framing (training-vs-serving vs. two arbitrary windows), not the underlying computation — consistent with `ML.VALIDATE_DATA_SKEW`/`ML.VALIDATE_DATA_DRIFT` sharing the same output schema in the tabular tier above.

---
## Step 5 — What these numbers actually are

Steps 2-4 read the `value` column and compared it to a threshold. This step computes both metrics by hand and checks them against the function.

The categorical side reproduces exactly. The numeric side does not, and chasing down why turns up the most operationally important thing in this notebook: **the numeric divergence is computed from a histogram whose bucket edges are set by each input's own minimum and maximum.**

### The categorical metrics, by hand

Both categorical metrics start from the same two things — the proportion of each category in the base dataset, and its proportion in the comparison dataset.

**L-infinity** ([Chebyshev distance](https://en.wikipedia.org/wiki/Chebyshev_distance)) is the largest absolute difference in proportion across the categories. One category decides it; the rest are ignored.

**[Jensen-Shannon divergence](https://en.wikipedia.org/wiki/Jensen%E2%80%93Shannon_divergence)** mixes the two distributions, measures how far each sits from that mixture with a Kullback-Leibler divergence, and averages the two. Every category contributes.

Work both through on a three-level feature first, where every intermediate quantity fits on screen.

```python
import numpy as np
import pandas as pd

# A three-level categorical feature: category counts in the base and comparison datasets
stats = pd.DataFrame({'base_n': [116, 86, 36], 'compare_n': [775, 795, 279]}, index=['A', 'B', 'C'])
stats['base_pct'] = stats['base_n'] / stats['base_n'].sum()
stats['compare_pct'] = stats['compare_n'] / stats['compare_n'].sum()

# L-infinity: the largest absolute change in proportion
stats['abs_change_pct'] = (stats['base_pct'] - stats['compare_pct']).abs()

# Jensen-Shannon divergence, per category: the mixture, a KL term from each side, then their average
stats['mix'] = (stats['base_pct'] + stats['compare_pct']) / 2
stats['base_kl'] = stats['base_pct'] * np.log2(stats['base_pct'] / stats['mix'])
stats['compare_kl'] = stats['compare_pct'] * np.log2(stats['compare_pct'] / stats['mix'])
stats['JSD'] = (stats['base_kl'] + stats['compare_kl']) / 2

display(stats.round(6))
print(f"L_INFTY                   = {stats['abs_change_pct'].max():.6f}   (the maximum of abs_change_pct)")
print(f"JENSEN_SHANNON_DIVERGENCE = {stats['JSD'].sum():.6f}   (the sum of JSD)")
```

Two details decide whether a hand calculation matches BigQuery's, and both are easy to get wrong in a way that produces a plausible number.

The logarithm is **base 2**, which is what bounds the result at 1.0 for any pair of distributions. And the reported quantity is the **divergence**, not the Jensen-Shannon *distance* — no square root is taken.

### The same two formulas, against the function

Now the real columns. Pull the category counts for `race`, `relationship`, and `sex` out of both Step 3 populations, run the identical arithmetic, and put the results beside what `ML.VALIDATE_DATA_DRIFT` returned.

```python
CENSUS = '`bigquery-public-data.ml_datasets.census_adult_income`'
BASE_POP = "workclass != ' Self-emp-inc'"
COMPARE_POP = "workclass = ' Self-emp-inc'"
CAT_COLS = ['race', 'relationship', 'sex']
NUM_COLS = ['age', 'education_num', 'hours_per_week']


def drift(columns, options):
    """ML.VALIDATE_DATA_DRIFT over the two Step 3 populations, returning value keyed by column."""
    cols = ', '.join(columns)
    query = f"""
    SELECT input, value
    FROM ML.VALIDATE_DATA_DRIFT(
      (SELECT {cols} FROM {CENSUS} WHERE {BASE_POP}),
      (SELECT {cols} FROM {CENSUS} WHERE {COMPARE_POP}),
      STRUCT({options}))
    """
    return client.query(query).to_dataframe().set_index('input')['value']


def l_infinity(p, q):
    return np.abs(p - q).max()


def jensen_shannon_divergence(p, q):
    """Base-2 Jensen-Shannon divergence between two proportion vectors on the same support."""
    m = (p + q) / 2
    kl_p = np.where(p > 0, p * np.log2(np.where(p > 0, p, 1) / np.where(m > 0, m, 1)), 0.0)
    kl_q = np.where(q > 0, q * np.log2(np.where(q > 0, q, 1) / np.where(m > 0, m, 1)), 0.0)
    return ((kl_p + kl_q) / 2).sum()


def proportions(frame, column, support):
    return frame[column].value_counts(normalize=True).reindex(support).fillna(0).values


# One pull of the raw rows, split into the same two populations the function sees
raw = client.query(f"""
SELECT {', '.join(CAT_COLS + NUM_COLS)}, {COMPARE_POP} AS is_compare
FROM {CENSUS}
""").to_dataframe()
base_rows, compare_rows = raw[~raw['is_compare']], raw[raw['is_compare']]
print(f'base population: {len(base_rows):,} rows    comparison population: {len(compare_rows):,} rows')
```

```python
bq_linf = drift(CAT_COLS, "0.05 AS categorical_default_threshold")
bq_jsd = drift(CAT_COLS, "0.05 AS categorical_default_threshold, 'JENSEN_SHANNON_DIVERGENCE' AS categorical_metric_type")

rows = []
for column in CAT_COLS:
    support = sorted(set(base_rows[column]) | set(compare_rows[column]))
    p, q = proportions(base_rows, column, support), proportions(compare_rows, column, support)
    rows.append({
        'categories': len(support),
        'L_INFTY (BigQuery)': bq_linf[column], 'L_INFTY (by hand)': l_infinity(p, q),
        'JSD (BigQuery)': bq_jsd[column], 'JSD (by hand)': jensen_shannon_divergence(p, q),
    })
categorical = pd.DataFrame(rows, index=CAT_COLS)

display(categorical)
gap = max((categorical['L_INFTY (BigQuery)'] - categorical['L_INFTY (by hand)']).abs().max(),
          (categorical['JSD (BigQuery)'] - categorical['JSD (by hand)']).abs().max())
print(f'largest disagreement across all six numbers: {gap:.2e}')
```

Both metrics, all three columns, agreeing to the last bit — the largest disagreement across the six numbers is exactly zero. For a categorical column the reported value **is** a statistic of the data, and the worked example in the `MLOps/Model Monitoring/` readme is the whole algorithm.

The numeric side is where that stops being true.

### The numeric metric is not the divergence of the values

Jensen-Shannon divergence needs a discrete distribution, and `education_num` already is one — sixteen distinct integers. So take each distinct value as its own category and run the identical function.

```python
bq_numeric = drift(NUM_COLS, "0.1 AS numerical_default_threshold")

rows = []
for column in NUM_COLS:
    support = sorted(set(base_rows[column]) | set(compare_rows[column]))
    p, q = proportions(base_rows, column, support), proportions(compare_rows, column, support)
    rows.append({
        'distinct values': len(support),
        'JSD (BigQuery)': bq_numeric[column],
        'JSD over the values': jensen_shannon_divergence(p, q),
    })
numeric = pd.DataFrame(rows, index=NUM_COLS)
numeric['ratio'] = numeric['JSD (BigQuery)'] / numeric['JSD over the values']
display(numeric)
```

None of the three match, and the pattern of how they miss is the tell.

Jensen-Shannon divergence over a partition of the values is maximized by the finest partition — merging two bins can only move it down. One bin per distinct value **is** the finest partition, so `JSD over the values` is a **ceiling** on what any bucketing of that column's data can produce.

`age` and `hours_per_week` sit below their ceilings, which is exactly what a coarser summary of the same data should do. `education_num` sits **4.5x above** its ceiling. No bucketing of these two sets of values can produce that number, so whatever the function computed, it is not a divergence between the values at all.

`ML.TFDV_DESCRIBE` from Step 4 says what it is instead — the statistics proto carries the histogram the metric is actually built from.

```python
import json


def standard_histograms(where):
    """The STANDARD (equal-width) histogram per numeric column, out of the TFDV statistics proto."""
    proto = json.loads(client.query(f"""
        SELECT dataset_feature_statistics_list
        FROM ML.TFDV_DESCRIBE((SELECT {', '.join(NUM_COLS)} FROM {CENSUS} WHERE {where}))
    """).to_dataframe().iloc[0, 0])
    out = {}
    for feature in proto['datasets'][0]['features']:
        for histogram in feature['num_stats']['histograms']:
            # the proto carries two: 'QUANTILES', and the equal-width one, which is untyped
            if histogram.get('type') is None:
                out[feature['name']] = [(b.get('low_value', 0.0), b.get('high_value', 0.0), b['sample_count'])
                                        for b in histogram['buckets']]
    return out


base_hist, compare_hist = standard_histograms(BASE_POP), standard_histograms(COMPARE_POP)

side_by_side = pd.DataFrame({
    'base low': [b[0] for b in base_hist['education_num']],
    'base high': [b[1] for b in base_hist['education_num']],
    'base count': [round(b[2], 2) for b in base_hist['education_num']],
    'compare low': [b[0] for b in compare_hist['education_num']],
    'compare high': [b[1] for b in compare_hist['education_num']],
    'compare count': [round(b[2], 2) for b in compare_hist['education_num']],
})
display(side_by_side)
for label, hist in [('base', base_hist['education_num']), ('compare', compare_hist['education_num'])]:
    print(f'{label:8s} range {hist[0][0]} to {hist[-1][1]}, bucket width {hist[0][1] - hist[0][0]:.4f}')
```

Ten equal-width buckets — and **the width comes from each dataset's own range**. The base population's `education_num` starts at 1 and the comparison population's starts at 2, so the two grids are offset and share only their right-hand edge.

The counts are fractional because the histogram is interpolated rather than tallied: mass that spans a boundary is split across the buckets in proportion to how much of it falls on each side.

Line the two grids up on their combined set of edges, splitting each bucket's mass the same proportional way, and the function's numbers come back.

```python
def realign(histogram, edges):
    """Redistribute a histogram's mass onto a new set of edges, assuming uniform density within a bucket."""
    out = np.zeros(len(edges) - 1)
    for low, high, count in histogram:
        if high == low:  # a zero-width bucket lands whole in the bin containing it
            index = min(max(int(np.searchsorted(edges, low, side='right')) - 1, 0), len(out) - 1)
            out[index] += count
            continue
        for index in range(len(out)):
            overlap = min(high, edges[index + 1]) - max(low, edges[index])
            if overlap > 0:
                out[index] += count * overlap / (high - low)
    return out / out.sum()


rows = []
for column in NUM_COLS:
    edges = np.array(sorted({edge for low, high, _ in base_hist[column] + compare_hist[column]
                             for edge in (low, high)}))
    reproduced = jensen_shannon_divergence(realign(base_hist[column], edges),
                                           realign(compare_hist[column], edges))
    rows.append({'shared edges': len(edges),
                 'JSD (BigQuery)': bq_numeric[column],
                 'JSD over the histograms': reproduced,
                 'abs difference': abs(bq_numeric[column] - reproduced)})
display(pd.DataFrame(rows, index=NUM_COLS))
```

All three reproduce. The algorithm behind a numeric drift value is:

1. each input gets its **own** ten-bucket equal-width histogram, spanning its own minimum to its own maximum;
2. the two histograms are realigned onto the union of both sets of bucket edges, each bucket's mass split across the pieces in proportion to width;
3. Jensen-Shannon divergence, base 2, over the two aligned histograms.

The `shared edges` column says which columns step 2 actually moved. Eleven edges means the two ten-bucket grids landed on top of each other and the realignment is a no-op; twenty-one means they share a single edge and every bucket gets cut up.

That explains the earlier table. `hours_per_week` is the control — both populations span 1 to 99, the grids coincide, and its value is pure coarsening of a 94-valued column, which is why it lands well under its ceiling. `age` is the same story with 73 distinct values. `education_num` went the other way: with only sixteen distinct values, ten buckets throw away little, but one population starts at 1 and the other at 2, so the grids are offset and step 2 spreads each bucket's mass across a finer partition of mismatched pieces. That manufactures a difference the values themselves do not hold, and here it is far larger than anything the coarsening took away.

**This is not a bug, and it is worth being precise about what it is.** BigQuery is implementing TFDV's semantics, where the metric is defined on the statistics proto rather than on the data, and the proto's histogram is a fixed-size summary. Three properties combine to produce the gap: the bucket count is fixed at ten regardless of the column's cardinality, the edges are per-dataset rather than shared, and the realignment assumes uniform density inside a bucket. Any one of them on its own would be harmless.

Together they have an operational consequence.

### One row clears the alarm

Add a single row to the comparison population, holding a value the base population already contains in quantity, chosen only so that the two ranges match.

```python
def education_num_drift(compare_sql):
    return client.query(f"""
    SELECT input, ROUND(value, 6) AS value, threshold, is_anomaly
    FROM ML.VALIDATE_DATA_DRIFT(
      (SELECT education_num FROM {CENSUS} WHERE {BASE_POP}),
      ({compare_sql}),
      STRUCT(0.1 AS numerical_default_threshold))
    """).to_dataframe()


as_is = f'SELECT education_num FROM {CENSUS} WHERE {COMPARE_POP}'
print('comparison population as-is:')
display(education_num_drift(as_is))
print('with one row of education_num = 1 added:')
display(education_num_drift(as_is + ' UNION ALL SELECT 1'))

print(f"rows added: 1 of {len(compare_rows):,}")
print(f"base-population rows already holding education_num = 1: {(base_rows['education_num'] == 1).sum():,}")
print(f"comparison-population minimum, before: {compare_rows['education_num'].min()}   after: 1")
```

The alarm clears, from a single added row in over a thousand.

The row is not an outlier under any ordinary reading — its value is one the base population holds in quantity, and it is at the bottom of the scale rather than off it. It matters only because it is the comparison population's new minimum, which re-cuts all ten bucket edges and lands them exactly on the base population's.

Three things follow, in increasing order of effort:

- **On categorical columns, `L_INFTY` and Jensen-Shannon divergence are both statistics of the data.** There is no histogram in either one. Read them as they come.
- **A numeric drift value is only meaningful alongside the two ranges it was computed from.** `ML.DESCRIBE_DATA`'s `min` and `max` in `functions/exploration` (`functions/exploration/`) is the cheapest way to see them, and a range that moves between windows is the signal that the number will not be comparable.
- **Where a numeric column's range moves between windows for reasons that are not drift, bucketize it yourself** — `ML.BUCKETIZE` with fixed split points, or a `CASE` — and monitor the bucket label as a categorical column. Then the edges are yours, they are identical in every window, and the metric is back to being a statistic of the data.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT input, metric, ROUND(value, 4) AS value, threshold, is_anomaly
FROM ML.VALIDATE_DATA_DRIFT(
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass != ' Self-emp-inc'),
  (SELECT age, education_num, hours_per_week
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   WHERE workclass = ' Self-emp-inc'),
  STRUCT(0.1 AS numerical_default_threshold)
)
ORDER BY input
```

---
## Examples — BigFrames

There is **no** direct BigFrames equivalent for any of these four — nothing built in for skew, drift, or TFDV protos. (BigFrames does offer `DataFrame.describe()`, which is comparable-but-not-identical profiling; that comparison belongs with `ML.DESCRIBE_DATA` in `functions/exploration` (`functions/exploration/`).)

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
