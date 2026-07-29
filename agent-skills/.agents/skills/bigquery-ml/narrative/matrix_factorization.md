# Matrix Factorization — BigQuery ML

Train a **collaborative-filtering recommendation** model with `CREATE MODEL` (model_type = `MATRIX_FACTORIZATION`) — factorizes a sparse (user, item, rating) matrix into low-dimensional user and item latent factor vectors — then walk the full model lifecycle: evaluate, recommend, inspect factors, generate embeddings, item-item similarity search, introspect features/training, and tune hyperparameters.

**Lifecycle:** `CREATE MODEL` → `ML.EVALUATE` → `ML.RECOMMEND` (user→items, item→users) → `ML.WEIGHTS` → `ML.GENERATE_EMBEDDING` → `VECTOR_SEARCH` → `ML.FEATURE_INFO` → `ML.TRAINING_INFO` → hyperparameter tuning (`ML.TRIAL_INFO`)

**The one model type in this entire project that needs real infrastructure setup first:**
- **`MATRIX_FACTORIZATION` cannot train under on-demand (per-byte) pricing** — verified directly: attempting `CREATE MODEL` without a reservation fails immediately with `"Training Matrix Factorization models is not available for on-demand usage."` Every other model type in this project trains fine on-demand; this one requires a BigQuery slot reservation.
- **The reservation's edition matters too, not just its existence** — verified: a `STANDARD` edition reservation still fails, with a *different* error (`"Using BQML related functionalities is disallowed in STANDARD edition"`). `ENTERPRISE` (or higher) is required for any BQML training, matrix factorization included.
- This notebook creates a small **autoscaling** BigQuery Editions reservation (`ENTERPRISE`, 0 baseline slots, scales up to 100 only while a job actually runs) in Setup, and deletes it in Cleanup. This is **not** a capacity commitment — no upfront purchase, no minimum term; it bills per-second only for slot-time actually consumed while queries run, and idles at zero cost otherwise.
- **A newly created reservation assignment needs time to propagate** — verified: `CREATE MODEL` failed on the very first attempt right after creating and assigning a fresh reservation, and succeeded only after waiting.
- No `TRANSFORM` clause exists for this model type — the training query must produce exactly a (user, item, rating) triple.

**Data:** [`bigquery-public-data.google_analytics_sample`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) (Google Merchandise Store demo data, July 2017) — an **IMPLICIT** feedback signal built from product-detail-page view counts per (visitor, product) pair: 42,178 users × 320 items across ~1.3M interactions. `feedback_type='IMPLICIT'` fits this data (a behavioral proxy, not an explicit star rating) — see `RESOURCES.md` (RESOURCES.md) for how `EXPLICIT` feedback differs (different options, different `ML.EVALUATE` metrics).

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (matrix factorization) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-matrix-factorization) | [ML.RECOMMEND docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-recommend) | `setup` (Setup guide)

> **Cost note (measured, not estimated):** this notebook creates a temporary BigQuery Editions reservation to enable training — there's no capacity commitment and no charge while it sits idle, but training under `ENTERPRISE` autoscale bills per slot-hour of actual usage. Building and validating this notebook (base model + tuning job + the BigFrames example below, each retrained at least once) consumed **~6.4 cumulative slot-hours** of real, measured usage — check the [current BigQuery Editions pricing](https://cloud.google.com/bigquery/pricing) to estimate the actual cost for your project/region before running. The reservation is deleted in Cleanup; if a run is interrupted before Cleanup, delete it manually (see Cleanup for the exact commands) to avoid ongoing charges.

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
RESERVATION_ID = 'bqml-mf-temp'  # Temporary reservation name (Setup creates it, Cleanup removes it)
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

`ENTERPRISE` edition, 0 baseline slots, autoscaling up to 100 slots — no capacity commitment, billed per-second only while queries actually run. Assigned to this project for `QUERY`-type jobs (BQML training runs as a `QUERY` job). Waits ~90 seconds afterward for the assignment to actually take effect — a real, verified propagation delay, not an arbitrary pause.

**Idempotent:** if this cell is re-run (e.g. after an interrupted prior run whose Cleanup never executed), it detects and reuses the existing reservation/assignment instead of erroring or creating a duplicate — and skips the 90-second wait when reusing an already-propagated assignment.

```python
import time
from google.cloud import bigquery_reservation_v1
from google.api_core.exceptions import AlreadyExists

reservation_client = bigquery_reservation_v1.ReservationServiceClient()
reservation_parent = f'projects/{PROJECT_ID}/locations/{LOCATION}'
reservation_name = f'{reservation_parent}/reservations/{RESERVATION_ID}'

# Idempotent: reuse an existing reservation/assignment (e.g. from an interrupted
# prior run) instead of erroring or creating a duplicate.
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
## Step 1 — Create the model with `CREATE MODEL`

`feedback_type = 'IMPLICIT'` fits this data — `view_count` is a behavioral proxy signal, not an explicit star rating. `num_factors = 16` is a deliberate, modest choice for a 320-item catalog. There is no `TRANSFORM` clause for this model type — the training `SELECT` must produce exactly a (user, item, rating) triple.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_ga`
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
"""
client.query(query).result()
print('Model matrix_factorization_ga created')
```

---
## Step 2 — Evaluate with `ML.EVALUATE`

IMPLICIT feedback gets ranking-style metrics — `mean_average_precision` and `normalized_discounted_cumulative_gain` (both higher-is-better, bounded [0,1]), plus `mean_squared_error` and `average_rank`. `EXPLICIT` models get a different, regression-style metric set instead (see `RESOURCES.md` (RESOURCES.md)) — the two feedback types aren't evaluated the same way.

> **Verified:** retraining this exact model (same name, same SQL) does not reproduce `mean_average_precision` exactly — one training run reached `0.873`, another reached `0.860`. Matrix factorization's WALS training shows measurable retraining variance, similar to `models/kmeans` (K-Means)/`RANDOM_FOREST_*` elsewhere in this project, unlike PCA's full determinism or the DNN family's bit-for-bit reproducibility under a fixed name.

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_ga`)
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Recommend items for a user with `ML.RECOMMEND`

Passing only the user column scores every item for that user.

> **GOTCHA (verified):** calling this for a `visitor_id` **not present** in the training data does **not** error — it silently returns a full ranked list. `RESOURCES.md` (RESOURCES.md)'s general cold-start note ("cannot recommend for users or items absent from training data") describes the intent, not the observed runtime behavior: comparing the output for a confirmed real trained user against an obviously fake user ID shows completely different top-5 lists, consistent with the fake user falling back to item-side bias/popularity alone rather than genuine personalization (no user factor was ever learned for it). Don't assume a non-empty `ML.RECOMMEND` result means the input user actually existed in training.

```python
query = f"""
SELECT visitor_id, product_name, predicted_view_count_confidence
FROM ML.RECOMMEND(
  MODEL `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_ga`,
  (SELECT '9790296909741758431' AS visitor_id)
)
ORDER BY predicted_view_count_confidence DESC
LIMIT 5
"""
client.query(query).to_dataframe()
```

---
## Step 4 — Recommend users for an item with `ML.RECOMMEND`

Passing only the item column scores every user for that item — the symmetric counterpart to Step 3.

```python
query = f"""
SELECT visitor_id, product_name, predicted_view_count_confidence
FROM ML.RECOMMEND(
  MODEL `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_ga`,
  (SELECT 'Google Youth Girl Hoodie' AS product_name)
)
ORDER BY predicted_view_count_confidence DESC
LIMIT 5
"""
client.query(query).to_dataframe()
```

---
## Step 5 — Inspect the learned factors with `ML.WEIGHTS`

One row per user AND per item (distinguished by `processed_input`), each with a `factor_weights` `ARRAY<STRUCT<factor, weight>>` (length = `num_factors`) and an `intercept` (per-user/per-item bias term).

> **GOTCHA (verified):** there is also exactly one extra row with `processed_input=NULL` and `feature='global__INTERCEPT__'` — the single global bias term shared across the whole model, separate from every user's/item's own intercept.

```python
query = f"""
SELECT processed_input, COUNT(*) AS n
FROM ML.WEIGHTS(MODEL `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_ga`)
GROUP BY processed_input
"""
client.query(query).to_dataframe()
```

---
## Step 6 — Factor vectors as embeddings with `ML.GENERATE_EMBEDDING`

> **GOTCHA (verified):** for `MATRIX_FACTORIZATION`, `ML.GENERATE_EMBEDDING` takes **only the model** — no input table/query argument at all. Passing one errors immediately: `"Function ML.GENERATE_EMBEDDING for MATRIX_FACTORIZATION models only expects 1 argument but 2 were passed."` This is a genuinely different signature from `models/pca` (PCA)/`models/autoencoder` (Autoencoder) (both require a 2nd input-data argument) — it returns embeddings for **every** user and item in the model in one call, mirroring `ML.WEIGHTS`' `processed_input`/`feature` shape rather than `ML.PREDICT`'s.
>
> **Second GOTCHA (verified):** the embedding array has **`num_factors + 1` elements (17 here, not 16)** — one more than `ML.WEIGHTS`' `factor_weights` array for the same model (confirmed 16 elements there, matching `num_factors` exactly). The extra element is almost certainly the per-user/per-item `intercept` appended onto the raw factor vector. Don't assume the embedding array length always equals `num_factors` for this model type.

```python
query = f"""
SELECT processed_input, feature, ml_generate_embedding_result
FROM ML.GENERATE_EMBEDDING(MODEL `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_ga`)
LIMIT 5
"""
client.query(query).to_dataframe()
```

---
## Step 7 — Item-item similarity with `VECTOR_SEARCH`

Materialize the item embeddings (Step 6's output filtered to `processed_input='product_name'`) into a real table — `VECTOR_SEARCH` doesn't accept `ML.GENERATE_EMBEDDING` output directly as its base-table argument, the same limitation already verified in `models/autoencoder` (Autoencoder).

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_item_embeddings` AS
SELECT feature AS product_name, ml_generate_embedding_result AS embedding
FROM ML.GENERATE_EMBEDDING(MODEL `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_ga`)
WHERE processed_input = 'product_name'
"""
client.query(query).result()
print('Table matrix_factorization_item_embeddings created')
```

> **Verified:** querying "Google Youth Girl Hoodie" surfaces other youth apparel (youth tees, youth t-shirts) as its nearest neighbors — the learned item factors capture real product-category structure, not just noise.

```python
query = f"""
SELECT query.product_name AS query_product, base.product_name AS similar_product, distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_item_embeddings`, 'embedding',
  (SELECT product_name, embedding
   FROM `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_item_embeddings`
   WHERE product_name = 'Google Youth Girl Hoodie'),
  top_k => 6,
  distance_type => 'COSINE'
)
ORDER BY distance
"""
client.query(query).to_dataframe()
```

---
## Step 8 — Introspect the training columns with `ML.FEATURE_INFO`

```python
query = f"""
SELECT *
FROM ML.FEATURE_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_ga`)
"""
client.query(query).to_dataframe()
```

---
## Step 9 — Training loss curve with `ML.TRAINING_INFO`

> **Verified:** `eval_loss` is `NULL` throughout for this model — unlike the supervised model types in this project, `MATRIX_FACTORIZATION`'s `ML.TRAINING_INFO` doesn't populate a held-out `eval_loss` column here.

```python
query = f"""
SELECT *
FROM ML.TRAINING_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_ga`)
"""
client.query(query).to_dataframe()
```

---
## Step 10 — Hyperparameter tuning

Tunes `num_factors`, `l2_reg`, and `wals_alpha` (IMPLICIT-only) together, maximizing `mean_average_precision` (the IMPLICIT default objective).

> **Verified:** tuning improved on Step 2's baseline here — the best trial (`num_factors=26`, `l2_reg=2.88`, `wals_alpha=49.2`) reached `mean_average_precision=0.899`, versus this run's untuned baseline of `0.860`. A separate training of the identical baseline and tuning config reached different specific numbers (baseline `0.873`, best tuned trial `0.915` with `wals_alpha=30.8` instead) — consistent with Step 2's retraining-variance finding, the exact hyperparameter search results aren't bit-for-bit reproducible either. **The qualitative result held in both runs: tuning beat the untuned baseline.** Contrast with `models/autoencoder` (Autoencoder), where an equally-sized 4-trial search failed to beat its untuned baseline at all.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_ga_tuned`
OPTIONS(
  model_type = 'MATRIX_FACTORIZATION',
  feedback_type = 'IMPLICIT',
  user_col = 'visitor_id',
  item_col = 'product_name',
  rating_col = 'view_count',
  num_factors = HPARAM_RANGE(8, 32),
  l2_reg = HPARAM_RANGE(0.1, 10.0),
  wals_alpha = HPARAM_RANGE(20.0, 60.0),
  num_trials = 4,
  max_parallel_trials = 2
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
"""
client.query(query).result()
print('Tuned model created')
```

```python
query = f"""
SELECT
  trial_id,
  hyperparameters,
  hparam_tuning_evaluation_metrics.mean_average_precision AS mean_average_precision,
  is_optimal
FROM ML.TRIAL_INFO(MODEL `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_ga_tuned`)
ORDER BY mean_average_precision DESC
"""
client.query(query).to_dataframe()
```

Calling `ML.EVALUATE` on a tuned model with no extra arguments returns every trial's metrics in one result (one row per `trial_id`) — there's no `STRUCT(trial_id)` 2-argument form for `ML.EVALUATE` the way `ML.RECOMMEND`/`ML.PREDICT` accept one; passing a `STRUCT` as a 2nd argument errors (`"argument 2 must be a relation"`).

```python
query = f"""
SELECT *
FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.matrix_factorization_ga_tuned`)
"""
client.query(query).to_dataframe()
```

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

### Evaluate with `%%bigquery`

```sql
%%bigquery --project {PROJECT_ID}

SELECT *
FROM ML.EVALUATE(MODEL `statmike-mlops-349915.bq_ml.matrix_factorization_ga`)
```

---
## Examples — BigFrames

BigFrames provides a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood. **Matrix factorization has a genuine first-class wrapper: `bigframes.ml.decomposition.MatrixFactorization`.**

> **GOTCHA (verified against the live installed constructor signature):** `MatrixFactorization(feedback_type=..., num_factors=..., user_col=..., item_col=..., rating_col=..., l2_reg=...)` — there is **no `wals_alpha` parameter**, unlike the SQL `CREATE MODEL` syntax. For `feedback_type='implicit'`, BigFrames trains with BigQuery ML's default `wals_alpha` (40) with no way to override it through this wrapper — use SQL directly if you need to set `wals_alpha`.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION
```

```python
from bigframes.ml.decomposition import MatrixFactorization

query = f"""
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
"""
df = bpd.read_gbq(query)

# Train (creates a BigQuery ML model behind the scenes)
model = MatrixFactorization(
    feedback_type='implicit',
    num_factors=16,
    user_col='visitor_id',
    item_col='product_name',
    rating_col='view_count',
)
model.fit(df)

# Evaluate
model.score(df).to_pandas()
```
