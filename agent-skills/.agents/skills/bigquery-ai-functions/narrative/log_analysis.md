# Log Analysis — BigQuery AI Functions

An end-to-end log analysis pipeline that composes four AI functions to analyze application support tickets:

1. **Generate** sample support tickets with `AI.GENERATE_TABLE`
2. **Classify** each ticket by category with `AI.CLASSIFY`
3. **Score** each ticket for priority with `AI.SCORE`
4. **Summarize** patterns by category with `AI.AGG` (the star of this workflow)

**What this demonstrates:**
- `AI.AGG` as the natural aggregation function — summarize groups of tickets without manual batching
- Composing classify → score → aggregate in a single analytical pipeline
- Using `TO_JSON_STRING` to pass structured data to `AI.AGG`
- Comparing `AI.AGG` with the manual `STRING_AGG` + `AI.GENERATE` approach

**Functions used:** `functions/ai_generate_table` (`AI.GENERATE_TABLE`) | `functions/ai_classify` (`AI.CLASSIFY`) | `functions/ai_score` (`AI.SCORE`) | `functions/ai_agg` (`AI.AGG`)

**Prerequisites:** `setup` (Setup guide) | `RESOURCES.md` (Function reference)

---
## Setup

Set your project and location, authenticate, and create shared resources.

> This workflow uses `AI.GENERATE_TABLE` (requires a connection and remote model) and `AI.CLASSIFY`, `AI.SCORE`, `AI.AGG` (no model needed). See the `setup` (Setup Reference) for details.

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
  OPTIONS (endpoint = 'gemini-2.5-flash')
''').result()
print('Model gemini_flash ready')
```

---
## Step 1 — Generate sample support tickets with AI.GENERATE_TABLE

Generate 30 realistic IT support tickets from seed categories. Each ticket has a user, description, resolution, and timestamps — mimicking real helpdesk data.

```python
output_schema = """user_name STRING OPTIONS(description = "The employee who submitted the ticket"),
       ticket_description STRING OPTIONS(description = "Detailed description of the issue"),
       resolution STRING OPTIONS(description = "How the issue was resolved, or current status if unresolved"),
       resolution_hours FLOAT64 OPTIONS(description = "Hours from ticket creation to resolution, or NULL if unresolved")"""

query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_log_tickets` AS
SELECT ticket_id, user_name, ticket_description, resolution, resolution_hours
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT
    ticket_id,
    CONCAT(
      'Generate one realistic IT support ticket. Category: ', category,
      '. Scenario: ', scenario,
      '. Write a detailed description (2-3 sentences) and a resolution. ',
      'Create a believable employee name. ',
      'Set resolution_hours between 0.5 and 48, or null if unresolved.'
    ) AS prompt
   FROM UNNEST([
     STRUCT(1 AS ticket_id, 'access' AS category, 'new employee needs VPN access' AS scenario),
     STRUCT(2, 'access', 'password reset for locked account'),
     STRUCT(3, 'access', 'MFA token not working after phone upgrade'),
     STRUCT(4, 'access', 'shared drive permissions denied'),
     STRUCT(5, 'access', 'SSO login loop on new laptop'),
     STRUCT(6, 'hardware', 'laptop screen flickering intermittently'),
     STRUCT(7, 'hardware', 'keyboard keys sticking after coffee spill'),
     STRUCT(8, 'hardware', 'docking station not detecting external monitors'),
     STRUCT(9, 'hardware', 'battery draining in under 2 hours'),
     STRUCT(10, 'hardware', 'trackpad unresponsive after OS update'),
     STRUCT(11, 'software', 'Slack keeps crashing on startup'),
     STRUCT(12, 'software', 'Excel macro broken after Office update'),
     STRUCT(13, 'software', 'VPN disconnects every 30 minutes'),
     STRUCT(14, 'software', 'Docker containers failing to build'),
     STRUCT(15, 'software', 'IDE license expired and blocking work'),
     STRUCT(16, 'network', 'Wi-Fi drops in conference room B'),
     STRUCT(17, 'network', 'cannot reach internal wiki from remote'),
     STRUCT(18, 'network', 'latency spikes during video calls'),
     STRUCT(19, 'network', 'DNS resolution failing for staging servers'),
     STRUCT(20, 'network', 'printer not found on office network'),
     STRUCT(21, 'security', 'suspicious login from unknown location'),
     STRUCT(22, 'security', 'phishing email reported by multiple users'),
     STRUCT(23, 'security', 'unauthorized app installed on work laptop'),
     STRUCT(24, 'security', 'sensitive file shared externally by accident'),
     STRUCT(25, 'security', 'antivirus flagging a development tool'),
     STRUCT(26, 'data', 'accidental deletion of production database rows'),
     STRUCT(27, 'data', 'ETL pipeline failing with schema mismatch'),
     STRUCT(28, 'data', 'dashboard showing stale data after migration'),
     STRUCT(29, 'data', 'backup restoration needed for corrupted file'),
     STRUCT(30, 'data', 'BigQuery query hitting quota limits')
   ])),
  STRUCT(
    \"\"\"{output_schema}\"\"\" AS output_schema
  )
)
'''
client.query(query).result()

tickets = client.query(
    f'SELECT ticket_id, user_name, LEFT(ticket_description, 80) AS description_preview, resolution_hours FROM `{PROJECT_ID}.{DATASET_ID}.workflow_log_tickets` ORDER BY ticket_id'
).to_dataframe()
print(f'{len(tickets)} tickets generated')
tickets.head(10)
```

---
## Step 2 — Classify tickets by category with AI.CLASSIFY

Use `AI.CLASSIFY` to categorize each ticket. The generated data has known categories, but in a real scenario you'd classify unstructured ticket text into operational categories.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_log_classified` AS
SELECT
  ticket_id,
  user_name,
  ticket_description,
  resolution,
  resolution_hours,
  AI.CLASSIFY(
    ticket_description,
    [('access', 'Account access, permissions, authentication, SSO, VPN credentials'),
     ('hardware', 'Physical device issues: laptops, monitors, keyboards, docking stations'),
     ('software', 'Application bugs, crashes, license issues, build failures'),
     ('network', 'Connectivity, Wi-Fi, DNS, latency, printer discovery'),
     ('security', 'Suspicious activity, phishing, unauthorized access, data leaks'),
     ('data', 'Database issues, ETL failures, backups, query performance')]
  ) AS category
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_log_tickets`
'''
client.query(query).result()

classified = client.query(f'''
  SELECT category, COUNT(*) AS count,
    ROUND(AVG(IFNULL(resolution_hours, 0)), 1) AS avg_hours
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_log_classified`
  GROUP BY category
  ORDER BY count DESC
''').to_dataframe()
print('Ticket distribution by category:')
classified
```

---
## Step 3 — Score tickets for priority with AI.SCORE

Use `AI.SCORE` to rate each ticket's business impact on a 1–10 scale. This helps triage which issues affect the most people or business operations.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_log_scored` AS
SELECT
  ticket_id,
  user_name,
  ticket_description,
  resolution,
  resolution_hours,
  category,
  AI.SCORE(CONCAT(
    'Rate the business impact of this IT support ticket on a scale of 1 to 10, ',
    'where 1 is minor inconvenience and 10 is critical business disruption ',
    '(e.g. data loss, security breach, entire team blocked): ',
    ticket_description,
    ' Resolution: ', IFNULL(resolution, 'UNRESOLVED')
  )) AS priority
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_log_classified`
'''
client.query(query).result()

scored = client.query(f'''
  SELECT category,
    ROUND(AVG(priority), 1) AS avg_priority,
    ROUND(MAX(priority), 1) AS max_priority,
    COUNT(*) AS count
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_log_scored`
  GROUP BY category
  ORDER BY avg_priority DESC
''').to_dataframe()
print('Priority scores by category:')
scored
```

### High-priority tickets

Tickets scoring 7+ that need immediate attention.

```python
high_priority = client.query(f'''
  SELECT ticket_id, user_name, category, priority,
    LEFT(ticket_description, 120) AS description
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_log_scored`
  WHERE priority >= 7
  ORDER BY priority DESC
''').to_dataframe()

if len(high_priority) == 0:
    print('No high-priority tickets — operations are running smoothly!')
else:
    print(f'{len(high_priority)} high-priority tickets:')
    high_priority
```

---
## Step 4 — Summarize patterns with AI.AGG

This is where `AI.AGG` shines. Instead of manually concatenating tickets into a prompt with `STRING_AGG`, we let `AI.AGG` handle the batching and aggregation automatically. It returns one summary per category — identifying common patterns, root causes, and recommended actions.

```python
query = f'''
SELECT
  category,
  AI.AGG(
    TO_JSON_STRING(STRUCT(
      ticket_id, user_name, ticket_description,
      resolution, resolution_hours, priority
    )),
    'You are an IT operations analyst. Analyze these support tickets for this category. '
    'Identify: (1) common patterns or root causes, (2) average resolution effectiveness, '
    '(3) any systemic issues that need proactive fixes, (4) one actionable recommendation. '
    'Be concise.'
  ) AS category_analysis
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_log_scored`
GROUP BY category
'''
df_analysis = client.query(query).to_dataframe()
for _, row in df_analysis.iterrows():
    print(f'=== {row["category"].upper()} ===')
    print(row['category_analysis'])
    print()
```

### Overall incident summary with AI.AGG

Without `GROUP BY`, `AI.AGG` aggregates all tickets into a single cross-category summary — an operational overview for leadership.

```python
query = f'''
SELECT
  AI.AGG(
    TO_JSON_STRING(STRUCT(ticket_id, category, ticket_description, priority, resolution_hours)),
    'You are a VP of IT writing a weekly operations report. Summarize all support tickets into a '
    'brief executive report (3-4 paragraphs). Cover: overall volume and category breakdown, '
    'most critical issues, resolution performance, and top 2 recommendations for the coming week.'
  ) AS weekly_report
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_log_scored`
'''
df = client.query(query).to_dataframe()
print(df.iloc[0]['weekly_report'])
```
