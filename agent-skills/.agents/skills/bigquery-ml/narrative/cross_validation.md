# Cross-Validation — BigQuery ML

BigQuery ML has **no native k-fold cross-validation** — `CREATE MODEL`'s `data_split_method` only supports single-split holdout (`AUTO_SPLIT`, `RANDOM`, `CUSTOM`, `SEQ`, `NO_SPLIT`). Hand-roll k-fold with deterministic hash-based fold assignment, train k models, and measure real fold-to-fold metric variance — then check whether a single holdout estimate is actually representative.

**Models used:** `LOGISTIC_REG`
**Functions used:** `ML.EVALUATE`

**Why this matters, concretely:** `workflows/anomaly_fraud_detection` (`workflows/anomaly_fraud_detection/`)'s supervised `BOOSTED_TREE_CLASSIFIER` had a held-out eval split with only **~15 real fraud cases** (`ML.CONFUSION_MATRIX` showed TP=13, FN=2). A metric computed from just 15 positive examples is exactly the kind of high-variance situation cross-validation exists to quantify — one unlucky (or lucky) split can make a model look meaningfully better or worse than it really is.

**Data:** [`bigquery-public-data.ml_datasets.ulb_fraud_detection`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — the same dataset as `anomaly_fraud_detection`, for direct continuity.

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
## Step 1 — Deterministic fold assignment

`ulb_fraud_detection` has no natural row-id column — hash the full row via `TO_JSON_STRING` for a stable, deterministic fold assignment. `K = 5` (fewer than the classic 10, deliberately — keeps 5 `CREATE MODEL` calls fast to train/rerun while still clearly demonstrating fold-to-fold variance).

```python
K = 5

query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.cross_validation_folds` AS
SELECT
  *,
  MOD(ABS(FARM_FINGERPRINT(TO_JSON_STRING(t))), {K}) AS fold
FROM `bigquery-public-data.ml_datasets.ulb_fraud_detection` t
"""
client.query(query).result()

query = f"""
SELECT fold, COUNT(*) AS n_rows, SUM(Class) AS n_fraud
FROM `{PROJECT_ID}.{DATASET_ID}.cross_validation_folds`
GROUP BY fold
ORDER BY fold
"""
client.query(query).to_dataframe()
```

Fold sizes are close to even (~56.7K-57.2K rows each), but the fraud *count* per fold ranges from 81 to 111 out of 492 total — a nearly 40% relative spread. This alone previews why a single split's fraud-detection metrics can be noisy: which fold a rare event happens to land in matters.

---
## Step 2 — Train 5 per-fold `LOGISTIC_REG` models, submitted concurrently

Each fold model trains on every row **except** its own fold (`data_split_method='NO_SPLIT'`, since fold assignment is manual, not BQML's own split). `auto_class_weights=TRUE` for the same severe imbalance already established in `anomaly_fraud_detection`.

Submit all 5 `CREATE MODEL` jobs without waiting, then wait for all — BigQuery runs distinctly-named `CREATE MODEL` jobs from one client in true parallel (same pattern verified in `workflows/regression_based_forecasting` (`workflows/regression_based_forecasting/`)), so this finishes in roughly the time of one model, not five.

```python
def train_fold_model(fold_id):
    query = f"""
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.cross_validation_fold_{fold_id}`
    OPTIONS(
      model_type = 'LOGISTIC_REG',
      input_label_cols = ['Class'],
      auto_class_weights = TRUE,
      data_split_method = 'NO_SPLIT'
    ) AS
    SELECT * EXCEPT(fold)
    FROM `{PROJECT_ID}.{DATASET_ID}.cross_validation_folds`
    WHERE fold != {fold_id}
    """
    return client.query(query)  # submitted asynchronously — caller awaits .result()

jobs = {fold_id: train_fold_model(fold_id) for fold_id in range(K)}
for fold_id, job in jobs.items():
    job.result()
print(f'Trained {K} fold models')
```

---
## Step 3 — `ML.EVALUATE` each fold model against its own held-out fold

`UNION ALL` across all 5 folds into one comparison table — the point is to see the real spread, not just one number.

```python
def evaluate_fold(fold_id):
    return f"""
    SELECT {fold_id} AS fold, *
    FROM ML.EVALUATE(
      MODEL `{PROJECT_ID}.{DATASET_ID}.cross_validation_fold_{fold_id}`,
      (SELECT * EXCEPT(fold) FROM `{PROJECT_ID}.{DATASET_ID}.cross_validation_folds` WHERE fold = {fold_id})
    )
    """

query = " UNION ALL ".join(evaluate_fold(fold_id) for fold_id in range(K)) + " ORDER BY fold"
fold_metrics = client.query(query).to_dataframe()
fold_metrics
```

**Verified: meaningful fold-to-fold variance on every metric** — precision ranges 0.068-0.099, recall 0.847-0.932, `roc_auc` 0.968-0.985 — from the exact same modeling recipe applied to 5 different 80%-of-data training sets. Any one of these folds, taken alone, would tell a somewhat different story about "how good is this model."

---
## Step 4 — Aggregate (mean ± stddev) vs. a same-model-type single holdout

Compute the mean and standard deviation of each metric across the 5 folds, then train **one** ordinary single 80/20 holdout model — same model type, same options — for a fair, controlled comparison.

> **GOTCHA:** don't compare this to `anomaly_fraud_detection`'s single-holdout numbers directly — that workflow used `BOOSTED_TREE_CLASSIFIER`, a different model type. Comparing across model types would confound model choice with sampling variance. The controlled comparison here uses the identical `LOGISTIC_REG` recipe for both the folds and the single holdout.

```python
summary = fold_metrics[['precision', 'recall', 'accuracy', 'f1_score', 'roc_auc']].agg(['mean', 'std'])
summary
```

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.cross_validation_single_holdout`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['Class'],
  auto_class_weights = TRUE,
  data_split_method = 'RANDOM',
  data_split_eval_fraction = 0.2
) AS
SELECT * EXCEPT(fold) FROM `{PROJECT_ID}.{DATASET_ID}.cross_validation_folds`
"""
client.query(query).result()

query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.cross_validation_single_holdout`)"
client.query(query).to_dataframe()
```

**Verified: the single holdout's precision (~0.089) and recall (~0.893) land close to their fold means (0.083 and 0.901) — but its `roc_auc` (~0.974) lands on the low side, about one standard deviation below the 5-fold mean (0.980 ± 0.007).** Not a dramatic outlier, but a real, honest illustration: even a single holdout that "looks fine" in isolation carries meaningful uncertainty that a single number can't reveal — you'd only know it was on the low end by actually cross-validating.

---
## Related content

- `workflows/anomaly_fraud_detection` (`workflows/anomaly_fraud_detection/`) — the small-eval-set-count problem that motivates this workflow.
- `models/logistic_regression` (`models/logistic_regression/`) — `LOGISTIC_REG` mechanics in depth, not repeated here.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT fold, COUNT(*) AS n_rows, SUM(Class) AS n_fraud
FROM `statmike-mlops-349915.bq_ml.cross_validation_folds`
GROUP BY fold
ORDER BY fold
```

---
## Examples — BigFrames

No direct BigFrames equivalent — k-fold cross-validation is hand-rolled SQL here (BQML has no native k-fold support in either interface), and BigFrames' `bigframes.ml.linear_model.LogisticRegression` doesn't add anything beyond what's already shown for `LOGISTIC_REG` in `models/logistic_regression` (`models/logistic_regression/`).
