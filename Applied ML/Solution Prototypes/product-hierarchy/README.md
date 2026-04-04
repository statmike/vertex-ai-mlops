![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FSolution+Prototypes%2Fproduct-hierarchy&file=README.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/product-hierarchy/README.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/Solution%2520Prototypes/product-hierarchy/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/Solution%2520Prototypes/product-hierarchy/README.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/Solution%2520Prototypes/product-hierarchy/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/Solution%2520Prototypes/product-hierarchy/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/Solution%20Prototypes/product-hierarchy/README.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/Solution%20Prototypes/product-hierarchy/README.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Product Hierarchy

Classify products into a Department → Category hierarchy using nine approaches across three paradigms: flat classification, top-down hierarchical classifiers, and multi-task learning.

## Notebooks

### 1. [product-hierarchy.ipynb](product-hierarchy.ipynb) — Python-First (Synthetic Data)

Generates a synthetic product catalog and ambiguous "incoming vendor products" using **Gemini structured output** with Pydantic schemas, then classifies the new products using all nine approaches in Python.

**Part 1: Flat Classification** — Each Department/Category path is treated as an independent label.

| # | Approach | Method |
|---|----------|--------|
| 1 | Fuzzy String Matching | Levenshtein distance via `thefuzz` `token_set_ratio` |
| 2 | Semantic Embeddings (Nearest Neighbor) | `gemini-embedding-001` cosine similarity to closest catalog item |
| 3 | Centroid Matching | Cosine similarity to mean embedding per category |
| 4 | Gradient Boosting Classifier | scikit-learn GBC trained on embedding vectors |

**Part 2: Local Classifiers (Top-Down)** — Predict Department first, then route to a per-department Category classifier. Demonstrates cascading error risk.

| # | Approach | Method |
|---|----------|--------|
| 5 | Hierarchical Embeddings | Nearest neighbor within best-matching department |
| 6 | Hierarchical Centroids | Department centroid → category centroid (two-step) |
| 7 | Hierarchical Gradient Boosting | Cascading GBC: 1 department model + 5 per-department category models |

**Part 3: Multi-Task Learning** — Keras neural networks with shared hidden layers and separate output heads for Department and Category.

| # | Approach | Method |
|---|----------|--------|
| 8 | Independent Heads | Two softmax outputs sharing hidden layers — can produce invalid dept/category combinations |
| 9 | Conditional Category Head | Department prediction feeds into category head — learns valid combinations naturally |

The notebook concludes with a side-by-side comparison of all nine approaches and a decision guide for choosing the right paradigm.

### 2. [product-hierarchy-bq.ipynb](product-hierarchy-bq.ipynb) — SQL-First (Real Data in BigQuery)

Takes the same nine approaches and applies them to **real data** (~29K products from `bigquery-public-data.thelook_ecommerce.products`) using **BigQuery SQL** wherever possible. Embeddings, vector search, centroid computation, and model training all happen in the data warehouse — no data movement required.

| # | Approach | Implementation |
|---|----------|----------------|
| 1 | Levenshtein Distance | Spark — Dataproc Serverless |
| 2 | Semantic Embeddings (Nearest Neighbor) | SQL — `VECTOR_SEARCH` |
| 3 | Centroid Matching | SQL — `VECTOR_SEARCH` with unnest/avg/re-aggregate centroids |
| 4 | Gradient Boosting Classifier | SQL — `CREATE MODEL` (BOOSTED_TREE_CLASSIFIER) |
| 5 | Hierarchical Embeddings | SQL — `VECTOR_SEARCH` with department routing |
| 6 | Hierarchical Centroids | SQL — `VECTOR_SEARCH` (dept + category centroids) |
| 7 | Hierarchical GBC | SQL — Cascading `CREATE MODEL` + `ML.PREDICT` |
| 8 | MTL — Independent Heads | Python — Keras (embeddings pulled from BQ) |
| 9 | MTL — Conditional Category Head | Python — Keras (embeddings pulled from BQ) |

**Bonus — Serve Keras Models via BigQuery ML:** The Keras MTL models are exported as TensorFlow SavedModel, uploaded to GCS, and imported into BigQuery with `CREATE MODEL ... OPTIONS(MODEL_TYPE='TENSORFLOW')`. Predictions are then served with `ML.PREDICT` entirely in SQL — bringing Python-trained deep learning models into the same SQL-based serving path as the BQML-native approaches.

**Key differences from notebook 1:** 90/10 stratified train/test split, `text-embedding-005` via `AI.EMBED` (768-dim) — the standard embedding endpoint for BigQuery AI functions (notebook 1 uses `gemini-embedding-001` via the GenAI SDK), and statistically meaningful accuracy on ~2,900 test products.

## Prerequisites

- A Google Cloud project with billing enabled
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and authenticated
- Required APIs enabled (each notebook includes a cell to enable these):

| API | Notebook 1 | Notebook 2 | Purpose |
|-----|:---:|:---:|---------|
| [Vertex AI](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com) | x | x | Gemini models, embeddings |
| [BigQuery](https://console.cloud.google.com/apis/library/bigquery.googleapis.com) | | x | Data storage, BQML, `AI.EMBED`, `VECTOR_SEARCH` |
| [BigQuery Connection](https://console.cloud.google.com/apis/library/bigqueryconnection.googleapis.com) | | x | Required for `AI.EMBED` to call Vertex AI models |
| [Dataproc](https://console.cloud.google.com/apis/library/dataproc.googleapis.com) | | x | Approach 1 — Spark Connect via Dataproc Serverless |

## Environment Setup

### Option 1: Local environment

Set up a local Python environment and register it as a Jupyter kernel. From this directory (`Applied ML/Solution Prototypes/product-hierarchy/`):

**Python version:** This project requires Python >= 3.10. Use whichever version manager you prefer:
- **pyenv**: `pyenv install 3.11 && pyenv local 3.11` — all tools below will use it automatically
- **uv**: downloads a compatible version automatically if one isn't found
- **system**: any system Python >= 3.10 works

**uv** (recommended)
```bash
uv sync
uv run python -m ipykernel install --user --name product-hierarchy --display-name "Product Hierarchy"
```

**pip**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m ipykernel install --user --name product-hierarchy --display-name "Product Hierarchy"
```

**poetry**
```bash
poetry install
poetry run python -m ipykernel install --user --name product-hierarchy --display-name "Product Hierarchy"
```

Then select the **Product Hierarchy** kernel in your notebook.

### Option 2: Standalone

Each notebook includes an environment setup cell that installs required packages into your current kernel using `uv` (if available) with `pip` fallback. No pre-configuration needed — just run the notebook.
