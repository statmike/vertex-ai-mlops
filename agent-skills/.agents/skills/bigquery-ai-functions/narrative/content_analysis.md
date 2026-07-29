# Content Analysis Pipeline — BigQuery AI Functions

An end-to-end content analysis pipeline that composes four AI functions together:

1. **Generate** sample product reviews with `AI.GENERATE_TABLE`
2. **Classify** each review by topic with `AI.CLASSIFY`
3. **Score** each review for urgency with `AI.SCORE`
4. **Summarize** findings with `AI.GENERATE` (and alternatively with `AI.AGG`)

**What this demonstrates:**
- Composing multiple AI functions in a single analytical pipeline
- Using `AI.GENERATE_TABLE` to create realistic sample data
- Combining managed functions (`AI.CLASSIFY`, `AI.SCORE`) with generation functions
- Aggregating AI-enriched data into executive summaries
- Comparing manual aggregation (`STRING_AGG` + `AI.GENERATE`) vs purpose-built `AI.AGG`

**Functions used:** `functions/ai_generate_table` (`AI.GENERATE_TABLE`) | `functions/ai_classify` (`AI.CLASSIFY`) | `functions/ai_score` (`AI.SCORE`) | `functions/ai_generate` (`AI.GENERATE`) | `functions/ai_agg` (`AI.AGG`)

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create shared resources.

> This workflow requires a connection and a remote model for `AI.GENERATE_TABLE`. See the `setup` (Setup Reference) for details.

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
# Create remote Gemini model (idempotent)
client.query(f'''
CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`
  REMOTE WITH CONNECTION `{PROJECT_ID}.{LOCATION}.{CONNECTION_ID}`
  OPTIONS (endpoint = 'gemini-2.5-flash')
''').result()
print('Model gemini_flash ready')
```

---
## Step 1 — Generate sample reviews with AI.GENERATE_TABLE

Use `AI.GENERATE_TABLE` to create realistic product reviews. Each input row gets one output row — so we provide multiple product categories to generate a diverse set of reviews.

```python
output_schema = """review_text STRING OPTIONS(description = "The full review text written by the customer"),
       product_name STRING OPTIONS(description = "Specific product name mentioned or inferred"),
       star_rating INT64 OPTIONS(description = "Star rating from 1 to 5")"""

query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_content_reviews` AS
SELECT review_text, product_name, star_rating
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT CONCAT(
     'Write a realistic customer review for a ', product_type,
     ' product. Make some reviews very positive, some negative, and some mixed. ',
     'Vary the length and writing style.'
   ) AS prompt
   FROM UNNEST([
     'wireless headphones', 'laptop stand', 'USB-C hub', 'mechanical keyboard',
     'portable monitor', 'webcam', 'desk lamp', 'ergonomic mouse',
     'noise machine', 'cable management kit', 'monitor arm', 'standing desk mat'
   ]) AS product_type),
  STRUCT(
    """{output_schema}""" AS output_schema
  )
)
'''
client.query(query).result()

reviews = client.query(
    f'SELECT product_name, star_rating, LEFT(review_text, 80) AS review_preview FROM `{PROJECT_ID}.{DATASET_ID}.workflow_content_reviews`'
).to_dataframe()
print(f'{len(reviews)} reviews generated')
reviews
```

---
## Step 2 — Classify reviews by topic with AI.CLASSIFY

Use `AI.CLASSIFY` to categorize each review into a topic. BigQuery auto-optimizes the classification prompt.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_content_classified` AS
SELECT
  review_text,
  product_name,
  star_rating,
  AI.CLASSIFY(
    review_text,
    [('quality', 'About product build quality, durability, or materials'),
     ('usability', 'About ease of use, setup, or user experience'),
     ('value', 'About price, value for money, or cost-effectiveness'),
     ('support', 'About customer service, warranty, or returns'),
     ('features', 'About specific product features or capabilities')]
  ) AS topic
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_content_reviews`
'''
client.query(query).result()

# Show analytical insight: topic × star rating cross-tabulation
classified = client.query(
    f'SELECT topic, star_rating, product_name FROM `{PROJECT_ID}.{DATASET_ID}.workflow_content_classified`'
).to_dataframe()
print('Topic distribution by star rating:')
cross_tab = classified.groupby('topic')['star_rating'].agg(['count', 'mean']).round(1)
cross_tab.columns = ['reviews', 'avg_stars']
print(cross_tab.sort_values('reviews', ascending=False).to_string())
print(f'\nProducts by topic:')
for topic in classified['topic'].unique():
    products = classified[classified['topic'] == topic]['product_name'].tolist()
    print(f'  {topic}: {", ".join(products)}')
```

---
## Step 3 — Score reviews for urgency with AI.SCORE

Use `AI.SCORE` to rate each review's urgency on a 1–10 scale. This helps prioritize which reviews need immediate attention — surfacing product issues that require action.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_content_scored` AS
SELECT
  review_text,
  product_name,
  star_rating,
  topic,
  AI.SCORE(CONCAT(
    'Rate the urgency of this customer review on a scale of 1 to 10, ',
    'where 1 is no action needed and 10 is requires immediate attention ',
    '(e.g. safety issue, defective product, very unhappy customer): ',
    review_text
  )) AS urgency
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_content_classified`
'''
client.query(query).result()

scored = client.query(
    f'SELECT product_name, star_rating, topic, urgency FROM `{PROJECT_ID}.{DATASET_ID}.workflow_content_scored` ORDER BY urgency DESC'
).to_dataframe()

# Urgency distribution
print('Urgency breakdown:')
scored['urgency_level'] = scored['urgency'].apply(
    lambda x: 'HIGH (7-10)' if x >= 7 else ('MEDIUM (4-6)' if x >= 4 else 'LOW (1-3)')
)
print(scored['urgency_level'].value_counts().to_string())
print(f'\nAll reviews ranked by urgency:')
scored[['product_name', 'star_rating', 'topic', 'urgency']]
```

### Action items — high urgency reviews

These reviews scored 5+ urgency and may need immediate attention from product teams.

```python
action_items = client.query(f'''
  SELECT product_name, star_rating, topic, urgency, review_text
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_content_scored`
  WHERE urgency >= 5
  ORDER BY urgency DESC
''').to_dataframe()

if len(action_items) == 0:
    print('No high-urgency reviews — all products are in good shape!')
else:
    print(f'{len(action_items)} reviews need attention:\n')
    for _, row in action_items.iterrows():
        print(f'[Urgency {row["urgency"]:.0f}] {row["product_name"]} ({row["topic"]}, {row["star_rating"]} stars)')
        print(f'  {row["review_text"][:200]}')
        print()
```

---
## Step 4 — Summarize findings with AI.GENERATE

Aggregate all the classified and scored reviews, then use `AI.GENERATE` to produce an executive summary of the findings.

```python
query = f'''
WITH summary_data AS (
  SELECT
    COUNT(*) AS total_reviews,
    ROUND(AVG(star_rating), 1) AS avg_stars,
    ROUND(AVG(urgency), 1) AS avg_urgency,
    COUNTIF(urgency >= 7) AS high_urgency_count,
    STRING_AGG(
      CONCAT(product_name, ' (', topic, ', ', star_rating, ' stars, urgency ', CAST(urgency AS STRING), '): ', review_text),
      ' | '
    ) AS all_reviews
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_content_scored`
)
SELECT (AI.GENERATE(
  CONCAT(
    'You are a product analytics manager. Analyze these customer reviews and provide an executive summary. ',
    'Include: (1) overall sentiment overview, (2) top issues by topic, (3) urgent items needing immediate action, ',
    '(4) recommendations for product teams. ',
    'Stats: ', CAST(s.total_reviews AS STRING), ' reviews, ',
    'avg rating ', CAST(s.avg_stars AS STRING), '/5, ',
    'avg urgency ', CAST(s.avg_urgency AS STRING), '/10, ',
    CAST(s.high_urgency_count AS STRING), ' high-urgency reviews. ',
    'Reviews: ', s.all_reviews
  )
)).result AS executive_summary
FROM summary_data s
'''
df = client.query(query).to_dataframe()
print(df.iloc[0]['executive_summary'])
```

### Alternative — Summarize with AI.AGG

`AI.AGG` is purpose-built for this task: it aggregates rows into a summary per group with automatic batching. Compare how much simpler this is than the manual `STRING_AGG` + `AI.GENERATE` approach above — no need to manually concatenate all reviews into a single prompt.

```python
query = f'''
SELECT
  topic,
  AI.AGG(
    TO_JSON_STRING(STRUCT(product_name, star_rating, urgency, review_text)),
    'You are a product analytics manager. Summarize the key themes, sentiment, and any urgent issues for this topic group.'
  ) AS topic_summary
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_content_scored`
GROUP BY topic
'''
df_agg = client.query(query).to_dataframe()
for _, row in df_agg.iterrows():
    print(f'=== {row["topic"]} ===')
    print(row['topic_summary'])
    print()
```
