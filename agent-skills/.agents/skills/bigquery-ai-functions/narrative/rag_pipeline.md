# RAG Pipeline — BigQuery AI Functions

A complete Retrieval-Augmented Generation (RAG) pipeline built entirely in BigQuery SQL:

1. **Generate** a knowledge base with `AI.GENERATE_TABLE`
2. **Embed** documents with `AI.EMBED`
3. **Search** for relevant context with `VECTOR_SEARCH`
4. **Answer** questions with `AI.GENERATE`, grounded in retrieved documents
5. **Promote exact tokens** with hybrid `VECTOR_SEARCH` when a keyword decides whether the answer is right

**What this demonstrates:**
- Building a full RAG system without leaving BigQuery
- Asymmetric embedding pattern (RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY)
- Composing search results into grounded prompts
- Measuring what a lexical leg changes about the retrieved context — and how far that change can reach
- Choosing between batch retrieval (many questions at once) and hybrid retrieval (one question, exact-token promotion)

**Functions used:** `functions/ai_generate_table` (`AI.GENERATE_TABLE`) | `functions/ai_embed` (`AI.EMBED`) | `functions/vector_search` (`VECTOR_SEARCH`) (semantic + hybrid) | `functions/ai_generate` (`AI.GENERATE`)

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
## Step 1 — Generate a knowledge base with AI.GENERATE_TABLE

Use `AI.GENERATE_TABLE` to create a realistic FAQ knowledge base for a fictional cloud platform. Each input row generates one FAQ entry with a question, answer, and category.

One further entry is appended as a literal row instead of being generated. Step 5 needs a document that carries an opaque status code *verbatim*, and a model rewrites its wording on every run — it may reformat the code, or leave it out. Spelling that one entry out makes the token a fixed property of the corpus rather than something to hope for, and the cell prints how many entries actually carry it.

```python
output_schema = """question STRING OPTIONS(description = "The FAQ question"),
       answer STRING OPTIONS(description = "Detailed answer with technical specifics"),
       category STRING OPTIONS(description = "Category: Compute, Networking, Security, Database, DevOps, or Monitoring")"""

# Step 5 needs one entry carrying an opaque token verbatim, so that entry is written out here
# rather than generated. Everything downstream reads the token from this constant.
status_code = 'ERR-4417'
status_code_question = 'What does status code ERR-4417 mean?'
status_code_answer = (
    'ERR-4417 is returned when a scheduled job is throttled because the account is already running '
    'its maximum number of concurrent jobs. Stagger the schedule or request a higher concurrency '
    'quota; a retry inside the same window returns ERR-4417 again.')

query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_rag_knowledge` AS
SELECT question, answer, category
FROM AI.GENERATE_TABLE(
  MODEL `{PROJECT_ID}.{DATASET_ID}.gemini_flash`,
  (SELECT CONCAT(
     'Write a detailed FAQ entry about "', topic, '" for a cloud computing platform. ',
     'The answer should be 2-3 sentences with specific technical details.'
   ) AS prompt
   FROM UNNEST([
     'how to create a virtual machine',
     'setting up a load balancer',
     'configuring a firewall',
     'creating a database backup',
     'monitoring application performance',
     'setting up auto-scaling',
     'managing API keys',
     'configuring DNS records',
     'setting up CI/CD pipelines',
     'managing user permissions',
     'encrypting data at rest',
     'setting up logging and alerts'
   ]) AS topic),
  STRUCT(
    """{output_schema}""" AS output_schema
  )
)
UNION ALL
SELECT '{status_code_question}', '{status_code_answer}', 'DevOps'
'''
client.query(query).result()

kb = client.query(
    f'SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.workflow_rag_knowledge`'
).to_dataframe()
carries_token = int((kb['question'] + ' ' + kb['answer']).str.contains(status_code).sum())
print(f'{len(kb)} FAQ entries: {len(kb) - 1} written by the model, 1 written out above')
print(f'Entries carrying the token "{status_code}" verbatim: {carries_token}')
kb[['category', 'question']]
```

---
## Step 2 — Embed the knowledge base with AI.EMBED

Create embeddings for each FAQ answer using `RETRIEVAL_DOCUMENT` task type. We embed the concatenation of question + answer for richer context.

```python
query = f'''
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_rag_embedded` AS
SELECT
  question, answer, category,
  (AI.EMBED(
    content => CONCAT(question, ' ', answer),
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_DOCUMENT'
  )).result AS embedding
FROM `{PROJECT_ID}.{DATASET_ID}.workflow_rag_knowledge`
'''
client.query(query).result()

verify = client.query(f'''
  SELECT category, question, ARRAY_LENGTH(embedding) AS dims
  FROM `{PROJECT_ID}.{DATASET_ID}.workflow_rag_embedded`
''').to_dataframe()
print(f'All {len(verify)} entries embedded ({verify.iloc[0]["dims"]} dimensions)')
```

---
## Step 3 — Retrieve and generate (RAG)

The core RAG pattern: for each user question, retrieve the most relevant FAQ entries with `VECTOR_SEARCH`, then pass them as context to `AI.GENERATE` to produce a grounded answer.

```python
user_question = 'How do I protect my application from unauthorized access?'

query = f'''
WITH retrieved AS (
  SELECT
    base.question AS faq_question,
    base.answer AS faq_answer,
    base.category,
    distance
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_rag_embedded`,
    'embedding',
    query_value => (AI.EMBED(
      content => '{user_question}',
      endpoint => 'text-embedding-005',
      task_type => 'RETRIEVAL_QUERY'
    )).result,
    top_k => 3,
    distance_type => 'COSINE'
  )
),
context AS (
  SELECT STRING_AGG(
    CONCAT('Q: ', faq_question, ' | A: ', faq_answer),
    ' ||| '
  ) AS docs
  FROM retrieved
)
SELECT (AI.GENERATE(
  CONCAT(
    'You are a cloud platform support assistant. Answer the user question based ONLY on the provided context. ',
    'If the context does not contain enough information, say so. ',
    'Context: ', c.docs,
    ' --- User question: {user_question}'
  )
)).result AS answer
FROM context c
'''
df = client.query(query).to_dataframe()
print(f'Question: {user_question}\n')
print(df.iloc[0]['answer'])
```

### View the retrieved context

See which FAQ entries were retrieved and used as context for the answer.

```python
query = f'''
SELECT
  base.category,
  base.question,
  base.answer,
  distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_rag_embedded`,
  'embedding',
  query_value => (AI.EMBED(
    content => '{user_question}',
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_QUERY'
  )).result,
  top_k => 3,
  distance_type => 'COSINE'
)
'''
client.query(query).to_dataframe()
```

---
## Step 4 — Batch RAG: answer multiple questions

Process multiple user questions through the RAG pipeline at once. Each question retrieves its own context and gets a tailored answer.

```python
query = f'''
WITH questions AS (
  SELECT question
  FROM UNNEST([
    'How do I make my app handle more traffic automatically?',
    'What is the best way to back up my database?',
    'How do I set up monitoring for my services?'
  ]) AS question
),
retrieved AS (
  SELECT
    query.question AS user_question,
    base.question AS faq_question,
    base.answer AS faq_answer,
    distance
  FROM VECTOR_SEARCH(
    TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_rag_embedded`,
    'embedding',
    (SELECT question,
       (AI.EMBED(content => question, endpoint => 'text-embedding-005',
                 task_type => 'RETRIEVAL_QUERY')).result AS embedding
     FROM questions),
    top_k => 2,
    distance_type => 'COSINE'
  )
),
context_per_question AS (
  SELECT
    user_question,
    STRING_AGG(
      CONCAT('Q: ', faq_question, ' | A: ', faq_answer),
      ' ||| '
    ) AS context
  FROM retrieved
  GROUP BY user_question
)
SELECT
  user_question,
  (AI.GENERATE(
    CONCAT(
      'Answer this question concisely based on the context below. ',
      'Context: ', context,
      ' --- Question: ', user_question
    )
  )).result AS answer
FROM context_per_question
'''
df = client.query(query).to_dataframe()
for _, row in df.iterrows():
    print(f'Q: {row["user_question"]}')
    print(f'A: {row["answer"]}\n')
```

---
## Step 5 — Hybrid retrieval: semantic + keyword

Step 4 answered three questions in a single `VECTOR_SEARCH` call by passing a *query table*. That batch form is what makes RAG scale — and it is also the one form that cannot go hybrid. The lexical arguments are accepted only next to `query_value`, the single-question form; ask for both and BigQuery refuses the query with `lexical_search_columns is not supported when query_value is not specified.`

Hybrid retrieval earns that cost when an exact token decides whether the answer is right: a status code, a product name, a version string, a proper noun. Embeddings encode meaning, and an opaque token carries almost none — `ERR-4417` reads like any other short code to an embedding model. The entry that documents it therefore lands wherever its *prose* puts it, and for a question phrased as a symptom that is somewhere in the middle of the ranking, outside the handful of entries that become the prompt.

Two arguments turn a semantic search into a hybrid one, and **no vector index is required** — BigQuery runs both legs brute force over this small table:

- `lexical_search_columns => ['question', 'answer']` — the `STRING` columns keywords are matched against
- `lexical_search_query_value => 'ERR-4417'` — the keyword text, which does **not** have to equal the semantic question

That split is the realistic shape of the feature. A support user describes the symptom in their own words while the application passes along the code from the alert or the ticket that opened the case. The question below never contains the token; the token travels beside it.

Both searches below pass `top_k => -1`, which returns every row in ranked order. That is what makes the comparison possible: you can see exactly where each retrieval mode places the entry that matters, not just whether it squeezed into the top three.

```python
hybrid_question = 'How do we make our application handle bursts of traffic without falling over?'
lexical_term = status_code  # the token written into the knowledge base in Step 1, not copied from output
context_size = 3  # how many retrieved entries Step 3 feeds into the grounded prompt

query = f'''
SELECT
  TO_HEX(MD5(CONCAT(base.question, ' ', base.answer))) AS faq_id,
  base.category,
  base.question,
  base.answer,
  distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_rag_embedded`,
  'embedding',
  query_value => (AI.EMBED(
    content => '{hybrid_question}',
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_QUERY'
  )).result,
  top_k => -1,
  distance_type => 'COSINE'
)
ORDER BY distance
'''
semantic_ranked = client.query(query).to_dataframe()
semantic_ranked.insert(0, 'rank', range(1, len(semantic_ranked) + 1))

print(f'Question: {hybrid_question}')
print(f'Semantic-only ranking of all {len(semantic_ranked)} FAQ entries '
      f'(the first {context_size} would become the RAG context):')
semantic_ranked[['rank', 'category', 'question', 'distance']]
```

### The same question, retrieved with a lexical leg

Identical query with two arguments added. `distance_type => 'COSINE'` still governs the semantic leg, but the `distance` column it returns is no longer a cosine distance — the next section takes that number apart.

```python
query = f'''
SELECT
  TO_HEX(MD5(CONCAT(base.question, ' ', base.answer))) AS faq_id,
  base.category,
  base.question,
  base.answer,
  distance
FROM VECTOR_SEARCH(
  TABLE `{PROJECT_ID}.{DATASET_ID}.workflow_rag_embedded`,
  'embedding',
  query_value => (AI.EMBED(
    content => '{hybrid_question}',
    endpoint => 'text-embedding-005',
    task_type => 'RETRIEVAL_QUERY'
  )).result,
  top_k => -1,
  distance_type => 'COSINE',
  lexical_search_columns => ['question', 'answer'],
  lexical_search_query_value => '{lexical_term}'
)
ORDER BY distance
'''
hybrid_ranked = client.query(query).to_dataframe()
hybrid_ranked.insert(0, 'rank', range(1, len(hybrid_ranked) + 1))

print(f'Question: {hybrid_question}')
print(f'Lexical term: {lexical_term}')
hybrid_ranked[['rank', 'category', 'question', 'distance']]
```

### Recall comparison

"Did the right document come back?" is the only retrieval question that matters to a RAG answer. Score it the same way for both modes: treat every FAQ entry that literally mentions the token as relevant, then ask how many of them land inside the `context_size` window that gets pasted into the prompt.

The two result sets are joined on `faq_id`, the content hash computed in each query, because the knowledge base is regenerated on every run and has no primary key of its own — joining on question text alone would fan out if Gemini ever produced two entries with the same wording.

The cell prints the outcome rather than asserting it: the recall table for both modes, the entries hybrid added to the context window, the entries it pushed out to make room, and how far the token-bearing entry moved. Read all four as measurements of this run. The size of the move is not arbitrary either — Reciprocal Rank Fusion fixes how far a perfect keyword match can carry a row, and the next section derives that limit from the returned scores.

```python
gold_pattern = lexical_term.lower()  # the token itself, matched case-insensitively


def mark_matches(ranked):
    text = (ranked['question'] + ' ' + ranked['answer']).str.lower()
    return ranked.assign(mentions_term=text.str.contains(gold_pattern, regex=False))


semantic_marked = mark_matches(semantic_ranked)
hybrid_marked = mark_matches(hybrid_ranked)

assert semantic_marked['faq_id'].is_unique, 'duplicate FAQ text in the knowledge base — rerun Step 1'
relevant_total = int(semantic_marked['mentions_term'].sum())
print(f'{relevant_total} of {len(semantic_marked)} FAQ entries mention "{lexical_term}"')

summary = []
for label, ranked in [('semantic only', semantic_marked), ('hybrid', hybrid_marked)]:
    in_context = int(ranked.head(context_size)['mentions_term'].sum())
    matched_ranks = ranked.loc[ranked['mentions_term'], 'rank']
    summary.append({
        'retrieval': label,
        f'relevant entries in top {context_size}': in_context,
        f'recall@{context_size}': round(in_context / relevant_total, 2) if relevant_total else None,
        'best rank of a relevant entry': int(matched_ranks.min()) if len(matched_ranks) else None,
    })
display(pd.DataFrame(summary))

# what the lexical leg changed about the context window that reaches the prompt
sem_window = set(semantic_ranked.head(context_size)['faq_id'])
hyb_window = set(hybrid_ranked.head(context_size)['faq_id'])
titles = dict(zip(hybrid_ranked['faq_id'], hybrid_ranked['question']))
added = [titles[i] for i in hybrid_ranked['faq_id'] if i in hyb_window - sem_window]
dropped = [titles[i] for i in semantic_ranked['faq_id'] if i in sem_window - hyb_window]
print(f'Entries hybrid added to the top {context_size} that semantic-only missed: {added or "none"}')
print(f'Entries hybrid pushed out of the top {context_size} to make room: {dropped or "none"}')

# where the lexical leg moved each relevant entry
moves = (semantic_marked.loc[semantic_marked['mentions_term'], ['faq_id', 'question', 'rank']]
         .rename(columns={'rank': 'semantic_rank'})
         .merge(hybrid_marked[['faq_id', 'rank']].rename(columns={'rank': 'hybrid_rank'}),
                on='faq_id'))
moves['positions_gained'] = moves['semantic_rank'] - moves['hybrid_rank']
moves[['question', 'semantic_rank', 'hybrid_rank', 'positions_gained']]
```

### Reading the hybrid `distance`

Under hybrid retrieval the `distance` column is **not** a distance. Semantic-only values above are cosine distances, where a perfect match is `0`; hybrid values cluster tightly just above `0.967`, and a row that is its own best match still scores about `0.967`, never `0`. The two columns are **not comparable** — do not plot them on one axis, do not threshold hybrid values with a cosine cutoff, and do not call a hybrid value a cosine distance. Use it for ordering, nothing else.

What the number is: **one minus a Reciprocal Rank Fusion score**. Each leg — the vector search and the lexical (BM25) search — produces its own ranked list, and every row scores the sum of `1 / (k + rank)` over the two lists, with the standard constant `k = 60` on the vector leg. Taking the returned values apart row by row shows something the standard form does not predict: the two legs do not count from the same base. The lexical leg uses 61.

```
distance = 1 − ( 1/(60 + rank_vector) + 1/(61 + rank_lexical) )
```

Worked example — a row the vector leg ranks 5th and the lexical leg ranks 1st:

```
1/(60 + 5)     = 0.0153846153846154   ← rank 5 in the vector list
1/(61 + 1)     = 0.0161290322580645   ← rank 1 in the lexical list
                 -------------------
sum            = 0.0315136476426799
distance       = 1 − sum = 0.9684863523573201
```

Three consequences fall straight out of the formula:

- The floor is `1 − (1/61 + 1/62) = 0.96748`, scored by a row both legs rank first. That is why hybrid results look like a narrow band of numbers rather than a spread.
- Rank, not similarity, is what fuses. A lexical match that is barely better than the next one moves a row exactly as far as a decisive one does.
- **Every pooled row collects both terms.** BigQuery hands the lexical leg the top `10 * top_k` rows by vector rank, and inside that candidate pool it ranks *all* of them, not just the rows BM25 matched: the matches take lexical ranks `1..m` and every remaining candidate falls in behind them in its vector order. Both searches above pass `top_k => -1`, so the pool here is the entire knowledge base — which is why the decomposition below returns a lexical rank for every entry and not only for the one carrying the token. No pooled row is ever missing from a list, so no pooled row ever forfeits a term. An entry that never mentions `ERR-4417` still earns a lexical rank — its own vector rank, pushed down one place for each matching entry below it. Only where nothing matches at all does that reduce to `1 − ( 1/(60 + r) + 1/(61 + r) )` at vector rank `r`.

What a keyword match buys is lexical rank 1, worth `1/62 ≈ 0.0161`, and `top_k` bounds how far that carries a row twice over. The pool comes first: a row deeper than `10 * top_k` in the vector ranking is never handed to the lexical leg, so no match can promote it. Then the score. A matched row at vector rank `R` scores `1/(60 + R) + 1/62`; to make a window of `top_k` documents it has to beat the row on the last slot, which keeps vector rank `top_k` and, pushed down one place by the match, takes lexical rank `top_k + 1`, scoring `1/(60 + top_k) + 1/(61 + top_k + 1)`. The reach is the smaller of the two bounds:

| `top_k` | 2 | 3 | 5 | 10 | 20 | 30 | 40 | 50 | 51 | 64 | 100 | 208 | 300 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deepest semantic rank retrievable | 3 | 6 | 10 | 23 | 56 | 110 | 212 | 468 | 510 | 640 | 1,000 | 2,080 | 3,000 |

The score gate binds below `top_k = 51`; from there up the pool is the tighter one and reach settles at exactly `10 * top_k`. The searches here pass `top_k => -1` so that every entry comes back ranked and the whole comparison is visible; a production pipeline sets `top_k` to the number of documents it means to paste into the prompt. A three-document context window reaches vector rank 6, so on this run the lexical leg re-ranks the neighbourhood rather than rescuing an entry from the back of the list — the cell below recomputes that bound from the rank bases it measures. The sizing rule that falls out: to retrieve an entry sitting at vector rank `R` by its exact token, `top_k` has to be at least `R / 10` — a floor, not a recipe. That ratio is the pool bound alone, and below a few hundred ranks deep the score bound is the tighter of the two, so take the requirement from the reach table above: an entry at vector rank 100 needs `top_k = 29`, not 10. Only above the crossover at `top_k = 51` does `R / 10` become the answer itself.

> **Reverse-engineered from observation, not documented by Google.** The reference pages describe no fusion algorithm, return no score or rank column, and still define `distance` as the semantic distance — which the hybrid output contradicts. A Google Cloud blog post names "Reciprocal Rank Fusion and BM25" without publishing a formula. The decomposition above reproduces observed values exactly, rank-base asymmetry and all, but it is inferred from behavior and can change without notice. Build on the *ordering*; never hard-code the arithmetic.

The cell below re-derives it on this run's results: it takes each returned row's known vector rank, subtracts that leg's contribution from the observed score, and solves for the lexical rank the fusion must have used. Whole numbers confirm the `1/(k + rank)` shape. Whether those numbers form a permutation of `1..n` is a second, independent check, and it is the one that exposes the rank base. Solved with 60 on both legs, the implied ranks come out as `2..n + 1` over an `n`-entry knowledge base — for the thirteen entries here, ranks running `2..14`, with 14 one past the last rank such a list can hand out. That is not an anomaly in the data and not a rounding artifact; it is precisely what a lexical base of 61 looks like when it is decoded with 60. Every implied rank lands one too high, so subtract one to read the true 1-based lexical ranks: the entry carrying the token holds lexical rank 1, and the rest follow in the order the vector leg put them in.

```python
rrf_k = 60  # the standard Reciprocal Rank Fusion constant

decomposed = (hybrid_ranked[['rank', 'faq_id', 'question', 'distance']]
              .rename(columns={'rank': 'hybrid_rank', 'distance': 'hybrid_distance'})
              .merge(semantic_ranked[['faq_id', 'rank']].rename(columns={'rank': 'vector_rank'}),
                     on='faq_id'))


def implied_lexical_rank(row):
    """Solve 1 - (1/(k + rank_vector) + 1/(k + rank_lexical)) = distance for rank_lexical."""
    residual = (1 - row['hybrid_distance']) - 1 / (rrf_k + row['vector_rank'])
    if residual <= 1e-9:
        return float('nan')  # no lexical term in the sum: only the vector leg returned this row
    return 1 / residual - rrf_k


decomposed['implied_lexical_rank'] = decomposed.apply(implied_lexical_rank, axis=1)
decomposed['is_whole_number'] = (
    (decomposed['implied_lexical_rank'] - decomposed['implied_lexical_rank'].round()).abs() < 1e-6)

whole = int(decomposed['is_whole_number'].sum())
n = len(decomposed)
print(f'{whole} of {n} returned rows decompose to whole-number lexical ranks at k = {rrf_k}.')

# Whole numbers confirm the 1/(k + rank) shape. They do not confirm the rank base: check the
# implied ranks against 1..n, the only set an n-document lexical list can hand out.
implied = sorted(int(r) for r in decomposed.loc[decomposed['is_whole_number'],
                                                'implied_lexical_rank'].round())
expected = list(range(1, n + 1))
lexical_base = None
if whole < n:
    print(f'{n - whole} row(s) do not fit the formula at all — the undocumented scoring has '
          f'changed and only the result ordering can be trusted.')
elif implied == expected:
    lexical_base = rrf_k
    print(f'The implied ranks are a permutation of 1..{n}: both legs count from 1 and the formula '
          f'is complete as written.')
elif implied == [r + implied[0] - 1 for r in expected]:
    offset = implied[0] - 1
    lexical_base = rrf_k + offset
    print(f'The implied ranks are 1..{n} shifted by exactly +{offset}: they run {implied[0]}..'
          f'{implied[-1]}, and no {n}-document list can hand out a rank of {implied[-1]}. '
          f'The two legs do not share a rank base — the lexical term is '
          f'1/({lexical_base} + rank_lexical) against 1/({rrf_k} + rank_vector) for the vector '
          f'leg. Subtract {offset} from the column below to read true 1-based lexical ranks: the '
          f'row carrying the token holds lexical rank 1, and every other row follows behind it in '
          f'the order the vector leg put them in.')
else:
    print(f'The implied ranks are whole numbers but neither a permutation of 1..{n} nor a uniform '
          f'shift of one: {implied}. Trust the ordering, not the arithmetic.')

display(decomposed[['hybrid_rank', 'question', 'hybrid_distance', 'vector_rank',
                    'implied_lexical_rank', 'is_whole_number']])

# How far can lexical rank 1 carry a row? It has to outscore the row the vector leg ranked at the
# edge of the context window, which keeps its vector rank and takes the lexical rank just below
# the matched row. Everything here is arithmetic on the base the decomposition just measured.
if lexical_base is not None:
    def fused_score(vector_rank, lexical_rank):
        return 1 / (rrf_k + vector_rank) + 1 / (lexical_base + lexical_rank)

    edge = fused_score(context_size, context_size + 1)
    reach = [v for v in range(1, n + 1) if fused_score(v, 1) > edge]
    if reach:
        print(f'\nA row the lexical leg ranks first outscores the row the vector leg ranked '
              f'#{context_size} only from vector rank {min(reach)} through {max(reach)} of {n}. '
              f'Deeper in the semantic ranking than that, one perfect keyword match still cannot '
              f'reach a {context_size}-document context window: hybrid promotes, it does not rescue.')
    else:
        print(f'\nNo vector rank lets a lexical-rank-1 row into the top {context_size} on this run.')
```

### Batch RAG or hybrid retrieval? A rule for choosing

|  | Batch RAG (Step 4) | Hybrid retrieval (Step 5) |
|---|---|---|
| Query form | query table — many questions in one call | `query_value` — exactly one question per call |
| Lexical leg | not available | `lexical_search_columns` + `lexical_search_query_value` |
| Cost per question | one scan of the base table amortized across the whole batch | one embedding call and one scan per question |
| Score returned | cosine distance — comparable across rows, runs and queries | fused RRF value — ordering only |
| Reach | whatever the embedding ranks | set by `top_k` twice over — 6 vector ranks deep at 3 documents, 23 at 10, and never deeper than `10 × top_k` |
| Fails at | questions that hinge on a literal token | question volume, and — at a small context window — tokens buried deep in the semantic ranking |

**The rule:** batch when the question set is large and phrased in ordinary language, where meaning alone retrieves the right document. Go hybrid, one query at a time, when a specific token has to appear in the retrieved context for the answer to be correct — a SKU, an error code, a version string, an API name, a customer name.

**Know what hybrid is buying, and size the window to match.** The two fusion terms are comparable in size, so lexical rank 1 lifts a row by a bounded number of positions — the cell above computes how many for this run. At a three-document window that bound is vector rank 6, which makes hybrid a re-ranker: it pays off only where the semantic leg already placed the entry in the neighbourhood. The bound moves fast as the window widens, but never stops being a bound: above `top_k = 50` it is the `10 × top_k` candidate pool that binds, because a row deeper than that is never shown to the lexical leg. Size for the target — to surface an entry at vector rank `R` by its exact token, `R / 10` rows is the minimum to retrieve and re-rank, and below a few hundred ranks deep it is not enough on its own: an entry at vector rank 100 needs `top_k = 29` rather than 10. Take the number from the reach table in the section above. When the token *is* the question and you want a guarantee rather than an arithmetic bound, filter on it directly with `WHERE REGEXP_CONTAINS(...)` before or instead of the vector search — a predicate cannot be outranked by a fusion score, and it has no pool.

**When both are true** — many questions *and* token-sensitive answers — do not try to make one call do both, because the API will not let you. Route instead: run the cheap batch pass over every question, then re-retrieve with hybrid only for the questions that carry a literal token. Detect those with `REGEXP_CONTAINS` against a token pattern, or route on the entity your application already knows it is asking about. Fanning out one call per question is the price of the lexical leg; paying it only for the minority of questions that need it keeps batch economics for the rest.
