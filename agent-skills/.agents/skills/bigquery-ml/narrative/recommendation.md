# Recommendation — BigQuery ML

Extends `models/matrix_factorization` (`models/matrix_factorization/`)'s algorithm demo into a full workflow: a non-personalized **popularity baseline** (to quantify what personalization actually buys you), **batch top-N generation** for many users at once (the real production pattern), and an empirical **cold-start deep dive**.

**Models used:** `MATRIX_FACTORIZATION`
**Functions used:** `ML.EVALUATE`, `ML.RECOMMEND`

`MATRIX_FACTORIZATION`'s own mechanics (`ML.WEIGHTS`, `ML.GENERATE_EMBEDDING`, item-item `VECTOR_SEARCH`, hyperparameter tuning) are already covered in depth in `models/matrix_factorization` (`models/matrix_factorization/`) and not repeated here.

> **Real cost note:** like `models/matrix_factorization/`, this model type requires a slot reservation to train. This notebook creates a temporary **Enterprise-edition autoscale reservation** (0 baseline slots, autoscale to 100, billed per-second only while queries run, no capacity commitment) and deletes it in Cleanup.

**Data:** [`bigquery-public-data.google_analytics_sample.ga_sessions_*`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) (July 2017) — the same IMPLICIT-feedback setup as `models/matrix_factorization/`, for direct comparability.

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (MATRIX_FACTORIZATION) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-matrix-factorization) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. A temporary reservation is created in the next section (required for this model type only).

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
RESERVATION_ID = 'bqml-reco-temp'  # Temporary reservation name (Setup creates it, Cleanup removes it)
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

### Create a temporary slot reservation (required for this model type only)

Same pattern as `models/matrix_factorization` (`models/matrix_factorization/`): `ENTERPRISE` edition, 0 baseline slots, autoscaling up to 100 slots, no capacity commitment. Waits ~90 seconds for the assignment to propagate.

**Idempotent:** safe to re-run (e.g. after an interrupted prior run) — reuses an existing reservation/assignment instead of erroring.

```python
import time
from google.cloud import bigquery_reservation_v1
from google.api_core.exceptions import AlreadyExists

reservation_client = bigquery_reservation_v1.ReservationServiceClient()
reservation_parent = f'projects/{PROJECT_ID}/locations/{LOCATION}'
reservation_name = f'{reservation_parent}/reservations/{RESERVATION_ID}'

try:
    reservation = reservation_client.create_reservation(
        parent=reservation_parent,
        reservation_id=RESERVATION_ID,
        reservation=bigquery_reservation_v1.Reservation(
            slot_capacity=0,
            edition=bigquery_reservation_v1.Edition.ENTERPRISE,
            autoscale=bigquery_reservation_v1.Reservation.Autoscale(max_slots=100),
            ignore_idle_slots=True,
        ),
    )
    print(f'Created {reservation.name}')
except AlreadyExists:
    reservation = reservation_client.get_reservation(name=reservation_name)
    print(f'Reservation already exists — reusing {reservation.name}')

existing_assignments = list(reservation_client.list_assignments(parent=reservation.name))
if existing_assignments:
    assignment = existing_assignments[0]
    print(f'Assignment already exists — reusing {assignment.name}')
else:
    assignment = reservation_client.create_assignment(
        parent=reservation.name,
        assignment=bigquery_reservation_v1.Assignment(
            job_type=bigquery_reservation_v1.Assignment.JobType.QUERY,
            assignee=f'projects/{PROJECT_ID}',
        ),
    )
    print(f'Created {assignment.name}, waiting ~90s for it to propagate...')
    time.sleep(90)

print('Ready to train.')
```

---
## Step 1 — Train `MATRIX_FACTORIZATION`

Identical training query to `models/matrix_factorization` (`models/matrix_factorization/`), for a fair, directly comparable baseline.

```python
query = """
CREATE OR REPLACE MODEL `{project}.{dataset}.recommendation_mf`
OPTIONS(
  model_type = 'MATRIX_FACTORIZATION',
  feedback_type = 'IMPLICIT',
  user_col = 'visitor_id',
  item_col = 'product_name',
  rating_col = 'view_count',
  num_factors = 16
) AS
SELECT
  fullVisitorId AS visitor_id,
  product.v2ProductName AS product_name,
  COUNT(*) AS view_count
FROM `bigquery-public-data.google_analytics_sample.ga_sessions_*`,
UNNEST(hits) AS hits,
UNNEST(hits.product) AS product
WHERE _TABLE_SUFFIX BETWEEN '20170701' AND '20170801'
  AND product.v2ProductName IS NOT NULL AND product.v2ProductName != '(not set)'
GROUP BY visitor_id, product_name
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()
print('Model recommendation_mf created')
```

```python
query = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.recommendation_mf`)"
client.query(query).to_dataframe()
```

`mean_average_precision` ≈ 0.86 — consistent with `models/matrix_factorization/`'s untuned baseline (retraining `MATRIX_FACTORIZATION` is genuinely non-deterministic, per that notebook's verified note — exact numbers here will vary run to run).

---
## Step 2 — Non-personalized popularity baseline

What "no ML" looks like: simply rank items by total views across everyone. This is the yardstick the rest of this notebook measures personalization against.

```python
query = """
CREATE OR REPLACE TABLE `{project}.{dataset}.recommendation_popularity` AS
SELECT
  product.v2ProductName AS product_name,
  COUNT(*) AS total_views
FROM `bigquery-public-data.google_analytics_sample.ga_sessions_*`,
UNNEST(hits) AS hits,
UNNEST(hits.product) AS product
WHERE _TABLE_SUFFIX BETWEEN '20170701' AND '20170801'
  AND product.v2ProductName IS NOT NULL AND product.v2ProductName != '(not set)'
GROUP BY product_name
ORDER BY total_views DESC
""".format(project=PROJECT_ID, dataset=DATASET_ID)
client.query(query).result()

query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.recommendation_popularity` LIMIT 10"
client.query(query).to_dataframe()
```

---
## Step 3 — Batch top-N generation for many users at once

`models/matrix_factorization/` only demos one user (or one item) at a time. In production you generate recommendations for many users in a single pass — pass a table of users to `ML.RECOMMEND` and rank with `ROW_NUMBER()`.

```python
query = f"""
SELECT visitor_id, product_name, predicted_view_count_confidence, rank
FROM (
  SELECT
    visitor_id, product_name, predicted_view_count_confidence,
    ROW_NUMBER() OVER (PARTITION BY visitor_id ORDER BY predicted_view_count_confidence DESC) AS rank
  FROM ML.RECOMMEND(
    MODEL `{PROJECT_ID}.{DATASET_ID}.recommendation_mf`,
    (SELECT DISTINCT fullVisitorId AS visitor_id
     FROM `bigquery-public-data.google_analytics_sample.ga_sessions_*`
     WHERE _TABLE_SUFFIX BETWEEN '20170701' AND '20170801'
     LIMIT 5)
  )
)
WHERE rank <= 5
ORDER BY visitor_id, rank
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Does personalization actually differ from popularity?

If a user's personalized top-10 just reproduces the global popularity top-10, `MATRIX_FACTORIZATION` isn't buying you anything over Step 2's simple baseline. Quantify the overlap for a real user from the training data.

```python
query = f"""
WITH personalized AS (
  SELECT product_name
  FROM ML.RECOMMEND(
    MODEL `{PROJECT_ID}.{DATASET_ID}.recommendation_mf`,
    (SELECT '7953155863181185949' AS visitor_id)
  )
  ORDER BY predicted_view_count_confidence DESC
  LIMIT 10
),
popularity AS (
  SELECT product_name FROM `{PROJECT_ID}.{DATASET_ID}.recommendation_popularity` LIMIT 10
)
SELECT COUNT(*) AS overlap_count
FROM personalized JOIN popularity USING (product_name)
"""
client.query(query).to_dataframe()
```

**Verified: 0/10 overlap for this user.** This user's personalized top-10 shares nothing with the global top-10 most-viewed products — strong evidence personalization is doing real, distinct work, not just reproducing what's already popular.

---
## Step 5 — Cold-start deep dive: what actually happens for an absent user?

> **GOTCHA (verified, extends `models/matrix_factorization/`'s note):** calling `ML.RECOMMEND` for a `visitor_id` **not present in training** does not error — it silently returns a ranking. Proving this ranking is *not* personalized: two different absent visitor IDs should get the identical list if it's really just a global fallback.

```python
query_a = f"""
SELECT '__cold_user_a__' AS probe, product_name, predicted_view_count_confidence
FROM ML.RECOMMEND(MODEL `{PROJECT_ID}.{DATASET_ID}.recommendation_mf`, (SELECT '__cold_user_a__' AS visitor_id))
ORDER BY predicted_view_count_confidence DESC LIMIT 5
"""
query_b = f"""
SELECT '__cold_user_b__' AS probe, product_name, predicted_view_count_confidence
FROM ML.RECOMMEND(MODEL `{PROJECT_ID}.{DATASET_ID}.recommendation_mf`, (SELECT '__cold_user_b__' AS visitor_id))
ORDER BY predicted_view_count_confidence DESC LIMIT 5
"""
df_a = client.query(query_a).to_dataframe()
df_b = client.query(query_b).to_dataframe()
print('Identical rankings for two different absent users:', df_a['product_name'].tolist() == df_b['product_name'].tolist())
df_a
```

**Verified: identical.** The "recommendation" for an absent user is really just the model's global item-bias ranking — not personalization at all. How does that fallback compare to Step 2's popularity baseline?

```python
query = f"""
WITH cold AS (
  SELECT product_name
  FROM ML.RECOMMEND(MODEL `{PROJECT_ID}.{DATASET_ID}.recommendation_mf`, (SELECT '__cold_user_a__' AS visitor_id))
  ORDER BY predicted_view_count_confidence DESC LIMIT 10
),
popularity AS (
  SELECT product_name FROM `{PROJECT_ID}.{DATASET_ID}.recommendation_popularity` LIMIT 10
)
SELECT COUNT(*) AS overlap_count
FROM cold JOIN popularity USING (product_name)
"""
client.query(query).to_dataframe()
```

**Verified: substantial overlap (9/10 this run — a separate pre-validation run saw 6/10; `MATRIX_FACTORIZATION` retraining is non-deterministic, see `models/matrix_factorization/`).** `MATRIX_FACTORIZATION`'s own built-in fallback for absent users already closely approximates the popularity baseline, run to run. **Practical implication:** for truly new users, you likely don't need a separate cold-start/popularity system bolted on — `ML.RECOMMEND`'s default behavior for an absent `visitor_id` already does something very close to that automatically.

---
## Related content

- `models/matrix_factorization` (`models/matrix_factorization/`) — the algorithm mechanics in depth: `ML.WEIGHTS`, `ML.GENERATE_EMBEDDING`, item-item `VECTOR_SEARCH`, hyperparameter tuning.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

```sql
%%bigquery --project {PROJECT_ID}

SELECT * FROM `statmike-mlops-349915.bq_ml.recommendation_popularity`
LIMIT 10
```

---
## Examples — BigFrames

Skipped here to avoid duplicating this notebook's billed Enterprise-reservation training cost — `bigframes.ml.decomposition.MatrixFactorization` is fully demonstrated in `models/matrix_factorization` (`models/matrix_factorization/`).
