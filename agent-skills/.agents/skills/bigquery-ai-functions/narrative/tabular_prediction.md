# Zero-Shot Tabular Prediction — BigQuery AI Functions

Predict on a tabular dataset with **no model training**. BigQuery's Tabular Foundation Model (TabFM) learns the task in-context from a training relation you hand it at query time:

1. **Split** the Palmer Penguins dataset into train and test with a deterministic hash
2. **Predict** a numeric target (`body_mass_g`) with `AI.PREDICT`
3. **Predict** a categorical target (`sex`) with the same function and a different `label_col`
4. **Score** both with `AI.EVALUATE`, which returns the same metric names `ML.EVALUATE` does
5. **Find** where the model adds the least value with `AI.KEY_DRIVERS`, measured against a naive baseline
6. **Narrate** a model card with `AI.GENERATE`

**What this demonstrates:**
- Zero-shot prediction: no `CREATE MODEL`, no connection, no endpoint, no training job
- Regression and classification from one function, distinguished only by the label column's type
- `predicted_<label>_probs` — the per-class probabilities that come back with a classification
- Framing "where is my model weak?" as a contribution-analysis question without making it circular
- Run-to-run drift: TabFM is not deterministic, and Step 4 measures how far two runs of identical SQL land apart
- An honest head-to-head against trained BigQuery ML models on the identical rows

**Functions used:** `functions/ai_predict` (`AI.PREDICT`) | `functions/ai_evaluate` (`AI.EVALUATE`) | `functions/ai_key_drivers` (`AI.KEY_DRIVERS`) | `functions/ai_generate` (`AI.GENERATE`)

**Compare with BigQuery ML:** `bq-ml/models/linear_regression` (`linear_regression`) and `bq-ml/models/boosted_tree_regressor` (`boosted_tree_regressor`) train on this exact dataset, label, and row filter.

**Launch stage:** `AI.PREDICT` and the TabFM branch of `AI.EVALUATE` are in Preview (BigQuery release notes, 2026-08-31).

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create shared resources.

> `AI.PREDICT`, `AI.EVALUATE`, and `AI.KEY_DRIVERS` run on end-user credentials and need no connection, model, or endpoint. `AI.GENERATE` routes to Gemini using a BigQuery connection — see the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection for AI.GENERATE
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

### Connection for AI.GENERATE

`AI.GENERATE` (Step 6) needs a BigQuery Cloud resource connection with the Vertex AI User role. This is idempotent — skip if you already created it in another notebook.

```python
import subprocess as _sp, json as _json

# Create connection (idempotent)
_sp.run(['bq', 'mk', '--connection', '--location', LOCATION,
         '--connection_type', 'CLOUD_RESOURCE',
         '--project_id', PROJECT_ID, CONNECTION_ID],
        capture_output=True, text=True)

# Get service account and grant the Vertex AI User role
r = _sp.run(['bq', 'show', '--connection', '--format=json',
             '--project_id', PROJECT_ID, '--location', LOCATION, CONNECTION_ID],
            capture_output=True, text=True, check=True)
sa = _json.loads(r.stdout)['cloudResource']['serviceAccountId']
_sp.run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
         f'--member=serviceAccount:{sa}', '--role=roles/aiplatform.user', '--quiet'],
        capture_output=True, text=True)
print(f'Connection {CONNECTION_ID} ready (SA: {sa})')
```

---
## Step 1 — Split the data

TabFM is *in-context*: the training data is an argument to the query, not a stored artifact. There is no model object to create, so the only preparation this workflow needs is a clean train/test split.

`FARM_FINGERPRINT` gives a deterministic split — rerunning the notebook always partitions the same rows the same way, so every run trains on one fixed set and scores another (333 rows in, 239 train and 94 test). That is the *only* thing pinned down here. TabFM itself is not deterministic: identical SQL over the identical split returns slightly different predictions each time it runs, and Step 4 prints how far apart two runs land. The row filter (`body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')`) is deliberately identical to the one used by `bq-ml/models/linear_regression` (`bq-ml/models/linear_regression/`), which is what makes the head-to-head at the end meaningful.

`AI.PREDICT` accepts `STRING`, `BOOL`, `INT64`, `FLOAT64`, `NUMERIC`, and `BIGNUMERIC` columns only — no `DATE`, `TIMESTAMP`, `JSON`, `GEOGRAPHY`, `ARRAY`, or `STRUCT`. All seven penguin columns qualify as-is, so nothing needs casting or extracting here.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_split` AS
SELECT
  species,
  island,
  culmen_length_mm,
  culmen_depth_mm,
  flipper_length_mm,
  sex,
  body_mass_g,
  IF(ABS(MOD(FARM_FINGERPRINT(FORMAT('%t', t)), 10)) < 7, 'TRAIN', 'TEST') AS split
FROM `bigquery-public-data.ml_datasets.penguins` AS t
WHERE body_mass_g IS NOT NULL
  AND sex IN ('MALE', 'FEMALE')
"""
client.query(query).result()

client.query(f"""
  SELECT
    split,
    COUNT(*) AS n_rows,
    ROUND(AVG(body_mass_g), 1) AS avg_body_mass_g,
    COUNTIF(sex = 'MALE') AS male_rows,
    COUNT(DISTINCT species) AS species_count
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_split`
  GROUP BY split
  ORDER BY split
""").to_dataframe()
```

---
## Step 2 — Predict a numeric target with AI.PREDICT

`AI.PREDICT` takes two relations — a **training** relation (features plus the label) and a **prediction** relation — and one named argument, `label_col`. Every column in the training relation other than the label is treated as a feature.

The label column is allowed to be present in the prediction relation too. TabFM excludes it from the features and passes it straight through to the output, which is what lets us compute residuals below without inventing a join key.

Because `body_mass_g` is `FLOAT64`, this is a regression. The output is every column of the prediction relation plus one new column, `predicted_body_mass_g`. Task selection is type-driven and implicit: there is no `task_type` argument, so a categorical label stored as `INT64` would silently be regressed. Cast that kind of label to `STRING` first.

> **Size ceiling.** The training relation is carried in-context, so it is memory-bound rather than disk-bound. Around 10,000 training rows the call fails with `Resources exceeded during query execution: The query could not be executed in the allotted memory.` Keep the training relation at **5,000 rows or fewer**; sample or aggregate anything larger before handing it to TabFM. This split uses 239 rows, well inside the ceiling. The two documented limits are 20 feature columns and 10 classes; a call takes 30–95 seconds regardless of how small the data is.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_regression` AS
SELECT *
FROM AI.PREDICT(
  (SELECT * EXCEPT(split) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_split` WHERE split = 'TRAIN'),
  (SELECT * EXCEPT(split) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_split` WHERE split = 'TEST'),
  label_col => 'body_mass_g'
)
"""
client.query(query).result()

# Materialized on purpose: each TabFM call costs 30-95 seconds and Steps 5 and 6 reuse these rows
client.query(f"""
  SELECT species, island, sex, body_mass_g, predicted_body_mass_g,
         ROUND(body_mass_g - predicted_body_mass_g, 1) AS residual
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_regression`
  ORDER BY ABS(body_mass_g - predicted_body_mass_g) DESC
  LIMIT 10
""").to_dataframe()
```

---
## Step 3 — Predict a categorical target with AI.PREDICT

Nothing about the call changes except `label_col`. Because `sex` is a `STRING`, TabFM switches to classification and returns two new columns instead of one: `predicted_sex`, and `predicted_sex_probs` of type `ARRAY<STRUCT<label STRING, prob FLOAT64>>` holding a probability for every class.

**Why `sex` and not `species`?** `species` is trivially separable from bill and flipper measurements — TabFM separates the three species essentially perfectly on this split (1.000 across accuracy, precision, recall, and F1), which teaches nothing about reading a classifier. Predicting `sex` from body measurements is genuinely hard and produces a realistic confusion pattern. The multi-class case, including how `predicted_species_probs` distributes across three labels, belongs in the `functions/ai_predict` (`AI.PREDICT` function notebook).

The query below unnests `predicted_sex_probs` to pull out the probability TabFM assigned to the class it actually chose — the model's confidence in its own answer, averaged per actual/predicted pair.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_classification` AS
SELECT *
FROM AI.PREDICT(
  (SELECT * EXCEPT(split) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_split` WHERE split = 'TRAIN'),
  (SELECT * EXCEPT(split) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_split` WHERE split = 'TEST'),
  label_col => 'sex'
)
"""
client.query(query).result()

# Confusion matrix, plus how confident TabFM was in the class it picked
client.query(f"""
  SELECT
    sex AS actual,
    predicted_sex,
    COUNT(*) AS n,
    ROUND(AVG((SELECT p.prob FROM UNNEST(predicted_sex_probs) AS p WHERE p.label = predicted_sex)), 3)
      AS avg_confidence
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_classification`
  GROUP BY actual, predicted_sex
  ORDER BY actual, predicted_sex
""").to_dataframe()
```

---
## Step 4 — Score both predictions with AI.EVALUATE

`AI.EVALUATE` has two mutually exclusive syntaxes. The forecasting form, used in `workflows/time_series_intelligence` (Time Series Intelligence), takes `data_col` and `timestamp_col` and scores a TimesFM forecast against actuals. The TabFM form takes the *same two relations you gave `AI.PREDICT`* plus `label_col`, re-runs the prediction internally, and returns one row of metrics chosen by the label's type:

| Label type | Metrics returned |
|---|---|
| `INT64`, `FLOAT64`, `NUMERIC`, `BIGNUMERIC` | `mean_absolute_error`, `mean_squared_error`, `mean_squared_log_error`, `median_absolute_error`, `r2_score`, `explained_variance` |
| `STRING`, `BOOL` | `precision`, `recall`, `accuracy`, `f1_score` (the first three macro-averaged across classes) |

Two things worth noticing. The regression names are **identical to `ML.EVALUATE`'s**, so the head-to-head at the end of this notebook lines up column for column — the metric *names* match, even though the evaluation samples do not. And the classification branch is thin: **no** `log_loss`, **no** `roc_auc`, **no** confusion matrix, and — unlike the forecasting branch — **no** `ai_evaluate_status` column at all. Four numbers, and threshold tuning is not something you can do with them.

`AI.EVALUATE` re-runs TabFM rather than reading the tables from Steps 2 and 3, so this cell costs two more model calls — and it scores its own fresh predictions, not the rows Steps 2 and 3 materialized. TabFM is not deterministic, so the two runs disagree. Rather than assert by how much, the cell recomputes MAE and accuracy directly from the Step 2 and Step 3 tables and prints them beside `AI.EVALUATE`'s: the `difference` column is the model's run-to-run drift on identical inputs. Materialize predictions you intend to reuse rather than expecting to reproduce them.

```python
reg_metrics = client.query(f"""
  SELECT * FROM AI.EVALUATE(
    (SELECT * EXCEPT(split) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_split` WHERE split = 'TRAIN'),
    (SELECT * EXCEPT(split) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_split` WHERE split = 'TEST'),
    label_col => 'body_mass_g'
  )
""").to_dataframe()

clf_metrics = client.query(f"""
  SELECT * FROM AI.EVALUATE(
    (SELECT * EXCEPT(split) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_split` WHERE split = 'TRAIN'),
    (SELECT * EXCEPT(split) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_split` WHERE split = 'TEST'),
    label_col => 'sex'
  )
""").to_dataframe()

print('Regression (body_mass_g):')
display(reg_metrics)
print('Classification (sex):')
display(clf_metrics)

# AI.EVALUATE ran TabFM again, so it scored a different set of predictions than Steps 2 and 3
# materialized. Recompute the same two headline metrics from those tables and print the drift.
materialized = client.query(f"""
  SELECT
    (SELECT AVG(ABS(body_mass_g - predicted_body_mass_g))
     FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_regression`) AS mae,
    (SELECT COUNTIF(sex = predicted_sex) / COUNT(*)
     FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_classification`) AS accuracy
""").to_dataframe()

drift = pd.DataFrame([
    {'metric': 'mean_absolute_error',
     'ai_evaluate_run': round(float(reg_metrics.iloc[0]['mean_absolute_error']), 4),
     'step_2_3_tables': round(float(materialized.iloc[0]['mae']), 4)},
    {'metric': 'accuracy',
     'ai_evaluate_run': round(float(clf_metrics.iloc[0]['accuracy']), 4),
     'step_2_3_tables': round(float(materialized.iloc[0]['accuracy']), 4)},
])
drift['difference'] = (drift['ai_evaluate_run'] - drift['step_2_3_tables']).round(4)
print('Identical training and test relations, two separate TabFM runs:')
display(drift)
```

---
## Step 5 — Where does the model add the least? AI.KEY_DRIVERS

An aggregate metric hides *where* a model works and where it does not. `AI.KEY_DRIVERS` does contribution analysis: it compares an interest set against a reference set and surfaces the segments that explain the gap between them.

The tempting framing — high-error rows as interest, low-error rows as reference — is circular. It partitions the rows *by* the metric and then asks which segments explain a difference in that same metric, so every segment shows a positive difference, the ranking just re-sorts by segment size, and the two sides have deliberately unequal composition.

Instead, compare **two models over the same rows**. Every test penguin appears twice:

| Copy | `is_tabfm` | `abs_error` |
|---|---|---|
| interest | `TRUE` | `ABS(actual − TabFM prediction)` |
| reference | `FALSE` | `ABS(actual − mean body mass of the training split)` |

The training-mean baseline is the weakest honest predictor there is, so this asks "how much did TabFM buy us, and where?". Interest and reference have equal row counts by construction — the documentation recommends roughly equal numbers of test and control rows — `abs_error` is genuinely summable, and the variable that splits the two sides is *which model produced the error*, not the error itself. That makes the reading unambiguous:

- **large negative `difference`** → TabFM cut a lot of error in that segment
- **least-negative (or positive) `difference`** → TabFM added the least there
- **positive `unexpected_difference`** → the segment improved less than the overall trend predicts

One honest caveat about what this does and does not measure: it ranks segments by *improvement over the baseline*, not by absolute error. A segment can be near the bottom of this ranking because TabFM struggled there, or because the baseline was already close. The absolute `tabfm_error` column stays in the output so you can tell those two cases apart.

`AI.KEY_DRIVERS` needs `INT64`, `BOOL`, or `STRING` dimensions and accepts at most 12 of them, so the continuous `flipper_length_mm` is bucketed into three bands and the verbose species name is trimmed to its first word. Four dimensions are used here.

```python
# rf-string: the SQL below contains a regex literal, so the Python string must be raw
query = rf"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_h2h` AS
WITH baseline AS (
  SELECT AVG(body_mass_g) AS mean_mass
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_split`
  WHERE split = 'TRAIN'
)
SELECT
  REGEXP_EXTRACT(species, r'^(\w+)') AS species,
  island,
  sex,
  CASE
    WHEN flipper_length_mm < 190 THEN 'flipper: short'
    WHEN flipper_length_mm < 210 THEN 'flipper: medium'
    ELSE 'flipper: long'
  END AS flipper_size,
  ABS(body_mass_g - predicted_body_mass_g) AS abs_error,
  TRUE AS is_tabfm
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_regression`

UNION ALL

SELECT
  REGEXP_EXTRACT(t.species, r'^(\w+)') AS species,
  t.island,
  t.sex,
  CASE
    WHEN t.flipper_length_mm < 190 THEN 'flipper: short'
    WHEN t.flipper_length_mm < 210 THEN 'flipper: medium'
    ELSE 'flipper: long'
  END AS flipper_size,
  ABS(t.body_mass_g - b.mean_mass) AS abs_error,
  FALSE AS is_tabfm
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_split` AS t
CROSS JOIN baseline AS b
WHERE t.split = 'TEST'
"""
client.query(query).result()

query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_drivers` AS
SELECT
  ARRAY_TO_STRING(drivers, ', ') AS segment,
  metric_interest AS tabfm_error,
  metric_reference AS baseline_error,
  difference,
  relative_difference,
  unexpected_difference,
  apriori_support,
  contribution
FROM AI.KEY_DRIVERS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_h2h`,
  metric_col => 'abs_error',
  dimension_cols => ['species', 'island', 'sex', 'flipper_size'],
  interest_label_col => 'is_tabfm',
  top_k => 25
)
"""
client.query(query).result()

# The headline: total TabFM error against total baseline error over every test row
overall = client.query(f"""
  SELECT ROUND(tabfm_error) AS tabfm_error,
         ROUND(baseline_error) AS baseline_error,
         ROUND(difference) AS difference,
         ROUND(relative_difference, 3) AS relative_difference,
         ROUND(unexpected_difference) AS unexpected_difference,
         ROUND(apriori_support, 3) AS apriori_support
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_drivers`
  WHERE segment = 'all'
""").to_dataframe()
print('Overall, TabFM vs the training-mean baseline (the `all` row, excluded from every ranking below):')
display(overall)

# Where TabFM bought the most: most negative difference first
client.query(f"""
  SELECT segment,
         ROUND(tabfm_error) AS tabfm_error,
         ROUND(baseline_error) AS baseline_error,
         ROUND(difference) AS difference,
         ROUND(relative_difference, 3) AS relative_difference
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_drivers`
  WHERE segment != 'all'
  ORDER BY difference ASC
  LIMIT 10
""").to_dataframe()
```

### The segments where TabFM helps least

Ranking by `difference` ascending shows the biggest wins. Flip the question to find the weak spots and rank by `unexpected_difference` descending instead — that column measures how far a segment deviated from the overall trend, so the largest positive values are the segments that improved least relative to everything else.

Every ranking query here filters out the `all` segment. It is not a segment — it is the population row printed above as the headline cross-check, and its `apriori_support` of 1.0 says so. Because it covers every test row, its `difference` is the whole-population total and it would head any ascending-`difference` ranking on size alone; and having no complement to deviate from, its `unexpected_difference` carries no segment-level meaning. `workflows/metric_diagnostics` (Metric Diagnostics) excludes the same row for the same reason.

Read `tabfm_error` alongside the ranking: a segment with a small absolute error and a small improvement is one the baseline already handled, not one the model failed at.

```python
client.query(f"""
  SELECT segment,
         ROUND(tabfm_error) AS tabfm_error,
         ROUND(relative_difference, 3) AS relative_difference,
         ROUND(unexpected_difference) AS unexpected_difference,
         ROUND(apriori_support, 3) AS apriori_support
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_drivers`
  WHERE segment != 'all'
  ORDER BY unexpected_difference DESC
  LIMIT 10
""").to_dataframe()
```

---
## Step 6 — Narrate a model card with AI.GENERATE

The numbers are in place: aggregate metrics from Step 4, and the segments TabFM helped least from Step 5. `AI.GENERATE` turns them into a model card — what the model does, how well it does it, and where it should not be trusted — grounded in those numbers instead of guessed.

The metric values are pulled out of the Step 4 dataframes into Python variables first, so the whole query is built with a single f-string rather than two layers of interpolation.

```python
reg_mae = round(float(reg_metrics.iloc[0]['mean_absolute_error']), 1)
reg_r2 = round(float(reg_metrics.iloc[0]['r2_score']), 3)
clf_acc = round(float(clf_metrics.iloc[0]['accuracy']), 3)

query = f"""
WITH weak AS (
  SELECT STRING_AGG(
    CONCAT(
      segment,
      ': TabFM error ', CAST(ROUND(tabfm_error) AS STRING),
      ' vs baseline ', CAST(ROUND(baseline_error) AS STRING),
      ' (relative ', CAST(ROUND(relative_difference, 3) AS STRING),
      ', support ', CAST(ROUND(apriori_support, 3) AS STRING), ')'
    ),
    ' ||| '
    ORDER BY unexpected_difference DESC
    LIMIT 8
  ) AS weak_rows
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_tabpred_drivers`
  WHERE segment != 'all'
)
SELECT (AI.GENERATE(
  CONCAT(
    'You are an ML engineer writing a model card. A zero-shot tabular foundation model (BigQuery TabFM, ',
    'called through AI.PREDICT with no training) predicts penguin body mass in grams from species, island, ',
    'bill length and depth, flipper length, and sex. On a held-out 30 percent test split it scored ',
    'mean absolute error {reg_mae} grams and r-squared {reg_r2}. A companion classifier predicting sex from ',
    'the same features scored accuracy {clf_acc}. A contribution analysis compared the model error against a ',
    'training-mean baseline over the same rows; the segments listed below improved LEAST relative to that ',
    'baseline, so they are the places the model adds the least value. Write a model card with these sections: ',
    '(1) Intended use, (2) Performance summary, (3) Where the model adds least and what might explain it, ',
    '(4) Limitations and when NOT to use zero-shot prediction. Be concrete and cite the numbers. ',
    'Weak segments: ', weak_rows
  )
)).result AS model_card
FROM weak
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['model_card'])
```

---
## Head-to-head: zero-shot TabFM vs trained BigQuery ML models

This notebook never ran a `CREATE MODEL`. `bq-ml/models/linear_regression` (`bq-ml/models/linear_regression/`) and `bq-ml/models/boosted_tree_regressor` (`bq-ml/models/boosted_tree_regressor/`) train on the identical table, label, and row filter, and their `ML.EVALUATE` output uses the same six column names `AI.EVALUATE` returns here.

**This comparison is indicative, not controlled.** The two `bq-ml` figures are those notebooks' stored `ML.EVALUATE` output, which scores an `AUTO_SPLIT` holdout — a different set of rows than this notebook's deterministic `FARM_FINGERPRINT` 70/30 split. Same data, same label, same feature set, different evaluation sample; and the TabFM side moves a little on every rerun besides. Treat the gap as a direction, not a measurement — that is why the table below prints an `evaluated_on` column next to every number.

The TabFM row is read straight out of the Step 4 `AI.EVALUATE` result, so the table always reports what this run actually produced rather than a figure typed in once.

```python
# bq-ml figures: the stored ML.EVALUATE output of those two notebooks (AUTO_SPLIT holdout).
# TabFM figures: this run's AI.EVALUATE result, so this table cannot drift from the cells above.
tabfm_mae = float(reg_metrics.iloc[0]['mean_absolute_error'])
tabfm_r2 = float(reg_metrics.iloc[0]['r2_score'])

rows = [
    ('AI.PREDICT (TabFM, zero-shot)', 'FARM_FINGERPRINT 70/30 (this notebook)',
     tabfm_mae, tabfm_r2, 'nothing - one query'),
    ('LINEAR_REG (bq-ml)', 'AUTO_SPLIT holdout',
     226.413652, 0.875223, 'a model object, training, retraining'),
    ('BOOSTED_TREE_REGRESSOR (bq-ml)', 'AUTO_SPLIT holdout',
     108.817581, 0.967942, 'a model object, training, hyperparameters'),
]
h2h = pd.DataFrame([{
    'approach': a,
    'evaluated_on': e,
    'mae': round(m, 1),
    'r2': round(r, 3),
    'mae_vs_tabfm_pct': round(100 * (m - tabfm_mae) / tabfm_mae, 1),
    'you_manage': y,
} for a, e, m, r, y in rows])
display(h2h)
print('mae_vs_tabfm_pct is negative where the trained model has the lower error.')
print('Different evaluation samples - read it as a direction, not a measurement.')
```

**Read the result honestly.** Zero-shot TabFM lands in the neighborhood of the trained linear model — the printed `mae_vs_tabfm_pct` says how close on this run — having done no training at all, which makes it an excellent first look: triage, exploration, and answering "is there any signal here?". The tuned boosted tree is in a different tier. Zero-shot is a starting point, not a replacement.

There is no penguins classifier in `bq-ml` — `models/logistic_regression/` trains on `census_adult_income`, and every `bq-ml` model built on penguins is a regressor or unsupervised — so the `sex` classification in Step 3 has no counterpart to compare against.

**When to reach for which.** `AI.PREDICT` when there is no model and you want an answer now, when the schema keeps changing, or when the dataset is small enough to pass in-context. `CREATE MODEL` when accuracy matters, when you need feature importance or explainability, or when you will score the same schema repeatedly and want each scoring run to be cheap.
