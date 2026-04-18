# Serving — Planned Notebooks

Tracking upcoming notebooks for the `MLOps/Serving` folder. Each builds on the existing endpoint notebooks and custom container pattern already established in this folder.

---

## 1. Every Way to Request Predictions

**File:** `Vertex AI Endpoint - Prediction Methods.ipynb`

**Goal:** Comprehensive, multi-language reference for every way to send prediction requests to a Vertex AI Endpoint — from high-level Python SDK to raw gRPC, REST in multiple languages, streaming, and batch. One model, one endpoint, every client path.

**Prior art:** [05Tools - Prediction - Online.ipynb](../../05%20-%20TensorFlow/05Tools%20-%20Prediction%20-%20Online.ipynb) covers Python SDK layers (high-level, gapic, v1, v1beta1), REST (curl, requests), gcloud CLI, sync/async batching with concurrency benchmarks, and error handling with retries. We borrow the async/concurrency benchmarking approach but consolidate the redundant client sections (v1/v1beta1/gapic were repeated 4x), simplify async code to use the SDK's built-in `predict_async()`, and add gRPC, streaming, multi-language examples, and endpoint type compatibility.

**Setup:**
- Same HuggingFace sentiment model + custom FastAPI container used across the other Serving notebooks (consistency)
- Deploy to a **dedicated public endpoint** (most capable type — gRPC, streaming, dedicated URL, all methods supported)
- Simple text instances for sentiment analysis

### Endpoint Type Compatibility (top of notebook)

Chart at the top showing which prediction methods work with which endpoint types. Each method section also notes its endpoint compatibility.

| Method | Dedicated Public | Shared Public | PSC Private | VPC Peering Private |
|--------|:---:|:---:|:---:|:---:|
| `predict` (SDK / REST / gRPC) | Yes | Yes | Yes | Yes |
| `rawPredict` (SDK / REST / gRPC) | Yes | Yes | Yes | Yes |
| `streamRawPredict` / SSE | **Yes** | No | **Yes** | No |
| Dedicated endpoint direct URL | **Yes** | No | No | No |
| `directPredict` / `directRawPredict` | **Yes** | No | **Yes** | No |
| gRPC protocol | **Yes** | No | **Yes** | No |
| `gcloud ai endpoints predict` | Yes | Yes | Yes* | Yes* |
| Batch Prediction | Yes | Yes | No | No |

_*CLI works for management but prediction routing differs for private endpoints_

**Sections:**

### Python SDK (High-Level) — `google-cloud-aiplatform`
- `endpoint.predict(instances)` — standard prediction
- `endpoint.raw_predict(body, headers)` — raw with custom headers, returns `Response`
- `endpoint.predict_async(instances)` — built-in async coroutine (simplifies the old manual asyncio pattern)
- `endpoint.stream_raw_predict(body, headers)` — streaming, returns iterator
- Note: `raw_predict_async` does not exist at this layer — use the gapic async client for that

### Python SDK (Low-Level) — `aiplatform_v1`
- `aiplatform_v1.PredictionServiceClient` — predict, raw_predict (sync)
- `aiplatform_v1.PredictionServiceAsyncClient` — predict, raw_predict, stream_raw_predict (all async)
- Note: `aiplatform.gapic.PredictionServiceClient` is the same as `aiplatform_v1`
- Note: `aiplatform_v1beta1` exists for preview features (mention, don't duplicate)
- This layer gives raw_predict async, which the high-level SDK lacks

### REST API — Python `requests`
- Use `google.auth.default()` + `google.auth.transport.requests.Request()` for token management (modern — no shelling out to `gcloud auth print-access-token`)
- `:predict` and `:rawPredict` endpoints
- Show URL construction: `https://{REGION}-aiplatform.googleapis.com/v1/{endpoint.resource_name}:predict`

### REST API — Python `httpx` (async)
- Modern async HTTP client
- Same REST endpoints but with `httpx.AsyncClient`
- Natural pairing with asyncio concurrency patterns

### REST API — `curl`
- Command-line examples for predict and rawPredict
- Using `gcloud auth print-access-token` for bearer token

### REST API — Node.js
- Using `fetch` (built-in since Node 18) or `axios`
- Auth via `google-auth-library` (`GoogleAuth` / `getAccessToken()`)
- Same REST endpoints — shows the language-agnostic nature of the REST API

### REST API — Java
- Using `java.net.http.HttpClient` (built-in since Java 11)
- Auth via `GoogleCredentials` from `google-auth-library-oauth2-http`
- Same REST endpoints

### REST API — Go
- Using `net/http` (stdlib)
- Auth via `golang.org/x/oauth2/google` for default credentials
- Same REST endpoints

### Client Libraries — Node.js, Java, Go (generated)
- Brief section showing that official client libraries exist for all major languages
- Node.js: `@google-cloud/aiplatform` → `v1.PredictionServiceClient`
- Java: `com.google.cloud:google-cloud-aiplatform` → `PredictionServiceClient`
- Go: `cloud.google.com/go/aiplatform/apiv1` → `PredictionClient`
- Also available: C# (`Google.Cloud.AIPlatform.V1`), Ruby (`google-cloud-ai_platform-v1`)
- All are auto-generated from `prediction_service.proto` — work with protobuf types directly
- Show one example (Node.js) with the generated client for comparison with REST

### gcloud CLI
- `gcloud ai endpoints predict` with `--json-request`
- `gcloud ai endpoints raw-predict` with `--request`

### gRPC (Python)
- Channel setup with `grpc.secure_channel` and Google auth credentials
- `PredictionServiceStub` from the generated proto
- Request construction with `PredictRequest`
- When to use: lower latency for high-throughput, binary payloads, bidirectional streaming potential
- Latency comparison with REST (same request, both protocols)
- Note: only available on dedicated and PSC endpoints (not shared public or VPC peering)

### Streaming (SSE)
- `endpoint.stream_raw_predict(body, headers)` — high-level SDK, returns sync iterator
- `PredictionServiceAsyncClient.stream_raw_predict()` — gapic async
- REST: `POST :streamRawPredict`
- Use case: token-by-token generation, progress updates, long-running inference
- Note: only available on dedicated and PSC endpoints

### Dedicated Endpoint Direct URL
- Dedicated endpoints get a unique DNS: `{endpoint_id}.{region}-{project_number}.prediction.vertexai.goog`
- Direct HTTP/gRPC to this URL (bypasses the regional API router)
- Show how to discover and use the `dedicated_endpoint_dns` field
- Note: only available on dedicated public endpoints

### PSC Private Endpoint (explanatory)
- How requests differ: self-signed TLS (`verify=False` / `curl -k`), private IP instead of public DNS
- Requires VPC-local forwarding rule — not accessible from peered networks
- Cross-reference to [Vertex AI Private Endpoint With PSC](./Vertex%20AI%20Private%20Endpoint%20With%20PSC.ipynb) for full setup and live demo
- Cross-reference to [Vertex AI PSC Endpoint - Pipeline Model Swap](./Vertex%20AI%20PSC%20Endpoint%20-%20Pipeline%20Model%20Swap.ipynb) for automated deployment

### Sync vs Async Concurrency
- Synchronous batching: vary `batch_size`, measure throughput
- Async concurrency using `endpoint.predict_async()` with `asyncio.gather` — much simpler than the old manual pattern since the SDK now has built-in async
- `asyncio.Semaphore` for managed concurrency limits
- Benchmark table: batch_size x concurrency_limit x elapsed time

### Error Handling and Retries
- Common errors: 503 (model server), 429 (quota)
- Exponential backoff pattern with retry limits
- Integration with the async concurrency pattern

### Batch Prediction (brief)
- `aiplatform.BatchPredictionJob.create()` with JSONL, BigQuery, file list input sources
- When to choose batch vs online
- Cross-reference to [Understanding Prediction IO With FastAPI](./Understanding%20Prediction%20IO%20With%20FastAPI.ipynb) which covers batch in more depth

### Summary Table
Method x language x protocol x async support x streaming x endpoint compatibility x notes

**Status:** Complete

---

## 2. Cloud Run Serving

**File:** `Serving Models on Cloud Run.ipynb`

**Goal:** Deploy the same custom container to Cloud Run and compare with Vertex AI Endpoints. Same model, different platform — when to choose which.

**Setup:**
- Same HuggingFace sentiment model + custom FastAPI container (DistilBERT + BERT)
- Deploy to Cloud Run (IAM-authenticated by default)

**Sections:**
- Deploy container to Cloud Run with `run_v2` Python SDK, setting `AIP_*` env vars explicitly for container portability
- Authentication deep dive: ID tokens vs access tokens, `google.oauth2.id_token.fetch_id_token()`, granting `roles/run.invoker`, public access with `allUsers`
- Traffic splitting between revisions: deploy v1 (DistilBERT), update to v2 (BERT), split 50/50, shift 100% to v2
- Configuration reference: autoscaling comparison, GPU on Cloud Run, decision framework
- Cleanup

**Status:** Complete

---

## 3. Autoscaling Deep Dive

**File:** `Vertex AI Endpoint - Autoscaling.ipynb`

**Goal:** Understand and observe autoscaling behavior on Vertex AI Endpoints through load testing and live metric visualization.

**Setup:**
- Same HuggingFace sentiment model + custom FastAPI container
- Deploy to a dedicated public endpoint with configurable autoscaling (min=1, max=5)

**Sections:**
- Autoscaling mechanics explainer: formula, evaluation cycle, 5-minute lookback window, default thresholds
- Cloud Monitoring metric discovery and reusable query helper with sparse metric handling
- 4-panel matplotlib dashboard: replicas (actual vs target), CPU utilization, predictions/sec, P95 latency
- Experiment 1: CPU-triggered scale-up/scale-down with full lifecycle observation
- Experiment 2: Request-count scaling via `mutateDeployedModel` REST API (no redeploy)
- Experiment 3: Lower CPU threshold (30%) to show earlier trigger
- Configuration reference: all parameters, `mutateDeployedModel` vs redeploy, cost implications, gotchas
- Cleanup

**Status:** Complete
