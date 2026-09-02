# AI.PREDICT — BigQuery AI Functions

`AI.PREDICT` is a **table-valued function** that performs regression and classification on structured data with **TabFM**, Google's pre-trained tabular foundation model. Hand it a training input and a prediction input in the same query and it returns predictions — there is no `CREATE MODEL`, no training job, no connection, no endpoint, and no model object to manage or clean up.

**When to use it:**
- Get a baseline prediction on a tabular dataset without training or tuning anything
- Score a small table ad hoc, where standing up and maintaining a model isn't worth the effort
- Prototype a predictive feature in SQL before deciding whether a trained model is justified

**Alternatives:**
- `functions/ai_forecast` (`AI.FORECAST`) — the built-in TimesFM model for time series: use it when you are extending a value forward in time rather than labeling rows
- `functions/ai_evaluate` (`AI.EVALUATE`) — the companion metrics function; its TabFM branch takes the same training and prediction inputs and returns accuracy metrics instead of predictions
- `CREATE MODEL` plus `ML.PREDICT` in `bq-ml/models` (`../bq-ml/models/`) — trained BigQuery ML models: use them when you need a persisted, reusable model, more than 20 features, more than 10 classes, explainability, or control over the algorithm and its hyperparameters

**The task type comes from the label column's type, not from an argument:** a `STRING` or `BOOL` label runs classification, and an `INT64`, `FLOAT64`, `NUMERIC`, or `BIGNUMERIC` label runs regression. A categorical label stored as `0`/`1` therefore runs as regression — cast it to `STRING` first. Example 6 runs one label both ways and prints what each call returns.

**Preview (verified 2026-09-01):** the documented limits are 20 feature columns and 10 classes. Feature and label columns must be `STRING`, `BOOL`, `INT64`, `FLOAT64`, `NUMERIC`, or `BIGNUMERIC`; `DATE`, `TIMESTAMP`, `BYTES`, `JSON`, `GEOGRAPHY`, `ARRAY`, and `STRUCT` are rejected. The predictions are not reproducible: repeating an identical call returns slightly different numbers, so materialize results instead of re-running (example 7). Row-count ceilings and `NULL` handling are undocumented too — examples 5 through 8 measure what they can and label the rest as observation.

**Featured in:** `workflows/tabular_prediction` (Zero-Shot Tabular Prediction) | `workflows/metric_diagnostics` (Metric Diagnostics) | `workflows/data_enrichment` (Data Enrichment)

**References:** `RESOURCES.md` (Full syntax reference) | [Official documentation](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-predict) | `setup` (Setup guide)

---
## Setup

Set your project and location, and authenticate.

> `AI.PREDICT` needs no connection, no `CREATE MODEL`, and no dataset — it uses your end-user credentials and runs the built-in TabFM model inside BigQuery. See the `setup` (Setup Reference) for details.

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

# Register %%bigquery cell magic (auto-loaded in Colab, needed elsewhere)
%load_ext bigquery_magics
```

---
## Examples — SQL

Progressive examples from simplest to most advanced. `AI.PREDICT(TRAINING_INPUT, PREDICTION_INPUT [, label_col => 'LABEL_COL'])` is a table-valued function, so it goes in `FROM`. It returns the prediction input's columns plus `predicted_<label>`, and for classification also `predicted_<label>_probs`.

### Setup: A deterministic train/test split

Every example below splits `bigquery-public-data.ml_datasets.penguins` the same way: hash the whole row with `FARM_FINGERPRINT(TO_JSON_STRING(p))`, keep buckets 0-7 for training and buckets 8-9 as holdout.

The official examples use `RAND() <= 0.8` inside a CTE that is referenced twice. BigQuery does not guarantee that a CTE is evaluated once, so a row can land in both splits or in neither. A row hash is stable across references and across runs. Penguins has no primary key, so the same hash doubles as the `row_id` used to join predictions back to their actual values.

The cell below creates nothing — it just reports the split and confirms the hash is unique per row.

```python
query = """
WITH penguins AS (
  SELECT
    p.*,
    FARM_FINGERPRINT(TO_JSON_STRING(p)) AS row_id,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
)
SELECT
  COUNT(*) AS rows_total,
  COUNT(DISTINCT row_id) AS distinct_row_ids,
  COUNTIF(split_bucket < 8) AS training_rows,
  COUNTIF(split_bucket >= 8) AS holdout_rows
FROM penguins
"""
client.query(query).to_dataframe()
```

### 1. Regression — predict body mass

`body_mass_g` is `FLOAT64`, so `AI.PREDICT` runs a regression and returns `predicted_body_mass_g` with the same type.

The training input carries the six feature columns plus the label. The prediction input drops the label and carries `row_id` instead: the prediction input may hold columns that are not in the training data, and they pass straight through to the output — which is what makes the join back to the actual values possible. Holding the label out of the prediction input also keeps the answer out of the model's view; the official examples leave it in.

Verified 2026-09-02: the reference page describes passthrough columns as coming from the *training* input, while the rows that come back carry the *prediction* input's columns — which is what the `row_id` join below relies on. Put the join key on the prediction side.

```python
query = """
WITH penguins AS (
  SELECT
    p.*,
    FARM_FINGERPRINT(TO_JSON_STRING(p)) AS row_id,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
),
predictions AS (
  SELECT *
  FROM AI.PREDICT(
    -- Training data: features + label, no row_id
    (SELECT * EXCEPT(row_id, split_bucket) FROM penguins WHERE split_bucket < 8),
    -- Prediction data: features + row_id, label removed
    (SELECT * EXCEPT(row_id, split_bucket, body_mass_g), row_id FROM penguins WHERE split_bucket >= 8),
    label_col => 'body_mass_g')
)
SELECT
  h.species,
  h.island,
  h.body_mass_g AS actual_body_mass_g,
  pr.predicted_body_mass_g,
  ROUND(pr.predicted_body_mass_g - h.body_mass_g, 1) AS error_g
FROM predictions AS pr
JOIN penguins AS h USING (row_id)
ORDER BY h.row_id
LIMIT 10
"""
client.query(query).to_dataframe()
```

### 2. Binary classification — predict `sex` and read the probabilities

A `STRING` label switches the task to classification. Alongside `predicted_sex`, `AI.PREDICT` returns `predicted_sex_probs`, an `ARRAY<STRUCT<label STRING, prob FLOAT64>>` holding every candidate class and its probability. The `label` subfield is always `STRING`, even when the label column is `BOOL`.

`CROSS JOIN UNNEST` flattens that array into one row per class, which is the clearest way to see its shape. Example 3 shows the other idiom: a scalar subquery that pulls one class out and keeps one row per prediction.

`sex` holds three values in this table — `MALE`, `FEMALE`, and a literal `.` placeholder — plus NULLs. Filtering down to the two real classes is a label-cleaning step you own; `AI.PREDICT` does not do it for you.

```python
query = """
WITH penguins AS (
  SELECT
    p.*,
    FARM_FINGERPRINT(TO_JSON_STRING(p)) AS row_id,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE sex IN ('MALE', 'FEMALE')
),
predictions AS (
  SELECT *
  FROM AI.PREDICT(
    (SELECT * EXCEPT(row_id, split_bucket) FROM penguins WHERE split_bucket < 8),
    (SELECT * EXCEPT(row_id, split_bucket, sex), row_id FROM penguins WHERE split_bucket >= 8),
    label_col => 'sex')
)
SELECT
  h.species,
  h.body_mass_g,
  h.sex AS actual_sex,
  pr.predicted_sex,
  probs.label AS class_label,
  ROUND(probs.prob, 6) AS class_prob
FROM predictions AS pr
JOIN penguins AS h USING (row_id)
CROSS JOIN UNNEST(pr.predicted_sex_probs) AS probs
ORDER BY h.row_id, class_prob DESC
LIMIT 10
"""
client.query(query).to_dataframe()
```

### 3. Multi-class — predict `species`, and the 10-class ceiling

Three classes, same call shape. A scalar subquery over `predicted_species_probs` pulls the probability of the winning class, giving one confidence value per row instead of one row per class.

Penguin species is very nearly a pure function of the body measurements, so accuracy lands at or near 1.0 and confidence sits at near-certainty. That is a property of this dataset, not evidence that TabFM is accurate on yours — a problem this separable is also solved by a two-line logistic regression. Read degenerate metrics as a signal to find a harder test set, not as a result worth reporting.

Classification is capped at **10 distinct label values**. That cap is checked when the query runs rather than when it is analyzed, so a too-wide label fails a few seconds in, after the query has started. The second block forces the error by turning `flipper_length_mm` into a per-millimeter string label.

```python
query = """
WITH penguins AS (
  SELECT
    p.*,
    FARM_FINGERPRINT(TO_JSON_STRING(p)) AS row_id,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
),
predictions AS (
  SELECT *
  FROM AI.PREDICT(
    (SELECT * EXCEPT(row_id, split_bucket) FROM penguins WHERE split_bucket < 8),
    (SELECT * EXCEPT(row_id, split_bucket, species), row_id FROM penguins WHERE split_bucket >= 8),
    label_col => 'species')
)
SELECT
  COUNT(*) AS holdout_rows,
  COUNT(DISTINCT h.species) AS classes_in_holdout,
  COUNTIF(pr.predicted_species = h.species) AS correct,
  ROUND(COUNTIF(pr.predicted_species = h.species) / COUNT(*), 4) AS accuracy,
  ROUND(MIN((SELECT prob FROM UNNEST(pr.predicted_species_probs) WHERE label = pr.predicted_species)), 4) AS min_confidence
FROM predictions AS pr
JOIN penguins AS h USING (row_id)
"""
display(client.query(query).to_dataframe())

# More than 10 distinct label values: rejected once the query starts running
too_many_classes = """
WITH penguins AS (
  SELECT
    p.culmen_length_mm,
    p.culmen_depth_mm,
    p.body_mass_g,
    CAST(CAST(p.flipper_length_mm AS INT64) AS STRING) AS flipper_mm,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE flipper_length_mm IS NOT NULL AND body_mass_g IS NOT NULL
)
SELECT *
FROM AI.PREDICT(
  (SELECT * EXCEPT(split_bucket) FROM penguins WHERE split_bucket < 8),
  (SELECT * EXCEPT(split_bucket, flipper_mm) FROM penguins WHERE split_bucket >= 8),
  label_col => 'flipper_mm')
"""
try:
    client.query(too_many_classes).result()
except Exception as e:
    print('Too many classes ->', str(e).splitlines()[0])
```

### 4. `label_col` defaults to a column named `label`

`label_col` is optional. When the training input already has a column literally named `label`, drop the argument — the two positional table arguments are all `AI.PREDICT` needs. The output column follows the label name, so it comes back as `predicted_label`.

Its companion is stricter: on `AI.EVALUATE`'s TabFM branch, `label_col` is **required** even when the column is named `label` (verified 2026-09-01 — omitting it returns `AI.EVALUATE expects either timestamp_col and data_col ... or label_col`).

```python
query = """
WITH penguins AS (
  SELECT
    p.* EXCEPT(body_mass_g),
    p.body_mass_g AS label,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
)
SELECT species, island, sex, predicted_label
FROM AI.PREDICT(
  (SELECT * EXCEPT(split_bucket) FROM penguins WHERE split_bucket < 8),
  (SELECT * EXCEPT(split_bucket, label) FROM penguins WHERE split_bucket >= 8))
ORDER BY predicted_label DESC
LIMIT 10
"""
client.query(query).to_dataframe()
```

### 5. The limits — 20 feature columns, and six allowed column types

Both of these are enforced while the query is analyzed, so they fail instantly and cost nothing: no model inference runs.

- **20 feature columns.** Penguins has six. The first block pads the training input out to 21 and reads the error back. The documented escalation path is an email to `bqml-feedback@google.com`.
- **Column types.** Feature and label columns must be `STRING`, `BOOL`, `INT64`, `FLOAT64`, `NUMERIC`, or `BIGNUMERIC`. `DATE`, `TIMESTAMP`, `BYTES`, `JSON`, `GEOGRAPHY`, `ARRAY`, and `STRUCT` are all rejected (verified 2026-09-01). The second block adds a `DATE` column and shows the rejection; the third `EXTRACT`s that date into integer parts and runs.

Encoding a date is a modeling decision as much as a workaround. Year, month, and day-of-week are periodic features; a day offset from a fixed origin is a trend feature. Pick the ones that match the pattern you expect, and keep an eye on the 20-column budget while you add them.

```python
# (a) 21 feature columns — one over the documented cap of 20
extra_features = ',\n    '.join(
    f'culmen_depth_mm * {i} AS extra_feature_{i:02d}' for i in range(1, 16)
)
too_wide = f"""
WITH wide AS (
  SELECT
    p.*,
    {extra_features}
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
)
SELECT *
FROM AI.PREDICT(
  (SELECT * FROM wide),
  (SELECT * EXCEPT(body_mass_g) FROM wide),
  label_col => 'body_mass_g')
"""
try:
    client.query(too_wide).result()
except Exception as e:
    print('Too many features ->', str(e).splitlines()[0])

# (b) A DATE feature — rejected as an unsupported type
with_date = """
WITH dated AS (
  SELECT
    p.*,
    DATE_ADD(DATE '2026-01-01', INTERVAL CAST(p.culmen_length_mm AS INT64) DAY) AS observed_on
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
)
SELECT *
FROM AI.PREDICT(
  (SELECT * FROM dated),
  (SELECT * EXCEPT(body_mass_g) FROM dated),
  label_col => 'body_mass_g')
"""
try:
    client.query(with_date).result()
except Exception as e:
    print('Unsupported type ->', ' '.join(str(e).splitlines()[:2]))

# (c) The workaround — EXTRACT the date into INT64 parts
encoded_date = """
WITH dated AS (
  SELECT
    p.*,
    DATE_ADD(DATE '2026-01-01', INTERVAL CAST(p.culmen_length_mm AS INT64) DAY) AS observed_on
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
),
encoded AS (
  SELECT
    * EXCEPT(observed_on),
    EXTRACT(YEAR FROM observed_on) AS observed_year,
    EXTRACT(MONTH FROM observed_on) AS observed_month,
    EXTRACT(DAYOFWEEK FROM observed_on) AS observed_dayofweek,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(dated))), 10) AS split_bucket
  FROM dated
)
SELECT species, observed_year, observed_month, observed_dayofweek, predicted_body_mass_g
FROM AI.PREDICT(
  (SELECT * EXCEPT(split_bucket) FROM encoded WHERE split_bucket < 8),
  (SELECT * EXCEPT(split_bucket, body_mass_g) FROM encoded WHERE split_bucket >= 8),
  label_col => 'body_mass_g')
ORDER BY predicted_body_mass_g DESC
LIMIT 5
"""
client.query(encoded_date).to_dataframe()
```

### 6. The silent one — an INT64-coded categorical runs as regression

There is no `task_type` argument, so the label column's type is the only thing that selects the task. That makes one very common encoding a trap: `sex` stored as `1`/`0` rather than `MALE`/`FEMALE` is a category to you and a number to TabFM. The query succeeds either way — no error, no warning, and nothing in the output announces which task ran.

The cell below sends the same label through `AI.PREDICT` twice over the same split, once as `STRING` and once as an `INT64` code, and prints the columns each call adds. Classification returns `predicted_sex` plus `predicted_sex_probs`; regression returns a single floating-point column and no probabilities at all, with values on a continuous scale rather than confined to the two codes — the printed range and the count of predictions that land exactly on `0` or `1` say how far the two differ.

The rule generalizes past 0/1. A 1-5 star rating, a survey code, a priority level: as `INT64` each one is a regression target, and you get 3.7 with no class probabilities. Cast a coded categorical to `STRING` before you pass it, and remember that the fix is invisible in the SQL if you do not — the only symptom is a fractional prediction and a missing `_probs` column.

```python
# (a) The label as STRING — classification
as_string = """
WITH penguins AS (
  SELECT
    p.*,
    FARM_FINGERPRINT(TO_JSON_STRING(p)) AS row_id,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE sex IN ('MALE', 'FEMALE')
),
holdout AS (
  SELECT * FROM penguins WHERE split_bucket >= 8
)
SELECT h.sex AS actual_sex, pr.*
FROM AI.PREDICT(
  (SELECT * EXCEPT(row_id, split_bucket) FROM penguins WHERE split_bucket < 8),
  (SELECT * EXCEPT(row_id, split_bucket, sex), row_id FROM holdout),
  label_col => 'sex') AS pr
JOIN holdout AS h USING (row_id)
ORDER BY row_id
"""

# (b) The same label encoded 0/1 as INT64 — regression, no error and no warning
as_int64 = """
WITH penguins AS (
  SELECT
    p.* EXCEPT(sex),
    IF(p.sex = 'MALE', 1, 0) AS sex_code,
    FARM_FINGERPRINT(TO_JSON_STRING(p)) AS row_id,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE p.sex IN ('MALE', 'FEMALE')
),
holdout AS (
  SELECT * FROM penguins WHERE split_bucket >= 8
)
SELECT pr.*
FROM AI.PREDICT(
  (SELECT * EXCEPT(row_id, split_bucket) FROM penguins WHERE split_bucket < 8),
  (SELECT * EXCEPT(row_id, split_bucket, sex_code), row_id FROM holdout),
  label_col => 'sex_code') AS pr
ORDER BY row_id
"""

string_run = client.query(as_string).to_dataframe()
int64_run = client.query(as_int64).to_dataframe()

print('STRING label -> columns AI.PREDICT adds:',
      [c for c in string_run.columns if c.startswith('predicted_')])
print('INT64  label -> columns AI.PREDICT adds:',
      [c for c in int64_run.columns if c.startswith('predicted_')])
print(f"INT64  label -> the predicted column comes back as {int64_run['predicted_sex_code'].dtype}, "
      f"ranging {int64_run['predicted_sex_code'].min():.4f} to {int64_run['predicted_sex_code'].max():.4f}")
print('INT64  label -> predictions equal to one of the two codes (0 or 1):',
      int(int64_run['predicted_sex_code'].isin([0, 1]).sum()), 'of', len(int64_run))

display(
    string_run[['row_id', 'actual_sex', 'predicted_sex']]
    .merge(int64_run[['row_id', 'predicted_sex_code']], on='row_id')
    .head(8)
)
```

### 7. Determinism and `NULL` features — measured, because neither is documented

The split is deterministic; the predictions are not. TabFM averages several differently shuffled passes over the input — the `n_ensembles` that example 8's pricing formula multiplies by — and that average does not repeat exactly. Two identical calls therefore return the same rows with slightly different numbers.

The cell below runs one query twice with the query cache turned off (the cache would hand back the first result verbatim and hide the effect) and prints how many predictions moved and by how much. Expect a small drift rather than a different answer: enough to break an exact-equality test, not enough to change a decision.

The practical rule is to materialize predictions into a table and join to that table. Re-running the call to "get the same rows back" gives you different numbers, and any before/after comparison against a fresh run measures the model's noise along with whatever you changed.

`NULL` handling is undocumented as well, so the cell reports it rather than asserting it: how many holdout rows carry a missing feature value, how many of those come back scored, and whether both runs return the full holdout. A `NULL` in the *label* column is a separate matter — the split every example uses filters those rows out before training.

```python
repeatable = """
WITH penguins AS (
  SELECT
    p.*,
    FARM_FINGERPRINT(TO_JSON_STRING(p)) AS row_id,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
),
holdout AS (
  SELECT * FROM penguins WHERE split_bucket >= 8
)
SELECT
  pr.row_id,
  pr.predicted_body_mass_g,
  (h.species IS NULL OR h.island IS NULL OR h.sex IS NULL
   OR h.culmen_length_mm IS NULL OR h.culmen_depth_mm IS NULL
   OR h.flipper_length_mm IS NULL) AS has_null_feature
FROM AI.PREDICT(
  (SELECT * EXCEPT(row_id, split_bucket) FROM penguins WHERE split_bucket < 8),
  (SELECT * EXCEPT(row_id, split_bucket, body_mass_g), row_id FROM holdout),
  label_col => 'body_mass_g') AS pr
JOIN holdout AS h USING (row_id)
"""

# Cache off: an identical query would otherwise return the first run's rows and prove nothing
no_cache = bigquery.QueryJobConfig(use_query_cache=False)
run_a = client.query(repeatable, job_config=no_cache).to_dataframe()
run_b = client.query(repeatable, job_config=no_cache).to_dataframe()

both = run_a.merge(run_b, on='row_id', suffixes=('_a', '_b'))
gap = (both['predicted_body_mass_g_a'] - both['predicted_body_mass_g_b']).abs()

print(f'Holdout rows returned — run A: {len(run_a)}, run B: {len(run_b)}')
print(f'Rows whose two predictions differ: {int((gap > 0).sum())} of {len(both)}')
print(f'Difference between the runs — max: {gap.max():.1f} g, mean: {gap.mean():.1f} g, '
      f"on predictions averaging {run_a['predicted_body_mass_g'].mean():.0f} g")

null_feature = run_a[run_a['has_null_feature']]
print(f'Holdout rows carrying a NULL feature: {len(null_feature)} — '
      f"{int(null_feature['predicted_body_mass_g'].notna().sum())} came back with a prediction")
```

### 8. Sizing and cost

**Size.** No maximum training-row count is documented. Measured on this project's on-demand slots (2026-09-01): a call fails with `Resources exceeded during query execution: The query could not be executed in the allotted memory` at 10,000 training rows, while 8,000 rows succeeds in about 94 seconds and 5,000 rows in about 93 seconds. That is an observed resource ceiling on one billing configuration, not a documented limit — it can move with column count, slot availability, or a reservation. Treat roughly 5,000 training rows as the safe working assumption and sample or stratify above it. Every call also takes 30-95 seconds regardless of input size, so latency rather than row count is usually what bounds an interactive workflow.

**Cost today.** During Preview, `AI.PREDICT` bills the ordinary way: in slots on Enterprise and Enterprise Plus editions, or by bytes processed under on-demand pricing.

**Pricing changes on 2026-10-30 (announced, not yet in effect).** Google has announced that TabFM in BigQuery moves to token-based pricing on that date — TabFM tokens for the model inference, plus the usual slots or bytes processed for the rest of the query. The published formulas are `input tokens = (train_rows * columns + predict_rows * (columns - 1)) * n_ensembles` and `output tokens = predict_rows * n_ensembles`, at $0.05 per million input tokens and $0.20 per million output tokens. `n_ensembles` — the number of differently shuffled passes the model averages — has no documented value and no argument to control it, so a dollar figure is **not** computable from the documentation as written. The query below reports the per-pass token counts: everything in those formulas except the `n_ensembles` multiplier. If you are reading this on or after 2026-10-30, re-check the [BigQuery pricing page](https://docs.cloud.google.com/bigquery/pricing) before relying on either the formulas or the rates.

Note that `AI.EVALUATE` does not reuse an `AI.PREDICT` result — its TabFM branch takes the same two inputs and runs the same inference again. Running both over one split pays for the model twice.

```python
query = """
WITH penguins AS (
  SELECT MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
),
sizing AS (
  SELECT
    COUNTIF(split_bucket < 8) AS train_rows,
    COUNTIF(split_bucket >= 8) AS predict_rows,
    7 AS columns_referenced  -- 6 feature columns + the label column
  FROM penguins
)
SELECT
  train_rows,
  predict_rows,
  columns_referenced,
  train_rows * columns_referenced + predict_rows * (columns_referenced - 1) AS input_tokens_per_pass,
  predict_rows AS output_tokens_per_pass
FROM sizing
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same call using IPython magics — SQL directly in the cell.

### Regression with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

WITH penguins AS (
  SELECT
    p.*,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
)
SELECT species, island, sex, predicted_body_mass_g
FROM AI.PREDICT(
  (SELECT * EXCEPT(split_bucket) FROM penguins WHERE split_bucket < 8),
  (SELECT * EXCEPT(split_bucket, body_mass_g) FROM penguins WHERE split_bucket >= 8),
  label_col => 'body_mass_g')
ORDER BY predicted_body_mass_g DESC
LIMIT 5
```

---
## Examples — BigFrames

There is no native BigFrames API for `AI.PREDICT` yet — `bigframes.bigquery.ai` exposes no `predict` (checked against bigframes 2.39.0, this project's pin in `uv.lock`). Use `session.read_gbq_query()` to run the SQL and return a BigFrames DataFrame.

Two things about that round trip. `read_gbq_query()` re-materializes the result and does not preserve the query's `ORDER BY`, so the sort is reapplied on the DataFrame below rather than trusted from the SQL. And because the predictions are not reproducible (example 7), the same SQL run here and in the magics cell above can return different values — that is the model, not BigFrames.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
query = """
WITH penguins AS (
  SELECT
    p.*,
    MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(p))), 10) AS split_bucket
  FROM `bigquery-public-data.ml_datasets.penguins` AS p
  WHERE body_mass_g IS NOT NULL
)
SELECT species, island, sex, predicted_body_mass_g
FROM AI.PREDICT(
  (SELECT * EXCEPT(split_bucket) FROM penguins WHERE split_bucket < 8),
  (SELECT * EXCEPT(split_bucket, body_mass_g) FROM penguins WHERE split_bucket >= 8),
  label_col => 'body_mass_g')
ORDER BY predicted_body_mass_g DESC
LIMIT 5
"""
# read_gbq_query() does not preserve the query's ORDER BY — reapply the sort on the DataFrame
bpd.read_gbq_query(query).sort_values('predicted_body_mass_g', ascending=False)
```
