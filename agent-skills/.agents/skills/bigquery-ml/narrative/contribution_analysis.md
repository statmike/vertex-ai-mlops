# Contribution Analysis — BigQuery ML

Train a **contribution analysis** (a.k.a. key-driver) model with `CREATE MODEL` (model_type = `CONTRIBUTION_ANALYSIS`) — detects which segments of multi-dimensional data most explain a change in a metric between a **test** set and a **control** set. Not a predictive model — there's no `ML.PREDICT`; insights are read afterward with `ML.GET_INSIGHTS`.

**Lifecycle:** `CREATE MODEL` → `ML.GET_INSIGHTS` (summable, ratio, and category metrics — three different output shapes) → more-than-12-dimension support → tuning knobs (`min_apriori_support`/`top_k_insights_by_apriori_support`, `pruning_method`) → confirm unsupported functions

**Fifteenth model type in this project, and the last one in Phase 3 — closes out the unsupervised + insight models phase.**

**Cross-link, not a duplicate:** the simplified, model-free equivalent — `bq-ai-functions/functions/ai_key_drivers` (`AI.KEY_DRIVERS`) (a single table-valued function, no `CREATE MODEL`) — is owned by the sibling `bq-ai-functions` project. This notebook uses the **same dataset and the same test/control split** as that sibling notebook (NYC Citi Bike, April 2016 vs. April 2017) specifically to make a direct comparison possible, and focuses on what `CONTRIBUTION_ANALYSIS` can do that `AI.KEY_DRIVERS` cannot:
- **Summable-ratio metrics** (`SUM(a)/SUM(b)`) and **summable-by-category metrics** (`SUM(a)/COUNT(DISTINCT b)`) — `AI.KEY_DRIVERS` only supports a single summable column.
- **More than 12 dimensions** — `AI.KEY_DRIVERS` caps `dimension_cols` at 12; verified `CONTRIBUTION_ANALYSIS` trains successfully with 13.
- For plain summable-metric use cases, prefer `AI.KEY_DRIVERS` first — it's simpler and skips the `CREATE MODEL` step entirely.

**Verified, not just documented:**
- **`ML.GET_INSIGHTS` has three genuinely different output schemas depending on the metric type** — summable, ratio, and category metrics each return a different set of derived-statistic columns (see Steps 2, 4, 6). This isn't called out in the official reference at the time this was tested.
- **The training query may contain ONLY the columns referenced by `contribution_metric`/`dimension_id_cols`/`is_test_col`** — any extra column errors immediately.
- **13 dimensions trains successfully, but costs real time** — ~13 minutes with all-low-cardinality dimensions, vs. ~5 seconds for a 3-dimension model on the same data. A separate attempt with several high-cardinality dimensions at the same count ran over 18 minutes and then failed with a generic internal error.

**Data:** [`bigquery-public-data.new_york_citibike.citibike_trips`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — test = April 2017, control = April 2016 (same split as the `AI.KEY_DRIVERS` sibling notebook). Metric: trip duration (seconds). Dimensions: user type, gender, start station (plus extra columns for the ratio/category examples).

**References:** `RESOURCES.md` (Full reference) | `bq-ai-functions/RESOURCES.md` (AI.KEY_DRIVERS reference) | [CREATE MODEL (contribution analysis) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-contribution-analysis) | [ML.GET_INSIGHTS docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-get-insights) | `setup` (Setup guide)

> **Training time:** most steps here train in seconds — this model type is fast. The exception is Step 7 (13 dimensions), which takes roughly 13 minutes. Budget ~20 minutes total for a full Restart & Run All.

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> Contribution analysis trains on data already in BigQuery — no connection or remote model required. The model is created with `CREATE MODEL` and stored in your dataset. See the `setup` (Setup Reference) for details.

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

### Materialize the training data

`n=1` (for the ratio-metric example) and `bikeid` (for the category-metric example) are included alongside the core columns.

> **GOTCHA (verified):** `CONTRIBUTION_ANALYSIS`'s training `SELECT` may contain **only** the columns referenced by `contribution_metric`, `dimension_id_cols`, and `is_test_col` — any extra column errors immediately (`"Only is_test, dimension id, and contribution metric columns are allowed as input columns"`). Each step below `SELECT`s only the exact subset of these columns it needs from this shared table.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_trips` AS
SELECT
  tripduration,
  1 AS n,
  bikeid,
  usertype,
  gender,
  start_station_name,
  (EXTRACT(YEAR FROM starttime) = 2017) AS is_test
FROM `bigquery-public-data.new_york_citibike.citibike_trips`
WHERE EXTRACT(MONTH FROM starttime) = 4
  AND EXTRACT(YEAR FROM starttime) IN (2016, 2017)
  AND tripduration IS NOT NULL
"""
client.query(query).result()
print('Table contribution_analysis_trips created')
```

---
## Step 1 — Create the model with `CREATE MODEL` (a summable metric)

`contribution_metric = 'SUM(tripduration)'` is the plain summable form — the same capability `bq-ai-functions/functions/ai_key_drivers` (`AI.KEY_DRIVERS`) covers with `metric_col='tripduration'`. Same data, same test/control split, same dimensions as that sibling notebook's Example 1, for direct comparison.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_summable`
OPTIONS(
  model_type = 'CONTRIBUTION_ANALYSIS',
  contribution_metric = 'SUM(tripduration)',
  dimension_id_cols = ['usertype', 'gender', 'start_station_name'],
  is_test_col = 'is_test',
  top_k_insights_by_apriori_support = 15,
  pruning_method = 'PRUNE_REDUNDANT_INSIGHTS'
) AS
SELECT tripduration, usertype, gender, start_station_name, is_test
FROM `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_trips`
"""
client.query(query).result()
print('Model contribution_analysis_summable created')
```

---
## Step 2 — Read insights with `ML.GET_INSIGHTS` (summable-metric output shape)

> **Verified output columns for a SUMMABLE metric:** `contributors`, `metric_test`, `metric_control`, `difference`, `relative_difference`, `unexpected_difference`, `relative_unexpected_difference`, `apriori_support`, `contribution` (= `ABS(difference)`) — plus each dimension broken out into its own column. This exactly matches `AI.KEY_DRIVERS`' output shape (`drivers`/`metric_interest`/`metric_reference` vs. `contributors`/`metric_test`/`metric_control` — same fields, different names).

```python
query = f"""
SELECT *
FROM ML.GET_INSIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_summable`)
ORDER BY contribution DESC
LIMIT 10
"""
client.query(query).to_dataframe()
```

---
## Step 3 — A summable-RATIO metric (beyond `AI.KEY_DRIVERS`)

`contribution_metric = 'SUM(a)/SUM(b)'` — `AI.KEY_DRIVERS` has no equivalent; it only supports a single summable column. Here `SUM(tripduration)/SUM(n)` is average trip duration, expressed as a ratio of two summable quantities (`n=1` per row, so `SUM(n)` = row count).

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_ratio`
OPTIONS(
  model_type = 'CONTRIBUTION_ANALYSIS',
  contribution_metric = 'SUM(tripduration)/SUM(n)',
  dimension_id_cols = ['usertype', 'gender', 'start_station_name'],
  is_test_col = 'is_test',
  top_k_insights_by_apriori_support = 15,
  pruning_method = 'PRUNE_REDUNDANT_INSIGHTS'
) AS
SELECT tripduration, n, usertype, gender, start_station_name, is_test
FROM `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_trips`
"""
client.query(query).result()
print('Model contribution_analysis_ratio created')
```

---
## Step 4 — `ML.GET_INSIGHTS` on the ratio model: a DIFFERENT output shape

> **GOTCHA (verified):** a ratio metric's `ML.GET_INSIGHTS` output is **not** the same shape as Step 2's summable output. `difference`/`relative_difference`/`unexpected_difference`/`relative_unexpected_difference` are gone; in their place: `metric_test_over_metric_control`, `metric_test_over_complement`, `metric_control_over_complement`, and `aumann_shapley_attribution`. `contribution` here **equals `ABS(aumann_shapley_attribution)`** (a Shapley-value-based attribution) — not `ABS(difference)` as it is for summable metrics, but the same "take the absolute value" pattern (verified on rows where `aumann_shapley_attribution` is negative, e.g. `usertype=Subscriber`: `aumann_shapley_attribution=-49.86`, `contribution=49.86`). Don't assume `ML.GET_INSIGHTS` has one fixed output schema across metric types.

```python
query = f"""
SELECT *
FROM ML.GET_INSIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_ratio`)
ORDER BY contribution DESC
LIMIT 10
"""
client.query(query).to_dataframe()
```

---
## Step 5 — A summable-by-CATEGORY metric (beyond `AI.KEY_DRIVERS`)

`contribution_metric = 'SUM(a)/COUNT(DISTINCT b)'` — also beyond `AI.KEY_DRIVERS`. `SUM(tripduration)/COUNT(DISTINCT bikeid)` is total ride minutes accumulated per unique bike used — a bike-utilization measure.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_category`
OPTIONS(
  model_type = 'CONTRIBUTION_ANALYSIS',
  contribution_metric = 'SUM(tripduration)/COUNT(DISTINCT bikeid)',
  dimension_id_cols = ['usertype', 'gender', 'start_station_name'],
  is_test_col = 'is_test',
  top_k_insights_by_apriori_support = 15,
  pruning_method = 'PRUNE_REDUNDANT_INSIGHTS'
) AS
SELECT tripduration, bikeid, usertype, gender, start_station_name, is_test
FROM `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_trips`
"""
client.query(query).result()
print('Model contribution_analysis_category created')
```

---
## Step 6 — `ML.GET_INSIGHTS` on the category model: a THIRD output shape

> **GOTCHA (verified):** summable-by-category's output is a third distinct shape — `difference`/`relative_difference` return (like summable), but `unexpected_difference`/`relative_unexpected_difference` are replaced by `metric_test_over_population`/`metric_control_over_population`. `contribution` here is `ABS(difference)` again (like summable), not `aumann_shapley_attribution`. Three metric types, three different `ML.GET_INSIGHTS` schemas — verified directly, not called out in the official reference at the time this was tested.

```python
query = f"""
SELECT *
FROM ML.GET_INSIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_category`)
ORDER BY contribution DESC
LIMIT 10
"""
client.query(query).to_dataframe()
```

---
## Step 7 — More than 12 dimensions (beyond `AI.KEY_DRIVERS`' cap)

`AI.KEY_DRIVERS` caps `dimension_cols` at 12. This step builds a second table with 13 dimension columns — all deliberately low-cardinality, to isolate dimension *count* from per-dimension *cardinality*.

> **GOTCHA (verified, real cost tradeoff):** this trains successfully but takes roughly **13 minutes** — vs. ~5 seconds for Step 1's 3-dimension model on the same row count. More dimensions is combinatorially more expensive, even at low cardinality per dimension. A separate attempt with 13 dimensions where several were **high-cardinality** (raw station IDs, individual bike IDs) ran for over 18 minutes and then failed with a generic internal-error message rather than a clean validation error — BigQuery framed it as "usually a transient issue," but it did not reproduce with low-cardinality dimensions at the same count, suggesting per-dimension cardinality (not just dimension count) drives the real cost/risk.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_trips_lowcard` AS
SELECT
  tripduration,
  usertype,
  gender,
  CAST(EXTRACT(HOUR FROM starttime) AS STRING) AS start_hour,
  CAST(EXTRACT(DAYOFWEEK FROM starttime) AS STRING) AS day_of_week,
  CAST(EXTRACT(DAY FROM starttime) AS STRING) AS day_of_month,
  CASE WHEN birth_year < 1970 THEN 'older' WHEN birth_year < 1990 THEN 'middle' ELSE 'younger' END AS age_band,
  CASE WHEN start_station_id = end_station_id THEN 'round_trip' ELSE 'one_way' END AS trip_type,
  CASE WHEN tripduration > 600 THEN 'long' ELSE 'short' END AS duration_band,
  CASE WHEN EXTRACT(DAYOFWEEK FROM starttime) IN (1,7) THEN 'weekend' ELSE 'weekday' END AS is_weekend,
  CASE WHEN EXTRACT(HOUR FROM starttime) BETWEEN 7 AND 9 OR EXTRACT(HOUR FROM starttime) BETWEEN 16 AND 18 THEN 'rush' ELSE 'non_rush' END AS is_rush_hour,
  CASE WHEN EXTRACT(HOUR FROM starttime) BETWEEN 22 AND 23 OR EXTRACT(HOUR FROM starttime) BETWEEN 0 AND 5 THEN 'night' ELSE 'day' END AS is_night,
  CAST(NTILE(4) OVER (ORDER BY tripduration) AS STRING) AS duration_quartile,
  CASE WHEN EXTRACT(DAY FROM starttime) <= 15 THEN 'first_half' ELSE 'second_half' END AS month_half,
  (EXTRACT(YEAR FROM starttime) = 2017) AS is_test
FROM `bigquery-public-data.new_york_citibike.citibike_trips`
WHERE EXTRACT(MONTH FROM starttime) = 4
  AND EXTRACT(YEAR FROM starttime) IN (2016, 2017)
  AND tripduration IS NOT NULL
"""
client.query(query).result()
print('Table contribution_analysis_trips_lowcard created')
```

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_13dims`
OPTIONS(
  model_type = 'CONTRIBUTION_ANALYSIS',
  contribution_metric = 'SUM(tripduration)',
  dimension_id_cols = ['usertype', 'gender', 'start_hour', 'day_of_week', 'day_of_month', 'age_band', 'trip_type', 'duration_band', 'is_weekend', 'is_rush_hour', 'is_night', 'duration_quartile', 'month_half'],
  is_test_col = 'is_test',
  top_k_insights_by_apriori_support = 10,
  pruning_method = 'PRUNE_REDUNDANT_INSIGHTS'
) AS
SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_trips_lowcard`
"""
client.query(query).result()
print('Model contribution_analysis_13dims created (13 dimensions)')
```

```python
query = f"""
SELECT contributors, contribution
FROM ML.GET_INSIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_13dims`)
ORDER BY contribution DESC
LIMIT 10
"""
client.query(query).to_dataframe()
```

---
## Step 8 — `min_apriori_support`, `top_k_insights_by_apriori_support`, and `pruning_method`

> **Verified:** `min_apriori_support` and `top_k_insights_by_apriori_support` are genuinely mutually exclusive — specifying both errors immediately (`"Please specify only one of the MIN_APRIORI_SUPPORT or TOP_K_INSIGHTS_BY_APRIORI_SUPPORT options."`).
>
> **Verified:** `pruning_method` has a dramatic effect on output size. `NO_PRUNING` with a low `min_apriori_support` (0.001) on the same 3 dimensions as Step 1 returns 1,559 insight rows; Step 1's `PRUNE_REDUNDANT_INSIGHTS` + `top_k=15` returns exactly 15. Use `top_k_insights_by_apriori_support` + `PRUNE_REDUNDANT_INSIGHTS` (the default in every other step here) unless you specifically need every subset-redundant segment.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_no_pruning`
OPTIONS(
  model_type = 'CONTRIBUTION_ANALYSIS',
  contribution_metric = 'SUM(tripduration)',
  dimension_id_cols = ['usertype', 'gender', 'start_station_name'],
  is_test_col = 'is_test',
  min_apriori_support = 0.001,
  pruning_method = 'NO_PRUNING'
) AS
SELECT tripduration, usertype, gender, start_station_name, is_test
FROM `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_trips`
"""
client.query(query).result()
print('Model contribution_analysis_no_pruning created')
```

```python
query = f"""
SELECT COUNT(*) AS n_insights
FROM ML.GET_INSIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_no_pruning`)
"""
client.query(query).to_dataframe()
```

---
## Step 9 — Functions that do NOT apply to this model type

> **GOTCHA (verified):** no `TRANSFORM` clause — errors immediately (`"Transform clause is not supported for the model type CONTRIBUTION_ANALYSIS"`).
>
> **GOTCHA (verified):** `ML.PREDICT` and `ML.EVALUATE` both error, but with unhelpful messages that don't clearly say "not supported for this model type" — `ML.PREDICT` complains a `contributors` column is missing from the input; `ML.EVALUATE` (called with no arguments, as below) says the model "was not evaluated during training" and asks for data to evaluate with. Passing a data argument doesn't help either — it then asks for a `label` column instead, which this model type doesn't have. This model type simply has no `ML.PREDICT`/`ML.EVALUATE` — `ML.GET_INSIGHTS` is the only way to read results.

```python
# ML.PREDICT — expected to fail: "Column contributors is not found in the input data to the PREDICT function."
try:
    query = f"""SELECT * FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_summable`, (SELECT 1))"""
    client.query(query).result()
except Exception as e:
    print(f'ML.PREDICT failed as expected:\n{e}')
```

```python
# ML.EVALUATE — expected to fail: this model type produces no predictions/labels to evaluate.
try:
    query = f"""SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.contribution_analysis_summable`)"""
    client.query(query).result()
except Exception as e:
    print(f'ML.EVALUATE failed as expected:\n{e}')
```

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Get insights with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT contributors, contribution
FROM ML.GET_INSIGHTS(MODEL `statmike-mlops-349915.bq_ml.contribution_analysis_summable`)
ORDER BY contribution DESC
LIMIT 5
```

---
## Examples — BigFrames

BigFrames provides a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood. **There is no `bigframes.ml` wrapper for `CONTRIBUTION_ANALYSIS`** — confirmed by listing every submodule of the live installed `bigframes.ml` package (`cluster`, `decomposition`, `ensemble`, `forecasting`, `linear_model`, `remote`, etc. — no contribution-analysis module among them). Run the SQL `CREATE MODEL ... CONTRIBUTION_ANALYSIS` / `ML.GET_INSIGHTS` shown above via `bpd.read_gbq_query()` or the `%%bigquery` magics instead.
