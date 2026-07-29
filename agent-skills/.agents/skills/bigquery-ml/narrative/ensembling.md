# Ensembling — BigQuery ML

A **stacked ensemble** combining 3 heterogeneous model types — linear, boosting, bagging — each trained with the identical recipe already validated in this project's own model notebooks. Self-contained: retrains its own small copies rather than depending on those notebooks' models still existing.

**Models used:** `LOGISTIC_REG`, `BOOSTED_TREE_CLASSIFIER`, `RANDOM_FOREST_CLASSIFIER`
**Functions used:** `ML.PREDICT`, `ML.EVALUATE`

`LOGISTIC_REG`/`BOOSTED_TREE_CLASSIFIER`/`RANDOM_FOREST_CLASSIFIER`'s own mechanics are already covered in depth in `models/logistic_regression` (`models/logistic_regression/`), `models/boosted_tree_classifier` (`models/boosted_tree_classifier/`), and `models/random_forest_classifier` (`models/random_forest_classifier/`) and not repeated here — **this workflow's real content is the stacking methodology and an honest comparison against simpler alternatives.**

**Scope note:** `DNN_CLASSIFIER`/`WIDE_AND_DEEP_CLASSIFIER` could be added as a 4th/5th base model via the identical pattern below (both already trained on this exact dataset in `models/dnn_classifier/`/`models/wide_and_deep_classifier/`) — omitted here since both take 12-46 minutes to train in this project, which would make every rebuild of this notebook impractically slow.

**Data:** [`bigquery-public-data.ml_datasets.census_adult_income`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — the same feature set/label already used in `models/logistic_regression/`, `models/boosted_tree_classifier/`, `models/random_forest_classifier/`.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create) | `setup` (Setup guide)

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
## Step 0 — A 3-way TRAIN/VALIDATE/TEST split, plus a stable row ID

**Why 3-way, not the usual 2-way split:** if the meta-model trained on base models' predictions for rows those *same* base models were fit on, its apparent lift would partly be an illusion of overfitting, not real generalization — a classic stacking-leakage mistake. Base models train on `TRAIN` only; their predictions on `VALIDATE` (data they've never seen) become the meta-model's training features; `TEST` stays untouched by everything until the final comparison.

`census_adult_income` has no natural row-id column, and — verified live — joining predictions back together on raw feature columns causes fan-out duplicates (different people can share identical feature values across every column). A synthetic `ROW_NUMBER()` `row_id`, generated once here, fixes this for every join below.

```python
query = """
CREATE OR REPLACE TABLE `{project}.{dataset}.ensembling_split` AS
SELECT
  ROW_NUMBER() OVER() AS row_id,
  *,
  CASE
    WHEN MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))), 10) < 6 THEN 'TRAIN'
    WHEN MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))), 10) < 8 THEN 'VALIDATE'
    ELSE 'TEST'
  END AS split
FROM `bigquery-public-data.ml_datasets.census_adult_income` t
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()

query = f"""
SELECT split, COUNT(*) AS n,
  ROUND(SUM(CASE WHEN income_bracket = ' >50K' THEN 1 ELSE 0 END) / COUNT(*), 3) AS positive_rate
FROM `{PROJECT_ID}.{DATASET_ID}.ensembling_split`
GROUP BY split
"""
client.query(query).to_dataframe()
```

---
## Step 1 — Train 3 base models on `TRAIN` only

Identical recipes to `models/logistic_regression/`, `models/boosted_tree_classifier/`, `models/random_forest_classifier/` — just pointed at the `TRAIN` split instead of `AUTO_SPLIT`. Submitted concurrently — BigQuery runs distinctly-named `CREATE MODEL` jobs from one client in true parallel (same pattern as `workflows/cross_validation` (`workflows/cross_validation/`)), so this finishes in roughly the time of the slowest model (typically `RANDOM_FOREST_CLASSIFIER` or `BOOSTED_TREE_CLASSIFIER`, a few minutes), not the sum of all three.

```python
base_model_configs = {
    'ensembling_logistic': "model_type = 'LOGISTIC_REG'",
    'ensembling_boosted': "model_type = 'BOOSTED_TREE_CLASSIFIER'",
    'ensembling_rf': "model_type = 'RANDOM_FOREST_CLASSIFIER', num_parallel_tree = 50, tree_method = 'HIST'",
}

def train_base_model(model_name, options_prefix):
    query = f"""
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.{model_name}`
    OPTIONS(
      {options_prefix},
      input_label_cols = ['income_bracket'],
      auto_class_weights = TRUE,
      data_split_method = 'NO_SPLIT'
    ) AS
    SELECT age, workclass, education, education_num, marital_status, occupation,
           relationship, race, sex, hours_per_week, native_country, income_bracket
    FROM `{PROJECT_ID}.{DATASET_ID}.ensembling_split`
    WHERE split = 'TRAIN'
    """
    return client.query(query)  # submitted asynchronously — caller awaits .result()

jobs = {name: train_base_model(name, opts) for name, opts in base_model_configs.items()}
for name, job in jobs.items():
    job.result()
print(f'Trained {len(jobs)} base models')
```

---
## Step 2 — Meta-features: predict each base model on `VALIDATE`, join on `row_id`

Each base model's predicted probability of `income_bracket = ' >50K'` becomes one meta-feature column.

```python
def meta_features_query(split_name, dest_table):
    return f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.{dest_table}` AS
    WITH
    logistic_pred AS (
      SELECT row_id, income_bracket,
             (SELECT prob FROM UNNEST(predicted_income_bracket_probs) WHERE label = ' >50K') AS pred_logistic
      FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.ensembling_logistic`,
        (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ensembling_split` WHERE split = '{split_name}'))
    ),
    boosted_pred AS (
      SELECT row_id,
             (SELECT prob FROM UNNEST(predicted_income_bracket_probs) WHERE label = ' >50K') AS pred_boosted
      FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.ensembling_boosted`,
        (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ensembling_split` WHERE split = '{split_name}'))
    ),
    rf_pred AS (
      SELECT row_id,
             (SELECT prob FROM UNNEST(predicted_income_bracket_probs) WHERE label = ' >50K') AS pred_rf
      FROM ML.PREDICT(MODEL `{PROJECT_ID}.{DATASET_ID}.ensembling_rf`,
        (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ensembling_split` WHERE split = '{split_name}'))
    )
    SELECT l.row_id, l.income_bracket, l.pred_logistic, b.pred_boosted, r.pred_rf
    FROM logistic_pred l
    JOIN boosted_pred b USING (row_id)
    JOIN rf_pred r USING (row_id)
    """

client.query(meta_features_query('VALIDATE', 'ensembling_meta_features')).result()

query = f"SELECT COUNT(*) AS n FROM `{PROJECT_ID}.{DATASET_ID}.ensembling_meta_features`"
client.query(query).to_dataframe()
```

---
## Step 3 — Train the stacked meta-model on `VALIDATE`'s meta-features

A `LOGISTIC_REG` trained on the 3 base models' predicted probabilities as its only features.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.ensembling_stacker`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE,
  data_split_method = 'NO_SPLIT'
) AS
SELECT pred_logistic, pred_boosted, pred_rf, income_bracket
FROM `{PROJECT_ID}.{DATASET_ID}.ensembling_meta_features`
"""
client.query(query).result()
print('Model ensembling_stacker created')
```

---
## Step 4 — Final honest comparison on `TEST`: base models vs. simple average vs. stacker

Build `TEST`-split meta-features the same way, then compare five candidates: each of the 3 base models directly (`ML.EVALUATE`), a **simple average ensemble** (no training — just the mean predicted probability across the 3 base models, thresholded at 0.5), and the **stacked meta-model** (`ML.EVALUATE`).

> **Reminder from `models/random_forest_classifier/`: `RANDOM_FOREST_CLASSIFIER` retraining is genuinely non-deterministic.** Since `ensembling_rf`'s predictions feed both the simple-average ensemble and the stacker's training features, every number below that touches `pred_rf` — the `random_forest` row itself, the simple average, and the stacker — will shift slightly run to run. `logistic`/`boosted_tree` and the stacker's own `LOGISTIC_REG` fit are otherwise deterministic, but their downstream comparison numbers inherit RF's variance through the ensemble. Treat the specific values below as illustrative of one run, not fixed constants.

```python
client.query(meta_features_query('TEST', 'ensembling_meta_features_test')).result()

query = f"SELECT COUNT(*) AS n FROM `{PROJECT_ID}.{DATASET_ID}.ensembling_meta_features_test`"
client.query(query).to_dataframe()
```

```python
query = f"""
SELECT 'logistic' AS model, * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.ensembling_logistic`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ensembling_split` WHERE split = 'TEST'))
UNION ALL
SELECT 'boosted_tree' AS model, * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.ensembling_boosted`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ensembling_split` WHERE split = 'TEST'))
UNION ALL
SELECT 'random_forest' AS model, * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.ensembling_rf`,
  (SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.ensembling_split` WHERE split = 'TEST'))
"""
base_results = client.query(query).to_dataframe()
base_results
```

```python
query = f"""
WITH scored AS (
  SELECT income_bracket, (pred_logistic + pred_boosted + pred_rf) / 3 AS pred_avg
  FROM `{PROJECT_ID}.{DATASET_ID}.ensembling_meta_features_test`
),
labeled AS (
  SELECT income_bracket = ' >50K' AS actual_positive, pred_avg >= 0.5 AS predicted_positive
  FROM scored
),
counts AS (
  SELECT
    COUNTIF(actual_positive AND predicted_positive) AS tp,
    COUNTIF(NOT actual_positive AND predicted_positive) AS fp,
    COUNTIF(actual_positive AND NOT predicted_positive) AS fn,
    COUNTIF(NOT actual_positive AND NOT predicted_positive) AS tn
  FROM labeled
)
SELECT
  'simple_average' AS model,
  tp / (tp + fp) AS precision,
  tp / (tp + fn) AS recall,
  (tp + tn) / (tp + fp + fn + tn) AS accuracy,
  2 * (tp / (tp + fp)) * (tp / (tp + fn)) / ((tp / (tp + fp)) + (tp / (tp + fn))) AS f1_score
FROM counts
"""
simple_ensemble_result = client.query(query).to_dataframe()
simple_ensemble_result
```

```python
query = f"""
SELECT 'stacked_meta_model' AS model, * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.ensembling_stacker`,
  (SELECT pred_logistic, pred_boosted, pred_rf, income_bracket
   FROM `{PROJECT_ID}.{DATASET_ID}.ensembling_meta_features_test`))
"""
stacker_result = client.query(query).to_dataframe()
stacker_result
```

**Honest finding, in two parts because the two ensembling techniques don't agree on which metric they win:**
- **Among the 4 candidates `ML.EVALUATE` can score (the 3 base models + the stacker — `roc_auc` isn't computed for the hand-thresholded simple-average ensemble), the stacked meta-model wins on `roc_auc`** (≈0.896 vs. the best individual base model, `boosted_tree`, at ≈0.893) — a genuine, if modest, ranking-quality improvement from combining all three models' signal.
- **On F1 (a fixed-threshold metric, computed for all 5 candidates), the simple average ensemble edges out the stacker** (≈0.666 vs. ≈0.665) — the free, no-training approach is *slightly* better here, not worse.

Neither result is dramatic, and that's the honest takeaway: ensembling helped a little, in a metric-dependent way — unlike the legacy notebook this workflow modernizes (whose stacked ensemble did *not* clearly beat its best individual model at all), and unlike several other workflows in this project (`workflows/recommendation` (`recommendation`), `workflows/embeddings_classification` (`embeddings_classification`)) where a simpler baseline won outright and unambiguously. Worth reporting exactly as measured rather than forcing either narrative — "ensembling helps, sometimes, a little, depending what you're optimizing for" is a more honest lesson than either "ensembling always wins" or "ensembling is pointless." (Exact figures above are from one run — see the `RANDOM_FOREST_CLASSIFIER` non-determinism note before Step 4's first cell.)

---
## Related content

- `models/logistic_regression` (`models/logistic_regression/`), `models/boosted_tree_classifier` (`models/boosted_tree_classifier/`), `models/random_forest_classifier` (`models/random_forest_classifier/`) — each base model type's mechanics in depth.
- `workflows/cross_validation` (`workflows/cross_validation/`) — a complementary model-validation technique; both address different aspects of trusting a single number from `ML.EVALUATE`.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT split, COUNT(*) AS n
FROM `statmike-mlops-349915.bq_ml.ensembling_split`
GROUP BY split
```

---
## Examples — BigFrames

No direct BigFrames equivalent for stacking multiple heterogeneous model types into a meta-model — this is hand-rolled SQL/`ML.PREDICT` composition here. `bigframes.ml.linear_model.LogisticRegression`/`ensemble.XGBClassifier`/`ensemble.RandomForestClassifier` are already demonstrated individually in their respective `models/` notebooks.
