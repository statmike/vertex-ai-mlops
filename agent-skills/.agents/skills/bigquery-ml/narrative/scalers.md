# Scalers — BigQuery ML Model-Free Functions

Five manual feature-preprocessing functions that rescale numerical inputs into ML-ready features: `ML.STANDARD_SCALER`, `ML.MIN_MAX_SCALER`, `ML.MAX_ABS_SCALER`, `ML.ROBUST_SCALER` (all **analytic** — require an empty `OVER()`), and `ML.NORMALIZER` (a row-wise **scalar** function — no `OVER()`, operates on an `ARRAY`). No model is trained by these functions themselves — they transform data directly, standalone or inside a `CREATE MODEL ... TRANSFORM(...)` clause.

**When to use these:**
- Put numerical features on a common scale for distance/gradient-based models (`KMEANS`, `LINEAR_REG`/`LOGISTIC_REG`, `DNN_*`, `PCA`).
- `ML.MIN_MAX_SCALER` when a bounded `[0, 1]` range is specifically required (e.g. feeding a sigmoid-activated network layer).
- `ML.ROBUST_SCALER` when a column has outliers (centers on median, scales by IQR — unaffected by extreme values).
- `ML.MAX_ABS_SCALER` to preserve sign/sparsity (no centering, no shift toward zero).
- `ML.NORMALIZER` to give each row's feature vector unit norm (e.g. for embedding-like vectors feeding `VECTOR_SEARCH`/`ML.DISTANCE` — see `functions/distance` (`functions/distance/`)).

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — the same 3-4 numeric measurements used by `models/kmeans` (K-Means), `models/pca` (PCA), `models/autoencoder` (Autoencoder), and `models/transform_only` (Transform-Only), so results here connect directly to those notebooks.

**Featured in:** `models/transform_only` (`models/transform_only/`) (chains `ML.STANDARD_SCALER`/`ML.ROBUST_SCALER` into one reusable pipeline), `models/logistic_regression` (`models/logistic_regression/`) (`ML.STANDARD_SCALER` inline in a `TRANSFORM` clause).

**References:** `RESOURCES.md` (Full reference) | [Manual feature preprocessing docs](https://cloud.google.com/bigquery/docs/manual-preprocessing) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No connection needed — every function here runs entirely in-warehouse.

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
## Step 1 — `ML.STANDARD_SCALER`: z-score, and a real "matches AVG/STDDEV" gotcha

Analytic function, requires `OVER()`. Computes `(x - AVG(x)) / STDDEV(x)` across all rows — but which `STDDEV`?

> **GOTCHA (verified live):** `ML.STANDARD_SCALER` uses the **population** standard deviation (`STDDEV_POP`, divides by N), not the **sample** standard deviation BigQuery's plain `STDDEV()`/`STDDEV_SAMP()` computes by default (divides by N-1). The two differ by a small but real amount. If you ever try to "sanity check" `ML.STANDARD_SCALER` by hand-computing `(x - AVG(x)) / STDDEV(x)`, it will **not** match — you need `STDDEV_POP(x)` specifically.

```python
query = """
SELECT
  culmen_length_mm,
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS standard_scaled,
  (culmen_length_mm - AVG(culmen_length_mm) OVER()) / STDDEV_SAMP(culmen_length_mm) OVER() AS manual_sample_stddev,
  (culmen_length_mm - AVG(culmen_length_mm) OVER()) / STDDEV_POP(culmen_length_mm) OVER() AS manual_population_stddev
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
ORDER BY culmen_length_mm
LIMIT 5
"""
client.query(query).to_dataframe()
```

---
## Step 2 — `ML.MIN_MAX_SCALER`: bounded `[0, 1]`, and a verified prediction-time capping behavior

`(x - MIN) / (MAX - MIN)` — the only scaler here with a hard, bounded output range.

```python
query = """
SELECT
  culmen_length_mm,
  ML.MIN_MAX_SCALER(culmen_length_mm) OVER() AS min_max_scaled
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
ORDER BY culmen_length_mm
LIMIT 5
"""
client.query(query).to_dataframe()
```

**GOTCHA (verified live via a real model):** when `ML.MIN_MAX_SCALER` is embedded in a `TRANSFORM` clause, values outside the training min/max are **capped** to 0 or 1 at prediction time — not extrapolated past the bounds. Trained on `culmen_length_mm` in `[32.1, 59.6]`:

In production, this means any value beyond the training range collapses to the same `0`/`1` as the actual training min/max — the model can no longer distinguish a mildly out-of-range input from an extreme one (`60.0` and `600.0` would both map to exactly `1.0`).

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.scratch_minmax_capping_demo`
TRANSFORM(
  species,
  ML.MIN_MAX_SCALER(culmen_length_mm) OVER() AS culmen_length_scaled
)
OPTIONS(model_type='LOGISTIC_REG', input_label_cols=['species']) AS
SELECT species, culmen_length_mm
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()

query = """
SELECT culmen_length_mm, culmen_length_scaled
FROM ML.TRANSFORM(
  MODEL `{project}.{dataset}.scratch_minmax_capping_demo`,
  (SELECT * FROM UNNEST([32.1, 59.6, 20.0, 100.0]) AS culmen_length_mm)
)
""".format(project=PROJECT_ID, dataset=DATASET_ID)
df = client.query(query).to_dataframe()

client.query(f"DROP MODEL IF EXISTS `{PROJECT_ID}.{DATASET_ID}.scratch_minmax_capping_demo`").result()
df
```

---
## Step 3 — `ML.MAX_ABS_SCALER`: preserves sign, no centering

Divides by the max absolute value only — unlike the other scalers, it never shifts the data toward zero, so sign and relative sparsity survive intact. Best for data where the sign itself is meaningful. Switching to a small literal array here (rather than a `penguins` column) on purpose — every physical measurement in this dataset is positive, so sign preservation wouldn't be visible on real data; a column with genuine negative values is needed to see the effect.

```python
query = """
SELECT x, ML.MAX_ABS_SCALER(x) OVER() AS max_abs_scaled
FROM UNNEST([-10.0, -5.0, 0.0, 5.0, 8.0, 10.0]) AS x
ORDER BY x
"""
client.query(query).to_dataframe()
```

---
## Step 4 — `ML.ROBUST_SCALER`: outlier-robust, with all 3 optional parameters

`(x - median) / (q_hi - q_lo)` by default — centers on the median and scales by the interquartile range instead of mean/stddev, so extreme outliers don't distort the result. All three parameters are optional: `quantile_range` (default `[25, 75]`), `with_median` (default `TRUE`), `with_quantile_range` (default `TRUE`).

```python
query = """
SELECT
  culmen_length_mm,
  ML.ROBUST_SCALER(culmen_length_mm) OVER() AS robust_default,
  ML.ROBUST_SCALER(culmen_length_mm, [10, 90]) OVER() AS robust_custom_quantile_range,
  ML.ROBUST_SCALER(culmen_length_mm, [25, 75], FALSE) OVER() AS robust_no_median,
  ML.ROBUST_SCALER(culmen_length_mm, [25, 75], TRUE, FALSE) OVER() AS robust_no_scaling
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
ORDER BY culmen_length_mm
LIMIT 5
"""
client.query(query).to_dataframe()
```

**Outlier robustness, proven side by side:** inject one extreme outlier (`500`) into an otherwise tightly-clustered column (`10`-`14`). `ML.STANDARD_SCALER`'s mean/stddev get dragged toward the outlier, compressing every normal point into an indistinguishable narrow band. `ML.ROBUST_SCALER`'s median/IQR ignore the outlier entirely — normal points stay well-spread.

```python
query = """
WITH data AS (
  SELECT x FROM UNNEST([10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 500.0]) AS x
)
SELECT
  x,
  ROUND(ML.STANDARD_SCALER(x) OVER(), 3) AS standard_scaled,
  ROUND(ML.ROBUST_SCALER(x) OVER(), 3) AS robust_scaled
FROM data
ORDER BY x
"""
client.query(query).to_dataframe()
```

---
## Step 5 — `ML.NORMALIZER`: row-wise unit-norm scaling of an `ARRAY` (no `OVER()`)

The odd one out: a **scalar** function, not analytic — it doesn't look at other rows at all, so it takes no `OVER()`. Normalizes each row's `ARRAY` to unit p-norm independently. Default `p=2` (Euclidean); also accepts `p=1` (Manhattan), `p=0`, or `p=+inf` (via `CAST('+inf' AS FLOAT64)`).

```python
query = """
SELECT arr,
  ML.NORMALIZER(arr) AS p2_default,
  ML.NORMALIZER(arr, 1) AS p1_manhattan,
  ML.NORMALIZER(arr, 0) AS p0,
  ML.NORMALIZER(arr, CAST('+inf' AS FLOAT64)) AS p_inf
FROM (SELECT [3.0, 4.0] AS arr)
"""
client.query(query).to_dataframe()
```

Applied to a real per-penguin feature vector — each **row** gets unit norm, not each column. This is semantically different from the column scalers above: `ML.NORMALIZER` normalizes *across* the elements of one row's array.

```python
query = """
SELECT
  species,
  [culmen_length_mm, culmen_depth_mm, flipper_length_mm] AS measurements,
  ML.NORMALIZER([culmen_length_mm, culmen_depth_mm, flipper_length_mm]) AS normalized
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL
LIMIT 3
"""
client.query(query).to_dataframe()
```

---
## Step 6 — NULLs pass through untouched — scalers don't impute

`body_mass_g` has 2 `NULL` rows in this dataset. Scalers don't handle missing values — a `NULL` input produces a `NULL` output (not an error, not `0`). Downloaded into a pandas DataFrame, that `NULL` renders as `NaN` — normal numeric-dtype behavior, not a BQML bug. Pair scalers with `ML.IMPUTER` first if `NULL`s need a real value (see `functions/feature_engineering` (`functions/feature_engineering/`)).

```python
query = """
SELECT body_mass_g, ML.STANDARD_SCALER(body_mass_g) OVER() AS scaled
FROM `bigquery-public-data.ml_datasets.penguins`
ORDER BY body_mass_g IS NULL DESC
LIMIT 3
"""
client.query(query).to_dataframe()
```

---
## Step 7 — All four analytic scalers side by side, one column

The same `culmen_length_mm` values through all four analytic scalers at once — a direct visual comparison of output range and shape.

```python
query = """
SELECT
  culmen_length_mm,
  ROUND(ML.STANDARD_SCALER(culmen_length_mm) OVER(), 3) AS standard,
  ROUND(ML.MIN_MAX_SCALER(culmen_length_mm) OVER(), 3) AS min_max,
  ROUND(ML.MAX_ABS_SCALER(culmen_length_mm) OVER(), 3) AS max_abs,
  ROUND(ML.ROBUST_SCALER(culmen_length_mm) OVER(), 3) AS robust
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
ORDER BY culmen_length_mm
LIMIT 5
"""
client.query(query).to_dataframe()
```

---
## Step 8 — Embedded in a real `CREATE MODEL TRANSFORM` — auto-applies at `ML.PREDICT`

Contrast with `models/transform_only` (`models/transform_only/`): that notebook builds a **standalone** `TRANSFORM_ONLY` pipeline, which must be explicitly re-applied via `ML.TRANSFORM` before every downstream `ML.PREDICT` (and silently mispredicts if you forget — see its Step 7). **This** model embeds the `TRANSFORM` directly on the estimator itself, so `ML.PREDICT` on raw, unscaled input automatically applies the exact same scaling used at training time — no separate step, no risk of that gotcha.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.scalers_downstream_logistic_regression`
TRANSFORM(
  species,
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS culmen_length_scaled,
  ML.STANDARD_SCALER(culmen_depth_mm) OVER() AS culmen_depth_scaled,
  ML.ROBUST_SCALER(flipper_length_mm) OVER() AS flipper_length_scaled
)
OPTIONS(model_type = 'LOGISTIC_REG', input_label_cols = ['species']) AS
SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model scalers_downstream_logistic_regression created')

query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.scalers_downstream_logistic_regression`)"
client.query(query).to_dataframe()
```

`ML.PREDICT` on **raw, unscaled** `culmen_length_mm`/`culmen_depth_mm`/`flipper_length_mm` values — no `ML.TRANSFORM` call needed first, since the scaling is baked into the model:

```python
query = f"""
SELECT species, predicted_species
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.scalers_downstream_logistic_regression`,
  (SELECT species, culmen_length_mm, culmen_depth_mm, flipper_length_mm
   FROM `bigquery-public-data.ml_datasets.penguins`
   WHERE culmen_length_mm IS NOT NULL AND culmen_depth_mm IS NOT NULL AND flipper_length_mm IS NOT NULL
   LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  culmen_length_mm,
  ML.STANDARD_SCALER(culmen_length_mm) OVER() AS standard_scaled,
  ML.ROBUST_SCALER(culmen_length_mm) OVER() AS robust_scaled
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE culmen_length_mm IS NOT NULL
ORDER BY culmen_length_mm
LIMIT 5
```

---
## Examples — BigFrames

`bigframes.ml.preprocessing` has real classes for **three** of the five: `StandardScaler`, `MinMaxScaler`, `MaxAbsScaler` (verified via `inspect.signature` — all no-arg constructors, `.fit()`/`.transform()` pattern). There is **no** `RobustScaler` or `Normalizer` class in BigFrames — use SQL `TRANSFORM` for full parity on those two.

```python
import bigframes.pandas as bpd
from bigframes.ml.preprocessing import StandardScaler

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

df = bpd.read_gbq(
    "SELECT culmen_length_mm FROM `bigquery-public-data.ml_datasets.penguins` WHERE culmen_length_mm IS NOT NULL"
)
scaler = StandardScaler()
scaler.fit(df[['culmen_length_mm']])
scaler.transform(df[['culmen_length_mm']]).peek()
```
