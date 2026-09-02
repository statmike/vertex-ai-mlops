# Log Analysis — BigQuery AI Functions

An end-to-end log analysis pipeline that composes six functions to analyze application support tickets:

1. **Generate** sample support tickets with `AI.GENERATE_TABLE`
2. **Classify** each ticket by category with `AI.CLASSIFY`
3. **Score** each ticket for priority with `AI.SCORE`
4. **Summarize** patterns by category with `AI.AGG` (the star of this workflow)
5. **Retrieve** similar past incidents with `AI.EMBED` + hybrid `VECTOR_SEARCH`

**What this demonstrates:**
- `AI.AGG` as the natural aggregation function — summarize groups of tickets without manual batching
- Composing classify → score → aggregate in a single analytical pipeline
- Using `TO_JSON_STRING` to pass structured data to `AI.AGG`
- Where `AI.AGG` stops being trustworthy — it batches hierarchically, so the counts and totals it states are reconstructions rather than aggregates
- Hybrid retrieval — pairing semantic similarity with an exact lexical match on an error code, and measuring what fusion actually buys: the rows it adds, and how far up the ranking it can lift them

**Functions used:** `functions/ai_generate_table` (`AI.GENERATE_TABLE`) | `functions/ai_classify` (`AI.CLASSIFY`) | `functions/ai_score` (`AI.SCORE`) | `functions/ai_agg` (`AI.AGG`) | `functions/ai_embed` (`AI.EMBED`) | `functions/vector_search` (`VECTOR_SEARCH`) (hybrid)

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

Generate 30 realistic IT support tickets from seed categories. Each ticket has a user, description, resolution, and resolution time — mimicking real helpdesk data.

Every seed also carries an **error code**. The codes are written by hand in the SQL below rather than invented by the model, for two reasons: they stay identical on every run, and the prompt can require the model to quote the code verbatim inside the description. That gives Step 5 a stable token that appears both in a dedicated column and in free text.

Two codes repeat across seeds on purpose: `VPN-4033` covers a provisioning request and a disconnect complaint, and `AUTH-0142` covers two access tickets. A third code, `IDP-7761`, appears exactly once — on a data ticket about a quarterly archive job. That single ticket is what Step 5 has to find. The same identity-provider fault that locks users out also breaks the archive job's service credential, but nothing in the way the ticket is written resembles a login problem, so the code is the only thread connecting the two.

```python
output_schema = """user_name STRING OPTIONS(description = "The employee who submitted the ticket"),
       ticket_description STRING OPTIONS(description = "Detailed description of the issue"),
       resolution STRING OPTIONS(description = "How the issue was resolved, or current status if unresolved"),
       resolution_hours FLOAT64 OPTIONS(description = "Hours from ticket creation to resolution, or NULL if unresolved")"""

query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_log_tickets` AS
SELECT ticket_id, error_code, user_name, ticket_description, resolution, resolution_hours
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT
    ticket_id,
    error_code,
    CONCAT(
      'Generate one realistic IT support ticket. Category: ', category,
      '. Scenario: ', scenario,
      '. The user saw error code ', error_code,
      '. Mention this code verbatim in the description. ',
      'Write a detailed description (2-3 sentences) and a resolution. ',
      'Create a believable employee name. ',
      'Set resolution_hours between 0.5 and 48, or null if unresolved.'
    ) AS prompt
   FROM UNNEST([
     STRUCT(1 AS ticket_id, 'access' AS category, 'new employee needs VPN access' AS scenario, 'VPN-4033' AS error_code),
     STRUCT(2, 'access', 'password reset for locked account', 'AUTH-0142'),
     STRUCT(3, 'access', 'MFA token not working after phone upgrade', 'MFA-2210'),
     STRUCT(4, 'access', 'shared drive permissions denied', 'PERM-0307'),
     STRUCT(5, 'access', 'SSO login loop on new laptop', 'AUTH-0142'),
     STRUCT(6, 'hardware', 'laptop screen flickering intermittently', 'HW-1180'),
     STRUCT(7, 'hardware', 'keyboard keys sticking after coffee spill', 'HW-1204'),
     STRUCT(8, 'hardware', 'docking station not detecting external monitors', 'DOCK-0521'),
     STRUCT(9, 'hardware', 'battery draining in under 2 hours', 'PWR-0918'),
     STRUCT(10, 'hardware', 'trackpad unresponsive after OS update', 'DRV-3312'),
     STRUCT(11, 'software', 'Slack keeps crashing on startup', 'APP-5007'),
     STRUCT(12, 'software', 'Excel macro broken after Office update', 'APP-5119'),
     STRUCT(13, 'software', 'VPN disconnects every 30 minutes', 'VPN-4033'),
     STRUCT(14, 'software', 'Docker containers failing to build', 'BLD-7742'),
     STRUCT(15, 'software', 'IDE license expired and blocking work', 'LIC-6301'),
     STRUCT(16, 'network', 'Wi-Fi drops in conference room B', 'NET-2048'),
     STRUCT(17, 'network', 'cannot reach internal wiki from remote', 'NET-2065'),
     STRUCT(18, 'network', 'latency spikes during video calls', 'NET-2103'),
     STRUCT(19, 'network', 'DNS resolution failing for staging servers', 'DNS-0553'),
     STRUCT(20, 'network', 'printer not found on office network', 'NET-2211'),
     STRUCT(21, 'security', 'suspicious login from unknown location', 'SEC-9001'),
     STRUCT(22, 'security', 'phishing email reported by multiple users', 'SEC-9014'),
     STRUCT(23, 'security', 'unauthorized app installed on work laptop', 'SEC-9027'),
     STRUCT(24, 'security', 'sensitive file shared externally by accident', 'DLP-8802'),
     STRUCT(25, 'security', 'antivirus flagging a development tool', 'SEC-9033'),
     STRUCT(26, 'data', 'accidental deletion of production database rows', 'DB-3401'),
     STRUCT(27, 'data', 'ETL pipeline failing with schema mismatch', 'ETL-7120'),
     STRUCT(28, 'data', 'quarterly archive job writing zero-byte files to cold storage', 'IDP-7761'),
     STRUCT(29, 'data', 'backup restoration needed for corrupted file', 'BKP-4409'),
     STRUCT(30, 'data', 'BigQuery query hitting quota limits', 'QUOTA-0429')
   ])),
  STRUCT(
    """{output_schema}""" AS output_schema
  )
)
'''
client.query(query).result()

tickets = client.query(
    f'SELECT ticket_id, error_code, user_name, LEFT(ticket_description, 80) AS description_preview, resolution_hours FROM `{PROJECT_ID}.{DATASET_ID}.workflow_log_tickets` ORDER BY ticket_id'
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
  error_code,
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
  error_code,
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
    display(high_priority)
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

### Checking AI.AGG's arithmetic

`AI.AGG` never sees all 30 tickets in one model call. It batches them hierarchically and summarizes the summaries, so every count, total, and average in the report above is a figure the model reassembled from partial views — not an aggregate BigQuery computed. Volume numbers are both the first thing a reader checks and the easiest thing for this to get wrong.

The rule that follows: **reach for `GROUP BY` when the number has to be right, and for `AI.AGG` when the prose has to be good.** The cell below computes the same figures the report tries to state, prints them next to it for comparison, and then feeds them back into `AI.AGG` so the model spends its call on synthesis instead of counting.

```python
truth = client.query(f'''
  SELECT category,
    COUNT(*) AS tickets,
    ROUND(SUM(IFNULL(resolution_hours, 0)), 1) AS total_hours,
    ROUND(AVG(IFNULL(resolution_hours, 0)), 2) AS avg_hours
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_log_scored`
  GROUP BY category
  ORDER BY tickets DESC
''').to_dataframe()

print(f'Ground truth from GROUP BY — {int(truth["tickets"].sum())} tickets, '
      f'{truth["total_hours"].sum():.1f} total hours. '
      f'Compare against the report above:')
display(truth)

facts = '; '.join(
    f'{row.category}: {row.tickets} tickets, {row.total_hours} hours'
    for row in truth.itertuples()
)

query = f'''
SELECT
  AI.AGG(
    TO_JSON_STRING(STRUCT(ticket_id, category, ticket_description, priority, resolution_hours)),
    'You are a VP of IT writing a weekly operations report. The verified totals, computed in SQL, '
    'are: {facts}. Use those figures verbatim and do not recount anything. '
    'Write a brief executive report (3-4 paragraphs) covering the most critical issues, '
    'resolution performance, and the top 2 recommendations for the coming week.'
  ) AS weekly_report
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_log_scored`
'''
print('\n=== Grounded report — counting done by GROUP BY, prose by AI.AGG ===')
print(client.query(query).to_dataframe().iloc[0]['weekly_report'])
```

---
## Step 5 — Find similar past incidents with hybrid retrieval

Triage gets faster when whoever picks up a new ticket can see how the same problem was handled before. That is a retrieval problem, and it needs two different kinds of matching at the same time:

- **Semantic** — *users cannot authenticate after switching to a new device* should surface the MFA-after-phone-upgrade ticket even though the two share almost no words. Embeddings are good at this.
- **Lexical** — the same incident's log carries `IDP-7761`. An embedding model has no notion of what that token stands for, so the one earlier ticket carrying it can sit near the bottom of the semantic ranking simply because it is written about something else — a scheduled archive job, not a login.

`VECTOR_SEARCH` can run both at once. Its single-query syntax accepts `lexical_search_columns` and `lexical_search_query_value` alongside `query_value`, then fuses the two result lists into a single ranking. That is **hybrid search**.

Whether fusion actually changes *which rows come back* is a measurable question, not an assumption. The cells below run both searches over the same corpus and print the difference between the two result sets.

The tickets need embeddings first. `AI.EMBED` turns each description into an `ARRAY<FLOAT64>` stored in a new table, alongside the columns the search should return — including `resolution`, so every hit arrives with its fix attached.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_log_embedded` AS
SELECT
  ticket_id,
  error_code,
  category,
  priority,
  ticket_description,
  resolution,
  (AI.EMBED(
    content => ticket_description,
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_DOCUMENT'
  )).result AS embedding
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_log_scored`
'''
client.query(query).result()

embedded = client.query(f'''
  SELECT ticket_id, error_code, category, ARRAY_LENGTH(embedding) AS embedding_dims
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_log_embedded`
  ORDER BY ticket_id
''').to_dataframe()
print(f'{len(embedded)} tickets embedded')
embedded.head()
```

### Semantic search alone

The incident being triaged is *users cannot authenticate after switching to a new device*, and its log carries error code `IDP-7761`. Called with only `query_value`, `VECTOR_SEARCH` ranks tickets by embedding distance, so access tickets about logins and new devices dominate.

`AI.EMBED` builds the query vector inline, with `task_type => 'RETRIEVAL_QUERY'` to pair correctly with the `RETRIEVAL_DOCUMENT` vectors already stored.

A second call with `top_k => 30` ranks the entire corpus, so the cell can print exactly where the one ticket carrying the code lands. That position is the number the rest of this section turns on.

```python
INCIDENT_TEXT = 'users cannot authenticate after switching to a new device'
ERROR_CODE = 'IDP-7761'  # seeded onto exactly one ticket in Step 1 — a data ticket, not an access one
TOP_K = 12               # out of 30 tickets

QUERY_VECTOR = f'''(AI.EMBED(
    content => '{INCIDENT_TEXT}',
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_QUERY'
  )).result'''

query = f'''
SELECT
  base.ticket_id,
  base.error_code,
  base.category,
  base.priority,
  LEFT(base.ticket_description, 100) AS description,
  distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_log_embedded`,
  'embedding',
  query_value => {QUERY_VECTOR},
  top_k => {TOP_K},
  distance_type => 'COSINE'
)
ORDER BY distance
'''
semantic_only = client.query(query).to_dataframe()

# Rank the whole corpus so the code-carrying ticket's true position is visible
ranked = client.query(f'''
SELECT
  base.ticket_id,
  base.error_code,
  ROW_NUMBER() OVER (ORDER BY distance) AS semantic_rank
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_log_embedded`,
  'embedding',
  query_value => {QUERY_VECTOR},
  top_k => 30,
  distance_type => 'COSINE'
)
QUALIFY base.error_code = '{ERROR_CODE}'
''').to_dataframe()

TARGET = int(ranked['ticket_id'].iloc[0])
TARGET_SEMANTIC_RANK = int(ranked['semantic_rank'].iloc[0])
print(f'Ticket carrying {ERROR_CODE}: {TARGET} — semantic rank {TARGET_SEMANTIC_RANK} of 30')
print(f'Returned by semantic-only top {TOP_K}: {TARGET in set(semantic_only["ticket_id"])}')
print(f'Categories returned: {sorted(semantic_only["category"].unique().tolist())}')
semantic_only
```

### Hybrid — semantic similarity plus the exact code

Same query vector and the same `top_k`, now with a lexical query alongside it, so the two result sets are directly comparable.

- `lexical_search_columns` names the `STRING` columns to keyword-match. They do **not** have to be the column the embeddings came from, so the search can match the code in its own dedicated column *and* wherever the model quoted it in the description.
- `lexical_search_query_value` is the text to keyword-match, and it is independent of `query_value`. Here it is the error code, not the incident sentence — two different questions asked in one call.

Hybrid is single-query only: `lexical_search_columns` is rejected when `VECTOR_SEARCH` is called in its batch (query-table) form. A vector index is not required — without one, both sides run brute force, which is fine at this scale.

The cell prints the set difference in both directions. Fusion re-ranks everything, so a row it adds arrives at the expense of a row the semantic search would have returned.

```python
def hybrid_search(k):
    """Same query vector, plus a lexical query on the error code, fused into one top-k ranking."""
    return client.query(f'''
    SELECT
      base.ticket_id,
      base.error_code,
      base.category,
      base.priority,
      LEFT(base.ticket_description, 100) AS description,
      distance
    FROM VECTOR_SEARCH(
      TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_log_embedded`,
      'embedding',
      query_value => {QUERY_VECTOR},
      top_k => {k},
      distance_type => 'COSINE',
      lexical_search_columns => ['error_code', 'ticket_description'],
      lexical_search_query_value => '{ERROR_CODE}'
    )
    ORDER BY distance
    ''').to_dataframe()


hybrid = hybrid_search(TOP_K)

gained = sorted(int(t) for t in set(hybrid['ticket_id']) - set(semantic_only['ticket_id']))
dropped = sorted(int(t) for t in set(semantic_only['ticket_id']) - set(hybrid['ticket_id']))
print(f'Tickets hybrid added that semantic-only missed: {gained or "none"}')
print(f'Tickets hybrid dropped to make room: {dropped or "none"}')
print(f'Ticket {TARGET}, the only one carrying {ERROR_CODE}, in the hybrid top {TOP_K}: '
      f'{TARGET in set(hybrid["ticket_id"])}')
hybrid
```

### How far up can fusion lift a row?

Fusion does not put the exact-token match on top, and how deep in the ranking it can reach is decided by `top_k` — twice over, through two separate gates.

**Gate 1 — the candidate pool.** The lexical leg never sees the whole table. BigQuery hands it the top `10 * top_k` rows by semantic rank and BM25 scores only those. A row deeper than `10 * top_k` receives no lexical rank at all, so no token match, however exact, can reach it. At `top_k => 12` the pool is 120 rows, which covers this 30-ticket corpus several times over; on a 7,275-ticket archive the same `top_k` would leave 7,155 rows invisible to the keyword search.

**Gate 2 — the fused score.** Inside the pool both legs rank every candidate. BM25 matches take lexical ranks 1..m, and every pooled row the keyword search does not match falls in behind them in semantic order, so no pooled row is ever missing from a list. What a lexical match buys a row is promotion to lexical rank 1, worth `1/62 ≈ 0.0161` — a fixed amount of lift, competing against a page whose last slot is held by a row that also carries both terms. A matched row at semantic rank `R` scores `1/(60 + R) + 1/62`. It has to displace the row at semantic rank `top_k`, which the match itself pushes down to lexical rank `top_k + 1` and which therefore scores `1/(60 + top_k) + 1/(61 + top_k + 1)`.

A row has to clear both gates, so the reach is whichever one is tighter — `min(score reach, 10 * top_k)`:

| `top_k` | 2 | 3 | 5 | 10 | 20 | 30 | 40 | 50 | 51 | 64 | 100 | 208 | 300 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deepest semantic rank retrievable | 3 | 6 | 10 | 23 | 56 | 110 | 212 | 468 | 510 | 640 | 1,000 | 2,080 | 3,000 |

The score gate binds below `top_k = 51`; from 51 up the pool is the limit and reach grows strictly in proportion to `top_k`. There is no threshold past which it stops being a limit: at `top_k => 64` a matched row surfaces from semantic rank 640 at best.

That fixes the sizing rule for error-code lookup. **To surface a code buried at semantic rank `R`, `top_k` has to be at least `R/10`** — necessary, but not on its own sufficient. The two gates cross at `top_k = 51`, so for `R` under a few hundred it is the score gate that binds and `R/10` falls short: a code at semantic rank 100 needs `top_k => 29`, not 10, and one at rank 200 needs 40, not 20. Read the number to use off the reach table above rather than dividing. A code sitting at rank 2,072 in a 7,275-ticket archive needs `top_k => 208`; asking for it at `top_k => 64` returns nothing, because the pool stopped at 640. And when the code *is* the whole question, skip the arithmetic: `WHERE error_code = @code` has no pool and cannot be outranked by a fusion score.

The cell below prints where the code-carrying ticket lands in the full 30-row fused ranking, how many positions that is worth, and whether the *identical* hybrid query returns it at `top_k => 5`. The table above says what to expect. At `top_k => 30` the pool is 300 and the score reach is 110, so 110 is the binding number — far past anything a 30-ticket corpus can hide, and the ticket makes the page and climbs well up it. At `top_k => 5` the reach is 10; the lexical search still runs and still finds the row, but the row cannot buy its way onto a five-row page, and the result collapses back onto what semantic search alone would have returned.

```python
full_hybrid = hybrid_search(30)
fused_position = int(full_hybrid.index[full_hybrid['ticket_id'] == TARGET][0]) + 1
narrow = hybrid_search(5)

print(f'Ticket {TARGET} — vector rank {TARGET_SEMANTIC_RANK} of 30, '
      f'fused position {fused_position} of 30')
print(f'Positions gained by adding the lexical leg: {TARGET_SEMANTIC_RANK - fused_position}')
print(f'Returned by the same hybrid query at top_k => 5:  {TARGET in set(narrow["ticket_id"])}')
print(f'Returned by the same hybrid query at top_k => {TOP_K}: {TARGET in set(hybrid["ticket_id"])}')

narrow_gain = sorted(int(t) for t in set(narrow['ticket_id']) - set(semantic_only['ticket_id'].head(5)))
print(f'Rows the top_k => 5 hybrid adds over the semantic-only top 5: {narrow_gain or "none"}')
```

### What the hybrid `distance` column actually is

Under hybrid search, `distance` stops being a distance. Two things give it away: values land in a narrow band just under 1 instead of spreading across the COSINE range seen in the semantic-only result, and a row that matches perfectly does not score 0.

It is a **fused rank score**. Each of the two searches produces its own ranking, and the rankings are combined with Reciprocal Rank Fusion:

```
distance = 1 - ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) )
```

with 1-based ranks. A row ranked 1st by the vector search and 2nd by the lexical search scores:

```
1 - (1/61 + 1/63)
  = 1 - (0.01639344262295082 + 0.015873015873015872)
  = 0.9677335415040333
```

**What is measured, and what is inferred.** Only the vector rank is ever read directly — `VECTOR_SEARCH` returns no rank column, so `rank_vector` comes from a separate semantic-only run over the same rows and the lexical term is whatever remains. That pins *denominators*, not constants. Since `1/(61 + r)` and `1/(60 + (r + 1))` are the same number, two readings fit every observation identically:

| Reading | Vector leg | Lexical leg |
|---|---|---|
| A — two constants | k = 60, ranks `1..n` | k = 61, ranks `1..n` |
| B — one constant, offset ranks | k = 60, ranks `1..n` | k = 60, ranks `2..n+1` |

**B is the likelier.** k = 60 over 1-based ranks is canonical reciprocal rank fusion (Cormack, Clarke and Buettcher, 2009) and the default wherever the constant is exposed — Elasticsearch and OpenSearch name it `rank_constant` and default it to 60, Spanner and AlloyDB write 60 into their documented SQL — while 61 appears as the constant in no published implementation. The 60/61 form is kept throughout this notebook because it is the shortest expression that reproduces every observed value, not because two bases were deliberately chosen.

`0.9674775251189847` appears below as the best attainable score: the same arithmetic, `1/61 + 1/62`, evaluated at the best ranks a row can hold — rank 1 on *both* legs.

What that means when reading the column:

- **Lower is still better** — the reciprocal ranks are subtracted from 1, so a strong row on both signals subtracts the most.
- **The values are not comparable to VECTOR-mode distances.** A hybrid 0.967 and a cosine 0.967 have nothing to do with each other.
- **The magnitude carries no similarity information**, only the ordering does. Rank 1 on both signals gives `1 - (1/61 + 1/62) = 0.9674775251189847`, the best attainable score no matter how good the match is.
- **Each reciprocal term is small and decays fast.** The vector term tops out at `1/61 ≈ 0.0164` and the lexical term at `1/62 ≈ 0.0161`; by rank 10 a term is worth 0.0143 and by rank 25, 0.0118. The whole score lives inside a range narrower than 0.02, which is why one signal can never dominate the other.
- **No pooled row forfeits a term.** The lexical leg ranks the entire candidate pool — the top `10 * top_k` rows by vector rank — not just the keyword matches: BM25 hits take lexical ranks 1..m and every remaining pooled row falls in behind them in vector order. A row whose text contains nothing like the token still carries a lexical rank — its vector rank, pushed down one place for each matching row below it. Only where nothing matches at all does the page reduce to `1 - ( 1/(60 + r) + 1/(61 + r) )` at vector rank `r`. What an exact-token match changes is that rank, promoting the row to lexical rank 1. Rows outside the pool are never scored by BM25 at all, and a result set where every row's lexical rank equals its vector rank is the signature that nothing in the pool matched.
- **`distance_type` is still accepted in hybrid mode**, and it still governs how the vector leg orders its candidates — but the value returned in `distance` is the fused rank score, never a COSINE distance, whatever is passed.

> **This decomposition is reverse-engineered from observed behavior; Google does not document it.** The reference pages describe `distance` only as the distance "for the semantic search portion of a vector search" and say nothing about fusion, the constants, or the scale change. The formula here was recovered by matching returned values to all 16 significant digits. Treat it as an explanation of what the function does today, not a contract — it can change without notice.

The cell below rebuilds the arithmetic from live results rather than asserting it: it re-runs the semantic search across all 30 tickets to recover each row's vector rank, solves the formula for the lexical rank, and then reconstructs the fused score from those two integers. At `top_k => 12` the pool is 120 rows, so all 30 tickets sit inside it and every returned row has a lexical rank to recover. Every one of them comes back as an exact integer — that is the evidence the `1/(k + rank)` shape is right. It is not evidence about the base: under reading B the engine's own lexical ranks are one higher than the integers recovered here, the same numbers shifted.

```python
query = f'''
WITH incident AS (
  SELECT (AI.EMBED(
    content => '{INCIDENT_TEXT}',
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_QUERY'
  )).result AS query_vector
),
semantic AS (
  SELECT
    base.ticket_id AS ticket_id,
    ROW_NUMBER() OVER (ORDER BY distance) AS vector_rank,
    distance AS vector_distance
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_log_embedded`,
    'embedding',
    query_value => (SELECT query_vector FROM incident),
    top_k => 30,
    distance_type => 'COSINE')
),
fused AS (
  SELECT
    base.ticket_id AS ticket_id,
    base.error_code AS error_code,
    distance AS fused_distance
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_log_embedded`,
    'embedding',
    query_value => (SELECT query_vector FROM incident),
    top_k => {TOP_K},
    distance_type => 'COSINE',
    lexical_search_columns => ['error_code', 'ticket_description'],
    lexical_search_query_value => '{ERROR_CODE}')
),
terms AS (
  SELECT
    f.ticket_id,
    f.error_code,
    s.vector_rank,
    ROUND(s.vector_distance, 4) AS vector_distance,
    f.fused_distance,
    1 / (60 + s.vector_rank) AS vector_term,
    (1 - f.fused_distance) - 1 / (60 + s.vector_rank) AS lexical_term
  FROM fused f
  JOIN semantic s USING (ticket_id)
),
solved AS (
  -- The lexical leg ranks the whole candidate pool — the top 10 * top_k rows by vector
  -- rank — with BM25 matches taking ranks 1..m and every other pooled row following in
  -- vector order, so every returned row has a lexical rank to recover.
  SELECT
    *,
    CAST(ROUND(SAFE_DIVIDE(1, lexical_term) - 61) AS INT64) AS lexical_rank
  FROM terms
)
SELECT
  ticket_id,
  error_code,
  vector_rank,
  vector_distance,
  lexical_rank,
  fused_distance,
  1 - (vector_term + 1 / (61 + lexical_rank)) AS rebuilt_from_ranks
FROM solved
ORDER BY fused_distance
'''
rrf = client.query(query).to_dataframe()

gap = (rrf['rebuilt_from_ranks'] - rrf['fused_distance']).abs()
print(f'Rows whose fused score rebuilds exactly from the two integer ranks: '
      f'{int(gap.lt(1e-12).sum())} of {len(rrf)}')
print(f'Rows with a solved lexical rank: {int(rrf["lexical_rank"].notna().sum())} of {len(rrf)}')
print(f'Best solved lexical rank among the returned rows: {rrf["lexical_rank"].min()}')
rrf
```

Both halves of the workflow serve triage. The `AI.AGG` narratives in Step 4 answer the queue-level question — what is going wrong across all tickets this week — provided the numbers in them are checked against `GROUP BY`. Hybrid retrieval answers the ticket-level one: *has anyone seen this exact error before, and what fixed it?* Because `resolution` travels with every hit, the answer comes back with the remedy already attached.

Two things about hybrid retrieval are worth carrying out of Step 5:

- **It is a re-ranking that also widens.** The lexical leg changes the fused score of every row, so a row it adds arrives at the expense of a row the semantic search would have returned. Step 5 prints both sides of that trade rather than claiming only the upside.
- **`top_k` decides how far the widening reaches, through two gates.** BM25 only ever sees the top `10 * top_k` rows by semantic rank, and inside that pool a match is worth `1/62 ≈ 0.0161` of lift against the row holding the last slot. The tighter of the two fixes the deepest rank a matched row can climb from: 10 at `top_k => 5`, 110 at `top_k => 30`, 640 at `top_k => 64`. Size `top_k` short of that reach and the lexical leg does its work while the row it found never appears. For a code expected at semantic rank `R`, `R/10` is the floor and not the recipe — under a few hundred ranks deep the score gate binds first, so take the value from the reach table in Step 5. When an identifier is the whole question and the answer has to be certain, `WHERE error_code = @code` is the right tool — a predicate has no pool and cannot be outranked by a fusion score.
