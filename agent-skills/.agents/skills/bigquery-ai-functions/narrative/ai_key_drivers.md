# AI.KEY_DRIVERS — BigQuery AI Functions

`AI.KEY_DRIVERS` is a table-valued function that performs **key driver / contribution analysis**: it compares an interest set against a reference set and surfaces the data segments that most explain the change in a summable metric. No model creation, connection, or endpoint required.

**When to use it:**
- You want to explain *why* a metric moved between two periods (this month vs last)
- You want to compare a test group against a control group and attribute the difference
- You need to find which customer segments, geographies, or product categories drive a KPI change
- You want root-cause analysis without building and managing a contribution analysis model

**Alternatives:**
- Contribution analysis model + [`ML.GET_INSIGHTS`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ml-get-insights) — use when you need more than 12 dimensions or non-summable (ratio / by-category) metrics. `AI.KEY_DRIVERS` is the simpler, model-free equivalent for summable metrics. See `bq-ml/models/contribution_analysis` (`../bq-ml/models/contribution_analysis/`), which uses this exact dataset and interest/reference split for a direct comparison — it verifies both differentiators live and finds that `ML.GET_INSIGHTS`'s output schema actually differs by metric type (summable vs. ratio vs. category each return different derived-statistic columns), a nuance not covered here.

**Featured in:** `workflows/metric_diagnostics` (Metric Diagnostics) | `workflows/time_series_intelligence` (Time Series Intelligence)

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-key-drivers) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a temporary dataset for this notebook.

> This function doesn't require a connection or model — it uses end-user credentials automatically. See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
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
## Examples — SQL

Progressive examples from simplest to most advanced. Each cell adds one new concept.

`AI.KEY_DRIVERS` needs a single table containing both the **interest** (test) and **reference** (control) rows, distinguished by a `BOOL` column, plus a summable metric and 1–12 dimension columns.

### Setup: Create sample data from NYC Citi Bike

Materialize a compact slice of the public [NYC Citi Bike](https://console.cloud.google.com/marketplace/details/city-of-new-york/nyc-citi-bike) trips dataset. We compare **April 2017 (interest)** against **April 2016 (reference)** and ask which segments drove the change in total trip duration.

- **Metric:** `tripduration` (seconds) — a summable metric
- **Dimensions:** `usertype` (Customer / Subscriber), `gender`, `start_station_name`
- **Interest label:** `is_interest` — `TRUE` for 2017, `FALSE` for 2016

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.ai_key_drivers_trips` AS
SELECT
  tripduration,
  usertype,
  gender,
  start_station_name,
  (EXTRACT(YEAR FROM starttime) = 2017) AS is_interest
FROM `bigquery-public-data.new_york_citibike.citibike_trips`
WHERE EXTRACT(MONTH FROM starttime) = 4
  AND EXTRACT(YEAR FROM starttime) IN (2016, 2017)
  AND tripduration IS NOT NULL
"""
client.query(query).result()

# Show the interest/reference balance
client.query(f"""
  SELECT
    is_interest,
    COUNT(*) AS trips,
    SUM(tripduration) AS total_duration
  FROM `{PROJECT_ID}.{DATASET_ID}.ai_key_drivers_trips`
  GROUP BY is_interest
  ORDER BY is_interest
""").to_dataframe()
```

### 1. Basic key driver analysis

`AI.KEY_DRIVERS` requires `metric_col`, `dimension_cols`, and `interest_label_col`. Here `top_k => 15` returns the 15 highest-support insights and prunes the rest. The `["all"]` row is the whole-population change; the other rows are segments.

```python
query = f"""
SELECT * EXCEPT(usertype, gender, start_station_name)
FROM AI.KEY_DRIVERS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_key_drivers_trips`,
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender', 'start_station_name'],
  interest_label_col => 'is_interest',
  top_k => 15
)
"""
client.query(query).to_dataframe()
```

### 2. `SUM(metric)` form and sorting by contribution

`metric_col` accepts either the bare column name or `SUM(column_name)` — they are equivalent. Sort by `contribution` (the absolute size of each segment's movement) to rank the biggest drivers.

```python
query = f"""
SELECT
  drivers,
  metric_interest,
  metric_reference,
  difference,
  contribution
FROM AI.KEY_DRIVERS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_key_drivers_trips`,
  metric_col => 'SUM(tripduration)',
  dimension_cols => ['usertype', 'gender'],
  interest_label_col => 'is_interest',
  top_k => 10
)
ORDER BY contribution DESC
"""
client.query(query).to_dataframe()
```

### 3. Find segments defying the overall trend

`unexpected_difference` compares a segment's actual change to the change you'd *expect* given how every other segment moved. Large absolute values flag segments that behaved differently from the population — often the most actionable insights.

```python
query = f"""
SELECT
  drivers,
  difference,
  unexpected_difference,
  apriori_support
FROM AI.KEY_DRIVERS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_key_drivers_trips`,
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender', 'start_station_name'],
  interest_label_col => 'is_interest',
  top_k => 25
)
ORDER BY ABS(unexpected_difference) DESC
LIMIT 10
"""
client.query(query).to_dataframe()
```

### 4. Control segment size with `min_apriori_support`

`apriori_support` measures how large a segment is relative to the population. `min_apriori_support` (default `0.1`) excludes segments below the threshold. Use a smaller value to include more (smaller) segments, or `0` to include every segment.

> `min_apriori_support` and `top_k` are **mutually exclusive** — use one or the other.

```python
query = f"""
SELECT
  drivers,
  difference,
  ROUND(relative_difference, 3) AS pct_change,
  ROUND(apriori_support, 4) AS apriori_support
FROM AI.KEY_DRIVERS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_key_drivers_trips`,
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender'],
  interest_label_col => 'is_interest',
  min_apriori_support => 0.05
)
ORDER BY contribution DESC
"""
client.query(query).to_dataframe()
```

### 5. See redundant insights with `enable_pruning => FALSE`

By default `AI.KEY_DRIVERS` prunes redundant insights (a segment whose dimensions are a subset of a larger segment with the same metric). Set `enable_pruning => FALSE` to see the full unpruned breakdown — useful when you want every combination.

```python
query = f"""
SELECT
  drivers,
  difference,
  contribution
FROM AI.KEY_DRIVERS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_key_drivers_trips`,
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender'],
  interest_label_col => 'is_interest',
  min_apriori_support => 0.05,
  enable_pruning => FALSE
)
ORDER BY contribution DESC
"""
client.query(query).to_dataframe()
```

### 6. Interpreting the output columns

The output columns describe each segment's movement:
- `metric_interest` / `metric_reference` — the metric sum in each group
- `difference` = `metric_interest - metric_reference`
- `relative_difference` = `difference / metric_reference` (percent change; `NULL` when a segment only exists in the interest set)
- `contribution` = `ABS(difference)` (magnitude of the move)
- `apriori_support` — segment size relative to the population

```python
query = f"""
SELECT
  drivers,
  metric_interest,
  metric_reference,
  difference,
  ROUND(relative_difference, 3) AS pct_change,
  contribution
FROM AI.KEY_DRIVERS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_key_drivers_trips`,
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender', 'start_station_name'],
  interest_label_col => 'is_interest',
  top_k => 15
)
ORDER BY contribution DESC
"""
client.query(query).to_dataframe()
```

### 7. Inline subquery — build the interest/reference split on the fly

You don't need a pre-materialized table. Construct the `BOOL` interest column and the dimensions directly in a subquery over the raw data.

```python
query = f"""
SELECT * EXCEPT(usertype, gender)
FROM AI.KEY_DRIVERS(
  (SELECT
     tripduration,
     usertype,
     gender,
     (EXTRACT(YEAR FROM starttime) = 2017) AS is_interest
   FROM `bigquery-public-data.new_york_citibike.citibike_trips`
   WHERE EXTRACT(MONTH FROM starttime) = 4
     AND EXTRACT(YEAR FROM starttime) IN (2016, 2017)
     AND tripduration IS NOT NULL),
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender'],
  interest_label_col => 'is_interest',
  top_k => 10
)
ORDER BY contribution DESC
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same analysis using IPython magic commands. Magics let you write SQL directly in notebook cells without Python string wrapping.

Key patterns:
- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Key drivers with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  drivers,
  difference,
  contribution
FROM AI.KEY_DRIVERS(
  TABLE `statmike-mlops-349915.bq_ai_functions.ai_key_drivers_trips`,
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender'],
  interest_label_col => 'is_interest',
  top_k => 10
)
ORDER BY contribution DESC
```

---
## Examples — BigFrames

There is no native BigFrames API for `AI.KEY_DRIVERS` yet. Use `session.read_gbq_query()` to execute the SQL and return a BigFrames DataFrame.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

### AI.KEY_DRIVERS via `read_gbq_query()`

```python
query = f"""
SELECT
  drivers,
  difference,
  contribution
FROM AI.KEY_DRIVERS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.ai_key_drivers_trips`,
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender', 'start_station_name'],
  interest_label_col => 'is_interest',
  top_k => 10
)
ORDER BY contribution DESC
"""
bpd.read_gbq_query(query)
```
