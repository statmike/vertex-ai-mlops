# Hierarchical Forecasting — BigQuery ML

Compare two ways of producing forecasts that are consistent across a hierarchy (`State → County → City → Store`): BigQuery ML's built-in **bottom-up** reconciliation (`hierarchical_time_series_cols`, already covered in `models/arima_plus` (`models/arima_plus/`) Step 10) versus a from-scratch **top-down** disaggregation (the forecast-proportions method), which BigQuery ML has no built-in option for at all.

**Models used:** `ARIMA_PLUS`
**Functions used:** `ML.FORECAST`, `ML.EVALUATE`

Modernizes `Applied ML/Forecasting/BigQuery ML For Hierarchical Forecasting.ipynb`. This workflow assumes the bottom-up mechanics are already understood (see `models/arima_plus/` Step 10 for that verification) and focuses on the harder, uncovered half: building a top-down alternative and comparing its accuracy against the built-in approach at every level of a real hierarchy.

**Data:** [`bigquery-public-data.iowa_liquor_sales.sales`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets), a real `State → County → City → Store` hierarchy. Scoped to 2 counties (POLK, LINN), 2 cities each (Des Moines/Ankeny; Cedar Rapids/Marion), 2 stores each — 8 stores, 15 series total across all 4 levels. Aggregated to **weekly** totals, not daily — real per-store sale-day coverage is only ~15-30% at daily granularity (most liquor stores don't sell every single day) versus ~90%+ at weekly, so weekly avoids most of the interpolation daily granularity would otherwise require. TEST = the last 8 weeks; `horizon = 8`.

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> This workflow trains `ARIMA_PLUS` models on data already in BigQuery — no connection or remote model required. See the `setup` (Setup Reference) for details.

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

`county`/`city` in the raw source data are occasionally inconsistent for the same `store_number` (a handful of historical rows have them blank) — GOTCHA (verified): rather than trust those columns directly, this maps each store to its county/city explicitly, so every row for a given store always lands in the same hierarchy branch. `splits` marks the last 8 weeks as `TEST`.

```python
STORE_COUNTY_CITY = {
    '2190': ('POLK', 'DES MOINES'),   # Central City Liquor
    '4829': ('POLK', 'DES MOINES'),   # Central City 2
    '2666': ('POLK', 'ANKENY'),       # Hy-Vee Food Store #2
    '4083': ('POLK', 'ANKENY'),       # Fareway Stores #909
    '3773': ('LINN', 'CEDAR RAPIDS'), # Benz Distributing
    '2647': ('LINN', 'CEDAR RAPIDS'), # Hy-Vee #7
    '3868': ('LINN', 'MARION'),       # Wal-Mart 3630
    '4180': ('LINN', 'MARION'),       # Smokin' Joe's #10
}
county_case = ' '.join(f"WHEN '{s}' THEN '{c}'" for s, (c, _) in STORE_COUNTY_CITY.items())
city_case = ' '.join(f"WHEN '{s}' THEN '{ci}'" for s, (_, ci) in STORE_COUNTY_CITY.items())
store_list = ', '.join(f"'{s}'" for s in STORE_COUNTY_CITY)

query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_prepped` AS
WITH weekly AS (
  SELECT
    CASE store_number {county_case} END AS county,
    CASE store_number {city_case} END AS city,
    store_number,
    DATE_TRUNC(date, WEEK) AS week,
    SUM(bottles_sold) AS units_sold
  FROM `bigquery-public-data.iowa_liquor_sales.sales`
  WHERE store_number IN ({store_list}) AND date BETWEEN '2018-01-01' AND '2024-12-31'
  GROUP BY county, city, store_number, week
)
SELECT *, IF(week > DATE('2024-11-03'), 'TEST', 'TRAIN') AS splits
FROM weekly
"""
client.query(query).result()

query = f"""
SELECT county, city, store_number, COUNT(*) AS n_weeks, MIN(week) AS min_week, MAX(week) AS max_week
FROM `{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_prepped`
GROUP BY county, city, store_number
ORDER BY county, city, store_number
"""
client.query(query).to_dataframe()
```

---
## Step 1 — Base-level forecasting (no hierarchy)

One `ARIMA_PLUS` model, `time_series_id_col = ['county', 'city', 'store_number']` — each store forecast independently, with no relationship to its city/county totals. This is the baseline every hierarchical technique below is compared against implicitly: without hierarchy support, aggregating these forecasts up to city/county/state would just be an unreconciled sum with no guarantee of matching a top-level forecast trained directly on the aggregate.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.hier_base_forecast`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'week',
  time_series_data_col = 'units_sold',
  time_series_id_col = ['county', 'city', 'store_number'],
  data_frequency = 'WEEKLY',
  holiday_region = 'US',
  horizon = 8
) AS
SELECT county, city, store_number, week, units_sold
FROM `{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_prepped`
WHERE splits = 'TRAIN'
"""
client.query(query).result()
print('Model hier_base_forecast created')
```

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.hier_base_forecast`,
  (SELECT county, city, store_number, week, units_sold
   FROM `{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_prepped` WHERE splits = 'TEST'),
  STRUCT(TRUE AS perform_aggregation))
ORDER BY county, city, store_number
"""
client.query(query).to_dataframe()
```

---
## Step 2 — Built-in bottom-up hierarchical forecasting

Add `hierarchical_time_series_cols = ['county', 'city', 'store_number']` — the mechanics (three levels reconciled in one model, bottom-up summation, no top-down option) are already verified in detail in `models/arima_plus` (`models/arima_plus/`) Step 10. Repeating just enough here to confirm it on this specific 4-level hierarchy (state total + county + city + store, one level deeper than the Citi Bike example) before comparing it against the custom top-down approach below.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.hier_bottomup_forecast`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'week',
  time_series_data_col = 'units_sold',
  time_series_id_col = ['county', 'city', 'store_number'],
  hierarchical_time_series_cols = ['county', 'city', 'store_number'],
  data_frequency = 'WEEKLY',
  holiday_region = 'US',
  horizon = 8
) AS
SELECT county, city, store_number, week, units_sold
FROM `{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_prepped`
WHERE splits = 'TRAIN'
"""
client.query(query).result()
print('Model hier_bottomup_forecast created')
```

```python
# Confirmed bottom-up, exact to the penny: county forecast == sum of its cities' forecasts,
# and the overall state total == sum of the counties. Same mechanic verified in models/arima_plus/,
# now confirmed one hierarchy level deeper (county -> city -> store, plus the state total).
query = f"""
WITH f AS (
  SELECT county, city, store_number, forecast_timestamp, forecast_value
  FROM ML.FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.hier_bottomup_forecast`, STRUCT(8 AS horizon))
)
SELECT
  forecast_timestamp,
  (SELECT forecast_value FROM f WHERE county = 'POLK' AND city IS NULL
     AND forecast_timestamp = t.forecast_timestamp) AS polk_direct,
  (SELECT SUM(forecast_value) FROM f WHERE county = 'POLK' AND city IS NOT NULL AND store_number IS NULL
     AND forecast_timestamp = t.forecast_timestamp) AS polk_summed_from_cities,
  (SELECT forecast_value FROM f WHERE county IS NULL
     AND forecast_timestamp = t.forecast_timestamp) AS state_direct,
  (SELECT SUM(forecast_value) FROM f WHERE county IS NOT NULL AND city IS NULL
     AND forecast_timestamp = t.forecast_timestamp) AS state_summed_from_counties
FROM (SELECT DISTINCT forecast_timestamp FROM f) t
ORDER BY forecast_timestamp
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Custom top-down forecasting (forecast proportions)

BigQuery ML has no built-in top-down option — disaggregating a higher-level forecast down through the hierarchy requires a custom implementation. The **forecast-proportions** method: forecast every level of the hierarchy *independently* as flat, unrelated series, then work top to bottom, splitting each level's already-finalized forecast across its children in proportion to their own independent (raw) forecasts.

### Flatten every hierarchy level into one series set

Represent the state total, each county, each city, and each store as its own row in one long table — tagged with its own level, its own series id, and its parent's series id. One `ARIMA_PLUS` model then forecasts all 15 series (1 state + 2 counties + 4 cities + 8 stores) independently, with no relationship between them yet.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_topdown_flat` AS
WITH state_level AS (
  SELECT 'state' AS hierarchy_level, 'Iowa' AS hierarchy_series, 'none' AS hierarchy_parent,
    week, SUM(units_sold) AS units_sold, splits
  FROM `{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_prepped`
  GROUP BY week, splits
),
county_level AS (
  SELECT 'county' AS hierarchy_level, county AS hierarchy_series, 'Iowa' AS hierarchy_parent,
    week, SUM(units_sold) AS units_sold, splits
  FROM `{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_prepped`
  GROUP BY county, week, splits
),
city_level AS (
  SELECT 'city' AS hierarchy_level, city AS hierarchy_series, county AS hierarchy_parent,
    week, SUM(units_sold) AS units_sold, splits
  FROM `{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_prepped`
  GROUP BY city, county, week, splits
),
store_level AS (
  SELECT 'store' AS hierarchy_level, store_number AS hierarchy_series, city AS hierarchy_parent,
    week, units_sold, splits
  FROM `{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_prepped`
)
SELECT * FROM state_level
UNION ALL SELECT * FROM county_level
UNION ALL SELECT * FROM city_level
UNION ALL SELECT * FROM store_level
"""
client.query(query).result()

query = f"""
SELECT hierarchy_level, COUNT(DISTINCT hierarchy_series) AS n_series
FROM `{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_topdown_flat`
GROUP BY hierarchy_level
"""
client.query(query).to_dataframe()
```

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.hier_topdown_forecast`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'week',
  time_series_data_col = 'units_sold',
  time_series_id_col = ['hierarchy_level', 'hierarchy_series', 'hierarchy_parent'],
  data_frequency = 'WEEKLY',
  holiday_region = 'US',
  horizon = 8
) AS
SELECT hierarchy_level, hierarchy_series, hierarchy_parent, week, units_sold
FROM `{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_topdown_flat`
WHERE splits = 'TRAIN'
"""
client.query(query).result()
print('Model hier_topdown_forecast created')
```

### The disaggregation formula, shown explicitly for one level

For each county, its **final** forecast is fixed already (the state's final forecast, since state is the top of the hierarchy). Each county's own **raw** forecast (from the flat model above, ignoring the hierarchy) is only used to compute a *proportion*: `raw_county / sum_of_raw_counties`. The county's disaggregated final forecast is then `state_final × proportion`.

```python
query = f"""
WITH raw AS (
  SELECT hierarchy_level, hierarchy_series, hierarchy_parent, forecast_timestamp, forecast_value
  FROM ML.FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.hier_topdown_forecast`, STRUCT(8 AS horizon))
),
state_final AS (
  SELECT forecast_timestamp, forecast_value AS state_final_value
  FROM raw WHERE hierarchy_level = 'state'
),
county_raw_sum AS (
  SELECT forecast_timestamp, SUM(forecast_value) AS total_raw
  FROM raw WHERE hierarchy_level = 'county'
  GROUP BY forecast_timestamp
)
SELECT
  r.hierarchy_series AS county, r.forecast_timestamp, r.forecast_value AS county_raw_forecast,
  ROUND(SAFE_DIVIDE(r.forecast_value, s.total_raw), 4) AS proportion_of_state,
  ROUND(sf.state_final_value * SAFE_DIVIDE(r.forecast_value, s.total_raw), 2) AS county_final_forecast
FROM raw r
JOIN state_final sf ON r.forecast_timestamp = sf.forecast_timestamp
JOIN county_raw_sum s ON r.forecast_timestamp = s.forecast_timestamp
WHERE r.hierarchy_level = 'county'
ORDER BY r.forecast_timestamp, county
"""
client.query(query).to_dataframe()
```

### Generalizing the cascade to all 4 levels

Doing this level by level by hand gets unwieldy for a deeper hierarchy. `build_hierarchical_topdown_forecast` below generalizes the exact pattern above — flatten every level, train one flat model, then cascade the same proportion formula from the top down through however many levels are given — for **any** ordered list of hierarchy columns, not just this specific 4-level one.

```python
def build_hierarchical_topdown_forecast(client, project_id, dataset_id, prepped_table,
                                         timestamp_col, value_col, hierarchy_cols,
                                         horizon, base_name, holiday_region='US', data_frequency='WEEKLY'):
    """Builds a from-scratch top-down (forecast-proportions) hierarchical forecast for ANY
    ordered list of hierarchy_cols (top to bottom). Returns the results table's full ID,
    with one row per (level, series, timestamp) and a final_value column."""
    flat_table = f'{project_id}.{dataset_id}.{base_name}_flat'
    model_name = f'{project_id}.{dataset_id}.{base_name}_model'
    results_table = f'{project_id}.{dataset_id}.{base_name}_results'

    # 1) Flatten every level (an implicit 'top' root, plus each hierarchy_cols entry) into one
    #    long table, each row tagged with its own level, series id, and parent series id.
    level_queries = [f"""
        SELECT 'top' AS hierarchy_level, 'Overall' AS hierarchy_series, 'none' AS hierarchy_parent,
          {timestamp_col}, SUM({value_col}) AS {value_col}, splits
        FROM `{prepped_table}` GROUP BY {timestamp_col}, splits
    """]
    for i, col in enumerate(hierarchy_cols):
        group_cols = ', '.join(hierarchy_cols[:i + 1])
        parent_expr = "'Overall'" if i == 0 else f"CAST({hierarchy_cols[i - 1]} AS STRING)"
        level_queries.append(f"""
            SELECT '{col}' AS hierarchy_level, CAST({col} AS STRING) AS hierarchy_series,
              {parent_expr} AS hierarchy_parent, {timestamp_col}, SUM({value_col}) AS {value_col}, splits
            FROM `{prepped_table}` GROUP BY {group_cols}, {timestamp_col}, splits
        """)
    client.query(f"CREATE OR REPLACE TABLE `{flat_table}` AS " + " UNION ALL ".join(level_queries)).result()

    # 2) Train one ARIMA_PLUS model treating every level's series as independent.
    client.query(f"""
        CREATE OR REPLACE MODEL `{model_name}`
        OPTIONS(model_type='ARIMA_PLUS', time_series_timestamp_col='{timestamp_col}',
          time_series_data_col='{value_col}', time_series_id_col=['hierarchy_level','hierarchy_series','hierarchy_parent'],
          data_frequency='{data_frequency}', holiday_region='{holiday_region}', horizon={horizon}) AS
        SELECT hierarchy_level, hierarchy_series, hierarchy_parent, {timestamp_col}, {value_col}
        FROM `{flat_table}` WHERE splits = 'TRAIN'
    """).result()

    # 3) Cascade the forecast-proportions disaggregation top to bottom, one level at a time.
    levels = ['top'] + hierarchy_cols
    cte_parts = [f"""raw AS (
        SELECT hierarchy_level, hierarchy_series, hierarchy_parent, forecast_timestamp, forecast_value
        FROM ML.FORECAST(MODEL `{model_name}`, STRUCT({horizon} AS horizon))
    )""", """final_top AS (
        SELECT hierarchy_level, hierarchy_series, hierarchy_parent, forecast_timestamp, forecast_value AS final_value
        FROM raw WHERE hierarchy_level = 'top'
    )"""]
    for i, level in enumerate(levels[1:]):
        parent_alias = 'final_top' if i == 0 else f'final_{levels[i]}'
        cte_parts.append(f"""sums_{level} AS (
            SELECT hierarchy_parent, forecast_timestamp, SUM(forecast_value) AS total_raw
            FROM raw WHERE hierarchy_level = '{level}' GROUP BY hierarchy_parent, forecast_timestamp
        )""")
        cte_parts.append(f"""final_{level} AS (
            SELECT r.hierarchy_level, r.hierarchy_series, r.hierarchy_parent, r.forecast_timestamp,
              p.final_value * COALESCE(SAFE_DIVIDE(r.forecast_value, s.total_raw), 0) AS final_value
            FROM raw r
            JOIN {parent_alias} p ON r.hierarchy_parent = p.hierarchy_series AND r.forecast_timestamp = p.forecast_timestamp
            JOIN sums_{level} s ON r.hierarchy_parent = s.hierarchy_parent AND r.forecast_timestamp = s.forecast_timestamp
            WHERE r.hierarchy_level = '{level}'
        )""")
    union_selects = " UNION ALL ".join(
        f"SELECT hierarchy_level, hierarchy_series, hierarchy_parent, forecast_timestamp, final_value FROM final_{level}"
        for level in levels
    )
    client.query("CREATE OR REPLACE TABLE `" + results_table + "` AS WITH " + ",\n".join(cte_parts) + "\n" + union_selects).result()
    return results_table

topdown_results_table = build_hierarchical_topdown_forecast(
    client, PROJECT_ID, DATASET_ID,
    prepped_table=f'{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_prepped',
    timestamp_col='week', value_col='units_sold',
    hierarchy_cols=['county', 'city', 'store_number'],
    horizon=8, base_name='hier_auto_topdown'
)
print('Top-down results table:', topdown_results_table)
```

```python
# Sanity check: the function's county-level output matches the manually-computed
# county_final_forecast values shown explicitly above, exactly.
query = f"""
SELECT hierarchy_series AS county, forecast_timestamp, ROUND(final_value, 2) AS county_final_forecast
FROM `{topdown_results_table}`
WHERE hierarchy_level = 'county'
ORDER BY forecast_timestamp, county
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Compare accuracy: built-in bottom-up vs. custom top-down

Both approaches produce a reconciled forecast at every level. Evaluate both against the real TEST-period actuals, at every level, using the same MAE/MAPE metrics.

```python
query = f"""
WITH actuals AS (
  SELECT hierarchy_level, hierarchy_series, week AS forecast_timestamp, units_sold AS actual_value
  FROM `{PROJECT_ID}.{DATASET_ID}.hierarchical_forecasting_topdown_flat`
  WHERE splits = 'TEST'
),
bqml_raw AS (
  SELECT county, city, store_number, forecast_timestamp, forecast_value
  FROM ML.FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.hier_bottomup_forecast`, STRUCT(8 AS horizon))
),
bqml_transformed AS (
  SELECT
    CASE WHEN county IS NULL THEN 'state' WHEN city IS NULL THEN 'county'
         WHEN store_number IS NULL THEN 'city' ELSE 'store' END AS hierarchy_level,
    CASE WHEN county IS NULL THEN 'Iowa' WHEN city IS NULL THEN county
         WHEN store_number IS NULL THEN city ELSE store_number END AS hierarchy_series,
    forecast_timestamp, forecast_value AS bqml_forecast_value
  FROM bqml_raw
),
topdown AS (
  SELECT
    CASE hierarchy_level WHEN 'top' THEN 'state' WHEN 'store_number' THEN 'store' ELSE hierarchy_level END AS hierarchy_level,
    IF(hierarchy_level = 'top', 'Iowa', hierarchy_series) AS hierarchy_series,
    forecast_timestamp, final_value AS topdown_forecast_value
  FROM `{topdown_results_table}`
),
joined AS (
  SELECT a.hierarchy_level, a.hierarchy_series, a.actual_value, b.bqml_forecast_value, t.topdown_forecast_value
  FROM actuals a
  LEFT JOIN bqml_transformed b ON a.hierarchy_level=b.hierarchy_level AND a.hierarchy_series=b.hierarchy_series
    AND a.forecast_timestamp=DATE(b.forecast_timestamp)
  LEFT JOIN topdown t ON a.hierarchy_level=t.hierarchy_level AND a.hierarchy_series=t.hierarchy_series
    AND a.forecast_timestamp=DATE(t.forecast_timestamp)
)
SELECT
  hierarchy_level, hierarchy_series,
  ROUND(AVG(ABS(actual_value - bqml_forecast_value)), 1) AS mae_bqml_bottomup,
  ROUND(AVG(ABS(actual_value - topdown_forecast_value)), 1) AS mae_custom_topdown,
  ROUND(AVG(ABS(actual_value - bqml_forecast_value) / NULLIF(actual_value, 0)) * 100, 1) AS mape_bqml_bottomup,
  ROUND(AVG(ABS(actual_value - topdown_forecast_value) / NULLIF(actual_value, 0)) * 100, 1) AS mape_custom_topdown
FROM joined
GROUP BY hierarchy_level, hierarchy_series
ORDER BY
  CASE hierarchy_level WHEN 'state' THEN 1 WHEN 'county' THEN 2 WHEN 'city' THEN 3 ELSE 4 END,
  hierarchy_series
"""
comparison = client.query(query).to_dataframe()
comparison
```

**GOTCHA (verified): MAPE is unstable when the actual value is near zero.** One store (4180, Marion) sold exactly 1 bottle in a single TEST week — an absolute forecast error of a few dozen bottles there translates into a MAPE in the *thousands of percent*, even though the same error would be unremarkable at that store's typical weekly volume. This isn't a modeling bug in either technique; it's a well-known property of any percentage-based metric once the denominator gets small. MAE is unaffected by this and is the more reliable metric for comparing techniques at the store level here.

**No universal winner between the two techniques** — the built-in bottom-up model wins on some series (e.g. Ankeny), the custom top-down wins on others (e.g. the overall state total, Polk county), and neither dominates. This is a genuinely different picture from `workflows/regression_based_forecasting/`'s comparison against plain `ARIMA_PLUS`, where one technique (`ARIMA_PLUS`) was consistently strong — here, both techniques start from the *same* underlying `ARIMA_PLUS` forecasts, just reconciled in different directions through the hierarchy, so it comes down to whether the true structure in this data happens to be closer to "each store moves independently" (favoring bottom-up, which never adjusts base forecasts) or "the top-level trend drives everything, and stores just share it out" (favoring top-down).
