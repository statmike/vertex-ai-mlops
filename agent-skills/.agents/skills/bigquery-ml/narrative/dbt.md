# dbt — BigQuery ML Pipeline

**This works end-to-end**: a real BQML model trained under dbt, two quality-gate tests (one passes, one is deliberately strict enough to fail), and a downstream table that dbt correctly refuses to build when a quality gate fails — the same "halt on a failed check" behavior as `pipelines/dataform` (`pipelines/dataform/`).

The one thing dbt doesn't ship out of the box is a *built-in* materialization for `CREATE MODEL` (Dataform's `type: "operations", hasOutput: true` is officially supported; dbt's core materializations — `table`, `view`, `incremental`, `ephemeral` — aren't built with BQML in mind). The fix is a small, one-time **custom materialization macro** (~15 lines, Step 2) that teaches dbt this one new trick. After that, everything else — `ref()`, tests, the build DAG, dependency-aware skipping — works exactly like any other dbt project.

**Workflow operationalized:** `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`)
**Tooling:** `dbt-core` + `dbt-bigquery` (via `dbtRunner`, dbt's programmatic Python API)

**Data:** [`bigquery-public-data.ga4_obfuscated_sample_ecommerce`](https://console.cloud.google.com/marketplace/product/bigquery-public-datasets)

**References:** `RESOURCES.md` (Full reference) | [dbt-bigquery setup](https://docs.getdbt.com/reference/warehouse-setups/bigquery-setup) | [Custom materializations](https://docs.getdbt.com/guides/create-new-materializations) | [dbt tests](https://docs.getdbt.com/docs/build/data-tests) | `setup` (Setup guide)

---
## Setup

Set your project and location, authenticate, and create a shared dataset. No BigQuery connection needed.

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
## Step 1 — Create a temporary dbt project

A dbt project is just a directory of files (`dbt_project.yml`, `models/`, `macros/`, `tests/`) — no GCP API or IAM setup needed beyond BigQuery access itself. `profiles.yml` uses `method: oauth`, reusing the same Application Default Credentials already active in this kernel.

```python
import tempfile, pathlib

project_dir = pathlib.Path(tempfile.mkdtemp(prefix='bq_ml_dbt_'))
(project_dir / 'models').mkdir()
(project_dir / 'macros').mkdir()
(project_dir / 'tests').mkdir()
(project_dir / 'profiles').mkdir()
print('Project directory:', project_dir)

(project_dir / 'dbt_project.yml').write_text(f"""
name: 'bq_ml_pipeline'
version: '1.0.0'
config-version: 2
profile: 'bq_ml_pipeline'
model-paths: ["models"]
macro-paths: ["macros"]
test-paths: ["tests"]
target-path: "target"
clean-targets:
  - "target"
models:
  bq_ml_pipeline:
    +materialized: table
""")

(project_dir / 'profiles' / 'profiles.yml').write_text(f"""
bq_ml_pipeline:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth
      project: {PROJECT_ID}
      dataset: {DATASET_ID}
      location: {LOCATION}
      threads: 4
""")
print('Project config written')
```

---
## Step 2 — Teach dbt one new trick: the `bqml_model` materialization

dbt's built-in materializations all wrap a model's compiled `SELECT` in a `CREATE ... AS (...)` statement of dbt's own choosing — none of them happen to be `CREATE MODEL`. A **custom materialization** is dbt's own supported extension point for exactly this kind of case: a macro named `materialization_<name>_<adapter>` that controls what DDL actually gets built. Once this one is defined, any model in the project can opt into it with `{{ config(materialized='bqml_model') }}` — a one-time addition, not a per-model workaround.

**Verified live gotcha**: passing model options as a bare custom config key (`config.get('model_options', '')`) triggers a real deprecation warning in dbt 1.12 — `Custom key 'model_options' found in config... Custom config keys should move into config.meta`. Fixed by nesting it under `meta` in both the model file and the macro.

```python
(project_dir / 'macros' / 'materialization_bqml_model.sql').write_text("""
{% materialization bqml_model, adapter='bigquery' %}

  {%- set target_relation = this -%}
  {%- set model_options = config.get('meta', {}).get('model_options', '') -%}
  {%- set model_ref = target_relation.database ~ '.' ~ target_relation.schema ~ '.' ~ target_relation.identifier -%}

  {{ run_hooks(pre_hooks) }}

  {% call statement('main') -%}
    CREATE OR REPLACE MODEL `{{ model_ref }}`
    OPTIONS(
      {{ model_options }}
    ) AS
    {{ sql }}
  {%- endcall %}

  {{ run_hooks(post_hooks) }}

  {{ return({'relations': [target_relation]}) }}

{% endmaterialization %}
""")
print('Custom materialization written')
```

---
## Step 3 — Write the models

Three dbt models, in dependency order via `{{ ref(...) }}`:
1. **`ga4_churn_pipeline_features`** — an ordinary `table` model. Same cohort/feature/label engineering as every other Phase 8 pipeline; dbt's native materialization handles this with no workaround needed.
2. **`ga4_churn_pipeline_model`** — uses the custom `bqml_model` materialization from Step 2, with `model_type`/`OPTIONS` passed via `config(meta={...})`.
3. **`ga4_churn_pipeline_scoring`** — batch `ML.PREDICT` output, an ordinary `table` model depending on both of the above.

```python
(project_dir / 'models' / 'ga4_churn_pipeline_features.sql').write_text("""
{{ config(materialized='table') }}

WITH events AS (
  SELECT
    user_pseudo_id,
    PARSE_DATE('%Y%m%d', event_date) AS event_date,
    event_name,
    device.category AS device_category,
    geo.country AS country,
    traffic_source.medium AS traffic_medium,
    (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'engagement_time_msec') AS engagement_time_msec
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
),
first_visit AS (
  SELECT user_pseudo_id, MIN(event_date) AS first_date
  FROM events
  GROUP BY user_pseudo_id
  HAVING first_date BETWEEN '2020-11-01' AND '2020-12-24'
),
feature_window AS (
  SELECT e.*, f.first_date
  FROM events e
  JOIN first_visit f USING (user_pseudo_id)
  WHERE e.event_date BETWEEN f.first_date AND DATE_ADD(f.first_date, INTERVAL 6 DAY)
),
label_window AS (
  SELECT DISTINCT e.user_pseudo_id
  FROM events e
  JOIN first_visit f USING (user_pseudo_id)
  WHERE e.event_date BETWEEN DATE_ADD(f.first_date, INTERVAL 7 DAY) AND DATE_ADD(f.first_date, INTERVAL 36 DAY)
)
SELECT
  fw.user_pseudo_id,
  ANY_VALUE(fw.first_date) AS first_date,
  ANY_VALUE(fw.device_category) AS device_category,
  ANY_VALUE(fw.country) AS country,
  ANY_VALUE(fw.traffic_medium) AS traffic_medium,
  COUNT(*) AS n_events,
  COUNT(DISTINCT fw.event_date) AS n_active_days,
  COUNTIF(fw.event_name = 'page_view') AS n_page_view,
  COUNTIF(fw.event_name = 'view_item') AS n_view_item,
  COUNTIF(fw.event_name = 'add_to_cart') AS n_add_to_cart,
  COUNTIF(fw.event_name = 'begin_checkout') AS n_begin_checkout,
  COUNTIF(fw.event_name = 'session_start') AS n_sessions,
  COUNTIF(fw.event_name = 'purchase') > 0 AS did_purchase,
  IFNULL(SUM(fw.engagement_time_msec), 0) AS total_engagement_time_msec,
  lw.user_pseudo_id IS NULL AS churned
FROM feature_window fw
LEFT JOIN label_window lw USING (user_pseudo_id)
GROUP BY fw.user_pseudo_id, lw.user_pseudo_id
""")

(project_dir / 'models' / 'ga4_churn_pipeline_model.sql').write_text("""
{{ config(
    materialized='bqml_model',
    meta={'model_options': "model_type = 'BOOSTED_TREE_CLASSIFIER', input_label_cols = ['churned'], auto_class_weights = TRUE, data_split_method = 'AUTO_SPLIT', enable_global_explain = TRUE"}
) }}

SELECT n_events, n_active_days, n_page_view, n_view_item, n_add_to_cart,
       n_begin_checkout, n_sessions, did_purchase, device_category, country,
       traffic_medium, total_engagement_time_msec, churned
FROM {{ ref('ga4_churn_pipeline_features') }}
WHERE first_date <= '2020-11-20'
""")

(project_dir / 'models' / 'ga4_churn_pipeline_scoring.sql').write_text("""
{{ config(materialized='table') }}

SELECT
  user_pseudo_id,
  predicted_churned,
  predicted_churned_probs
FROM ML.PREDICT(
  MODEL {{ ref('ga4_churn_pipeline_model') }},
  (SELECT * FROM {{ ref('ga4_churn_pipeline_features') }} WHERE first_date <= '2020-11-20' LIMIT 1000)
)
""")
print('3 models written')
```

---
## Step 4 — Write the tests (dbt's assertion mechanism)

Same convention as Dataform: a test is just a `SELECT` that must return **zero rows** to pass. `ga4_churn_pipeline_quality_reasonable` uses a realistic bar (`roc_auc < 0.6` fails); `ga4_churn_pipeline_quality_strict` uses a deliberately unrealistic one (`roc_auc < 0.99`) so this notebook demonstrates a genuine, live test failure — not a hypothetical.

```python
(project_dir / 'tests' / 'ga4_churn_pipeline_quality_reasonable.sql').write_text("""
SELECT * FROM ML.EVALUATE(MODEL {{ ref('ga4_churn_pipeline_model') }})
WHERE roc_auc < 0.6
""")

(project_dir / 'tests' / 'ga4_churn_pipeline_quality_strict.sql').write_text("""
SELECT * FROM ML.EVALUATE(MODEL {{ ref('ga4_churn_pipeline_model') }})
WHERE roc_auc < 0.99
""")
print('2 tests written')
```

---
## Step 5 — Run `dbt build`

`dbt build` runs models and tests together in one DAG-aware pass — this is the key detail. **Going into this build, the working assumption was that dbt tests are report-only and wouldn't block a downstream model the way Dataform's `dependOnDependencyAssertions` does — that assumption was wrong, and worth correcting live rather than asserting from prior knowledge.** `dbtRunner` is dbt's supported way to invoke it programmatically from Python (no subprocess/CLI parsing needed).

```python
import os
os.chdir(project_dir)

from dbt.cli.main import dbtRunner

runner = dbtRunner()
result = runner.invoke(['build', '--profiles-dir', 'profiles', '--no-partial-parse'])
print('Overall success:', result.success)
print()
for r in result.result.results:
    print(f'{r.node.name:40s} {r.status}')
```

**`ga4_churn_pipeline_scoring` shows `skipped` — genuinely blocked, not just reported.** `dbt build` really does skip a downstream model when a test on its upstream dependency fails, with no extra configuration needed (unlike Dataform, which needs the explicit `dependOnDependencyAssertions: true` flag). This protection is specific to `dbt build`, though — running `dbt run` then `dbt test` as two separate invocations (common in some CI pipelines, where "deploy" and "verify" are distinct stages) does **not** get it, since by the time `dbt test` runs, `dbt run` has already built everything regardless of what the tests will find.

---
## Step 6 — Confirm the model trained correctly

`use_query_cache=False` here for the same reason documented in `pipelines/cloud_workflows` (`pipelines/cloud_workflows/`) and `pipelines/dataform` (`pipelines/dataform/`): this exact query text has run against this exact model name across several pipeline notebooks, and BigQuery's query cache does not reliably invalidate when the model is replaced.

```python
query = f"SELECT roc_auc FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{DATASET_ID}.ga4_churn_pipeline_model`)"
job_config = bigquery.QueryJobConfig(use_query_cache=False)
client.query(query, job_config=job_config).to_dataframe()
```

---
## What this does and doesn't mean about dbt + BQML

The pipeline above worked completely: a real model trained, two quality gates evaluated correctly, one downstream table correctly blocked. The only thing that took extra work was the ~15-line materialization macro in Step 2 — written once, reusable for every future BQML model in a dbt project, not something to repeat per model.

Worth knowing about, not a shortcoming of what's above: **dbt's own newer, more "native" ML story is Python models via BigFrames** — pandas/scikit-learn-style code that transpiles to BQML under the hood, executed via a Dataproc cluster, Dataproc Serverless, or Colab Enterprise runtime. That's a different path (no literal `CREATE MODEL` DDL involved) and needs separate compute infrastructure this notebook doesn't stand up, since it would be disproportionate for what's really just a "here's another option" aside. The custom-materialization approach above is what teams reach for today when they want an actual, version-controlled, native BQML model artifact under dbt, with a literal `CREATE MODEL` statement they can read and audit — `pipelines/dataform` (`pipelines/dataform/`) gets there with officially-supported syntax instead of a macro, which is a real point in Dataform's favor for this specific use case, but "official support" and "works" are different questions — this notebook answers the second one with a clear yes.

---
## Related content

- `pipelines/dataform` (`pipelines/dataform/`) — the same idea with official, purpose-built `CREATE MODEL` support instead of a custom macro.
- `pipelines/sql_scripting` (`pipelines/sql_scripting/`) / `pipelines/cloud_workflows` (`pipelines/cloud_workflows/`) — non-dbt approaches to the same drift-check/quality-gate idea.
- `workflows/ga4_churn_prediction` (`workflows/ga4_churn_prediction/`) — the workflow this pipeline operationalizes.
