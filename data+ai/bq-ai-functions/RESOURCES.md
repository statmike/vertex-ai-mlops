![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fbq-ai-functions&file=RESOURCES.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/bq-ai-functions/RESOURCES.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/RESOURCES.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/RESOURCES.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/RESOURCES.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/bq-ai-functions/RESOURCES.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/RESOURCES.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/bq-ai-functions/RESOURCES.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# BigQuery AI Functions Resources

BigQuery AI functions let you use generative AI, embeddings, search, forecasting, and tabular prediction directly within SQL queries. These functions span several categories: general-purpose text/multimodal generation, managed classification and scoring, embedding generation and semantic/hybrid search, and predictive AI (forecasting, anomaly detection, regression, and classification). They connect to Vertex AI models (Gemini, embedding models, TimesFM, TabFM, and third-party models) and can process structured data, text, images, audio, video, and PDFs -- all from within BigQuery SQL.

For each function we collect top level info. The documentation url is provided for each as a research retrieval page to help fill in this structure for each:
Function Name
- short description of type of function and what it does
- what this function can be used for examples
- documentation url:
- syntax
- inputs: list all possible inputs and combinations, calling out use of object refs and schemas
- outputs: list all possible outputs and their schemas (can be links)
- type: table valued, ....
- supported models: which gen ai models can be requested
- best practices
- limitations
- locations
- provisioned throughput usage

## Sections

- [Choosing a Gemini Model Endpoint](#choosing-a-gemini-model-endpoint) — which endpoint to name, and what the choice commits you to *(on this page)*
- **[General Purpose Functions](reference/general-purpose-functions.md)** — `AI.GENERATE` and its typed variants (`_BOOL`, `_DOUBLE`, `_INT`, `_TABLE`, `_TEXT`), `ML.GENERATE_TEXT`, and `AI.COUNT_TOKENS`
- **[Managed Functions](reference/managed-functions.md)** — `AI.IF`, `AI.SCORE`, `AI.CLASSIFY`, `AI.AGG` — managed endpoints, no connection or model object to create
- **[Embedding Generation and Semantic Search](reference/embedding-generation-and-semantic-search.md)** — `AI.EMBED`, `AI.GENERATE_EMBEDDING`, `ML.GENERATE_EMBEDDING`, `AI.SIMILARITY`, `VECTOR_SEARCH`, `AI.SEARCH`, and hybrid search
- **[Predictive AI](reference/predictive-ai.md)** — `AI.FORECAST`, `AI.DETECT_ANOMALIES`, `AI.PREDICT`, `AI.EVALUATE` — the TimesFM and TabFM foundation models
- **[Augmented Analytics](reference/augmented-analytics.md)** — `AI.KEY_DRIVERS` — model-free contribution analysis, plus the pointer to `AI.CAUSAL_EFFECT`, which is [documented in `bq-ml`](../bq-ml/reference/model-free-functions.md#aicausal_effect) alongside the other causal estimators
- **[Document Processing](reference/document-processing.md)** — `ML.PROCESS_DOCUMENT` and `AI.PARSE_DOCUMENT`
- **[Unstructured Data Infrastructure](reference/unstructured-data-infrastructure.md)** — object tables, the `OBJ.*` functions, the ObjectRef / ObjectRefRuntime schema reference, and multimodal input patterns by function

---

## Choosing a Gemini Model Endpoint

Every generative function documents its supported models as "any GA or preview Gemini model." That is accurate but hides two things worth knowing before you pick one. This section is the single place they are recorded; the per-function entries do not repeat them.

**The default has not moved.** Omit `endpoint` and you get `gemini-2.5-flash`, on every function that takes the argument. Newer models being available does not change the default -- every example in this project runs on `gemini-2.5-flash` and its outputs reflect that model.

**Gemini 3.x models are available and are not the default.** `gemini-3.1-flash-lite` and `gemini-3.5-flash` reached GA on 2026-08-10 and work in all generative AI functions. To use one, pass it explicitly:

```sql
SELECT AI.GENERATE(('Summarize: ', body), endpoint => 'gemini-3.5-flash').result
FROM `PROJECT_ID.DATASET_ID.TABLE_ID`;
```

**GOTCHA -- Gemini 3.x is multi-regional only.** Unlike the 2.5 family, the 3.x models are not served from regional endpoints, only from the `us`, `eu`, and global multi-regional endpoints. If you pass a short model name, BigQuery resolves the endpoint for you, and the rule is not obvious:

| Query location | Endpoint used |
|----------------|---------------|
| `us`, or any single US region | `us` |
| `eu`, or any single EU region **except** `europe-west2` / `europe-west6` | `eu` |
| Everything else, **including `europe-west2` and `europe-west6`** | global |

The two European exceptions matter: a query running in London (`europe-west2`) silently uses the **global** endpoint, where you cannot control or know which region processes the request. If you have data processing location requirements, that is a compliance problem, not a performance note. Pin the endpoint explicitly with a fully qualified multi-regional name to avoid it:

```
https://aiplatform.us.rep.googleapis.com/v1/projects/PROJECT_ID/locations/us/publishers/google/models/MODEL_ID
```

Also note for cost planning: in `asia-northeast1`, `asia-south1`, `asia-southeast1`, and `europe-west2`, Gemini 3.5 Flash supports only Single Zone Provisioned Throughput.
