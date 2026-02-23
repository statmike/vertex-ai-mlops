"""Scheduled BM25 drift detection with conditional rebuild.

Step 9: Check whether the BM25 vocabulary has drifted from the current corpus.
If any drift metric exceeds its threshold, retrain the model with an incremented
version number and save the new vocabulary + metadata to BigQuery. The previous
version is preserved for comparison and rollback.

After a rebuild, run apply_bm25.py to compute new sparse embeddings and update
BQ chunk tables + VS2 DataObjects.

Designed to be run on a schedule (e.g., Cloud Scheduler -> Cloud Run function).
The schedule-based approach checks first, then rebuilds only if warranted.
"""

import string
import datetime

import nltk
from rank_bm25 import BM25Okapi
from google.cloud import bigquery
from config import (
    BQ_PROJECT, BQ_DATASET, BQ_TABLE_PREFIX,
    BM25_K1, BM25_B, BM25_EPSILON, BM25_NGRAMS,
    BM25_OOV_THRESHOLD, BM25_STALE_THRESHOLD, BM25_CORPUS_DELTA,
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
    """Preprocess text for BM25."""
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
    """Construct BM25 input: text_content + enrichment tags."""
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
# 1. Load current model metadata
# =============================================================================

print("=" * 60)
print("1. Loading current BM25 model metadata")
print("=" * 60)

model_table = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_bm25_model"
vocab_table = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_bm25_vocabulary"

model_rows = list(bq.query(
    f"SELECT * FROM `{model_table}` ORDER BY model_version DESC LIMIT 1"
).result())
if not model_rows:
    print("  No existing BM25 model found. Run build_bm25.py first.")
    exit(0)

model_meta = model_rows[0]
print(f"  Current version: {model_meta.model_version}")
print(f"  Corpus size: {model_meta.corpus_size}")
print(f"  Vocabulary size: {model_meta.vocab_size}")
print(f"  Trained at: {model_meta.trained_at}")

# Load stored vocabulary terms
vocab_rows = list(bq.query(
    f"SELECT term FROM `{vocab_table}` WHERE model_version = {model_meta.model_version}"
).result())
stored_vocab = {row.term for row in vocab_rows}

# =============================================================================
# 2. Read current corpus and compute terms
# =============================================================================

print("\n" + "=" * 60)
print("2. Reading current corpus")
print("=" * 60)

sources = [
    ("reddit", "SELECT chunk_id, text_content, topics, methods_mentioned"),
    ("zoom", "SELECT chunk_id, text_content, topics, action_items"),
    ("pdf", "SELECT chunk_id, text_content, topics, functions_referenced"),
]

all_bm25_texts = []
current_terms = set()

for source_type, query in sources:
    table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE_PREFIX}_{source_type}_chunks"
    rows = list(bq.query(f"{query} FROM `{table_ref}`").result())
    for row in rows:
        bm25_text = build_bm25_text(row, source_type)
        tokens = chunk_prep(bm25_text)
        current_terms.update(tokens)
        all_bm25_texts.append(bm25_text)
    print(f"  {source_type}: {len(rows)} chunks")

current_corpus_size = len(all_bm25_texts)
print(f"  Total: {current_corpus_size} chunks, {len(current_terms)} unique terms")

# =============================================================================
# 3. Compute drift metrics
# =============================================================================

print("\n" + "=" * 60)
print("3. Computing drift metrics")
print("=" * 60)

oov_terms = current_terms - stored_vocab
stale_terms = stored_vocab - current_terms

oov_rate = len(oov_terms) / len(current_terms) if current_terms else 0
stale_rate = len(stale_terms) / len(stored_vocab) if stored_vocab else 0
corpus_delta = abs(current_corpus_size - model_meta.corpus_size) / model_meta.corpus_size if model_meta.corpus_size else 0

print(f"  OOV rate:     {oov_rate:.1%} ({len(oov_terms)} new terms)  [threshold: {BM25_OOV_THRESHOLD:.0%}]")
print(f"  Stale rate:   {stale_rate:.1%} ({len(stale_terms)} stale terms)  [threshold: {BM25_STALE_THRESHOLD:.0%}]")
print(f"  Corpus delta: {corpus_delta:.1%} ({model_meta.corpus_size} -> {current_corpus_size})  [threshold: {BM25_CORPUS_DELTA:.0%}]")

# =============================================================================
# 4. Check thresholds
# =============================================================================

rebuild_needed = False
reasons = []

if oov_rate >= BM25_OOV_THRESHOLD:
    rebuild_needed = True
    reasons.append(f"OOV rate {oov_rate:.1%} >= {BM25_OOV_THRESHOLD:.0%}")

if stale_rate >= BM25_STALE_THRESHOLD:
    rebuild_needed = True
    reasons.append(f"Stale rate {stale_rate:.1%} >= {BM25_STALE_THRESHOLD:.0%}")

if corpus_delta >= BM25_CORPUS_DELTA:
    rebuild_needed = True
    reasons.append(f"Corpus delta {corpus_delta:.1%} >= {BM25_CORPUS_DELTA:.0%}")

if not rebuild_needed:
    print("\n" + "=" * 60)
    print("No rebuild needed — all metrics within thresholds.")
    print("=" * 60)
    exit(0)

print("\n" + "=" * 60)
print("REBUILD TRIGGERED")
for r in reasons:
    print(f"  - {r}")
print("=" * 60)

# =============================================================================
# 5. Retrain with incremented version
# =============================================================================

new_version = model_meta.model_version + 1
print(f"\nRebuilding BM25 model (version {model_meta.model_version} -> {new_version})")

# Tokenize full corpus
tokenized_corpus = [chunk_prep(text) for text in all_bm25_texts]

# Train
bm25_model = BM25Okapi(tokenized_corpus, k1=BM25_K1, b=BM25_B, epsilon=BM25_EPSILON)
vocabulary = bm25_model.idf.keys()
vocab_map = {word: i for i, word in enumerate(vocabulary)}
trained_at = datetime.datetime.now(datetime.timezone.utc)

print(f"  Vocabulary: {len(vocabulary)} terms")
print(f"  Average doc length: {bm25_model.avgdl:.1f}")

# Save vocabulary (append — preserves version history)
vocab_rows_new = [
    {"term": term, "term_index": idx, "idf": bm25_model.idf[term],
     "model_version": new_version, "trained_at": trained_at.isoformat()}
    for term, idx in vocab_map.items()
]
job_config = bigquery.LoadJobConfig(
    schema=[
        bigquery.SchemaField("term", "STRING"),
        bigquery.SchemaField("term_index", "INT64"),
        bigquery.SchemaField("idf", "FLOAT64"),
        bigquery.SchemaField("model_version", "INT64"),
        bigquery.SchemaField("trained_at", "TIMESTAMP"),
    ],
    write_disposition="WRITE_APPEND",
)
bq.load_table_from_json(vocab_rows_new, vocab_table, job_config=job_config).result()
print(f"  Vocabulary saved to BQ ({len(vocab_rows_new)} terms)")

# Save model metadata (append — preserves version history)
model_row = [{
    "model_version": new_version,
    "corpus_size": current_corpus_size,
    "vocab_size": len(vocabulary),
    "avgdl": bm25_model.avgdl,
    "k1": BM25_K1, "b": BM25_B, "epsilon": BM25_EPSILON,
    "ngrams": BM25_NGRAMS,
    "trained_at": trained_at.isoformat(),
}]
job_config = bigquery.LoadJobConfig(
    schema=[
        bigquery.SchemaField("model_version", "INT64"),
        bigquery.SchemaField("corpus_size", "INT64"),
        bigquery.SchemaField("vocab_size", "INT64"),
        bigquery.SchemaField("avgdl", "FLOAT64"),
        bigquery.SchemaField("k1", "FLOAT64"),
        bigquery.SchemaField("b", "FLOAT64"),
        bigquery.SchemaField("epsilon", "FLOAT64"),
        bigquery.SchemaField("ngrams", "INT64"),
        bigquery.SchemaField("trained_at", "TIMESTAMP"),
    ],
    write_disposition="WRITE_APPEND",
)
bq.load_table_from_json(model_row, model_table, job_config=job_config).result()
print(f"  Model metadata saved to BQ")

# =============================================================================
# Done
# =============================================================================

print("\n" + "=" * 60)
print(f"Rebuild complete! Model version: {new_version}")
print("=" * 60)
print(f"\n  Next: run apply_bm25.py to compute embeddings and update BQ + VS2")
print(f"    uv run python apply_bm25.py")
print(f"    uv run python apply_bm25.py --version {new_version}")
