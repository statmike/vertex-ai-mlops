# Deploying to Vertex AI Agent Engine

This folder contains everything needed to deploy the data-onboarding agents to [Vertex AI Agent Engine](https://docs.cloud.google.com/agent-builder/agent-engine/overview) — Google Cloud's managed runtime for production AI agents.

Agent Engine provides persistent sessions, Cloud Trace, Cloud Monitoring, Cloud Logging, and auto-scaling with no infrastructure to manage.

---

## Two Deployments, Two Root Agents

The data-onboarding system has two independent entry points, each deployed as a separate Agent Engine resource:

| Deployment | Root Agent | What it does |
|-----------|-----------|-------------|
| **`orchestrator`** | `agent_orchestrator` | Onboards data from a URL into BigQuery (crawl, download, design, create, validate) |
| **`chat`** | `agent_chat` | Answers questions about onboarded data (analytics, engineering, catalog exploration) |

They share the same underlying agent packages and configuration but serve different purposes and can be deployed, updated, and scaled independently.

---

## Quick Start

```bash
# Deploy
uv run python deploy/deploy.py chat                       # deploy chat agent
uv run python deploy/deploy.py orchestrator               # deploy orchestrator

# Manage
uv run python deploy/deploy.py chat --info                # show deployment info + console URL
uv run python deploy/deploy.py chat --test                # send a test query to the deployed agent
uv run python deploy/deploy.py chat --update              # update with latest code
uv run python deploy/deploy.py chat --delete              # tear down

# Skip the local smoke test before deploying
uv run python deploy/deploy.py chat --skip-local-test
```

---

## How It Works

### Source-File Deployment

This project uses the [source-file deployment method](https://docs.cloud.google.com/agent-builder/agent-engine/deploy) introduced in the [client-based SDK (v1.112.0+)](https://docs.cloud.google.com/agent-builder/deprecations/agent-engine-migration). Source-file deployment uploads your Python source directly — no pickle serialization, no GCS staging bucket required.

At deploy time, the script:

1. Collects all 12 `agent_*` packages plus the `deploy/` package
2. Generates a `requirements.txt` from `pyproject.toml` dependencies
3. Bundles everything into a tarball (~516 KiB, well under the 8 MB limit)
4. Uploads to Agent Engine with the entrypoint, class methods, and environment variables

### Entrypoint Modules

Agent Engine requires an [`AdkApp`](https://cloud.google.com/agent-builder/agent-engine/adk) instance as the entrypoint — not a raw ADK `Agent`. The `AdkApp` wrapper registers the standard API methods (`stream_query`, `create_session`, etc.) that Agent Engine exposes as HTTP endpoints.

Rather than modifying the existing `agent.py` files (which also serve `adk web` locally), thin entrypoint modules in this folder create the `AdkApp` wrapper:

```
deploy/
  entrypoint_chat.py           # imports agent_chat.agent.root_agent → wraps in AdkApp
  entrypoint_orchestrator.py   # imports agent_orchestrator.agent.root_agent → wraps in AdkApp
```

Each is just three lines:

```python
from vertexai.agent_engines import AdkApp
from agent_chat.agent import root_agent
app = AdkApp(agent=root_agent, enable_tracing=True)
```

The deploy script points Agent Engine to these:
- `entrypoint_module`: `deploy.entrypoint_chat`
- `entrypoint_object`: `app`

### Shared Deploy Script

A single `deploy.py` handles both deployments. The first positional argument selects which agent:

```bash
uv run python deploy/deploy.py chat [--flags]
uv run python deploy/deploy.py orchestrator [--flags]
```

All flags (`--update`, `--delete`, `--info`, `--test`, `--skip-local-test`) work the same for both. Each deployment tracks its own state in a `deployment.json` file:

```
deploy/
  chat/deployment.json            # chat agent deployment metadata
  orchestrator/deployment.json    # orchestrator deployment metadata
```

### Environment Variables

The deploy script reads your `.env` file and passes non-reserved variables to the deployed agent. Agent Engine automatically sets some variables (`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `PORT`, etc.) — these are filtered out to avoid conflicts.

The following are always enabled on deployed agents:

| Variable | Value | Purpose |
|----------|-------|---------|
| `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY` | `true` | Cloud Trace distributed tracing |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | `true` | Log prompt/response content |

All other `.env` variables (model names, dataset locations, crawl settings, etc.) are passed through as-is.

---

## Using Deployed Agents

For a hands-on walkthrough with runnable examples, see [interact.ipynb](interact.ipynb).

### From the Python SDK

```python
import vertexai

client = vertexai.Client(project="your-project", location="us-central1")
agent = client.agent_engines.get(name="projects/.../reasoningEngines/RESOURCE_ID")

# Create a session
session = await agent.async_create_session(user_id="user-123")

# Stream a query
async for event in agent.async_stream_query(
    user_id="user-123",
    session_id=session["id"],
    message="What tables are available?",
):
    content = event.get("content")
    if content:
        print(content)
```

### From curl (REST API)

```bash
PROJECT_ID=your-project
LOCATION=us-central1
RESOURCE_ID=your-resource-id

# Create session
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/reasoningEngines/${RESOURCE_ID}:query" \
  -d '{"class_method": "async_create_session", "input": {"user_id": "user-123"}}'

# Stream query
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/reasoningEngines/${RESOURCE_ID}:streamQuery?alt=sse" \
  -d '{
    "class_method": "async_stream_query",
    "input": {
        "user_id": "user-123",
        "session_id": "SESSION_ID",
        "message": "Compare short sale volumes across exchanges"
    }
  }'
```

### ADK Web UI with Agent Engine Sessions

You can run the ADK web UI locally but connect it to a deployed Agent Engine instance for persistent sessions. This gives you the local dev UI with cloud-backed session storage — useful for testing and debugging deployed agents interactively:

```bash
# Use the full resource name
uv run adk web \
  --session_service_uri="agentengine://projects/PROJECT_ID/locations/LOCATION/reasoningEngines/RESOURCE_ID"
# example: projects/1026793852137/locations/us-central1/reasoningEngines/4403271940115005440

# Or just the resource ID
uv run adk web --session_service_uri="agentengine://RESOURCE_ID"
```

You can also connect memory and artifact services to Agent Engine:

```bash
uv run adk web \
  --session_service_uri="agentengine://RESOURCE_ID" \
  --memory_service_uri="agentengine://RESOURCE_ID" \
  --artifact_service_uri="gs://your-bucket"
```

The resource ID is in `deploy/chat/deployment.json` (or `deploy/orchestrator/deployment.json`) after deploying, or use `--info`:

```bash
uv run python deploy/deploy.py chat --info
```

### Running Locally (No Deployment)

For local development and testing, use the ADK dev server with no deployment needed:

```bash
uv run adk web
```

Select the agent from the dropdown:
- **`agent_orchestrator`** — onboard data from a URL
- **`agent_chat`** — chat with onboarded data

By default, sessions are stored locally (SQLite in `.adk/`). Use `--session_service_uri="memory://"` for ephemeral in-memory sessions.

---

## Prerequisites

In addition to the APIs listed in the main [readme.md](../readme.md#required-google-cloud-apis), Agent Engine deployments require:

```bash
gcloud services enable telemetry.googleapis.com --project=YOUR_PROJECT_ID
```

This enables the Cloud Telemetry API, which Agent Engine uses to store distributed traces. Without it, tracing data is silently dropped and you'll see this warning in Cloud Logging:

> The 'telemetry.googleapis.com' has not been enabled in project YOUR_PROJECT. Until this API is enabled, telemetry data will not be stored.

### IAM Grants for the Reasoning Engine Service Agent

When deployed, agents run as the Reasoning Engine Service Agent — not your user credentials. This service account needs access to BigQuery, GCS, and Dataplex resources that the agents use at runtime.

The service account follows the pattern:
```
service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com
```

Some roles are granted automatically when Agent Engine is first enabled (`bigquery.dataViewer`, `bigquery.jobUser`). The following additional roles are required for this project's agents:

```bash
PROJECT_ID=YOUR_PROJECT_ID
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
RE_SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

# BigQuery connection access — needed by agent_catalog for AI.SEARCH/AI.EMBED
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$RE_SA" --role="roles/bigquery.connectionUser" --quiet

# GCS read access — needed by agent_orchestrator to read staged files
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$RE_SA" --role="roles/storage.objectViewer" --quiet

# Dataplex read access — needed by agent_context for lookupContext API (context cache)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$RE_SA" --role="roles/dataplex.viewer" --quiet
```

| Role | Why | Used by |
|------|-----|---------|
| `bigquery.connectionUser` | `AI.SEARCH` and `AI.EMBED` require access to the BQ Cloud Resource connection | `agent_catalog` |
| `storage.objectViewer` | Read files from GCS staging during onboarding | `agent_orchestrator` pipeline |
| `dataplex.viewer` | Dataplex `lookupContext` API for rich table metadata | `agent_context` (context cache) |

> **Without these grants**, the agents will partially work but fail on specific tools. For example, Catalog Explorer's `search_context` will return a permission error on the BQ connection.

To run the [interact.ipynb](interact.ipynb) notebook, install the Jupyter kernel (one-time setup):

```bash
uv pip install ipykernel
uv run python -m ipykernel install --user --name data-onboarding --display-name "Data Onboarding"
```

## Auto-Enabled Features

When deployed to Agent Engine, the following are automatically available with no additional configuration:

| Feature | What it provides |
|---------|-----------------|
| **Persistent sessions** | Cloud-based session storage — conversations survive restarts |
| **Cloud Monitoring** | Metrics dashboard for request counts, latencies, errors |
| **Cloud Logging** | Runtime event logs for debugging |
| **Cloud Trace** | Distributed tracing across agent calls and tool invocations (requires `telemetry.googleapis.com`) |
| **Prompt/response logging** | Full GenAI content capture for audit and debugging |

---

## File Structure

```
deploy/
  deploy.py                      # Shared CLI for deploying both agents
  entrypoint_chat.py             # AdkApp wrapper for agent_chat
  entrypoint_orchestrator.py     # AdkApp wrapper for agent_orchestrator
  __init__.py                    # Package marker (needed for entrypoint imports)
  interact.ipynb                 # Tutorial: query deployed agents (Python SDK + REST)
  readme.md                      # This file
  chat/
    deployment.json              # Tracks chat deployment state
  orchestrator/
    deployment.json              # Tracks orchestrator deployment state
```

---

## References

- [Vertex AI Agent Engine overview](https://docs.cloud.google.com/agent-builder/agent-engine/overview)
- [Deploy ADK agents to Agent Engine](https://google.github.io/adk-docs/deploy/agent-engine/deploy/)
- [SDK migration guide (v1.112.0+)](https://docs.cloud.google.com/agent-builder/deprecations/agent-engine-migration)
- [Agent Engine troubleshooting](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/troubleshooting/deploy)
- [Managing deployed agents](https://docs.cloud.google.com/agent-builder/agent-engine/manage)
