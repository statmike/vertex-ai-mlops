![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ml&file=RESOURCES.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ml/RESOURCES.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/RESOURCES.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/RESOURCES.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/RESOURCES.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ml/RESOURCES.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/RESOURCES.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ml/RESOURCES.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# BigQuery ML — Detailed Reference

BigQuery ML lets you create and run machine learning models using SQL. Models are first-class dataset objects created with `CREATE MODEL` and consumed with `ML.*` table-valued functions. Most model types train on data already in BigQuery — no connection, no data movement, and no separate training service.

This is the index to the deep per-item reference for the project; each section below is its own page under [`reference/`](reference/). For the map (tables + diagram + tree) see [README.md](README.md); for conventions, templates, the backlog, and the audit procedure see [PLANS.md](PLANS.md).

**How the pieces fit:**
- **`CREATE MODEL`** trains a model and stores it in a dataset. The `model_type` option selects the algorithm.
- **Lifecycle `ML.*` functions** operate on a trained model: evaluate it, predict with it, explain it, introspect it.
- **Model-free `ML.*` functions** transform data directly (preprocessing, distance, text, image) — no model required.
- **Model management** covers exporting models to GCS, importing external models, calling remote endpoints, and monitoring.

For each item we collect: a description and use cases, the documentation URL (a research-retrieval page for audits), syntax, inputs, outputs, the models it applies to / lifecycle functions it supports, best practices, limitations, the BigFrames equivalent, and a **tested repo example** wherever one exists.

## Sections

- [Scope & Cross-References](#scope--cross-references) — what this project owns, and where `bq-ai-functions` takes over *(on this page)*
- **[Comparison Tables](reference/comparison-tables.md)** — the fast answer to "which model / which function?" — `model_type` catalog, metric columns by task, capability matrix, explainability and connection matrices
- **[CREATE MODEL — Model Types](reference/create-model-model-types.md)** — every `model_type`, from `LINEAR_REG` through `ARIMA_PLUS_XREG`, imported (TensorFlow/ONNX/XGBoost), `REMOTE`, and `TRANSFORM_ONLY`
- **[Model Lifecycle Functions](reference/model-lifecycle-functions.md)** — the `ML.*` functions that act on a trained model — evaluate, predict, explain, weights, introspection, forecasting, `ML.TRANSFORM`
- **[Model-Free Functions](reference/model-free-functions.md)** — the `ML.*` functions that need no model — scalers, bucketizing, encoders, imputation, feature crosses, text, distance, image, time-series decomposition, `AI.CAUSAL_EFFECT` for intervention analysis, and `ML.METRICS` for scoring saved predictions
- **[Model Management & Monitoring](reference/model-management-monitoring.md)** — `EXPORT MODEL`, plus data description, skew/drift validation, and the TFDV functions
- [BigFrames (Python)](#bigframes-python) — the `bigframes.ml` surface that trains these same models from Python *(on this page)*

---

## Scope & Cross-References

This project (`bq-ml`) covers the **`CREATE MODEL` + `ML.*` lifecycle** — training models in SQL and the functions that evaluate, predict with, explain, and introspect them, plus model-free preprocessing and model management/monitoring.

Its sibling project **[`../bq-ai-functions/`](../bq-ai-functions/RESOURCES.md)** covers the **generative-AI / foundation-model `AI.*` (and LLM `ML.*`) functions** (Gemini-in-SQL, embeddings, TimesFM forecasting, document processing). Where a topic is owned there, this reference **hyperlinks out rather than duplicating it**:

| Topic encountered in bq-ml | Cross-link to bq-ai-functions (not duplicated here) |
|---|---|
| Contribution analysis (`CONTRIBUTION_ANALYSIS` model) | [`AI.KEY_DRIVERS`](../bq-ai-functions/RESOURCES.md) — the model-free equivalent |
| TimesFM forecasting (built-in foundation forecaster) | [`AI.FORECAST`, `AI.EVALUATE`, `AI.DETECT_ANOMALIES`](../bq-ai-functions/RESOURCES.md) |
| Document processing | [`ML.DOCUMENT_PROCESS`](../bq-ai-functions/RESOURCES.md) |
| LLM text generation | [`ML.GENERATE_TEXT`, `AI.GENERATE_*`](../bq-ai-functions/RESOURCES.md) |
| Foundation-model embeddings | [foundation `ML.GENERATE_EMBEDDING` / `AI.GENERATE_EMBEDDING`](../bq-ai-functions/RESOURCES.md) |
| Remote-model LLM endpoints | [the remote-model LLM pattern](../bq-ai-functions/RESOURCES.md) |

**Nuances kept in-scope here:** `ML.GENERATE_EMBEDDING` used to extract embeddings *from a trained `PCA` / `AUTOENCODER` / `MATRIX_FACTORIZATION` model* is a lifecycle use of a BQML model and is documented here; the foundation-model (text/multimodal) use cross-links out. The remote-model *mechanism* (`CREATE MODEL ... REMOTE WITH CONNECTION` querying a custom Vertex AI endpoint with `ML.PREDICT`) is documented here; LLM endpoint *usage* cross-links out.

**One `AI.*` function is owned here, not there.** The dividing line is *"does the reader manage a model artifact,"* not *"does the name start with `AI.`"*:

| Topic | Owned here, linked from bq-ai-functions |
|---|---|
| Intervention / causal-impact analysis | [`AI.CAUSAL_EFFECT`](reference/model-free-functions.md#aicausal_effect) — creates no model, and its subject is causal inference, which [`workflows/`](README.md#workflows) already covers in five other places. Its counterfactual is measurably plain `ARIMA_PLUS`. The sibling project keeps a pointer so its `AI.*` list stays complete. |

---

## BigFrames (Python)

BigFrames exposes a scikit-learn-style API (`bigframes.ml`) that trains BigQuery ML models under the hood — e.g. `bigframes.ml.linear_model.LinearRegression`/`LogisticRegression`, `bigframes.ml.ensemble.XGBClassifier`/`RandomForestClassifier`, `bigframes.ml.cluster.KMeans`, `bigframes.ml.decomposition.PCA`/`MatrixFactorization`, `bigframes.ml.forecasting.ARIMAPlus`, `bigframes.ml.preprocessing.*`, and `bigframes.ml.imported.{TensorFlowModel,ONNXModel,XGBoostModel}`. Each reference entry lists its BigFrames equivalent (or notes when none exists and SQL is the path). [bigframes.ml reference](https://cloud.google.com/python/docs/reference/bigframes/latest/bigframes.ml).
