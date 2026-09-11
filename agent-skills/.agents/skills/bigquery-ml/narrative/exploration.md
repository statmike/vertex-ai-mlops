# Exploratory Data Analysis — `ML.DESCRIBE_DATA` and `ML.CORRELATION`

Two model-free table-valued functions that answer the two questions you ask of a dataset before you model it. **`ML.DESCRIBE_DATA`** (GA) profiles every column — counts, nulls, min/max, quantiles, top values. **`ML.CORRELATION`** (Preview) measures what actually moves with a target column, across Pearson, Spearman, and Kendall, and slices the answer by every combination of the dimensions you name. Neither trains anything, neither needs a connection, and neither creates a model object.

They belong together because the second one is only trustworthy after the first. This notebook runs them in that order on the same table, and the profile is what tells us the data needs cleaning before a single correlation is worth reading.

**What this notebook establishes, all measured here rather than quoted:**

1. `ML.DESCRIBE_DATA` reports `num_nulls = 0` for a column whose missing values are the string `' ?'` — the profile is honest and still misleading.
2. `ML.CORRELATION`'s `PEARSON` is BigQuery's own `CORR()`, agreeing to ~15 significant digits.
3. `SPEARMAN` is **not** the textbook Spearman on tied data. It ranks with SQL `RANK()` (competition ranks), not mid-ranks, and the two answers differ in the second decimal place on this table.
4. `KENDALL` **is** the tie-corrected tau-b, matching SciPy to floating-point noise. So one method in this function corrects for ties and the other does not.
5. Kendall's cost is quadratic and it is not close: measured, then extrapolated from the measurement.
6. `dimension_cols` is exactly `GROUP BY CUBE`, down to the row count.
7. `segment_size` is not the number of rows the correlation was computed from.
8. Selecting the `segment` column changes the value of `correlation` in its last three digits.

**Data:** [`bigquery-public-data.ml_datasets.census_adult_income`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — the same table as `models/logistic_regression` (Logistic Regression) and `functions/data_quality` (Data Quality).

**Related content:** `functions/data_quality` (`functions/data_quality/`) takes profiling forward into monitoring — `ML.VALIDATE_DATA_SKEW`, `ML.VALIDATE_DATA_DRIFT`, and the TFDV pair. Profile here, monitor there. `functions/feature_engineering` (`functions/feature_engineering/`) is the next step once you know which columns matter, and `functions/bucketizing` (`functions/bucketizing/`) is what you need before a continuous column can serve as a dimension here.

**References:** `reference/model-free-functions.md` (Full reference) | [`ML.DESCRIBE_DATA`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-describe-data) | [`ML.CORRELATION`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-correlation) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No connection needed — both functions run entirely inside BigQuery.

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
## Step 1 — `ML.DESCRIBE_DATA`: profile before anything else

One row per input column. `top_k` controls how many top categorical values come back (default **1**); `num_quantiles` controls numeric quantile granularity (default **2**, which returns three boundaries: min, median, max). Numeric columns populate `mean`/`stddev`/`median`/`quantiles`/`num_zeros`; categorical columns populate `unique`/`top_values`/`avg_string_length` instead. Every column gets `num_rows`, `num_values`, `num_nulls`, `min`, and `max`.

```python
query = """
SELECT name, num_rows, num_values, num_nulls, num_zeros, min, max, mean, stddev, median, quantiles
FROM ML.DESCRIBE_DATA(
  TABLE `bigquery-public-data.ml_datasets.census_adult_income`,
  STRUCT(3 AS top_k, 4 AS num_quantiles)
)
WHERE name IN ('age', 'education_num', 'hours_per_week', 'capital_gain')
ORDER BY name
"""
client.query(query).to_dataframe()
```

`capital_gain` is the column to look at twice: `num_zeros` is most of the table, and with `num_quantiles => 4` every interior quantile boundary is still zero. That is a spike-at-zero distribution, and it is the reason a correlation involving it will come back small no matter how strong the relationship is among the non-zero rows.

Now the categorical columns.

```python
query = """
SELECT name, unique, num_nulls, avg_string_length, min, max, top_values
FROM ML.DESCRIBE_DATA(
  TABLE `bigquery-public-data.ml_datasets.census_adult_income`,
  STRUCT(3 AS top_k, 4 AS num_quantiles)
)
WHERE name IN ('workclass', 'income_bracket')
ORDER BY name
"""
client.query(query).to_dataframe()
```

### The profile is honest and still misleading

Read `workclass`: **`num_nulls` is 0** and **`min` is `' ?'`**. Both are true. The column has no `NULL` values because its missing values are stored as a string, and `' ?'` sorts first. A profile that stopped at `num_nulls` would report a complete column — and `unique` counts the placeholder as one of the categories.

`min`/`max` on a categorical column exist for exactly this. They are the cheapest available look at the alphabetical edges of a string column, which is where placeholder encodings (`' ?'`, `'N/A'`, `'-'`, `'unknown'`) tend to live.

```python
query = """
SELECT
  COUNT(*)                              AS total_rows,
  COUNTIF(workclass IS NULL)            AS actual_nulls,
  COUNTIF(TRIM(workclass) = '?')        AS placeholder_workclass,
  COUNTIF(TRIM(occupation) = '?')       AS placeholder_occupation,
  COUNTIF(TRIM(native_country) = '?')   AS placeholder_native_country
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).to_dataframe()
```

> **GOTCHA — the reference page names an output column that does not exist.** It lists the standard-deviation column as `stdev`. The function returns `stddev`. The error message is at least helpful about it.

```python
query = """
SELECT name, stdev
FROM ML.DESCRIBE_DATA((SELECT age FROM `bigquery-public-data.ml_datasets.census_adult_income`))
"""
try:
    client.query(query).result()
except Exception as e:
    print(str(e).split('; reason:')[0].strip())
```

---
## Step 2 — Materialize a cleaned table

The profile found the problem, so fix it before correlating: turn `' ?'` into a real `NULL` and keep the columns the rest of the notebook needs. This is also what gives Step 9 a column with **genuine** `NULL`s, which turns out to matter for reading `ML.CORRELATION`'s output.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.exploration_census` AS
SELECT
  education_num,
  age,
  hours_per_week,
  capital_gain,
  capital_loss,
  TRIM(sex)                      AS sex,
  TRIM(race)                     AS race,
  TRIM(marital_status)           AS marital_status,
  NULLIF(TRIM(workclass), '?')   AS workclass,
  TRIM(income_bracket)           AS income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).result()

client.query(f"""
SELECT COUNT(*) AS row_count, COUNTIF(workclass IS NULL) AS workclass_nulls
FROM `{PROJECT_ID}.{DATASET_ID}.exploration_census`
""").to_dataframe()
```

---
## Step 3 — `ML.CORRELATION`: one target against many metrics

The signature is one **target** column and one or more **correlation** columns, all numeric:

```sql
ML.CORRELATION(
  { TABLE table_name | (query_statement) },
  target_col              => 'target',
  target_correlation_cols => 'metric' | ['metric_1', 'metric_2', ...]
  [, dimension_cols       => 'dim'    | ['dim_1', 'dim_2', ...] ]
  [, method               => 'PEARSON' | 'SPEARMAN' | 'KENDALL' ]
)
```

With no `dimension_cols`, you get one row per correlation column over the whole table.

```python
query = f"""
SELECT target_col, corr_col, correlation, segment_size, segment_proportion
FROM ML.CORRELATION(
  TABLE `{PROJECT_ID}.{DATASET_ID}.exploration_census`,
  target_col => 'education_num',
  target_correlation_cols => ['age', 'hours_per_week', 'capital_gain', 'capital_loss']
)
ORDER BY ABS(correlation) DESC
"""
client.query(query).to_dataframe()
```

Nothing here is large — this is census data, not a physics experiment. `hours_per_week` is the strongest of the four, and `capital_gain` is exactly the muted number Step 1's `num_zeros` predicted.

Two output columns are worth naming now because they come back in Steps 8 and 10: `segment_size` is the row count of the **segment**, and `segment_proportion` is that count over the table total. Both describe the slice, not the correlation.

---
## Step 4 — `PEARSON` is `CORR()`

The default method should be BigQuery's own `CORR()` aggregate. Worth confirming rather than assuming, because it settles what the function is doing and gives the other two methods something to be measured against.

```python
query = f"""
WITH src AS (
  SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.exploration_census`
),
mlc AS (
  SELECT corr_col, correlation
  FROM ML.CORRELATION(TABLE src,
    target_col => 'education_num',
    target_correlation_cols => ['age', 'hours_per_week', 'capital_gain'])
),
native AS (
  SELECT 'age'            AS corr_col, CORR(education_num, age)            AS c FROM src
  UNION ALL
  SELECT 'hours_per_week',            CORR(education_num, hours_per_week)       FROM src
  UNION ALL
  SELECT 'capital_gain',              CORR(education_num, capital_gain)         FROM src
)
SELECT
  m.corr_col,
  m.correlation             AS ml_correlation,
  n.c                       AS native_corr,
  m.correlation = n.c       AS bit_identical,
  ABS(m.correlation - n.c)  AS abs_diff
FROM mlc m JOIN native n USING (corr_col)
ORDER BY corr_col
"""
client.query(query).to_dataframe()
```

Same statistic, to about 15 significant digits — and **not bit-identical**. The residual is float summation order, not a different formula. Which raises the obvious question of how stable that last digit really is.

> **GOTCHA — selecting the `segment` column changes the value of `correlation`.** Same data, same arguments, same method, query cache off. The only thing that varies is which output columns the outer `SELECT` asks for.

```python
tvf = f"""
  ML.CORRELATION(
    TABLE `{PROJECT_ID}.{DATASET_ID}.exploration_census`,
    target_col => 'education_num',
    target_correlation_cols => ['age'])
"""

projections = {
    'corr_col, correlation':           'corr_col, correlation',
    '+ segment_size':                  'corr_col, correlation, segment_size',
    '+ segment_proportion':            'corr_col, correlation, segment_proportion',
    '+ target_col':                    'corr_col, correlation, target_col',
    '+ segment  <-- the ARRAY column': 'corr_col, correlation, segment',
    'SELECT *':                        '*',
}

no_cache = bigquery.QueryJobConfig(use_query_cache=False)
rows = []
for label, proj in projections.items():
    value = client.query(f'SELECT {proj} FROM {tvf}',
                         job_config=no_cache).to_dataframe()['correlation'][0]
    rows.append({'projection': label, 'correlation': repr(value)})
pd.DataFrame(rows)
```

Two distinct values across six queries, and the split is clean: every projection that includes `segment` returns one value, every projection that omits it returns the other. Column pruning changes the physical plan, the plan changes the summation order, and the summation order changes the last three digits.

The difference lands in the sixteenth decimal place and it does not matter for any decision a correlation is used to make. It matters for exactly one thing: **never compare `ML.CORRELATION` output across queries with `=`.** Round first. This notebook does, everywhere it compares.

---
## Step 5 — `SPEARMAN` is not the Spearman you were taught

Spearman's rho is Pearson's r computed on **ranks**. The whole question is what happens to ties, and this table is nothing but ties: `education_num` takes 16 distinct values across 32,561 rows.

The textbook definition — and SciPy's, and pandas' default — gives tied observations the **average** of the ranks they span (mid-ranks). SQL's `RANK()` gives them all the **smallest** rank in the group (competition ranks). Those are different numbers. Which one does BigQuery use?

```python
from scipy import stats
import numpy as np

df = client.query(f"""
SELECT education_num, age, hours_per_week
FROM `{PROJECT_ID}.{DATASET_ID}.exploration_census`
""").to_dataframe()

ml_spearman = client.query(f"""
SELECT corr_col, correlation
FROM ML.CORRELATION(
  TABLE `{PROJECT_ID}.{DATASET_ID}.exploration_census`,
  target_col => 'education_num',
  target_correlation_cols => ['age', 'hours_per_week'],
  method => 'SPEARMAN')
""", job_config=no_cache).to_dataframe().set_index('corr_col')['correlation']

target = df['education_num'].astype(float)
out = []
for col in ['age', 'hours_per_week']:
    x = df[col].astype(float)
    row = {'corr_col': col, 'ML.CORRELATION SPEARMAN': ml_spearman[col]}
    for method in ['min', 'average', 'max', 'dense']:
        row[f'CORR of rank(method={method})'] = np.corrcoef(
            target.rank(method=method), x.rank(method=method))[0, 1]
    row['scipy.stats.spearmanr'] = stats.spearmanr(target, x).statistic
    out.append(row)
pd.DataFrame(out).set_index('corr_col').T
```

`method='min'` reproduces `ML.CORRELATION`; `method='average'` reproduces SciPy. They are not close to each other — the gap is in the second decimal place, which is a real difference in a number that only lives in the first two decimal places to begin with.

The same thing in pure SQL, which is really the explanation: BigQuery computes Spearman the way a SQL engine naturally would, as `CORR()` over `RANK()`.

```python
query = f"""
WITH src AS (SELECT education_num, age FROM `{PROJECT_ID}.{DATASET_ID}.exploration_census`),
ranked AS (
  SELECT RANK() OVER (ORDER BY education_num) AS rank_target,
         RANK() OVER (ORDER BY age)           AS rank_metric
  FROM src
)
SELECT
  ROUND((SELECT correlation FROM ML.CORRELATION(TABLE src,
           target_col => 'education_num',
           target_correlation_cols => ['age'],
           method => 'SPEARMAN')), 12)                           AS ml_spearman,
  ROUND((SELECT CORR(rank_target, rank_metric) FROM ranked), 12)  AS corr_of_sql_rank,
  (SELECT COUNT(*) - COUNT(DISTINCT education_num) FROM src)      AS tied_rows_in_target,
  (SELECT COUNT(*) - COUNT(DISTINCT age) FROM src)                AS tied_rows_in_metric
"""
client.query(query, job_config=no_cache).to_dataframe()
```

Identical to 12 decimal places. And the tie counts are the mechanism, so removing the ties has to make the disagreement vanish — with no ties, every ranking convention is the same ranking.

```python
query = """
WITH src AS (
  SELECT i AS t, MOD(i * 7919, 999983) AS x
  FROM UNNEST(GENERATE_ARRAY(1, 5000)) AS i
),
ranked AS (
  SELECT RANK() OVER (ORDER BY t) AS rt, RANK() OVER (ORDER BY x) AS rx FROM src
)
SELECT
  (SELECT COUNT(*) - COUNT(DISTINCT x) FROM src)  AS tied_rows_in_x,
  ROUND((SELECT correlation FROM ML.CORRELATION(TABLE src,
     target_col => 't', target_correlation_cols => ['x'], method => 'SPEARMAN')), 12) AS ml_spearman,
  ROUND((SELECT CORR(rt, rx) FROM ranked), 12)    AS corr_of_sql_rank
"""
display(client.query(query, job_config=no_cache).to_dataframe())

x = np.arange(1, 5001)
print('scipy.stats.spearmanr on the same tie-free series:',
      round(stats.spearmanr(x, (x * 7919) % 999983).statistic, 12))
```

Zero ties, and all three agree. So this is not a bug — it is an undocumented choice of tie convention that only shows up on tied data, which is to say on most real categorical-ish integer columns.

**What to do about it.** If you are publishing a Spearman coefficient that someone will check against R, SciPy, pandas, or a textbook, either say which convention produced it or compute mid-rank Spearman yourself. If you are ranking candidate features against each other, the convention barely matters — both orderings put `hours_per_week` ahead of `age`.

---
## Step 6 — `KENDALL` *is* tie-corrected

Kendall's tau has variants that differ in exactly the same place: tau-a ignores ties, **tau-b** corrects for them, tau-c adjusts for a rectangular table. Given Step 5, the interesting question is whether this function is consistent with itself.

```python
ml_kendall = client.query(f"""
SELECT corr_col, correlation
FROM ML.CORRELATION(
  TABLE `{PROJECT_ID}.{DATASET_ID}.exploration_census`,
  target_col => 'education_num',
  target_correlation_cols => ['age', 'hours_per_week'],
  method => 'KENDALL')
""", job_config=no_cache).to_dataframe().set_index('corr_col')['correlation']

out = []
for col in ['age', 'hours_per_week']:
    x = df[col].astype(float)
    tau_b = stats.kendalltau(target, x, variant='b').statistic
    tau_c = stats.kendalltau(target, x, variant='c').statistic
    out.append({
        'corr_col': col,
        'ML.CORRELATION KENDALL': ml_kendall[col],
        'scipy tau-b (tie-corrected)': tau_b,
        'scipy tau-c': tau_c,
        'abs diff vs tau-b': abs(ml_kendall[col] - tau_b),
    })
pd.DataFrame(out).set_index('corr_col').T
```

`KENDALL` is tau-b, to floating-point noise. Not tau-c, and not an uncorrected variant.

So within one function: **Kendall corrects for ties and Spearman does not.** Neither behavior is wrong on its own; the pair of them is the thing to know, because it means the three methods are not three views of the same convention. On this table Spearman reads *higher* than its textbook value while Kendall reads exactly its textbook value, so part of the gap between the two numbers is a real difference between the statistics and part of it is the tie handling.

---
## Step 7 — What Kendall costs

The documentation says the Kendall method has higher complexity and can be slow on large datasets, and recommends Pearson or Spearman for large tables. That is a claim with a number in it, so measure it: the same query at growing row counts, cache off, reading `slot_millis` off the finished job rather than trusting a stopwatch.

```python
import time

def timed(n, method, reps=2):
    sql = f"""
    SELECT correlation FROM ML.CORRELATION(
      (SELECT i AS t, MOD(i * 7919, 1000) AS x FROM UNNEST(GENERATE_ARRAY(1, {n})) AS i),
      target_col => 't', target_correlation_cols => ['x'], method => '{method}')
    """
    best = None
    for _ in range(reps):
        start = time.time()
        job = client.query(sql, job_config=bigquery.QueryJobConfig(use_query_cache=False))
        job.result()
        run = (round(time.time() - start, 2), job.slot_millis)
        if best is None or run[1] < best[1]:
            best = run          # min slot_ms: the standard way to de-noise a timing
    return best

records = []
for n in [1_000, 2_500, 5_000, 10_000, 20_000]:
    for method in ['PEARSON', 'SPEARMAN', 'KENDALL']:
        elapsed, slot_ms = timed(n, method)
        records.append({'n': n, 'method': method, 'elapsed_s': elapsed, 'slot_ms': slot_ms})

timings = pd.DataFrame(records)
timings.pivot(index='n', columns='method', values='slot_ms')
```

```python
slots = timings.pivot(index='n', columns='method', values='slot_ms')

print('slot_ms multiplier for the last doubling (10,000 -> 20,000 rows):')
for method in ['PEARSON', 'SPEARMAN', 'KENDALL']:
    print(f'  {method:9s} {slots[method][20_000] / slots[method][10_000]:7.1f}x')

# Fit only on n >= 5,000 -- below that, fixed query startup dominates and flattens the curve.
fit = slots.loc[5_000:]
n_log = np.log(fit.index.values.astype(float))

print(f"\n{'method':10s} {'fitted p in slot_ms ~ n^p':>26s} {'that fit, extrapolated to n = 1e6':>36s}")
for method in ['PEARSON', 'SPEARMAN', 'KENDALL']:
    slope, intercept = np.polyfit(n_log, np.log(fit[method].values.astype(float)), 1)
    at_1m = np.exp(intercept + slope * np.log(1e6))
    human = (f'{at_1m / 1000:,.1f} slot-seconds' if at_1m < 3_600_000
             else f'{at_1m / 3_600_000:,.0f} slot-hours')
    print(f'{method:10s} {"p = " + format(slope, ".2f"):>26s} {human:>36s}')
```

```python
# The other side of the same measurement: Pearson and Spearman at 1,000,000 rows, for real.
for method in ['PEARSON', 'SPEARMAN']:
    elapsed, slot_ms = timed(1_000_000, method)
    print(f'{method:9s} n=1,000,000  elapsed {elapsed:>6.2f}s  slot_ms {slot_ms:,}')
```

Pearson and Spearman show no size dependence at all across this range — their doubling multipliers scatter on both sides of 1× and their fitted exponents are noise around zero, because at these sizes the cost is query startup, not arithmetic. A million rows still returns in about a second.

Kendall's is the O(n²) pair comparison the statistic is defined by, showing up in the bill: every doubling of rows multiplies slot time several-fold, and the fitted exponent lands near 2 — which is what the definition demands and what the documentation's warning is actually about.

The extrapolation is a *fit*, not a measurement, and it is the number worth carrying: a million-row Kendall is a wholly different kind of query from a million-row Pearson. For calibration outside the fit, a `KENDALL` on 100,000 rows of this shape does not finish within 12 minutes and passes 11 slot-minutes before being cancelled.

**Practical rule:** run `KENDALL` on a sample or a single segment, never on a raw fact table. `SPEARMAN` gives you rank-based robustness at Pearson's price, which is usually what you actually wanted from Kendall.

---
## Step 8 — `dimension_cols` is `GROUP BY CUBE`

The documentation says dimension slicing works "similar to a `GROUP BY CUBE` operation." Measured, it is not similar — it is the same, down to the row count. With three dimensions you get the global row, every single-dimension slice, every pair, and every triple that exists in the data.

```python
query = f"""
WITH src AS (
  SELECT education_num, age, sex, race, marital_status
  FROM `{PROJECT_ID}.{DATASET_ID}.exploration_census`
),
cube_cells AS (
  SELECT sex, race, marital_status, COUNT(*) AS n
  FROM src
  GROUP BY CUBE (sex, race, marital_status)
)
SELECT
  (SELECT COUNT(*) FROM cube_cells)                            AS group_by_cube_cells,
  (SELECT COUNT(*) FROM ML.CORRELATION(TABLE src,
     target_col => 'education_num',
     target_correlation_cols => ['age'],
     dimension_cols => ['sex', 'race', 'marital_status']))     AS ml_correlation_rows,
  (SELECT COUNT(*) FROM cube_cells WHERE n = 1)                AS single_row_cells
"""
client.query(query, job_config=no_cache).to_dataframe()
```

```python
query = f"""
SELECT
  ARRAY_LENGTH(segment)        AS dims_in_segment,
  COUNT(*)                     AS rows_out,
  COUNTIF(correlation IS NULL) AS null_correlations,
  MIN(segment_size)            AS smallest_segment,
  MAX(segment_size)            AS largest_segment
FROM ML.CORRELATION(
  TABLE `{PROJECT_ID}.{DATASET_ID}.exploration_census`,
  target_col => 'education_num',
  target_correlation_cols => ['age'],
  dimension_cols => ['sex', 'race', 'marital_status'])
GROUP BY dims_in_segment
ORDER BY dims_in_segment
"""
client.query(query, job_config=no_cache).to_dataframe()
```

`ARRAY_LENGTH(segment)` is how many dimensions a row is *not* rolled up over, so the four groups are the four levels of the cube. Note what the engine does **not** do: it does not drop degenerate cells. A segment with a single row comes back with `correlation = NULL` rather than being filtered out, which is why the row count matches the CUBE exactly. If you are counting output rows to size a dashboard, count CUBE cells.

> **GOTCHA — `dimension_cols` accepts any groupable type, including `INT64`.** Pass a continuous numeric column by mistake and you get one segment per distinct value, silently.

```python
query = f"""
SELECT
  (SELECT COUNT(DISTINCT age) FROM `{PROJECT_ID}.{DATASET_ID}.exploration_census`) AS distinct_ages,
  (SELECT COUNT(*) FROM ML.CORRELATION(
     TABLE `{PROJECT_ID}.{DATASET_ID}.exploration_census`,
     target_col => 'education_num',
     target_correlation_cols => ['capital_gain'],
     dimension_cols => ['age'])) AS rows_out_using_age_as_a_dimension
"""
client.query(query, job_config=no_cache).to_dataframe()
```

One row per distinct age, plus the global rollup, and nothing errors. Bucketize continuous columns before using them as dimensions — `functions/bucketizing` (`functions/bucketizing/`) is the folder for that.

The hard ceiling is 12 dimension columns, and that error *is* explicit:

```python
query = """
SELECT COUNT(*) FROM ML.CORRELATION(
  TABLE `bigquery-public-data.ml_datasets.census_adult_income`,
  target_col => 'education_num',
  target_correlation_cols => ['age'],
  dimension_cols => ['workclass', 'functional_weight', 'education', 'marital_status',
                     'occupation', 'relationship', 'race', 'sex', 'capital_gain',
                     'capital_loss', 'hours_per_week', 'native_country', 'income_bracket'])
"""
try:
    client.query(query).result()
except Exception as e:
    print(str(e).split('; reason:')[0].strip())
```

---
## Step 9 — Two kinds of `NULL` in one dimension column

A dimension column in the output is `NULL` for two completely different reasons: the row is a **rollup** over that dimension, or the segment *is* the genuine `NULL` group in the data. This is why Step 2 turned `' ?'` into a real `NULL` — `workclass` now has both.

The `segment` array is the disambiguator. A dimension that was rolled up is **absent** from `segment`; a dimension holding a genuine `NULL` is **present** in `segment` with a `null` value.

```python
query = f"""
SELECT
  CASE
    WHEN workclass IS NULL
     AND NOT EXISTS (SELECT 1 FROM UNNEST(segment) s WHERE s.dimension_col = 'workclass')
      THEN 'ALL WORKCLASSES (rollup)'
    WHEN workclass IS NULL THEN 'MISSING (was " ?")'
    ELSE workclass
  END                          AS workclass_label,
  ROUND(correlation, 4)        AS correlation,
  segment_size,
  ROUND(segment_proportion, 4) AS segment_proportion
FROM ML.CORRELATION(
  TABLE `{PROJECT_ID}.{DATASET_ID}.exploration_census`,
  target_col => 'education_num',
  target_correlation_cols => ['hours_per_week'],
  dimension_cols => ['workclass'])
ORDER BY segment_size DESC
"""
client.query(query, job_config=no_cache).to_dataframe()
```

Without that `CASE`, the rollup row and the missing-data row are two rows both labelled `NULL`, sorted next to each other, with entirely different meanings. It is the kind of thing that survives review because the output *looks* fine.

And the missing group is not a rounding detail here: it is the fifth-largest segment, and its correlation has the opposite sign to the whole table's. Whatever caused `workclass` to go unrecorded is correlated with something, which is its own finding.

---
## Step 10 — `segment_size` is not the *n* the correlation used

`segment_size` counts rows in the segment. `correlation` is computed **pairwise** — for each correlation column, rows where either that column or the target is `NULL` are dropped. When the two differ, `segment_size` overstates the evidence behind the number sitting next to it.

Five rows, one `NULL` in each metric column:

```python
query = """
WITH src AS (
  SELECT 1 AS t, 2.0  AS x, 10.0 AS y UNION ALL
  SELECT 2,       4.0,       20.0     UNION ALL
  SELECT 3,       6.0,       NULL     UNION ALL
  SELECT 4,       9.0,       40.0     UNION ALL
  SELECT 5,       NULL,      55.0
)
SELECT
  m.corr_col,
  m.correlation,
  m.segment_size,
  h.pairwise_n,
  h.pairwise_corr,
  ROUND(m.correlation - h.pairwise_corr, 15) AS diff_vs_pairwise
FROM ML.CORRELATION(TABLE src, target_col => 't', target_correlation_cols => ['x', 'y']) m
JOIN (
  SELECT 'x' AS corr_col, COUNTIF(x IS NOT NULL) AS pairwise_n, CORR(t, x) AS pairwise_corr FROM src
  UNION ALL
  SELECT 'y',             COUNTIF(y IS NOT NULL),               CORR(t, y)                  FROM src
) h USING (corr_col)
ORDER BY m.corr_col
"""
client.query(query, job_config=no_cache).to_dataframe()
```

`segment_size` says 5 for both. Both correlations were computed from 4 rows, and both match `CORR()`'s pairwise answer. Two consequences:

- A `segment_size` filter is **not** a sample-size filter. `WHERE segment_size >= 30` does not guarantee 30 usable pairs.
- Two correlation columns on the same output row can rest on different sample sizes, and nothing in the output says so. If your columns have different `NULL` rates — which Step 1 will tell you — compute the pairwise counts yourself.

---
## Step 11 — Putting it together: the global correlation is nobody's correlation

This is what `dimension_cols` is for. One target, one metric, sliced by `sex` and `marital_status`, restricted to segments big enough to talk about.

```python
query = f"""
SELECT
  IFNULL(sex, 'ALL')            AS sex,
  IFNULL(marital_status, 'ALL') AS marital_status,
  ROUND(correlation, 4)         AS correlation,
  segment_size
FROM ML.CORRELATION(
  TABLE `{PROJECT_ID}.{DATASET_ID}.exploration_census`,
  target_col => 'education_num',
  target_correlation_cols => ['hours_per_week'],
  dimension_cols => ['sex', 'marital_status'])
WHERE segment_size >= 500
ORDER BY correlation DESC
"""
sliced = client.query(query, job_config=no_cache).to_dataframe()

overall = sliced.query("sex == 'ALL' and marital_status == 'ALL'")['correlation'].iloc[0]
slices = sliced.query("sex != 'ALL' or marital_status != 'ALL'")
print(f'whole-table correlation:  {overall}')
print(f'across the {len(slices)} slices with >= 500 rows: '
      f'{slices.correlation.min()} to {slices.correlation.max()}')
sliced
```

The whole-table number sits mid-table in a spread that runs from well under half its value to nearly twice it, and it is not the answer for any group in the table. Never-married respondents show the strongest link between education and hours worked; married ones the weakest. A single coefficient reported for this table would be arithmetically correct and analytically useless — which is the entire argument for `dimension_cols` existing.

The `>= 500` filter is doing real work, too. Without it the extremes of this output are tiny segments, and Step 10 is the reminder that even `segment_size` is only an upper bound on the evidence.

---
## Examples — `%%bigquery` Magics

The same operation using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  corr_col,
  ROUND(correlation, 4) AS correlation,
  segment_size
FROM ML.CORRELATION(
  TABLE `statmike-mlops-349915.bq_ml.exploration_census`,
  target_col => 'education_num',
  target_correlation_cols => ['age', 'hours_per_week', 'capital_gain', 'capital_loss'])
ORDER BY ABS(correlation) DESC
```

---
## Examples — BigFrames

There is **no** `bigframes.ml` wrapper for either function. BigFrames offers `DataFrame.describe()` and `DataFrame.corr()`, which are pandas-shaped equivalents compiled to BigQuery SQL — a different implementation, not these functions, and `DataFrame.corr()` supports Pearson only with no dimension slicing. To reach the BigQuery functions themselves, run the SQL through `read_gbq`.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

bdf = bpd.read_gbq(f"""
SELECT corr_col, ROUND(correlation, 4) AS correlation
FROM ML.CORRELATION(
  TABLE `{PROJECT_ID}.{DATASET_ID}.exploration_census`,
  target_col => 'education_num',
  target_correlation_cols => ['age', 'hours_per_week'])
""")
bdf
```
