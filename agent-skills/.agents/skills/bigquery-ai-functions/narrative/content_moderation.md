# Content Moderation — BigQuery AI Functions

An end-to-end content moderation pipeline that composes five AI functions:

1. **Generate** sample social media posts with `AI.GENERATE_TABLE`
2. **Flag** posts needing review with `AI.IF` (with optional few-shot `examples` for improved accuracy)
3. **Classify** flagged posts by violation type with `AI.CLASSIFY`
4. **Score** severity of flagged posts with `AI.SCORE`
5. **Summarize** moderation results with `AI.GENERATE` (and alternatively with `AI.AGG`)

**What this demonstrates:**
- Using `AI.IF` as a binary filter step — efficiently gate expensive downstream processing
- Improving flagging accuracy with few-shot `examples` — teach the model your moderation standards
- Composing filter → classify → score → summarize in one pipeline
- Each function adds value: `AI.IF` reduces volume, `AI.CLASSIFY` categorizes, `AI.SCORE` prioritizes
- Comparing manual aggregation (`STRING_AGG` + `AI.GENERATE`) vs purpose-built `AI.AGG`

**Functions used:** `functions/ai_generate_table` (`AI.GENERATE_TABLE`) | `functions/ai_if` (`AI.IF`) | `functions/ai_classify` (`AI.CLASSIFY`) | `functions/ai_score` (`AI.SCORE`) | `functions/ai_generate` (`AI.GENERATE`) | `functions/ai_agg` (`AI.AGG`)

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create shared resources.

> This workflow uses `AI.GENERATE_TABLE` (requires a connection and remote model) and `AI.IF`, `AI.CLASSIFY`, `AI.SCORE`, `AI.GENERATE` (no model needed). See the `setup` (Setup Reference) for details.

```python
PROJECT_ID = 'statmike-mlops-349915'  # <-- Replace with your project ID
LOCATION = 'US'  # BigQuery dataset location
DATASET_ID = 'bq_ai_functions'  # Shared dataset across all notebooks
CONNECTION_ID = 'bq_ai_functions'  # Shared connection
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

```python
import subprocess as _sp, json as _json

# Create connection (idempotent)
_sp.run(['bq', 'mk', '--connection', '--location', LOCATION,
         '--connection_type', 'CLOUD_RESOURCE',
         '--project_id', PROJECT_ID, CONNECTION_ID],
        capture_output=True, text=True)

# Get service account and grant Vertex AI User role
r = _sp.run(['bq', 'show', '--connection', '--format=json',
             '--project_id', PROJECT_ID, '--location', LOCATION, CONNECTION_ID],
            capture_output=True, text=True, check=True)
sa = _json.loads(r.stdout)['cloudResource']['serviceAccountId']
_sp.run(['gcloud', 'projects', 'add-iam-policy-binding', PROJECT_ID,
         f'--member=serviceAccount:{sa}', '--role=roles/aiplatform.user', '--quiet'],
        capture_output=True, text=True)
print(f'Connection {CONNECTION_ID} ready (SA: {sa})')
```

```python
# Create remote Gemini model for AI.GENERATE_TABLE (idempotent)
client.query(f'''
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`
  REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (endpoint = \'gemini-2.5-flash\')
''').result()
print('Model gemini_flash ready')
```

---
## Step 1 — Generate sample posts with AI.GENERATE_TABLE

Generate 20 social media posts from seed topics — a realistic mix of clean content and problematic posts. Each seed row describes a post category and topic; `AI.GENERATE_TABLE` generates a username and post text for each one.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_mod_posts` AS
SELECT post_id, username, post_text
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT
    post_id,
    CONCAT(
      'Generate one realistic social media post. Category: ', category,
      '. Topic: ', topic,
      '. Write 1-2 sentences. Create a believable username.'
    ) AS prompt
   FROM UNNEST([
     STRUCT(1 AS post_id, 'clean' AS category, 'positive product review of electronics' AS topic),
     STRUCT(2, 'clean', 'travel experience in another country'),
     STRUCT(3, 'clean', 'cooking recipe tip'),
     STRUCT(4, 'clean', 'tech discussion about a new phone'),
     STRUCT(5, 'clean', 'fitness motivation'),
     STRUCT(6, 'clean', 'book recommendation'),
     STRUCT(7, 'clean', 'pet appreciation post'),
     STRUCT(8, 'clean', 'hobby sharing about painting'),
     STRUCT(9, 'clean', 'local restaurant review'),
     STRUCT(10, 'clean', 'gardening update'),
     STRUCT(11, 'clean', 'music discovery'),
     STRUCT(12, 'clean', 'weekend hiking recap'),
     STRUCT(13, 'problematic', 'spam with fake URLs and too-good-to-be-true offers'),
     STRUCT(14, 'problematic', 'mild harassment targeting appearance'),
     STRUCT(15, 'problematic', 'obvious health misinformation about vaccines'),
     STRUCT(16, 'problematic', 'engagement bait clickbait'),
     STRUCT(17, 'problematic', 'spam promoting a get-rich-quick scheme'),
     STRUCT(18, 'problematic', 'personal attack and insult'),
     STRUCT(19, 'problematic', 'conspiracy theory misinformation'),
     STRUCT(20, 'problematic', 'phishing attempt disguised as urgent account warning')
   ])),
  STRUCT('username STRING, post_text STRING' AS output_schema)
)
'''
client.query(query).result()

posts = client.query(f'''
  SELECT post_id, username, post_text
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_posts`
  ORDER BY post_id
''').to_dataframe()
print(f'Generated {len(posts)} posts')
posts.head(10)
```

---
## Step 2 — Flag posts with AI.IF

`AI.IF` evaluates a natural language condition and returns TRUE or FALSE. Use it as a binary filter to identify posts needing review — this gates the more expensive downstream classification and scoring steps.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_mod_flagged` AS
SELECT
  post_id,
  username,
  post_text,
  AI.IF(
    CONCAT(
      'This social media post contains problematic content such as spam, ',
      'harassment, hate speech, or misinformation: ',
      post_text
    )
  ) AS needs_review
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_posts`
'''
client.query(query).result()

flagged = client.query(f'''
  SELECT needs_review, COUNT(*) AS count
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_flagged`
  GROUP BY needs_review
''').to_dataframe()
print('AI.IF flagging results:')
for _, row in flagged.iterrows():
    label = 'Flagged for review' if row['needs_review'] else 'Clean'
    print(f'  {label}: {row["count"]} posts')
```

### Step 2b — Improve flagging with few-shot examples

`AI.IF` accepts an `examples` parameter — an `ARRAY<STRUCT<STRING, BOOL>>` that teaches the model your moderation standards with labeled examples. This can improve accuracy for borderline cases where the model might otherwise be too lenient or too aggressive.

Here we re-run the same flagging step with few-shot examples and compare the results.

```python
query = f'''
WITH baseline AS (
  SELECT post_id, needs_review AS baseline_flag
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_flagged`
),
few_shot AS (
  SELECT
    post_id,
    AI.IF(
      CONCAT(
        'This social media post contains problematic content such as spam, ',
        'harassment, hate speech, or misinformation: ',
        post_text
      ),
      examples => [
        STRUCT("Amazing deal!! Click here now to win FREE money!!!" AS input, TRUE AS output),
        STRUCT("Just had a great weekend hiking with friends", FALSE),
        STRUCT("You're so ugly, nobody wants to see your posts", TRUE),
        STRUCT("I disagree with this policy and here is why", FALSE),
        STRUCT("EXPOSED: the government is secretly poisoning our water supply!!!", TRUE),
        STRUCT("I love my new coffee maker, best purchase this year!", FALSE)
      ]
    ) AS fewshot_flag
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_posts`
)
SELECT
  COUNTIF(b.baseline_flag AND f.fewshot_flag) AS both_flagged,
  COUNTIF(b.baseline_flag AND NOT f.fewshot_flag) AS baseline_only,
  COUNTIF(NOT b.baseline_flag AND f.fewshot_flag) AS fewshot_only,
  COUNTIF(NOT b.baseline_flag AND NOT f.fewshot_flag) AS both_clean
FROM baseline b
JOIN few_shot f USING (post_id)
'''
comparison = client.query(query).to_dataframe()
print('Baseline vs few-shot flagging comparison:')
print(f'  Both flagged:     {comparison.iloc[0]["both_flagged"]}')
print(f'  Baseline only:    {comparison.iloc[0]["baseline_only"]}')
print(f'  Few-shot only:    {comparison.iloc[0]["fewshot_only"]}')
print(f'  Both clean:       {comparison.iloc[0]["both_clean"]}')
```

---
## Step 3 — Classify flagged posts with AI.CLASSIFY

`AI.CLASSIFY` categorizes each flagged post into a violation type. Only flagged posts are classified — `AI.IF` already filtered out the clean ones, saving API calls.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_mod_classified` AS
SELECT
  post_id,
  username,
  post_text,
  AI.CLASSIFY(
    post_text,
    ['harassment', 'spam', 'hate_speech', 'misinformation']
  ) AS violation_type
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_flagged`
WHERE needs_review = TRUE
'''
client.query(query).result()

classified = client.query(f'''
  SELECT violation_type, COUNT(*) AS count
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_classified`
  GROUP BY violation_type
  ORDER BY count DESC
''').to_dataframe()
print('Violation type distribution:')
for _, row in classified.iterrows():
    print(f'  {row["violation_type"]}: {row["count"]}')
```

---
## Step 4 — Score severity with AI.SCORE

`AI.SCORE` rates each flagged post on a 0–1 severity scale. Higher scores indicate more severe violations that need immediate attention.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_mod_scored` AS
SELECT
  c.post_id,
  c.username,
  c.post_text,
  c.violation_type,
  AI.SCORE(
    CONCAT(
      'Rate the severity of this content violation. ',
      'Score 0 for borderline/mild issues, 1 for severe violations ',
      'requiring immediate action: ',
      c.post_text
    )
  ) AS severity_score
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_classified` c
'''
client.query(query).result()

scored = client.query(f'''
  SELECT post_id, username, violation_type,
    ROUND(severity_score, 2) AS severity_score, post_text
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_scored`
  ORDER BY severity_score DESC
''').to_dataframe()
print('Flagged posts ranked by severity:')
scored
```

### Step 4b — Action items

Show the highest-severity posts that need immediate attention (severity > 0.7).

```python
query = f'''
SELECT post_id, username, violation_type,
  ROUND(severity_score, 2) AS severity_score, post_text
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_scored`
WHERE severity_score > 0.7
ORDER BY severity_score DESC
'''
urgent = client.query(query).to_dataframe()
print(f'{len(urgent)} posts need immediate attention:')
urgent
```

---
## Step 5 — Executive summary with AI.GENERATE

Aggregate all pipeline results and generate an executive summary of the moderation run.

```python
query = f'''
WITH stats AS (
  SELECT
    (SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_posts`) AS total_posts,
    (SELECT COUNTIF(needs_review) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_flagged`) AS flagged_count,
    (SELECT COUNTIF(NOT needs_review) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_flagged`) AS clean_count,
    (SELECT STRING_AGG(CONCAT(violation_type, ': ', CAST(cnt AS STRING)), ', ')
     FROM (SELECT violation_type, COUNT(*) AS cnt
           FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_classified`
           GROUP BY violation_type)) AS violation_breakdown,
    (SELECT ROUND(AVG(severity_score), 2) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_scored`) AS avg_severity,
    (SELECT COUNTIF(severity_score > 0.7) FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_scored`) AS urgent_count
)
SELECT (AI.GENERATE(
  CONCAT(
    'Write a brief executive summary (2-3 paragraphs) of this content moderation pipeline run. ',
    'Total posts: ', CAST(total_posts AS STRING),
    '. Flagged for review: ', CAST(flagged_count AS STRING),
    '. Clean: ', CAST(clean_count AS STRING),
    '. Violation breakdown: ', IFNULL(violation_breakdown, 'none'),
    '. Average severity: ', CAST(IFNULL(avg_severity, 0) AS STRING),
    '. Posts needing immediate action (severity > 0.7): ', CAST(IFNULL(urgent_count, 0) AS STRING),
    '. End with a one-sentence takeaway.'
  )
)).result AS executive_summary
FROM stats
'''
df = client.query(query).to_dataframe()
print(df.iloc[0]['executive_summary'])
```

### Alternative — Summarize by violation type with AI.AGG

`AI.AGG` can summarize flagged posts per violation type directly — no manual `STRING_AGG` or stats CTEs needed. It automatically batches the data and returns one summary per group.

```python
query = f'''
SELECT
  violation_type,
  AI.AGG(
    TO_JSON_STRING(STRUCT(username, post_text, ROUND(severity_score, 2) AS severity)),
    'Summarize these flagged posts: what patterns do you see, how severe are the violations, and what moderation action would you recommend?'
  ) AS violation_summary
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_mod_scored`
GROUP BY violation_type
'''
df_agg = client.query(query).to_dataframe()
for _, row in df_agg.iterrows():
    print(f'=== {row["violation_type"]} ===')
    print(row['violation_summary'])
    print()
```
