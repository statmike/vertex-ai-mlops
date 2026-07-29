# Metric Diagnostics — BigQuery AI Functions

An end-to-end "why did my metric move?" pipeline:

1. **Build** a dataset with an interest period and a reference period
2. **Confirm** the headline shift with a plain SQL aggregate
3. **Explain** the change with `AI.KEY_DRIVERS` — find the segments that drove it
4. **Narrate** the key drivers in plain language with `AI.GENERATE`

**What this demonstrates:**
- Root-cause analysis of a metric change entirely in BigQuery SQL
- Key driver / contribution analysis with `AI.KEY_DRIVERS` (no model, no connection)
- Ranking segments by absolute `contribution` and by `unexpected_difference`
- Composing augmented analytics with generative AI for an executive summary

**Functions used:** `functions/ai_key_drivers` (`AI.KEY_DRIVERS`) | `functions/ai_generate` (`AI.GENERATE`)

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create a shared dataset.

> `AI.KEY_DRIVERS` uses end-user credentials and needs no connection or model. `AI.GENERATE` routes to Gemini using a BigQuery connection — see the `setup` (Setup Reference) for details.

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

`AI.GENERATE` (Step 4) needs a BigQuery Cloud resource connection with the Vertex AI User role. This is idempotent — skip if you already created it in another notebook.

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
## Step 1 — Build the dataset

We use the public [NYC Citi Bike](https://console.cloud.google.com/marketplace/details/city-of-new-york/nyc-citi-bike) trips dataset and compare two periods of the same season: **April 2017 (interest)** vs **April 2016 (reference)**. The metric is total trip duration; the dimensions are user type, gender, and start station.

Materializing a compact slice keeps every downstream query fast.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_trips` AS
SELECT
  tripduration,
  usertype,
  gender,
  start_station_name,
  (EXTRACT(YEAR FROM starttime) = 2017) AS is_interest
FROM `bigquery-public-data.new_york_citibike.citibike_trips`
WHERE EXTRACT(MONTH FROM starttime) = 4
  AND EXTRACT(YEAR FROM starttime) IN (2016, 2017)
  AND tripduration IS NOT NULL
"""
client.query(query).result()

stats = client.query(f"""
  SELECT
    IF(is_interest, 'Interest (Apr 2017)', 'Reference (Apr 2016)') AS period,
    COUNT(*) AS trips,
    SUM(tripduration) AS total_duration
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_trips`
  GROUP BY is_interest
  ORDER BY is_interest
""").to_dataframe()
stats
```

---
## Step 2 — Confirm the headline shift

Before asking *why*, confirm *what* changed. A plain SQL aggregate shows the overall move in total trip duration between the reference and interest periods. This is the number we want `AI.KEY_DRIVERS` to explain.

```python
query = f"""
SELECT
  SUM(IF(NOT is_interest, tripduration, 0)) AS reference_total,
  SUM(IF(is_interest, tripduration, 0)) AS interest_total,
  SUM(IF(is_interest, tripduration, 0)) - SUM(IF(NOT is_interest, tripduration, 0)) AS difference,
  ROUND(SAFE_DIVIDE(
    SUM(IF(is_interest, tripduration, 0)) - SUM(IF(NOT is_interest, tripduration, 0)),
    SUM(IF(NOT is_interest, tripduration, 0))
  ), 3) AS relative_change
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_trips`
"""
client.query(query).to_dataframe()
```

---
## Step 3 — Explain the change with AI.KEY_DRIVERS

`AI.KEY_DRIVERS` decomposes the headline shift into the segments that drove it. Each row is a segment (`drivers`), with its `contribution` (absolute size of the move) and `unexpected_difference` (how much it deviated from the overall trend).

We persist the result so Step 4 can summarize it.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_drivers` AS
SELECT
  ARRAY_TO_STRING(drivers, ', ') AS segment,
  metric_interest,
  metric_reference,
  difference,
  relative_difference,
  unexpected_difference,
  apriori_support,
  contribution
FROM AI.KEY_DRIVERS(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_trips`,
  metric_col => 'tripduration',
  dimension_cols => ['usertype', 'gender', 'start_station_name'],
  interest_label_col => 'is_interest',
  top_k => 20
)
"""
client.query(query).result()

# Top drivers by absolute contribution
client.query(f"""
  SELECT segment, metric_interest, metric_reference, difference, contribution
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_drivers`
  ORDER BY contribution DESC
  LIMIT 10
""").to_dataframe()
```

### Segments defying the overall trend

The biggest absolute movers are often just the biggest segments. `unexpected_difference` highlights segments that changed *differently* than the population would predict — frequently the more actionable insight.

```python
client.query(f"""
  SELECT segment, difference, unexpected_difference, apriori_support
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_drivers`
  WHERE segment != 'all'
  ORDER BY ABS(unexpected_difference) DESC
  LIMIT 10
""").to_dataframe()
```

---
## Step 4 — Narrate the key drivers with AI.GENERATE

`AI.KEY_DRIVERS` gives us the numbers; `AI.GENERATE` turns them into a plain-language executive summary. We aggregate the top driver rows into a single prompt and ask Gemini to explain what drove the metric change.

```python
query = f"""
WITH drivers AS (
  SELECT STRING_AGG(
    CONCAT(
      segment,
      ': difference ', CAST(ROUND(difference) AS STRING),
      ', unexpected ', CAST(ROUND(unexpected_difference) AS STRING),
      ', support ', CAST(ROUND(apriori_support, 3) AS STRING)
    ),
    ' ||| '
    ORDER BY contribution DESC
    LIMIT 12
  ) AS driver_rows
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_drivers`
  WHERE segment != 'all'
)
SELECT (AI.GENERATE(
  CONCAT(
    'You are a data analyst. Total NYC Citi Bike trip duration changed between April 2016 (reference) and ',
    'April 2017 (interest). The following segments were identified as key drivers of that change by a ',
    'contribution analysis. Each entry lists the segment, its absolute difference in trip-duration seconds, ',
    'its unexpected difference (deviation from the overall trend), and its apriori support (segment size). ',
    'Write a concise executive summary: (1) the overall direction of the change, (2) which segments drove it most, ',
    '(3) any segments that moved differently than expected. Use plain business language. ',
    'Key drivers: ', driver_rows
  )
)).result AS summary
FROM drivers
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['summary'])
```

The summary grounds its narrative in the `AI.KEY_DRIVERS` output — naming the specific segments and quantifying their contribution, rather than guessing. This is the augmented-analytics pattern: a statistical function finds *what* drove the change, and a generative function explains it in language a stakeholder can act on.
