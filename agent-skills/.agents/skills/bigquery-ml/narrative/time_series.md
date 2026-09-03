# Time Series Decomposition — BigQuery ML Model-Free Functions

Three table-valued functions that pull a time series apart **without training a model**: `ML.TREND` (the trend component), `ML.SEASONALITY` (per-period seasonal components), and `ML.DETECT_CHANGE_POINTS` (sustained structural shifts). No `CREATE MODEL`, no model object, no connection — a TVF straight over a table or a query. All three are **Preview** as of 2026-08-20.

> **Not the same as `ML.DETECT_ANOMALIES`.** Three functions, three different questions — and Step 8 measures on this exact series that the answers barely overlap:
>
> | Question | Function | Where it lives |
> |---|---|---|
> | Is *this row* an outlier? | `ML.DETECT_ANOMALIES` | `models/arima_plus` (ARIMA_PLUS), `models/kmeans` (K-Means), `models/pca` (PCA), `models/autoencoder` (Autoencoder) |
> | Did the series *shift* here? | `ML.DETECT_CHANGE_POINTS` | this notebook |
> | Has the *whole dataset* moved? | `ML.VALIDATE_DATA_DRIFT` | `functions/data_quality` (Data Quality) |

**When to use these:**
- `ML.TREND` — get the underlying direction of a series without committing to a model artifact.
- `ML.SEASONALITY` — extract weekly/yearly/etc. components; Step 7 shows these are **bit-identical** to what an ARIMA_PLUS model produces.
- `ML.DETECT_CHANGE_POINTS` — find sustained level shifts, the thing neither row-level anomaly detection nor dataset-level drift checks look for. Step 5 shows what it does on a series with a data outage, which is not what you might expect.

**Data:** [`bigquery-public-data.new_york_citibike.citibike_trips`](https://console.cloud.google.com/marketplace/product/city-of-new-york/nyc-citi-bike) aggregated to daily trip counts for five stations — the **identical series** used by `models/arima_plus` (ARIMA_PLUS), which is what makes the head-to-head in Step 7 apples-to-apples.

**References:** `RESOURCES.md` (Full reference) | [`ML.TREND`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-trend) | [`ML.SEASONALITY`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-seasonality) | [`ML.DETECT_CHANGE_POINTS`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-detect-change-points) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No connection needed — these functions run entirely inside BigQuery.

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

### Materialize the series

Daily trip counts per station, with a `splits` column marking everything after 2018-05-03 as `TEST`. This is the same recipe as `models/arima_plus` (`models/arima_plus/`) — a separate table so this notebook stands alone, but the identical series.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.time_series_trips` AS
WITH daily AS (
  SELECT
    start_station_name,
    DATE(starttime) AS date,
    COUNT(*) AS num_trips
  FROM `bigquery-public-data.new_york_citibike.citibike_trips`
  WHERE start_station_name IN (
    'Pershing Square North', 'E 17 St & Broadway', 'W 21 St & 6 Ave',
    'Lafayette St & E 8 St', 'West St & Chambers St'
  )
  GROUP BY start_station_name, date
)
SELECT *, IF(date > DATE('2018-05-03'), 'TEST', 'TRAIN') AS splits
FROM daily
"""
client.query(query).result()
print('Table time_series_trips created')
```

**These series have gaps** — a day with no trips produces no row at all. Worth measuring up front, because all three functions gap-fill internally, and on this data that turns out to drive the headline result of Step 5.

```python
query = f"""
SELECT
  start_station_name,
  COUNT(*) AS raw_rows,
  MIN(date) AS first_date,
  MAX(date) AS last_date,
  DATE_DIFF(MAX(date), MIN(date), DAY) + 1 AS calendar_span_days,
  DATE_DIFF(MAX(date), MIN(date), DAY) + 1 - COUNT(*) AS missing_days
FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
WHERE splits = 'TRAIN'
GROUP BY start_station_name
ORDER BY start_station_name
"""
client.query(query).to_dataframe()
```

Missing days are not scattered evenly. Where a station's absences are **contiguous**, the series has an outage rather than noise — and that distinction matters for every function below.

```python
query = f"""
WITH gaps AS (
  SELECT
    start_station_name,
    LAG(date) OVER (PARTITION BY start_station_name ORDER BY date) AS last_day_before,
    date AS first_day_after,
    DATE_DIFF(date, LAG(date) OVER (PARTITION BY start_station_name ORDER BY date), DAY) - 1 AS missing_days
  FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
  WHERE splits = 'TRAIN'
)
SELECT * EXCEPT(rn) FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY start_station_name ORDER BY missing_days DESC) AS rn
  FROM gaps WHERE missing_days > 0
) WHERE rn = 1
ORDER BY missing_days DESC
"""
client.query(query).to_dataframe()
```

---
## Step 1 — `ML.TREND`: the trend component, no model required

The signature, as the server itself enumerates it when handed a bad argument:

```
ML.TREND(TABLE, timestamp_col => STRING, data_col => STRING,
         [id_cols => ARRAY<STRING>], [horizon => INT64],
         [smoothing_window_size => INT64], [adjust_step_changes => BOOL])
```

Only the relation, `timestamp_col` and `data_col` are required. The first argument is a **relation** — a `TABLE` reference or a parenthesized subquery, not a string.

```python
trend_sql = f"""
SELECT *
FROM ML.TREND(
  (SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips'
)
ORDER BY date
"""
trend_df = client.query(trend_sql).to_dataframe()
print(f'rows: {len(trend_df)}   columns: {list(trend_df.columns)}')
trend_df.head(10)
```

**Two things the schema does not advertise.**

1. The timestamp and data columns keep their **original names** (`date`, `num_trips`) — the output is not renamed to a generic `time_series_timestamp`/`time_series_data` the way `ML.FORECAST`'s is. `trend` is the one added column.
2. `num_trips` comes back **`FLOAT64`** even though the input is an integer `COUNT(*)`, because the function returns the gap-filled series rather than echoing your raw values. Note the row count above against the `raw_rows` measured earlier.

> **GOTCHA — `status` is the empty string, never `NULL`.** Filtering with `status IS NULL` to find failures silently matches nothing. Test `status = ''` or `LENGTH(status) = 0` instead.

```python
print(f"num_trips dtype: {trend_df['num_trips'].dtype}")
print(f"distinct status values: {trend_df['status'].unique().tolist()}")
print(f"rows where status IS NULL:  {trend_df['status'].isna().sum()}")
print(f"rows where status == '':    {(trend_df['status'] == '').sum()}")
```

---
## Step 2 — Named arguments, and what `smoothing_window_size` does

Argument **names are case-insensitive** (`Timestamp_Col` works) and their order does not matter. `smoothing_window_size` widens the smoothing window applied to the trend.

```python
query = f"""
WITH default_trend AS (
  SELECT date, trend
  FROM ML.TREND(
    (SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
     WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
    timestamp_col => 'date', data_col => 'num_trips')
),
smoothed AS (
  SELECT date, trend
  FROM ML.TREND(
    (SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
     WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
    Data_Col => 'num_trips',        -- names are case-insensitive
    Timestamp_Col => 'date',        -- and order-independent
    smoothing_window_size => 30)
)
SELECT
  COUNT(*) AS n,
  ROUND(AVG(ABS(d.trend - s.trend)), 3) AS mean_abs_diff,
  ROUND(STDDEV(d.trend), 2) AS stddev_default,
  ROUND(STDDEV(s.trend), 2) AS stddev_window_30
FROM default_trend d JOIN smoothed s USING (date)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — `adjust_step_changes`: the default differs from ARIMA_PLUS's

> **GOTCHA.** `ML.TREND` defaults `adjust_step_changes` to **`FALSE`**. An `ARIMA_PLUS` model defaults the equivalent option to **`TRUE`** (readable off a trained model as `"adjustStepChanges": true`). A naive `ML.TREND` call therefore does *not* reproduce the model's trend — you have to opt in. Step 7 depends on this.

The cell below pins the default by differencing it against both explicit settings: a summed difference of exactly `0` identifies which one the default matches.

```python
def trend_variant(option_sql):
    return f"""
    SELECT date, trend
    FROM ML.TREND(
      (SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
       WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
      timestamp_col => 'date', data_col => 'num_trips'{option_sql})
    """

query = f"""
WITH d AS ({trend_variant('')}),
     t AS ({trend_variant(', adjust_step_changes => TRUE')}),
     f AS ({trend_variant(', adjust_step_changes => FALSE')})
SELECT
  COUNT(*) AS n,
  ROUND(SUM(ABS(d.trend - t.trend)), 4) AS summed_diff_vs_TRUE,
  ROUND(SUM(ABS(d.trend - f.trend)), 4) AS summed_diff_vs_FALSE,
  ROUND(AVG(ABS(t.trend - f.trend)), 3) AS mean_abs_diff_TRUE_vs_FALSE,
  ROUND(MAX(ABS(t.trend - f.trend)), 3) AS max_abs_diff_TRUE_vs_FALSE
FROM d JOIN t USING (date) JOIN f USING (date)
"""
client.query(query).to_dataframe()
```

---
## Step 4 — `ML.SEASONALITY`: one column per period, on a fixed schema

```
ML.SEASONALITY(TABLE, timestamp_col => STRING, data_col => STRING,
               [id_cols => ARRAY<STRING>], [SEASONALITIES => ARRAY<STRING>],
               [horizon => INT64])
```

```python
seasonality_sql = f"""
SELECT *
FROM ML.SEASONALITY(
  (SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips'
)
ORDER BY date
"""
seasonality_df = client.query(seasonality_sql).to_dataframe()
print(f'columns: {list(seasonality_df.columns)}')
seasonality_df.head(10)
```

> **GOTCHA — the period columns are a fixed schema, not a result.** All five periods (`yearly`, `quarterly`, `monthly`, `weekly`, `daily`, in descending period length) are always in the schema. A period the function did not fit is **not omitted** — it comes back `NULL` on every row. `SELECT *` therefore hands you all-`NULL` columns with no indication of why, and the schema tells you nothing about what was actually fitted. Count the `NULL`s instead.

```python
period_cols = ['yearly', 'quarterly', 'monthly', 'weekly', 'daily']
profile = pd.DataFrame({
    'period': period_cols,
    'null_rows': [int(seasonality_df[c].isna().sum()) for c in period_cols],
    'total_rows': len(seasonality_df),
})
profile['fitted'] = profile['null_rows'] < profile['total_rows']
profile
```

### Restricting periods with `SEASONALITIES`

Accepted values, established by sweeping candidates against the server: **`DAILY`, `WEEKLY`, `MONTHLY`, `QUARTERLY`, `YEARLY`**. The *values* are case-insensitive too — `'weekly'` and `'Weekly'` both work.

> **GOTCHA — the rejection message is only sometimes helpful.** Three wrong strings come back with the valid set spelled out:
>
> `HOURLY` / `NO_SEASONALITY` / `AUTO` → *"Invalid seasonality value 'HOURLY' in SEASONALITIES. **Supported values are YEARLY, QUARTERLY, MONTHLY, WEEKLY, DAILY.**"*
>
> Any other string — `MINUTELY`, `PER_MINUTE`, `PER_HOUR`, `AUTO_FREQUENCY`, `ANNUAL`, `''`, or an ordinary typo — gets the bare form with **no enumeration**:
>
> `BOGUS` → *"Invalid seasonality value 'BOGUS' in SEASONALITIES."*
>
> The three that do enumerate are plausible-but-wrong guesses drawn from neighbouring BigQuery ML vocabulary, but several other tokens from that same vocabulary (`PER_MINUTE`, `AUTO_FREQUENCY`, `PER_HOUR`) do **not** enumerate — so this is a recorded observation about the message, not an inferred rule about what the parser recognizes. Practical consequence: keep the valid list to hand, because a typo will not supply it.

```python
query = f"""
SELECT date, num_trips, ROUND(weekly, 3) AS weekly, ROUND(yearly, 3) AS yearly
FROM ML.SEASONALITY(
  (SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips',
  SEASONALITIES => ['weekly', 'YEARLY']   -- values are case-insensitive
)
ORDER BY date
"""
client.query(query).to_dataframe().head()
```

---
## Step 5 — `ML.DETECT_CHANGE_POINTS`: windows, not per-row flags

The shortest signature of the three — no `horizon`, no tuning options:

```
ML.DETECT_CHANGE_POINTS(TABLE, timestamp_col => STRING, data_col => STRING,
                        [id_cols => ARRAY<STRING>])
```

> **GOTCHA — this does not return one row per input row.** It returns one row per detected change **window**. There is no `is_change_point` boolean to filter and no full-partition output to join back; to attribute an input row to a window you range-join on `date BETWEEN begin_timestamp AND end_timestamp` (Step 8 does exactly that).

```python
change_points_sql = f"""
SELECT
  begin_timestamp, end_timestamp, status,
  metrics.count, ROUND(metrics.avg, 2) AS avg,
  metrics.min, metrics.max, ROUND(metrics.stddev, 2) AS stddev
FROM ML.DETECT_CHANGE_POINTS(
  (SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips'
)
"""
change_points = client.query(change_points_sql).to_dataframe()
print(f'{len(change_points)} change windows found in a series spanning 1,341 days')
change_points
```

> **GOTCHA — `metrics` describes the gap-filled series, not your rows.** These numbers will not tie out against a `GROUP BY` over the same date range, and the mismatch is not a rounding artifact. Two tells in the output above: `metrics.count` is one per *calendar day* in the window even where the base table has no row, and `metrics.min` is **fractional** despite `num_trips` being an integer `COUNT(*)` — that value was interpolated, not observed.

```python
first = change_points.iloc[0]
query = f"""
SELECT
  COUNT(*) AS n,
  ROUND(AVG(num_trips), 2) AS avg,
  MIN(num_trips) AS min,
  MAX(num_trips) AS max,
  ROUND(STDDEV(num_trips), 2) AS stddev
FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
WHERE start_station_name = 'Pershing Square North'
  AND date BETWEEN DATE('{first.begin_timestamp.date()}') AND DATE('{first.end_timestamp.date()}')
"""
raw = client.query(query).to_dataframe()

comparison = pd.DataFrame([
    {'source': 'raw GROUP BY over the window', 'count': raw['n'][0], 'avg': raw['avg'][0],
     'min': raw['min'][0], 'max': raw['max'][0], 'stddev': raw['stddev'][0]},
    {'source': 'metrics reported by the function', 'count': first['count'], 'avg': first['avg'],
     'min': first['min'], 'max': first['max'], 'stddev': first['stddev']},
])
print(f"window {first.begin_timestamp.date()} .. {first.end_timestamp.date()}")
comparison
```

### What those two change points actually are

The window above spans 2016-09-28 to 2016-10-04, but the base table's last row in that range is **2016-09-30**. Line that up against the outage measured in Setup and the two "change points" stop looking like organic structural shifts:

| | detected window | station's largest outage |
|---|---|---|
| first window | 2016-09-28 → 2016-10-04 | outage **begins** 2016-10-01 |
| second window | 2017-04-01 → 2017-04-03 | outage **ends** 2017-03-31 |

> **GOTCHA — on a gapped series, the gap-filling manufactures the structural break the function then reports.** Both detected change points sit on the two edges of a single 182-day data outage. The function is not wrong: after interpolation the series genuinely does step down into a flat stretch and step back up out of it. But the shift it found is an artifact of the missing data, not a change in ridership. **Check your series for outages before acting on a change point** — otherwise the alert fires on your pipeline, not on your business.

```python
query = f"""
SELECT date, num_trips
FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
WHERE start_station_name = 'Pershing Square North'
  AND date BETWEEN DATE('2016-09-26') AND DATE('2017-04-05')
ORDER BY date
"""
around_gap = client.query(query).to_dataframe()
print(f'rows present in the base table, 2016-09-26 .. 2017-04-05: {len(around_gap)}')
around_gap
```

---
## Step 6 — Seeing the decomposition

Observed series, extracted trend, weekly seasonality, and the detected change windows shaded across all three panels. The outage is unmistakable once plotted: a straight interpolated line through the top panel, a dip in the trend, and a weekly component that collapses to near-zero — with a red change window at each end of it.

```python
import matplotlib.pyplot as plt

decomp = trend_df[['date', 'num_trips', 'trend']].merge(
    seasonality_df[['date', 'weekly']], on='date').sort_values('date')

fig, axes = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
axes[0].plot(decomp['date'], decomp['num_trips'], color='#4285F4', linewidth=0.6)
axes[0].set_title('Observed — daily trips, Pershing Square North')
axes[1].plot(decomp['date'], decomp['trend'], color='#34A853', linewidth=1.4)
axes[1].set_title('ML.TREND — trend component')
axes[2].plot(decomp['date'], decomp['weekly'], color='#FBBC04', linewidth=0.6)
axes[2].set_title('ML.SEASONALITY — weekly component')

for _, cp in change_points.iterrows():
    for ax in axes:
        ax.axvspan(cp['begin_timestamp'], cp['end_timestamp'],
                   color='#EA4335', alpha=0.35, zorder=0)

axes[2].set_xlabel('date')
fig.suptitle('Model-free decomposition, with ML.DETECT_CHANGE_POINTS windows shaded', y=1.0)
plt.tight_layout()
plt.show()
```

---
## Step 7 — Head-to-head against `ARIMA_PLUS`: how close is "model-free"?

`ML.TREND` and `ML.SEASONALITY` run the ARIMA_PLUS decomposition without materializing a model. That claim is testable: train the model on the identical series, then difference the components.

Note the `adjust_step_changes => TRUE` in the `ML.TREND` branch below — Step 3 established that this is needed to match the model's default.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.time_series_scratch_arima`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'date',
  time_series_data_col = 'num_trips',
  horizon = 7
) AS
SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'
"""
client.query(query).result()
print('Model time_series_scratch_arima created')
```

```python
query = f"""
WITH arima AS (
  SELECT DATE(time_series_timestamp) AS date,
         trend                   AS arima_trend,
         seasonal_period_weekly  AS arima_weekly,
         seasonal_period_yearly  AS arima_yearly
  FROM ML.EXPLAIN_FORECAST(MODEL `{PROJECT_ID}.{DATASET_ID}.time_series_scratch_arima`,
                           STRUCT(7 AS horizon))
  WHERE time_series_type = 'history'
),
tvf_trend AS (
  SELECT date, trend
  FROM ML.TREND(
    (SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
     WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
    timestamp_col => 'date', data_col => 'num_trips',
    adjust_step_changes => TRUE)          -- match the model's default
  WHERE time_series_type = 'history'
),
tvf_seasonality AS (
  SELECT date, weekly, yearly
  FROM ML.SEASONALITY(
    (SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
     WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
    timestamp_col => 'date', data_col => 'num_trips')
  WHERE time_series_type = 'history'
)
SELECT
  COUNT(*) AS n,
  ROUND(AVG(ABS(arima_trend  - trend)),  3) AS trend_mean_abs_diff,
  ROUND(CORR(arima_trend, trend),        4) AS trend_corr,
  ROUND(AVG(ABS(arima_weekly - weekly)), 3) AS weekly_mean_abs_diff,
  ROUND(CORR(arima_weekly, weekly),      4) AS weekly_corr,
  ROUND(AVG(ABS(arima_yearly - yearly)), 3) AS yearly_mean_abs_diff,
  ROUND(CORR(arima_yearly, yearly),      4) AS yearly_corr
FROM arima JOIN tvf_trend USING (date) JOIN tvf_seasonality USING (date)
"""
client.query(query).to_dataframe().T
```

**The seasonal components are bit-identical.** `weekly` and `yearly` both come back at mean absolute difference `0.0` and correlation `1.0` against the trained model's `seasonal_period_weekly` / `seasonal_period_yearly`. `ML.SEASONALITY` is a genuine drop-in for the model's seasonal decomposition — the same numbers without the `CREATE MODEL`.

**The trend is very close but not identical** — correlation `0.9955`, mean absolute difference `8.337` (median `5.755`, p95 `25.121`, max `58.555`).

Two option differences remain between the two calls and this comparison does not separate them, so no single cause is claimed: the trained model also reports `"cleanSpikesAndDips": true` (`ML.TREND` exposes no equivalent option) and `"trendSmoothingWindowSize": -1` (auto), while `ML.TREND`'s `smoothing_window_size` default is unspecified. Either or both could account for the residual.

**Practical reading:** use `ML.SEASONALITY` freely in place of a model's seasonal components. Treat `ML.TREND` as very close but not a substitute if you need to reproduce a *specific* model's trend to the digit.

---
## Step 8 — Change points are not anomalies

The two live in the same neighbourhood and are easy to conflate. On this series they are measurably orthogonal — range-join the row-level anomalies against the change windows and count the overlap.

```python
query = f"""
WITH change_windows AS (
  SELECT DATE(begin_timestamp) AS b, DATE(end_timestamp) AS e
  FROM ML.DETECT_CHANGE_POINTS(
    (SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
     WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
    timestamp_col => 'date', data_col => 'num_trips')
),
anomalies AS (
  SELECT DATE(date) AS d
  FROM ML.DETECT_ANOMALIES(MODEL `{PROJECT_ID}.{DATASET_ID}.time_series_scratch_arima`,
                           STRUCT(0.95 AS anomaly_prob_threshold))
  WHERE is_anomaly
)
SELECT
  (SELECT COUNT(*) FROM anomalies)      AS row_level_anomalies,
  (SELECT COUNT(*) FROM change_windows) AS change_windows,
  (SELECT COUNT(*) FROM anomalies a JOIN change_windows c
    ON a.d BETWEEN c.b AND c.e)         AS overlap
"""
client.query(query).to_dataframe()
```

**Zero overlap.** Not one of the row-level anomalies falls inside a detected change window. These are orthogonal detectors, not two sensitivity settings on one detector — which matters before wiring either into an alert, because *"we already alert on anomalies"* does not mean structural shifts are covered.

On *this* series the separation is sharper than it would generally be, and Step 5 explains why: the change windows sit on the edges of an interpolated stretch, which is smooth by construction and therefore contains nothing for a row-level detector to flag. Read the zero as a demonstration that the two functions answer different questions, not as a measurement of how far apart their answers usually fall.

---
## Step 9 — `horizon`: these functions also forecast

> **GOTCHA — `horizon` is not a windowing or row-limit parameter.** Supplying it makes `ML.TREND` and `ML.SEASONALITY` **extend the series into the future**; the extra rows arrive with `time_series_type = 'forecast'` alongside the `history` rows. `ML.DETECT_CHANGE_POINTS` has no `horizon` argument.

```python
query = f"""
SELECT date, ROUND(num_trips, 2) AS num_trips, ROUND(trend, 2) AS trend, time_series_type
FROM ML.TREND(
  (SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips',
  horizon => 7
)
WHERE time_series_type = 'forecast'
ORDER BY date
"""
client.query(query).to_dataframe()
```

Seven rows, 2018-05-04 through 2018-05-10 — the `TRAIN` split ends 2018-05-03, so these extend exactly one horizon past it.

> **GOTCHA — the data column is not `NULL` on forecast rows.** `num_trips` carries the **forecast value** there, while `trend` carries only the trend component (nearly flat across these seven days). Nothing in the schema distinguishes an actual from a forecast except `time_series_type`, so an unfiltered `AVG(num_trips)` silently mixes observed history with predictions.

---
## Step 10 — `id_cols`: many series in one call

All three functions take `id_cols => ARRAY<STRING>` to decompose each series independently in a single pass, the same way ARIMA_PLUS's `time_series_id_col` does. The id columns are echoed in the output.

This is also where the gap-filling from Step 5 becomes visible: compare `rows_returned` below against the `raw_rows` measured in Setup.

```python
query = f"""
SELECT start_station_name, COUNT(*) AS rows_returned,
       MIN(date) AS first_date, MAX(date) AS last_date
FROM ML.TREND(
  (SELECT start_station_name, date, num_trips
   FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips` WHERE splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips',
  id_cols => ['start_station_name']
)
GROUP BY start_station_name
ORDER BY start_station_name
"""
client.query(query).to_dataframe()
```

Every station comes back with one row per calendar day between **its own** first and last observation. Pershing Square North returns fewer rows than the others only because it starts 2014-09-01 while they start 2013-07-01 — the function neither pads a late-starting series backwards nor truncates the others to match.

Change points across all five stations in one call:

```python
query = f"""
SELECT start_station_name, begin_timestamp, end_timestamp, metrics.count
FROM ML.DETECT_CHANGE_POINTS(
  (SELECT start_station_name, date, num_trips
   FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips` WHERE splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips',
  id_cols => ['start_station_name']
)
ORDER BY start_station_name, begin_timestamp
"""
client.query(query).to_dataframe()
```

Four of the five stations open a change window in the last week of September 2016 — the shared outage from Setup, showing up once per series.

Rather than eyeball that, separate the artifacts from the real findings mechanically: label each window with the size of the data gap whose edge it contains, if any.

```python
query = f"""
WITH gaps AS (
  SELECT
    start_station_name,
    LAG(date) OVER (PARTITION BY start_station_name ORDER BY date) AS last_before,
    date AS first_after,
    DATE_DIFF(date, LAG(date) OVER (PARTITION BY start_station_name ORDER BY date), DAY) - 1 AS missing_days
  FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
  WHERE splits = 'TRAIN'
),
change_windows AS (
  SELECT start_station_name, DATE(begin_timestamp) AS b, DATE(end_timestamp) AS e
  FROM ML.DETECT_CHANGE_POINTS(
    (SELECT start_station_name, date, num_trips
     FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips` WHERE splits = 'TRAIN'),
    timestamp_col => 'date', data_col => 'num_trips',
    id_cols => ['start_station_name'])
)
SELECT
  c.start_station_name, c.b AS begin_date, c.e AS end_date,
  (SELECT MAX(g.missing_days) FROM gaps g
    WHERE g.start_station_name = c.start_station_name
      AND g.missing_days >= 3
      AND (g.last_before BETWEEN c.b AND c.e OR g.first_after BETWEEN c.b AND c.e)
  ) AS gap_edge_missing_days
FROM change_windows c
ORDER BY c.start_station_name, c.b
"""
labelled = client.query(query).to_dataframe()
labelled['verdict'] = labelled['gap_edge_missing_days'].isna().map(
    {True: 'real change point', False: 'artifact of a data gap'})
labelled
```

**Six of the seven windows sit on the edge of a data gap.** Only one does not — `West St & Chambers St`, 2016-04-27 → 2016-05-07, which has all 11 days present and a genuine level shift across it: averaging the raw daily counts, the 30 days before the window run 248.1 trips/day, the window itself 210.9, and the 30 days after 373.4.

That is the practical workflow for this function, and it is two queries long: profile the gaps, then keep the change points that do not land on one. Without that filter, six of seven findings here would have been an ingestion story reported as a ridership story.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT date, num_trips, ROUND(trend, 2) AS trend
FROM ML.TREND(
  (SELECT date, num_trips FROM `statmike-mlops-349915.bq_ml.time_series_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips'
)
ORDER BY date
LIMIT 5
```

---
## Examples — BigFrames

There is **no** `bigframes.ml` wrapper for any of these three — `bigframes.ml.forecasting.ARIMAPlus` covers the *model* path (see `models/arima_plus` (ARIMA_PLUS)), not the model-free TVFs. Reach them from BigFrames by running the SQL through `read_gbq`, which keeps the result lazy and in BigQuery.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

bdf = bpd.read_gbq(f"""
SELECT date, num_trips, trend
FROM ML.TREND(
  (SELECT date, num_trips FROM `{PROJECT_ID}.{DATASET_ID}.time_series_trips`
   WHERE start_station_name = 'Pershing Square North' AND splits = 'TRAIN'),
  timestamp_col => 'date',
  data_col => 'num_trips'
)
""")
bdf.sort_values('date').head()
```
