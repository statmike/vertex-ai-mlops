# Metric Diagnostics — BigQuery AI Functions

An end-to-end "why did my metric move?" pipeline:

1. **Build** a dataset with an interest period and a reference period
2. **Confirm** the headline shift with a plain SQL aggregate
3. **Explain** the change with `AI.KEY_DRIVERS` — find the segments that drove it
4. **Project** what each segment should have done with `AI.PREDICT` — a counterfactual built from reference-period behavior
5. **Narrate** the findings in plain language with `AI.GENERATE`

**What this demonstrates:**
- Root-cause analysis of a metric change entirely in BigQuery SQL
- Guarding a `SUM` metric against outlier records, and checking that dimension encodings are stable across the two periods, before trusting any decomposition
- Key driver / contribution analysis with `AI.KEY_DRIVERS` (no model, no connection)
- Ranking segments by absolute `contribution` and by `unexpected_difference`
- Zero-training tabular regression with `AI.PREDICT` (TabFM) as a per-segment counterfactual
- Two independent notions of "unexpected": statistical deviation and learned projection residual
- Composing augmented analytics with generative AI for an executive summary

**Functions used:** `functions/ai_key_drivers` (`AI.KEY_DRIVERS`) | `functions/ai_predict` (`AI.PREDICT`) | `functions/ai_generate` (`AI.GENERATE`)

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create a shared dataset.

> `AI.KEY_DRIVERS` and `AI.PREDICT` use end-user credentials and need no connection or model. `AI.GENERATE` routes to Gemini using a BigQuery connection — see the `setup` (Setup Reference) for details.

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

`AI.GENERATE` (Step 5) needs a BigQuery Cloud resource connection with the Vertex AI User role. This is idempotent — skip if you already created it in another notebook.

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

**Guard the metric before you analyze it.** Citi Bike records a bike that is never returned as one enormous trip — the raw feed contains April trips lasting weeks. A `SUM` metric has no defense against that: a handful of such records can carry a double-digit share of the total and land at the top of every ranking downstream, where they read as changed rider behavior instead of missing hardware. The `tripduration BETWEEN 60 AND 86400` bound keeps trips from one minute to one day and drops the rest; the cell below prints how many records that removes and how much of the metric they were carrying, so the size of the problem is visible rather than assumed. Any sum-based diagnostic needs an equivalent bound chosen from the domain, not from the data.

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
  -- Guard: 1 minute to 1 day. Unreturned bikes are logged as multi-week trips.
  AND tripduration BETWEEN 60 AND 86400
"""
client.query(query).result()

# What the duration guard removed
guard = client.query(f"""
  SELECT
    COUNTIF(NOT keep) AS trips_dropped,
    ROUND(SAFE_DIVIDE(COUNTIF(NOT keep), COUNT(*)), 6) AS share_of_trips_dropped,
    SUM(IF(keep, 0, tripduration)) AS seconds_dropped,
    ROUND(SAFE_DIVIDE(SUM(IF(keep, 0, tripduration)), SUM(tripduration)), 4) AS share_of_metric_dropped
  FROM (
    SELECT tripduration, tripduration BETWEEN 60 AND 86400 AS keep
    FROM `bigquery-public-data.new_york_citibike.citibike_trips`
    WHERE EXTRACT(MONTH FROM starttime) = 4
      AND EXTRACT(YEAR FROM starttime) IN (2016, 2017)
      AND tripduration IS NOT NULL
  )
""").to_dataframe().iloc[0]
print(f"Duration guard dropped {int(guard.trips_dropped):,} trips "
      f"({guard.share_of_trips_dropped:.4%} of records) "
      f"carrying {guard.share_of_metric_dropped:.2%} of the raw metric")

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

### Do the dimensions mean the same thing in both periods?

A driver analysis compares two periods through a set of dimension values, and it assumes those values are coded the same way on both sides. When a field's encoding changes between periods, segments appear and disappear, and the decomposition attributes the *bookkeeping* change to behavior. This check runs before the decomposition, not after, because it decides how the output can be read.

`interest_over_reference` is the tell. Overall trip volume grew by roughly a third, so a stable bucket lands near that. A `NULL` means the bucket had no reference-period trips at all, and a ratio far above the population's means riders were reclassified into it.

```python
stability = client.query(f"""
  SELECT
    usertype,
    gender,
    COUNTIF(NOT is_interest) AS reference_trips,
    COUNTIF(is_interest) AS interest_trips,
    ROUND(SAFE_DIVIDE(COUNTIF(is_interest), COUNTIF(NOT is_interest)), 2) AS interest_over_reference
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_trips`
  GROUP BY usertype, gender
  ORDER BY usertype, gender
""").to_dataframe()

new_buckets = stability.loc[stability['reference_trips'] == 0, ['usertype', 'gender']]
print('usertype x gender buckets with zero reference-period trips '
      '(new in the interest period, not growth):')
print('  ' + ('\n  '.join(f'{u} / {g}' for u, g in new_buckets.itertuples(index=False))
              if len(new_buckets) else 'none'))
stability
```

---
## Step 3 — Explain the change with AI.KEY_DRIVERS

`AI.KEY_DRIVERS` decomposes the headline shift into the segments that drove it. Each row is a segment (`drivers`), with its `contribution` (absolute size of the move) and `unexpected_difference` (how much it deviated from the overall trend).

One of those rows is not a segment: `AI.KEY_DRIVERS` also emits an `all` row carrying the population-level move. That row is a free cross-check — its `difference` should equal the `difference` Step 2 computed in plain SQL — and it is excluded from the segment rankings that follow.

We persist the result so Step 5 can summarize it.

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

Read it next to `metric_reference`. A segment whose reference value is `0` did not exist in the reference period at all, so its entire interest-period metric registers as unexpected. Those rows rank on encoding, not behavior — which is exactly what the stability check above predicted for the `Customer` gender buckets.

```python
client.query(f"""
  SELECT segment, metric_reference, difference, unexpected_difference, apriori_support
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_drivers`
  WHERE segment != 'all'   -- the population row, not a segment
  ORDER BY ABS(unexpected_difference) DESC
  LIMIT 10
""").to_dataframe()
```

---
## Step 4 — Project the metric per segment with AI.PREDICT

`AI.KEY_DRIVERS` explains the past: it decomposes a move that already happened. `AI.PREDICT` asks a different question — *what should the interest period have looked like if reference-period behavior had held?* The gap between that projection and the actual number is a second, independent kind of "unexpected".

`AI.PREDICT` runs the built-in TabFM tabular foundation model. There is no `CREATE MODEL`, no connection, and no training job: the training rows travel with the query as in-context examples. That design sets the ground rule for this step — **the training input has to stay small.** The observed ceiling is low and undocumented: roughly 10,000 training rows fails with `Resources exceeded ... allotted memory`, 8,000 succeeds, and about 5,000 is the safe budget on on-demand slots (see `functions/ai_predict` (`AI.PREDICT`)). The trip table holds millions of rows, so we first roll it up to one row per segment per period, keeping only segments that appear in both periods with enough volume to model. The cell below prints the resulting segment count — the training input is the reference-period half of it, and it needs to land comfortably under that budget.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_segments` AS
WITH segments AS (
  SELECT
    usertype,
    gender,
    start_station_name,
    is_interest,
    COUNT(*) AS trips,
    SUM(tripduration) AS total_duration
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_trips`
  GROUP BY usertype, gender, start_station_name, is_interest
),
comparable AS (
  -- Only segments present in BOTH periods, with enough trips to be worth modeling
  SELECT usertype, gender, start_station_name
  FROM segments
  GROUP BY usertype, gender, start_station_name
  HAVING COUNT(DISTINCT is_interest) = 2 AND MIN(trips) >= 50
)
SELECT s.*
FROM segments AS s
JOIN comparable AS c
  ON s.usertype = c.usertype
 AND s.gender = c.gender
 AND s.start_station_name = c.start_station_name
"""
client.query(query).result()

client.query(f"""
  SELECT
    IF(is_interest, 'Interest (Apr 2017)', 'Reference (Apr 2016)') AS period,
    COUNT(*) AS segments,
    SUM(trips) AS trips,
    SUM(total_duration) AS total_duration
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_segments`
  GROUP BY is_interest
  ORDER BY is_interest
""").to_dataframe()
```

### Project the interest period from reference-period behavior

The projection trains on the **reference** rows and predicts on the **interest** rows:

- **Features:** `usertype`, `gender`, `start_station_name`, and `trips` — four columns, well inside the documented 20-feature limit. `trips` is what makes this a counterfactual instead of an echo: the prediction row carries the *April 2017* ride volume, so the model answers "given this segment at this volume, what total duration would April 2016 behavior imply?" Without it, a segment's reference and interest rows would be identical and the projection would simply repeat last year's number.
- **Label:** `total_duration`. It is `INT64`, so `AI.PREDICT` runs a regression and returns `predicted_total_duration`. A `STRING` or `BOOL` label would trigger classification instead — the task is chosen by the label's type, not by an argument. That cuts both ways: a categorical encoded as `INT64` (a 0/1 flag, a 1–5 rating) is silently treated as regression and comes back as fractions with no probabilities, so cast those to `STRING` before predicting.
- **Types:** features must be `STRING`, `BOOL`, `INT64`, `FLOAT64`, `NUMERIC` or `BIGNUMERIC`. Step 1 already reduced `starttime` to a boolean period flag, which is why there is no timestamp column here to trip over.
- **Deliberately absent from the prediction input:** the actual `total_duration`. The prediction input is allowed to carry extra columns, but handing the model the answer it is predicting is a risk with no upside — the actuals are joined back afterward on the segment keys.
- **Which rows come back:** the returned passthrough columns are the *prediction* relation's rows, one per prediction row. The reference page says they come from the training table; the observed behavior — and Google's own worked examples — say otherwise, and this notebook depends on the behavior. It is why `p.trips` and the join keys in the queries below are April 2017 values, and why joining `p` to the interest-period segments is correct rather than backwards. See `functions/ai_predict` (`AI.PREDICT`) for the discrepancy.

`AI.PREDICT` is in Preview and takes tens of seconds per call regardless of input size. Materializing the result lets the ranking below and the narration in Step 5 both read it without paying for inference twice. Its output is also not reproducible run to run, which is a second reason to materialize rather than re-issue the call.

```python
query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_projection` AS
SELECT *
FROM AI.PREDICT(
  -- Training data: reference period (April 2016) behavior
  (SELECT usertype, gender, start_station_name, trips, total_duration
   FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_segments`
   WHERE NOT is_interest),
  -- Prediction data: the same segments at their interest period (April 2017) volumes
  (SELECT usertype, gender, start_station_name, trips
   FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_segments`
   WHERE is_interest),
  label_col => 'total_duration'
)
"""
client.query(query).result()

# Portfolio view: reference, projection, actual — plus a naive volume-scaled baseline
portfolio = client.query(f"""
  SELECT
    COUNT(*) AS segments,
    SUM(r.total_duration) AS reference_total,
    CAST(ROUND(SUM(p.predicted_total_duration)) AS INT64) AS projected_total,
    SUM(a.total_duration) AS actual_total,
    SUM(CAST(ROUND(a.trips * SAFE_DIVIDE(r.total_duration, r.trips)) AS INT64)) AS volume_scaled_total,
    COUNTIF(a.total_duration < p.predicted_total_duration) AS segments_below_projection,
    CAST(ROUND(SUM(GREATEST(a.total_duration - p.predicted_total_duration, 0))) AS INT64) AS total_overshoot,
    CAST(ROUND(SUM(LEAST(a.total_duration - p.predicted_total_duration, 0))) AS INT64) AS total_shortfall
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_projection` AS p
  JOIN `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_segments` AS a
    ON a.is_interest
   AND a.usertype = p.usertype
   AND a.gender = p.gender
   AND a.start_station_name = p.start_station_name
  JOIN `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_segments` AS r
    ON NOT r.is_interest
   AND r.usertype = p.usertype
   AND r.gender = p.gender
   AND r.start_station_name = p.start_station_name
""").to_dataframe()

f = portfolio.iloc[0]
print(f"Projection tracks volume, not last year: projected {f.projected_total:,} vs "
      f"volume-scaled {f.volume_scaled_total:,} vs reference {f.reference_total:,}")
print(f"Segments below projection: {f.segments_below_projection:,} of {f.segments:,} "
      f"({f.segments_below_projection / f.segments:.0%})")
print(f"Aggregate gap: actual - projected = {f.actual_total - f.projected_total:,} s "
      f"({(f.actual_total - f.projected_total) / f.projected_total:+.1%})")
print(f"  broad shortfall across the below-projection segments: {f.total_shortfall:,} s")
print(f"  concentrated overshoot across the above-projection segments: +{f.total_overshoot:,} s")
portfolio
```

`reference_total` is what these segments recorded in April 2016, `projected_total` is what `AI.PREDICT` expects from April 2017 volumes under April 2016 behavior, and `actual_total` is what April 2017 actually recorded. `volume_scaled_total` is the naive alternative — each segment's reference seconds-per-trip multiplied by its interest-period trip count — and it is the sanity check on the whole step: a `projected_total` that lands on `reference_total` rather than tracking volume means the model is repeating last year instead of projecting, and the residuals below would carry no information.

`segments_below_projection` is the shape of the result, and it deserves reading rather than skipping. Most of the segments come in *under* their projection, and the portfolio as a whole falls a few percent short — riders took more trips in April 2017 but each trip was a little shorter, so scaling last year's seconds-per-trip by this year's volume overshoots almost everywhere. The printed split makes the two pictures reconcile: a broad negative shortfall spread over the majority of segments, against a smaller positive overshoot concentrated in a few. The ranking below is ordered by *absolute* residual precisely so both tails appear in it, instead of showing only the segments that ran long.

### Segments that missed their projection

The residual is `actual_total - projected_total`: negative where a segment delivered less duration than its volume implied, positive where it delivered more. Ranking on `ABS(residual)` shows both directions.

`max_trip_share` is the guard from Step 1 earning its keep — the longest single trip in the segment as a fraction of the segment's actual total. On a sum-based metric this column is the difference between a finding and an artifact: if it is a few percent, the residual describes many riders, and if it approaches 1 the residual is one record. Carry a column like it into any residual table you build.

```python
client.query(f"""
  WITH peaks AS (
    -- Longest single trip per interest-period segment: the artifact detector
    SELECT usertype, gender, start_station_name, MAX(tripduration) AS max_trip
    FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_trips`
    WHERE is_interest
    GROUP BY usertype, gender, start_station_name
  )
  SELECT
    p.usertype,
    p.gender,
    p.start_station_name,
    r.trips AS reference_trips,
    p.trips AS interest_trips,
    r.total_duration AS reference_total,
    CAST(ROUND(p.predicted_total_duration) AS INT64) AS projected_total,
    a.total_duration AS actual_total,
    CAST(ROUND(a.total_duration - p.predicted_total_duration) AS INT64) AS residual,
    ROUND(SAFE_DIVIDE(k.max_trip, a.total_duration), 4) AS max_trip_share
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_projection` AS p
  JOIN `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_segments` AS a
    ON a.is_interest
   AND a.usertype = p.usertype
   AND a.gender = p.gender
   AND a.start_station_name = p.start_station_name
  JOIN `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_segments` AS r
    ON NOT r.is_interest
   AND r.usertype = p.usertype
   AND r.gender = p.gender
   AND r.start_station_name = p.start_station_name
  JOIN peaks AS k
    ON k.usertype = p.usertype
   AND k.gender = p.gender
   AND k.start_station_name = p.start_station_name
  ORDER BY ABS(a.total_duration - p.predicted_total_duration) DESC
  LIMIT 10
""").to_dataframe()
```

`residual` is a *learned* expectation error: actual minus what a model of reference-period behavior expects at interest-period volume. `unexpected_difference` from Step 3 is a *statistical* expectation error: how far a segment moved from what the population-wide trend implied for it.

The two rankings disagree on purpose. A segment can be unremarkable to `AI.KEY_DRIVERS` — it moved with everyone else — and still miss its projection badly because its riders changed how long they ride. Reading both separates "this segment is large" from "this segment behaves differently now", and Step 5 hands both to the narrator.

Before drawing that behavioral reading, though, check `max_trip_share` on every row you plan to act on. Only a residual backed by a small `max_trip_share` is a statement about riders; a large one is a statement about a single record, and no amount of modeling downstream will fix it.

---
## Step 5 — Narrate the findings with AI.GENERATE

`AI.KEY_DRIVERS` gives us the contributions and `AI.PREDICT` gives us the projection residuals; `AI.GENERATE` turns both into a plain-language executive summary. We aggregate the top driver rows and the largest residuals into a single prompt and ask Gemini to explain what drove the metric change.

```python
query = f"""
WITH drivers AS (
  SELECT STRING_AGG(
    CONCAT(
      segment,
      ': difference ', CAST(ROUND(difference) AS STRING),
      ', unexpected ', CAST(ROUND(unexpected_difference) AS STRING),
      ', reference ', CAST(ROUND(metric_reference) AS STRING),
      ', support ', CAST(ROUND(apriori_support, 3) AS STRING)
    ),
    ' ||| '
    ORDER BY contribution DESC
    LIMIT 12
  ) AS driver_rows
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_drivers`
  WHERE segment != 'all'
),
projections AS (
  SELECT STRING_AGG(
    CONCAT(
      usertype, ' / ', gender, ' / ', start_station_name,
      ': projected ', CAST(projected_total AS STRING),
      ', actual ', CAST(actual_total AS STRING),
      ', residual ', CAST(residual AS STRING)
    ),
    ' ||| '
    ORDER BY ABS(residual) DESC
    LIMIT 8
  ) AS projection_rows
  FROM (
    SELECT
      p.usertype,
      p.gender,
      p.start_station_name,
      CAST(ROUND(p.predicted_total_duration) AS INT64) AS projected_total,
      a.total_duration AS actual_total,
      CAST(ROUND(a.total_duration - p.predicted_total_duration) AS INT64) AS residual
    FROM `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_projection` AS p
    JOIN `{PROJECT_ID}.{DATASET_ID}.workflow_metricdiag_segments` AS a
      ON a.is_interest
     AND a.usertype = p.usertype
     AND a.gender = p.gender
     AND a.start_station_name = p.start_station_name
  )
)
SELECT (AI.GENERATE(
  CONCAT(
    'You are a data analyst. Total NYC Citi Bike trip duration changed between April 2016 (reference) and ',
    'April 2017 (interest). The following segments were identified as key drivers of that change by a ',
    'contribution analysis. Each entry lists the segment, its absolute difference in trip-duration seconds, ',
    'its unexpected difference (deviation from the overall trend), its reference-period metric value, and ',
    'its apriori support (segment size). ',
    'A second list gives per-segment projections: the total trip duration the April 2017 ride volume would ',
    'have produced under April 2016 behavior, the actual April 2017 total, and the residual (actual minus ',
    'projected). ',
    'Write a concise executive summary: (1) the overall direction of the change, (2) which segments drove it most, ',
    '(3) any segments that moved differently than expected, (4) where the actual result diverged most from its ',
    'projection. Use plain business language. ',
    'Grounding rules: quote the supplied figures verbatim whenever you name a segment, and do not state any ',
    'ratio, multiple or percentage that is not given below. A segment whose reference value is 0 did not exist ',
    'in the reference period, so describe it as newly coded rather than as growth. ',
    'Key drivers: ', driver_rows,
    ' ||| Projection residuals: ', projection_rows
  )
)).result AS summary
FROM drivers, projections
"""
df = client.query(query).to_dataframe()
print(df.iloc[0]['summary'])
```

The prompt hands the model the driver rows and the residual rows as text and asks for prose, so the grounding rules in it are doing real work: quote the supplied figures, invent no ratios that were not given, and describe a zero reference value as a new encoding rather than as growth. Without those rules a summary of this shape reliably produces a plausible multiple or percentage that no input row supports.

Treat the result accordingly — it is a narrative layer, not a source of numbers. Every figure a stakeholder acts on should be joined back from `workflow_metricdiag_drivers` and `workflow_metricdiag_projection`, where it can be recomputed. That is the augmented-analytics division of labor: statistical functions find *what* drove the change and *what was expected instead*, and a generative function turns the rows already computed into language a stakeholder can act on.
