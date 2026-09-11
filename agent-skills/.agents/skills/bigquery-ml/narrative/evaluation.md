# Evaluation Without a Model — `ML.METRICS`

`ML.METRICS` computes evaluation metrics from a relation that already holds an **actual** column and a **predicted** column. There is no model argument. Nothing is trained, nothing is loaded, and the predictions can come from anywhere — BigQuery ML, Vertex AI batch prediction, a vendor scoring API, a CSV someone emailed you. **Preview** as of 2026-09-10.

> **The one-line difference from `ML.EVALUATE`.** `ML.EVALUATE` needs the model object. `ML.METRICS` needs only the numbers. Step 2 deletes the model and shows exactly what that buys you.

| You have | Use | Lives in |
|---|---|---|
| A trained model and an eval set | `ML.EVALUATE` | with each model — see `models` (Models) |
| Two columns: actual and predicted | `ML.METRICS` | this notebook |
| Raw data, and no model at all yet | `AI.EVALUATE` (trains TabFM/TimesFM internally) | `bq-ai-functions/functions/ai_evaluate` (`ai_evaluate`) |

**What this notebook measures, not just describes:**
- **Step 2** — the six regression metrics from `ML.METRICS` against `ML.EVALUATE` on the same predictions: they agree to at least 13 significant digits.
- **Step 4** — the **BOOL/STRING trap**. One table, one set of predictions: precision reads **0.5238** as `BOOL` and **0.7497** as `STRING`. Neither is wrong; they answer different questions.
- **Step 5** — whether `AI.EVALUATE` follows the same convention. It does, and that is measured here rather than taken from a doc line.
- **Step 6** — internal error **`80038528`**, which relation shapes trigger it, and the six mechanisms ruled out by direct test.

**Data:** [`bigquery-public-data.ml_datasets.penguins`](https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=ml_datasets&t=penguins), split deterministically with `FARM_FINGERPRINT`, so the TRAIN/TEST membership is identical on every run and in every project — the same dataset used by `models/linear_regression` (Linear Regression).

**References:** `RESOURCES.md` (Full reference) | [`ML.METRICS`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-metrics) | [`ML.EVALUATE`](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-evaluate) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No connection needed — `ML.METRICS` runs entirely inside BigQuery.

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

### Materialize the data

Every metric in this notebook is a specific number, so the split has to be reproducible. `FARM_FINGERPRINT` over the row's own values gives the same `TRAIN`/`TEST` membership on every run, in every project — unlike `RAND()`, and unlike a row number, which depends on scan order.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.evaluation_penguins` AS
SELECT
  species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g,
  IF(MOD(ABS(FARM_FINGERPRINT(FORMAT('%s|%s|%t|%t|%t|%s|%t',
       species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g))), 5) = 0,
     'TEST', 'TRAIN') AS splits
FROM `bigquery-public-data.ml_datasets.penguins`
WHERE body_mass_g IS NOT NULL AND sex IN ('MALE', 'FEMALE')
"""
client.query(query).result()

client.query(f"""
SELECT splits, COUNT(*) AS n
FROM `{PROJECT_ID}.{DATASET_ID}.evaluation_penguins`
GROUP BY splits ORDER BY splits
""").to_dataframe()
```

---
## Step 1 — The ordinary path: train, predict, `ML.EVALUATE`

Nothing new yet. A `LINEAR_REG` model on the `TRAIN` split, predictions on the `TEST` split saved to a table, and `ML.EVALUATE` for the metrics.

The one thing worth noticing: **the predictions are saved**. That table is the only artifact `ML.METRICS` will need.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.evaluation_scratch_reg`
OPTIONS(
  model_type = 'LINEAR_REG',
  input_label_cols = ['body_mass_g'],
  data_split_method = 'NO_SPLIT',
  category_encoding_method = 'DUMMY_ENCODING'
) AS
SELECT species, island, culmen_length_mm, culmen_depth_mm, flipper_length_mm, sex, body_mass_g
FROM `{PROJECT_ID}.{DATASET_ID}.evaluation_penguins`
WHERE splits = 'TRAIN'
"""
client.query(query).result()
print('Model trained')
```

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.evaluation_predictions` AS
SELECT
  body_mass_g AS actual_mass,
  predicted_body_mass_g AS predicted_mass
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.evaluation_scratch_reg`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.evaluation_penguins` WHERE splits = 'TEST'))
"""
client.query(query).result()

evaluate_df = client.query(f"""
SELECT * FROM ML.EVALUATE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.evaluation_scratch_reg`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.evaluation_penguins` WHERE splits = 'TEST'))
""").to_dataframe()
evaluate_df
```

---
## Step 2 — Delete the model. `ML.EVALUATE` dies; `ML.METRICS` does not.

This is the whole argument for the function, so it is worth doing literally rather than describing. The model is dropped, and then both functions are called on the same `TEST` predictions.

```python
client.query(f"DROP MODEL `{PROJECT_ID}.{DATASET_ID}.evaluation_scratch_reg`").result()
print('Model dropped\n')

# ML.EVALUATE now has nothing to evaluate.
try:
    client.query(f"""
    SELECT * FROM ML.EVALUATE(
      MODEL `{PROJECT_ID}.{DATASET_ID}.evaluation_scratch_reg`,
      (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.evaluation_penguins` WHERE splits = 'TEST'))
    """).result()
    print('ML.EVALUATE: unexpectedly succeeded')
except Exception as e:
    print(f'ML.EVALUATE failed: {str(e).splitlines()[0]}')
```

```python
metrics_df = client.query(f"""
SELECT * FROM ML.METRICS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.evaluation_predictions`,
  predicted_col => 'predicted_mass',
  actual_col    => 'actual_mass',
  task_type     => 'regression')
""").to_dataframe()

comparison = pd.concat([
    evaluate_df.T.rename(columns={0: 'ML.EVALUATE (model)'}),
    metrics_df.T.rename(columns={0: 'ML.METRICS (table)'}),
], axis=1)
comparison['bit_identical'] = comparison['ML.EVALUATE (model)'].eq(comparison['ML.METRICS (table)'])
comparison['relative_diff'] = (
    (comparison['ML.METRICS (table)'] - comparison['ML.EVALUATE (model)']).abs()
    / comparison['ML.EVALUATE (model)'].abs()
)

with pd.option_context('display.float_format', lambda v: f'{v:.17g}'):
    display(comparison)
```

**Every metric agrees to at least 13 significant digits**, and the `relative_diff` column is the honest way to see it: the gaps are around 1e-16, which is floating-point summation order over a different physical plan, not a difference in definition.

Read `bit_identical` as a curiosity, not a result. **Which of the six land exactly equal varies between runs** — the two functions sum the same numbers in different orders, and `CREATE MODEL` is not bit-deterministic either, so the predictions themselves shift in their last digit. A relative gap of 1e-16 between `ML.EVALUATE` and `ML.METRICS` is not a discrepancy to investigate; a gap of 1e-3 would be.

What the comparison actually establishes: the model contributed **nothing** to the metric that the saved predictions did not already contain. Once predictions are written down, the model is a training artifact, not an evaluation dependency.

---
## Step 3 — Where this earns its place

Nothing in the `ML.METRICS` call mentions a model, a connection, or a training run. Two same-typed columns are the entire contract, which is why it reaches cases `ML.EVALUATE` structurally cannot:

- **Predictions BigQuery never made** — Vertex AI batch prediction output, a vendor scoring API's results, a partner's monthly file.
- **Models that no longer exist** — retention policies delete models; the prediction logs outlive them.
- **Models you cannot call** — a deprecated endpoint, an expired contract, a model behind someone else's IAM.
- **Comparing across all of the above** — a BQML model, a scikit-learn model, and a vendor's API scored by one function with one definition of `r2_score`. That last part matters more than it sounds: "our MAE" and "their MAE" are only comparable when the same code computed both.

A worked comparison — the model against a constant-prediction baseline, both scored by `ML.METRICS`:

```python
client.query(f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.evaluation_baseline` AS
SELECT body_mass_g AS actual_mass, 4207.0 AS predicted_mass
FROM `{PROJECT_ID}.{DATASET_ID}.evaluation_penguins` WHERE splits = 'TEST'
""").result()

baseline_df = client.query(f"""
SELECT * FROM ML.METRICS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.evaluation_baseline`,
  predicted_col => 'predicted_mass', actual_col => 'actual_mass',
  task_type => 'regression')
""").to_dataframe()

pd.concat([
    metrics_df.T.rename(columns={0: 'LINEAR_REG'}),
    baseline_df.T.rename(columns={0: 'constant 4207 g'}),
], axis=1)
```

The baseline's `r2_score` of about **-0.006** is the sanity check working: a constant that is not quite the test set's mean scores slightly *worse* than the mean would, so R² lands just below zero. The model's **0.858** against that, and an MAE roughly **2.9×** lower, is a comparison neither `ML.EVALUATE` nor a stored evaluation could produce — the baseline has no model to evaluate.

---
## Step 4 — Classification, and a trap in the column type

The classification branch returns `precision`, `recall`, `accuracy`, and `f1_score`. What the documentation states plainly, and what is easy to read past, is that **the type of the actual/predicted columns changes what three of those four mean**.

A deliberately imbalanced problem makes it visible: *is this penguin a Chinstrap?* — 12 of the 62 `TEST` rows are.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.evaluation_scratch_clf`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['is_chinstrap'],
  data_split_method = 'NO_SPLIT',
  category_encoding_method = 'DUMMY_ENCODING'
) AS
SELECT island, culmen_depth_mm, body_mass_g,
       species = 'Chinstrap penguin (Pygoscelis antarctica)' AS is_chinstrap
FROM `{PROJECT_ID}.{DATASET_ID}.evaluation_penguins`
WHERE splits = 'TRAIN'
"""
client.query(query).result()

# One set of predictions, stored twice: as BOOL, and as the STRING rendering
# of the very same values.
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.evaluation_classifications` AS
SELECT
  is_chinstrap                            AS actual_bool,
  predicted_is_chinstrap                  AS predicted_bool,
  CAST(is_chinstrap AS STRING)            AS actual_string,
  CAST(predicted_is_chinstrap AS STRING)  AS predicted_string
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.evaluation_scratch_clf`,
  (SELECT island, culmen_depth_mm, body_mass_g,
          species = 'Chinstrap penguin (Pygoscelis antarctica)' AS is_chinstrap
   FROM `{PROJECT_ID}.{DATASET_ID}.evaluation_penguins` WHERE splits = 'TEST'))
"""
client.query(query).result()
print('Predictions saved in both encodings')
```

```python
client.query(f"""
SELECT 'BOOL' AS label_type, * FROM ML.METRICS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.evaluation_classifications`,
  predicted_col => 'predicted_bool', actual_col => 'actual_bool',
  task_type => 'classification')
UNION ALL
SELECT 'STRING', * FROM ML.METRICS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.evaluation_classifications`,
  predicted_col => 'predicted_string', actual_col => 'actual_string',
  task_type => 'classification')
ORDER BY label_type
""").to_dataframe()
```

> **GOTCHA — a `CAST` changes your precision by 43%.** Same table, same rows, same predictions. `precision` reads **0.5238** as `BOOL` and **0.7497** as `STRING`. `accuracy` is identical either way, because accuracy has no per-class definition to average.
>
> `BOOL` is scored as **binary** — the positive (`TRUE`) class alone. `STRING` is scored as **multiclass and macro-averaged**, even when there are exactly two classes.

The confusion matrix makes both numbers checkable by hand:

```python
confusion = client.query(f"""
SELECT actual_bool, predicted_bool, COUNT(*) AS n
FROM `{PROJECT_ID}.{DATASET_ID}.evaluation_classifications`
GROUP BY 1, 2 ORDER BY 1, 2
""").to_dataframe()
display(confusion.pivot(index='actual_bool', columns='predicted_bool', values='n'))

tp, fp, fn, tn = 11, 10, 1, 40
p_true,  r_true  = tp / (tp + fp), tp / (tp + fn)
p_false, r_false = tn / (tn + fn), tn / (tn + fp)
f1 = lambda p, r: 2 * p * r / (p + r)

print(f'BOOL   (TRUE class only)  precision={p_true:.10f}  recall={r_true:.10f}  f1={f1(p_true, r_true):.10f}')
print(f'STRING (macro over both)  precision={(p_true + p_false) / 2:.10f}  '
      f'recall={(r_true + r_false) / 2:.10f}  '
      f'f1={(f1(p_true, r_true) + f1(p_false, r_false)) / 2:.10f}')
```

Both rows reproduce exactly. Two details worth carrying away:

1. **Macro F1 is the mean of the per-class F1s**, not the F1 of the macro precision and recall. Those differ (0.7729 versus 0.7996 here), and the second one is a common hand-rolled mistake.
2. **On balanced data the two encodings agree.** That is how this hides: it costs nothing until the day the classes are lopsided, which is the day the metric mattered.

**Choose deliberately.** `BOOL` when one class is the event and the other is background — fraud, churn, defect, disease. `STRING` when the classes are peers and a rare class should count as much as a common one. Do not let a `CAST` upstream make that choice for you.

---
## Step 5 — Does `AI.EVALUATE` follow the same convention?

Worth knowing, because `bq-ai-functions/functions/ai_evaluate` (`AI.EVALUATE`)'s TabFM branch returns the **same four metric names**. If its BOOL/STRING behavior differed, the same word would mean different things in two adjacent BigQuery functions.

`AI.EVALUATE` takes data rather than predictions and trains internally, so its numbers are its own — but the convention is the question, and that is testable directly.

> **Do not put both label encodings in the relations you pass.** Each is a perfect predictor of the other, so leaving the unused one in leaks the label and scores 1.0 across the board. Each call below selects exactly one.

```python
IS_CHINSTRAP = "species = 'Chinstrap penguin (Pygoscelis antarctica)'"

def ai_evaluate(label_col, label_expr):
    def relation(split):
        return (f"(SELECT island, culmen_depth_mm, body_mass_g, {label_expr} AS {label_col} "
                f"FROM `{PROJECT_ID}.{DATASET_ID}.evaluation_penguins` WHERE splits = '{split}')")
    return client.query(f"""
    SELECT '{label_col}' AS label_col, precision, recall, f1_score, accuracy
    FROM AI.EVALUATE({relation('TRAIN')}, {relation('TEST')}, label_col => '{label_col}')
    """).to_dataframe()

pd.concat([
    ai_evaluate('label_bool', IS_CHINSTRAP),
    ai_evaluate('label_string', f'CAST({IS_CHINSTRAP} AS STRING)'),
], ignore_index=True)
```

**Same convention, measured.** The `BOOL` label returns precision **0.5217** and recall **1.0**; the `STRING` label returns **0.7609** and **0.89**. TabFM's own confusion matrix here is TP 12, FP 11, FN 0, TN 39 — so `BOOL` is reporting 12/23 and 12/12, the positive class alone, and `STRING` is reporting the two-class mean of (0.5217, 1.0000) and (1.0000, 0.7800). Identical rule to `ML.METRICS`.

So this is a **BigQuery-wide evaluation convention, not an `ML.METRICS` quirk** — which is the useful form of the lesson, because it transfers.

*(Four isolated runs of each call, with the query cache off, returned identical values. `AI.EVALUATE` carries a documented reproducibility caveat — see `bq-ai-functions/functions/ai_evaluate` (`ai_evaluate`) — so treat a single run's absolute numbers with more care than the BOOL-versus-STRING relationship they demonstrate.)*

---
## Step 6 — `TABLE` vs `(QUERY)`, and internal error `80038528`

`ML.METRICS` accepts either `TABLE t` or an inline `(QUERY_STATEMENT)`. The inline form is the natural one to reach for, and it is the one that breaks.

Here is a perfectly ordinary thing to want — score a constant baseline without materializing it first:

```python
query = f"""
SELECT * FROM ML.METRICS(
  (SELECT body_mass_g AS actual_mass, 4207.0 AS predicted_mass
   FROM `{PROJECT_ID}.{DATASET_ID}.evaluation_penguins` WHERE splits = 'TEST'),
  predicted_col => 'predicted_mass', actual_col => 'actual_mass',
  task_type => 'regression')
"""

# retry=None / job_retry=None matter here — see the note below the output.
try:
    client.query(query, retry=None).result(retry=None, job_retry=None)
    print('Succeeded')
except Exception as e:
    print('\n'.join(str(e).splitlines()[:1] + str(e).splitlines()[-1:]))
```

> **GOTCHA — the message says "transient". It is not.** The error text recommends retrying with back-off per the BigQuery SLA. This statement fails identically on every run.
>
> **And the client library believes it.** `internalError` is on `google-cloud-bigquery`'s default retryable list, so a plain `client.query(...).result()` here silently resubmits the job until its 600-second deadline expires — **12 job attempts over 604 seconds, measured**, before the exception finally surfaces. A call that should fail in two seconds hangs the notebook for ten minutes. That is why the cell above passes `retry=None` and `job_retry=None`. If a `ML.METRICS` cell ever seems to hang, this is the first thing to check.

The workaround is the `TABLE` form — which is exactly what Step 3 already did with `evaluation_baseline`, and it returned metrics without complaint.

**What was actually measured.** The `TABLE` form succeeded on every relation tried here (7 of 7), *including every relation whose `(QUERY_STATEMENT)` form failed*. No clean rule for when the query form breaks emerged, and six plausible explanations were ruled out by direct test:

| Ruled out | Evidence |
|---|---|
| Cross-project references | `bigquery-public-data.usa_names` works in query form; a copy of `penguins` inside the caller's own project still fails |
| `JOIN`s | A join across two of the caller's own tables works |
| `NULL`s in either column | Filtering both columns to `IS NOT NULL` does not help |
| `REQUIRED` (NOT NULL) schema modes | The failing copy has none |
| Row count | 62 rows works, 150 rows fails, 32,561 rows works |
| `WHERE` / `LIMIT` / computed expressions | Present in both working and failing cases |

Observed **failing** in query form: `ml_datasets.penguins`, `ml_datasets.iris`, a copy of `penguins` in the caller's own project, and `evaluation_penguins`. Observed **working**: `ml_datasets.census_adult_income`, `usa_names.usa_1910_2013`, `evaluation_predictions`, and `penguins` wrapped in a `GROUP BY`.

No mechanism is claimed here — the tests narrow it, they do not explain it. The practical advice is the point: **if the query form errors, do not spend time reshaping the subquery. Materialize it and pass `TABLE`.** This is a Preview function; behavior may change.

---
## Step 7 — Reproducibility

`ML.METRICS` reads a table and does arithmetic. There is no sampling, no model, and no inference call, so there should be nothing to vary between runs. Confirmed rather than assumed — three isolated executions with the query cache **off**:

```python
runs = pd.concat([
    client.query(
        f"""
        SELECT precision, recall, accuracy, f1_score FROM ML.METRICS(
          TABLE `{PROJECT_ID}.{DATASET_ID}.evaluation_classifications`,
          predicted_col => 'predicted_bool', actual_col => 'actual_bool',
          task_type => 'classification')
        """,
        job_config=bigquery.QueryJobConfig(use_query_cache=False),
    ).to_dataframe()
    for _ in range(3)
], ignore_index=True)

print(f'distinct result rows across 3 cache-off runs: {len(runs.drop_duplicates())}')
runs
```

One distinct row across three runs — bit-identical. That is worth stating next to `AI.EVALUATE`, which is **not** reproducible run to run even with its `model` pinned (measured in `bq-ai-functions/functions/ai_evaluate` (`ai_evaluate`)). When a metric has to be defensible — a model card, a release gate, a regulator's file — computing it from saved predictions with `ML.METRICS` gives you a number you can regenerate on demand.

---
## Examples — `%%bigquery` Magics

The same operation using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT
  ROUND(mean_absolute_error, 4) AS mae,
  ROUND(r2_score, 4) AS r2
FROM ML.METRICS(
  TABLE `statmike-mlops-349915.bq_ml.evaluation_predictions`,
  predicted_col => 'predicted_mass',
  actual_col => 'actual_mass',
  task_type => 'regression'
)
```

---
## Examples — BigFrames

There is **no** `bigframes.ml` wrapper for `ML.METRICS`. BigFrames offers `bigframes.ml.metrics` (`r2_score`, `accuracy_score`, and friends) which computes metrics client-side over a BigFrames Series — a different thing, and useful when the predictions are already in a DataFrame. To reach the BigQuery function itself, run the SQL through `read_gbq`, which keeps the work in BigQuery.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

bdf = bpd.read_gbq(f"""
SELECT * FROM ML.METRICS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.evaluation_predictions`,
  predicted_col => 'predicted_mass',
  actual_col => 'actual_mass',
  task_type => 'regression')
""")
bdf
```
