# Remote Models — BigQuery ML (Custom Vertex AI Endpoint)

Register a model deployed to a **Vertex AI Endpoint** as a BigQuery ML model with `CREATE MODEL ... REMOTE WITH CONNECTION`, so it can be queried in-warehouse with `ML.PREDICT`. Unlike `models/imported` (imported models), the model runs on the **Endpoint's** infrastructure — any framework, any size, GPUs if needed — and BigQuery sends rows to it through a Cloud Resource Connection.

**Lifecycle:** `CREATE MODEL` (train) → `EXPORT MODEL` → deploy to a Vertex AI Endpoint → create a connection + grant IAM → `CREATE MODEL ... REMOTE WITH CONNECTION` → `ML.PREDICT`

This notebook is the **full round trip**, picking up exactly where `models/export` (`models/export/`) leaves off: train in BQML → export → deploy → call back from BigQuery. It also covers two things that shape *why* the round trip looks the way it does: a simpler-looking native shortcut that's currently broken (Step 4), and a live proof that `REMOTE` works with models that never touched BigQuery ML at all (Step 5).

> **⚠️ Real, small dollar cost while the Endpoint is deployed.** Verified: a few minutes on the smallest general-purpose CPU machine type (`n1-standard-2`) for this example — far cheaper than `models/automl_classifier` (`models/automl_classifier/`)'s hours-long training, but genuinely billable, unlike every other notebook in this project. **Run Cleanup immediately after you're done experimenting** — don't leave the Endpoint deployed. Only **one** Endpoint carries real cost in this notebook: the genericity demo in Step 5 registers a second model but deliberately stops short of deploying it, and the native-shortcut demo in Step 4 creates its own scratch Endpoint just to prove the deploy fails, then deletes it immediately in the same cell — empty the whole time, so no cost accrues.

**When to use a remote model (vs. `models/imported` (imported), vs. plain `models/export` (`EXPORT MODEL`)):**
- The model is too large for the imported-model size limits (250-450 MB), needs a GPU, or uses a framework BigQuery can't import.
- You already have (or want) a Vertex AI Endpoint serving the model for other consumers, and want SQL-native batch scoring on top.
- Contrast with `models/imported` (`models/imported/`): imported models run **inside** BigQuery compute (frozen, size-limited, no endpoint); remote models run on the **endpoint's** infrastructure (any size, but needs a connection + a deployed, billable Endpoint).

**Data:** [`bigquery-public-data.ml_datasets.census_adult_income`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets) — same feature/label set as `models/logistic_regression` (Logistic Regression) and `models/export` (Export Models).

**References:** `RESOURCES.md` (Full reference) | [CREATE MODEL (remote, custom endpoint) docs](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-remote-model-https) | [Cloud Resource Connection](https://cloud.google.com/bigquery/docs/create-cloud-resource-connection) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset for the model.

> Unlike every other notebook in this project, a remote model genuinely **needs a BigQuery Cloud Resource Connection** — Step 6 creates one and grants it `roles/aiplatform.user`. This is a real IAM change on your project (narrowly scoped to one new service account) — review Step 6 before running it.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
REGION = 'us-central1'  # Vertex AI region for the Endpoint
DATASET_ID = 'bq_ml'  # Shared dataset across all bq-ml notebooks
BUCKET = 'statmike-mlops-349915'  # <-- Replace with your GCS bucket (same location as DATASET_ID)
CONNECTION_ID = 'bq_ml_remote_demo'  # Cloud Resource Connection created in Step 6
```

### Environment

> **Already set up the project environment?** The cell below is a no-op — packages are already in your kernel. See the `setup` (Setup Reference) for details.
>
> **Running standalone** (Colab, Colab Enterprise, Vertex AI Workbench)? The cell below installs required packages into your current kernel.

```python
from google.cloud import bigquery, storage
from google.cloud import aiplatform
import pandas as pd

client = bigquery.Client(project=PROJECT_ID)
gcs_client = storage.Client(project=PROJECT_ID)
gcs_bucket = gcs_client.bucket(BUCKET)
aiplatform.init(project=PROJECT_ID, location=REGION)
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
## Step 1 — Train and export a `LOGISTIC_REG` model

Same pattern as `models/export` (`models/export/`) Step 1-2 — a small, fast-training classifier, exported as a TensorFlow SavedModel.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.remote_source_logistic_regression`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  auto_class_weights = TRUE
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).result()
print('Model remote_source_logistic_regression created')

query = f"""
EXPORT MODEL `{PROJECT_ID}.{DATASET_ID}.remote_source_logistic_regression`
OPTIONS (URI = 'gs://{BUCKET}/bq_ml/remote/tf_export/1')
"""
client.query(query).result()
print('Model exported')
```

---
## Step 2 — Deploy the export to a Vertex AI Endpoint

Upload the exported SavedModel to Vertex AI Model Registry with a **pre-built TensorFlow-serving container** (no Dockerfile, no Cloud Build — matching `MLOps/Serving/Platforms/Vertex%20AI%20Pre-built%20Serving%20Containers.ipynb` (`MLOps/Serving/Platforms/Vertex AI Pre-built Serving Containers.ipynb`)'s simplest path), then deploy to the **smallest general-purpose CPU machine type** (`n1-standard-2`) to keep the billable window as cheap as possible.

> This step takes several minutes (endpoint provisioning) and starts the billable window — the Endpoint incurs cost from here until Cleanup.

```python
vertex_model = aiplatform.Model.upload(
    display_name='bq-ml-remote-demo-logreg',
    artifact_uri=f'gs://{BUCKET}/bq_ml/remote/tf_export/1/',
    serving_container_image_uri='us-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-15:latest',
)
vertex_model.wait()
print('Model uploaded:', vertex_model.resource_name)
```

```python
endpoint = aiplatform.Endpoint.create(display_name='bq-ml-remote-demo-endpoint')
print('Endpoint created:', endpoint.resource_name)

vertex_model.deploy(
    endpoint=endpoint,
    deployed_model_display_name='bq-ml-remote-demo-deployed',
    machine_type='n1-standard-2',
    min_replica_count=1,
    max_replica_count=1,
)
print('Deployed to:', endpoint.resource_name)

ENDPOINT_ID = endpoint.name
ENDPOINT_URL = f'https://{REGION}-aiplatform.googleapis.com/v1/{endpoint.resource_name}'
print('Endpoint URL for CREATE MODEL:', ENDPOINT_URL)
```

---
## Step 3 — `ML.PREDICT` the endpoint directly (sanity check)

Before wiring up BigQuery, confirm the endpoint itself answers — this isolates "is the endpoint healthy" from "is the BigQuery connection wired correctly" if something goes wrong later.

```python
test_instance = {
    'age': 39.0, 'workclass': 'Private', 'education': 'Bachelors', 'education_num': 13.0,
    'marital_status': 'Never-married', 'occupation': 'Tech-support', 'relationship': 'Not-in-family',
    'race': 'White', 'sex': 'Male', 'hours_per_week': 40.0, 'native_country': 'United-States',
}
endpoint.predict(instances=[test_instance]).predictions
```

---
## Step 4 — The native shortcut, and why this notebook doesn't use it

BigQuery ML can register a model directly to Vertex AI Model Registry with `model_registry='VERTEX_AI'` at `CREATE MODEL` time — no `EXPORT MODEL`, no manual container (see `models/export` (`models/export/`) Step 5). Google's own docs say you can "version, evaluate, and deploy the models for online prediction... without needing a serving container" — worth trying before assuming Steps 1-2's manual export+upload is unnecessary complexity.

> **Verified live: it doesn't currently work.** BQML bakes a full Sampled-Shapley `explanationSpec` into every model registered this way (confirmed via `gcloud ai models describe` — present unconditionally, no option to opt out). When Vertex AI tries to deploy it, it attempts to configure that explanation automatically and fails with a GraphDef version mismatch:
> ```
> InvalidArgument: 400 Error occurred in Explanation preprocessing. ValueError:
> NodeDef mentions attr 'debug_name' not in Op<name=VarHandleOp...>
> ```
> This is a confirmed, currently-open Google issue — [vertex-ai-samples#2723](https://github.com/GoogleCloudPlatform/vertex-ai-samples/issues/2723), reported against Google's own official BQML-online-prediction sample notebook, closed **"not planned."** A manually-uploaded model (Steps 1-2) has no baked-in explanation spec, so it never hits this path — which is why this notebook uses the manual route as primary, not as a simplification opportunity waiting to happen.

```python
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.remote_native_shortcut_demo`
OPTIONS(
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['income_bracket'],
  model_registry = 'VERTEX_AI',
  vertex_ai_model_id = 'bq_ml_remote_native_shortcut_demo'
) AS
SELECT
  age, workclass, education, education_num, marital_status, occupation,
  relationship, race, sex, hours_per_week, native_country, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
"""
client.query(query).result()
print('Registered directly to Vertex AI Model Registry -- no EXPORT MODEL, no container chosen')

native_model = aiplatform.Model('bq_ml_remote_native_shortcut_demo')
print('container_spec (empty -- BQML manages serving internally, not a container):', native_model.container_spec)

# .deploy() auto-creates an Endpoint if none is given -- create one explicitly so
# it can be torn down right below regardless of outcome, instead of leaking an
# orphaned Endpoint if deploy fails (as it's expected to).
scratch_endpoint = aiplatform.Endpoint.create(display_name='bq-ml-remote-native-shortcut-demo-endpoint')
try:
    native_model.deploy(endpoint=scratch_endpoint, machine_type='n1-standard-2', min_replica_count=1, max_replica_count=1)
    print('Deploy succeeded (!) -- Google may have fixed the underlying bug since this was last verified')
except Exception as e:
    print(f'Deploy failed as expected: {type(e).__name__}: {str(e)[:300]}')
finally:
    scratch_endpoint.delete(force=True)
    print('Scratch endpoint deleted (force=True in case a model partially attached)')

client.query(f'DROP MODEL IF EXISTS `{PROJECT_ID}.{DATASET_ID}.remote_native_shortcut_demo`').result()
print('Scratch model dropped (also removes its Vertex AI Model Registry entry)')
```

---
## Step 5 — `REMOTE` isn't limited to BQML models

Everything so far started with a model trained *in* BigQuery ML. `REMOTE WITH CONNECTION` doesn't care where the model came from — it just calls whatever's running on the endpoint. To prove that concretely: train an XGBoost model **entirely outside BigQuery** (same local-training approach as `models/imported` (`models/imported/`) Step 3, but with no BQML import involved this time), then register it to Vertex AI Model Registry with the pre-built `xgboost-cpu` container — a different container than the `tf2-cpu` one Step 2 used, since this is a genuinely different framework.

**Not deployed to a live Endpoint here** — a second live endpoint would double this notebook's billable footprint for a point Steps 1-3 already fully prove, and `MLOps/Serving/SQL%20Inference/BQML%20Remote%20Model%20on%20Vertex%20AI%20Endpoint.ipynb` (`MLOps/Serving/SQL Inference/BQML Remote Model on Vertex AI Endpoint.ipynb`) already executes this exact idea end-to-end (there with a HuggingFace/FastAPI container). The registration below is real and verified — deploying it from here would be the identical `aiplatform.Model.deploy()` + `CREATE MODEL ... REMOTE WITH CONNECTION` pattern already shown in Steps 2 and 7, just pointed at this model instead.

```python
import xgboost as xgb

df_local = client.query("""
SELECT age, education_num, hours_per_week, income_bracket
FROM `bigquery-public-data.ml_datasets.census_adult_income`
""").to_dataframe()

feature_cols = ['age', 'education_num', 'hours_per_week']
X_local = df_local[feature_cols].values.astype('float32')
y_local = (df_local['income_bracket'].str.strip() == '>50K').astype('float32').values

dtrain = xgb.DMatrix(X_local, label=y_local, feature_names=feature_cols)
booster = xgb.train({'objective': 'binary:logistic', 'max_depth': 4, 'eta': 0.3}, dtrain, num_boost_round=50)
preds = booster.predict(dtrain)
print('Local XGBoost train accuracy (3 numeric features only -- illustrative, not tuned):',
      ((preds > 0.5).astype(int) == y_local).mean())

booster.save_model('xgb_income_external.json')

blob = gcs_bucket.blob('bq_ml/remote/xgboost_external/model.bst')
blob.upload_from_filename('xgb_income_external.json')

xgboost_model = aiplatform.Model.upload(
    display_name='bq-ml-remote-demo-xgboost-external',
    artifact_uri=f'gs://{BUCKET}/bq_ml/remote/xgboost_external/',
    serving_container_image_uri='us-docker.pkg.dev/vertex-ai/prediction/xgboost-cpu.2-1:latest',
)
xgboost_model.wait()
print('Registered (not deployed):', xgboost_model.resource_name)
```

---
## Step 6 — Create the Cloud Resource Connection + grant IAM

Unlike every other model type in this project, a remote model **needs a BigQuery connection** so it can call the endpoint on your behalf. `roles/aiplatform.user` (labeled "Agent Platform User" in the current Cloud Console), granted to the connection's auto-provisioned service account, is the minimum permission for it to call `predict`.

> **This changes IAM on your project** — it grants one role to one newly-created, narrowly-scoped service account.

> **Verified live:** the `gcloud add-iam-policy-binding` call can fail transiently without raising — this cell checks its exit status explicitly and raises immediately with the real error instead of silently continuing (a silent failure here would otherwise surface confusingly as a permission error two cells later, in Step 7, with no clue why). IAM propagation time itself is also genuinely variable — it took over two minutes in one verified run despite the grant succeeding immediately — so Step 7 retries on a permission error rather than gambling on a single fixed wait.

> **Also verified live:** `bq mk --connection` on an ID that already exists fails with `"Already Exists: Connection ..."` (capitalized) — the check below is case-insensitive so re-running this cell (e.g. after a partial run) doesn't false-positive as a real failure.

```python
import subprocess, json, time

r_conn = subprocess.run(
    ['bq', 'mk', '--connection', '--location', LOCATION, '--connection_type', 'CLOUD_RESOURCE',
     '--project_id', PROJECT_ID, CONNECTION_ID],
    capture_output=True, text=True,
)
if r_conn.returncode != 0 and 'already exists' not in r_conn.stderr.lower():
    raise RuntimeError(f'Failed to create connection {CONNECTION_ID}:\n{r_conn.stderr}')

r_show = subprocess.run(
    ['bq', 'show', '--connection', '--format=json', '--project_id', PROJECT_ID, '--location', LOCATION, CONNECTION_ID],
    capture_output=True, text=True, check=True,
)
connection_sa = json.loads(r_show.stdout)['cloudResource']['serviceAccountId']
print('Connection service account:', connection_sa)

r_iam = subprocess.run(
    ['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
     f'--member=serviceAccount:{connection_sa}', '--role=roles/aiplatform.user', '--quiet'],
    capture_output=True, text=True,
)
if r_iam.returncode != 0:
    # Don't assume success -- a silently-swallowed failure here surfaces
    # confusingly as a permission error two cells later in Step 7, with no
    # clue why. Verified live: this can genuinely fail transiently.
    raise RuntimeError(f'Failed to grant roles/aiplatform.user to {connection_sa}:\n{r_iam.stderr}')
print('Granted roles/aiplatform.user')

time.sleep(60)  # initial wait -- Step 7 retries further, since propagation can exceed this
```

---
## Step 7 — `CREATE MODEL ... REMOTE WITH CONNECTION`

`INPUT`/`OUTPUT` is required for a custom endpoint (unlike the LLM/foundation remote-model variants documented in `bq-ai-functions` (`bq-ai-functions`)). Field **names must match** the endpoint's request/response field names exactly.

**Verified:** the TF-serving container's response uses the same three field names the SavedModel signature itself exposes (see `models/export` (`models/export/`) Step 2): `income_bracket_probs` (`ARRAY<FLOAT64>`), `income_bracket_values` (`ARRAY<STRING>`), `predicted_income_bracket` (`ARRAY<STRING>`).

> **Retries on a permission error** rather than a single attempt — see the note at the end of Step 6. This is the cell most likely to need more than one attempt on a fresh connection.

```python
from google.api_core.exceptions import BadRequest, Forbidden

query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.remote_logistic_regression`
INPUT(
  age FLOAT64, workclass STRING, education STRING, education_num FLOAT64,
  marital_status STRING, occupation STRING, relationship STRING, race STRING,
  sex STRING, hours_per_week FLOAT64, native_country STRING
)
OUTPUT(
  income_bracket_probs ARRAY<FLOAT64>,
  income_bracket_values ARRAY<STRING>,
  predicted_income_bracket ARRAY<STRING>
)
REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
OPTIONS(
  endpoint = '{ENDPOINT_URL}'
)
"""

# IAM propagation time is genuinely variable -- verified live taking over two
# minutes in one run despite the grant in Step 6 succeeding immediately.
# Retry on a permission error instead of gambling on a single fixed wait.
max_attempts = 8
for attempt in range(1, max_attempts + 1):
    try:
        client.query(query).result()
        print('Model remote_logistic_regression created')
        break
    except (BadRequest, Forbidden) as e:
        if 'permission' not in str(e).lower() or attempt == max_attempts:
            raise
        print(f'Attempt {attempt}/{max_attempts}: permission not yet propagated, waiting 20s...')
        time.sleep(20)
```

---
## Step 8 — `ML.PREDICT`: single/multi-row and batch table scoring

`ML.PREDICT` is the **only** supported lifecycle function for a remote model — no `ML.EVALUATE`, no `ML.EXPLAIN_PREDICT`, no `ML.FEATURE_INFO` (the model wasn't trained in BigQuery, so none of the training-side introspection applies). `remote_model_status` reports per-row call status — `NULL` means success.

```python
query = f"""
SELECT income_bracket, predicted_income_bracket, income_bracket_probs, remote_model_status
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.remote_logistic_regression`,
  (SELECT income_bracket, age, workclass, education, education_num, marital_status,
          occupation, relationship, race, sex, hours_per_week, native_country
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   LIMIT 5)
)
"""
client.query(query).to_dataframe()
```

Batch table scoring — the same call, scaled up. Verified: 0 `remote_model_status` errors across 200 rows.

```python
query = f"""
SELECT COUNT(*) AS n, COUNTIF(remote_model_status IS NOT NULL) AS errors
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.remote_logistic_regression`,
  (SELECT age, workclass, education, education_num, marital_status,
          occupation, relationship, race, sex, hours_per_week, native_country
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   LIMIT 200)
)
"""
client.query(query).to_dataframe()
```

---
## Related production content

This notebook stays focused on the `REMOTE WITH CONNECTION` mechanics. For deeper production patterns — custom containers, traffic splitting, autoscaling, cost optimization — see:
- `MLOps/Serving/SQL%20Inference/BQML%20Remote%20Model%20on%20Vertex%20AI%20Endpoint.ipynb` (`MLOps/Serving/SQL Inference/BQML Remote Model on Vertex AI Endpoint.ipynb`) — the same mechanism with a custom FastAPI container instead of a pre-built one.
- `MLOps/Serving/Online/readme.md` (`MLOps/Serving/Online/readme.md`) — the full Online Prediction series: endpoint types, prediction methods, autoscaling, cost optimization.

---
## Examples — `%%bigquery` Magics

The same operations using IPython magic commands — write SQL directly in cells without Python string wrapping.

- `%%bigquery` — run SQL, display results inline
- `%%bigquery df` — run SQL, capture results into a pandas DataFrame

```sql
%%bigquery --project {PROJECT_ID}

SELECT predicted_income_bracket, income_bracket_probs
FROM ML.PREDICT(
  MODEL `statmike-mlops-349915.bq_ml.remote_logistic_regression`,
  (SELECT age, workclass, education, education_num, marital_status,
          occupation, relationship, race, sex, hours_per_week, native_country
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   LIMIT 3)
)
```

---
## Examples — BigFrames

No direct BigFrames training equivalent for remote-endpoint registration — orchestrate the deploy with the Vertex AI SDK (Step 2 above) as usual, then either call `ML.PREDICT` via plain SQL (as this notebook does) or use the Vertex AI SDK's own `endpoint.predict()` directly from Python. This runs the same `ML.PREDICT` call through BigFrames' SQL passthrough.

```python
import bigframes.pandas as bpd

bpd.close_session()  # Reset session to apply project/location settings
bpd.options.bigquery.project = PROJECT_ID
bpd.options.bigquery.location = LOCATION

bf_query = f"""
SELECT predicted_income_bracket, income_bracket_probs
FROM ML.PREDICT(
  MODEL `{PROJECT_ID}.{DATASET_ID}.remote_logistic_regression`,
  (SELECT age, workclass, education, education_num, marital_status,
          occupation, relationship, race, sex, hours_per_week, native_country
   FROM `bigquery-public-data.ml_datasets.census_adult_income`
   LIMIT 3)
)
"""
bpd.read_gbq(bf_query).peek()
```
