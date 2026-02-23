"""Train a BM25 model and store the vocabulary + metadata in BigQuery.

Step 7a: Reads all chunks from BigQuery, builds BM25 input text (Approach B:
text_content + enrichment tags), trains a BM25Okapi model, and saves the vocabulary
and model parameters to BigQuery. Each training creates a new version — all versions
are retained for comparison and rollback.

After training, run apply_bm25.py to compute sparse embeddings and update BQ chunk
tables + VS2 DataObjects.

BM25 input uses Approach B: text_content concatenated with enrichment tag values
(topics, methods, functions, action items). This normalizes extracted concepts into the
BM25 vocabulary — a topic like "demand forecasting" tagged on both a Reddit chunk and
a PDF chunk produces shared BM25 terms that wouldn't appear in the raw text of both.
"""

import string
import datetime

import nltk
from rank_bm25 import BM25Okapi
from google.cloud import bigquery
from config import (
    BQ_PROJECT, BQ_DATASET, BQ_TABLE_PREFIX,
    BM25_K1, BM25_B, BM25_EPSILON, BM25_NGRAMS, BM25_MODEL_VERSION,
)

# --- NLTK setup ---

nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('wordnet', quiet=True)

lemmatizer = nltk.stem.WordNetLemmatizer()
stop_words = set(nltk.corpus.stopwords.words('english'))

# --- Client ---

bq = bigquery.Client(project=BQ_PROJECT)


# --- BM25 functions ---

def chunk_prep(text, ngrams=BM25_NGRAMS):
    """Preprocess text for BM25: lowercase, remove punctuation, tokenize,
    lemmatize, remove stopwords, generate n-grams."""
    text = text.lower().translate(str.maketrans('', '', string.punctuation))
    tokens = nltk.tokenize.word_tokenize(text)
    unigrams = [lemmatizer.lemmatize(t) for t in tokens
                if len(t) > 1 and t not in stop_words]
    if ngrams >= 2:
        all_grams = unigrams.copy()
        for n in range(2, ngrams + 1):
            all_grams.extend(' '.join(g) for g in zip(*[unigrams[i:] for i in range(n)]))
        return all_grams
    return unigrams


def build_bm25_text(row, source_type):
    """Construct BM25 input: text_content + enrichment tags (Approach B)."""
    parts = [row.text_content]
    if row.topics:
        parts.extend(row.topics)
    if source_type == 'reddit' and row.methods_mentioned:
        parts.extend(row.methods_mentioned)
    elif source_type == 'zoom' and row.action_items:
        parts.extend(row.action_items)
    elif source_type == 'pdf' and row.functions_referenced:
        parts.extend(row.functions_referenced)
    return ' '.join(parts)


# =============================================================================
# 1. Read all chunks from BigQuery
# =============================================================================

print("=" * 60)
print("1. Reading chunks from BigQuery")
print("=" * 60)

sources = [
    {
        "table": f"{BQ_TABLE_PREFIX}_reddit_chunks",
        "source_type": "reddit",
        "query": "SELECT chunk_id, text_content, topics, methods_mentioned",
    },
    {
        "table": f"{BQ_TABLE_PREFIX}_zoom_chunks",
        "source_type": "zoom",
        "query": "SELECT chunk_id, text_content, topics, action_items",
    },
    {
        "table": f"{BQ_TABLE_PREFIX}_pdf_chunks",
        "source_type": "pdf",
        "query": "SELECT chunk_id, text_content, topics, functions_referenced",
    },
]

all_chunks = []
for src in sources:
    table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{src['table']}"
    query = f"{src['query']} FROM `{table_ref}`"
    rows = list(bq.query(query).result())
    for row in rows:
        bm25_text = build_bm25_text(row, src["source_type"])
        all_chunks.append(bm25_text)
    print(f"  {src['source_type']}: {len(rows)} chunks")

print(f"  Total: {len(all_chunks)} chunks")

# =============================================================================
# 2. Preprocess and tokenize corpus
# =============================================================================

print("\n" + "=" * 60)
print("2. Preprocessing corpus")
print("=" * 60)

tokenized_corpus = [chunk_prep(text) for text in all_chunks]
print(f"  Tokenized {len(tokenized_corpus)} documents")
print(f"  Average tokens per document: {sum(len(t) for t in tokenized_corpus) / len(tokenized_corpus):.1f}")

# =============================================================================
# 3. Train BM25 model
# =============================================================================

print("\n" + "=" * 60)
print("3. Training BM25 model")
print("=" * 60)

bm25_model = BM25Okapi(
    tokenized_corpus,
    k1=BM25_K1,
    b=BM25_B,
    epsilon=BM25_EPSILON,
)

vocabulary = bm25_model.idf.keys()
vocab_map = {word: i for i, word in enumerate(vocabulary)}

print(f"  Vocabulary size: {len(vocabulary)}")
print(f"  Average document length: {bm25_model.avgdl:.1f}")
print(f"  k1={BM25_K1}, b={BM25_B}, epsilon={BM25_EPSILON}")

trained_at = datetime.datetime.now(datetime.timezone.utc)

# =============================================================================
# 4. Save vocabulary to BigQuery (append — preserves version history)
# =============================================================================

print("\n" + "=" * 60)
print("4. Saving vocabulary to BigQuery")
print("=" * 60)

vocab_table = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_bm25_vocabulary"

vocab_schema = [
    bigquery.SchemaField("term", "STRING"),
    bigquery.SchemaField("term_index", "INT64"),
    bigquery.SchemaField("idf", "FLOAT64"),
    bigquery.SchemaField("model_version", "INT64"),
    bigquery.SchemaField("trained_at", "TIMESTAMP"),
]

# Delete any existing rows for this version (idempotent re-run)
try:
    bq.query(f"DELETE FROM `{vocab_table}` WHERE model_version = {BM25_MODEL_VERSION}").result()
except Exception:
    pass  # Table may not exist yet

vocab_rows = [
    {
        "term": term,
        "term_index": idx,
        "idf": bm25_model.idf[term],
        "model_version": BM25_MODEL_VERSION,
        "trained_at": trained_at.isoformat(),
    }
    for term, idx in vocab_map.items()
]

job_config = bigquery.LoadJobConfig(
    schema=vocab_schema,
    write_disposition="WRITE_APPEND",
)
bq.load_table_from_json(vocab_rows, vocab_table, job_config=job_config).result()
print(f"  Wrote {len(vocab_rows)} terms for version {BM25_MODEL_VERSION}")

# Show version history
try:
    versions = list(bq.query(
        f"SELECT model_version, COUNT(*) as terms, MIN(trained_at) as trained_at "
        f"FROM `{vocab_table}` GROUP BY model_version ORDER BY model_version"
    ).result())
    print(f"  Version history: {len(versions)} version(s)")
    for v in versions:
        print(f"    v{v.model_version}: {v.terms} terms (trained {v.trained_at})")
except Exception:
    pass

# =============================================================================
# 5. Save model metadata to BigQuery (append — preserves version history)
# =============================================================================

print("\n" + "=" * 60)
print("5. Saving model metadata to BigQuery")
print("=" * 60)

model_table = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_bm25_model"

model_schema = [
    bigquery.SchemaField("model_version", "INT64"),
    bigquery.SchemaField("corpus_size", "INT64"),
    bigquery.SchemaField("vocab_size", "INT64"),
    bigquery.SchemaField("avgdl", "FLOAT64"),
    bigquery.SchemaField("k1", "FLOAT64"),
    bigquery.SchemaField("b", "FLOAT64"),
    bigquery.SchemaField("epsilon", "FLOAT64"),
    bigquery.SchemaField("ngrams", "INT64"),
    bigquery.SchemaField("trained_at", "TIMESTAMP"),
]

# Delete any existing row for this version (idempotent re-run)
try:
    bq.query(f"DELETE FROM `{model_table}` WHERE model_version = {BM25_MODEL_VERSION}").result()
except Exception:
    pass  # Table may not exist yet

model_row = [{
    "model_version": BM25_MODEL_VERSION,
    "corpus_size": len(all_chunks),
    "vocab_size": len(vocabulary),
    "avgdl": bm25_model.avgdl,
    "k1": BM25_K1,
    "b": BM25_B,
    "epsilon": BM25_EPSILON,
    "ngrams": BM25_NGRAMS,
    "trained_at": trained_at.isoformat(),
}]

job_config = bigquery.LoadJobConfig(
    schema=model_schema,
    write_disposition="WRITE_APPEND",
)
bq.load_table_from_json(model_row, model_table, job_config=job_config).result()
print(f"  Wrote model metadata for version {BM25_MODEL_VERSION}")

# =============================================================================
# Done
# =============================================================================

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
print(f"  Model version: {BM25_MODEL_VERSION}")
print(f"  Vocabulary: {len(vocabulary)} terms")
print(f"  Corpus: {len(all_chunks)} chunks")
print(f"  avgdl: {bm25_model.avgdl:.1f}")
print(f"\n  Next: run apply_bm25.py to compute embeddings and update BQ + VS2")
