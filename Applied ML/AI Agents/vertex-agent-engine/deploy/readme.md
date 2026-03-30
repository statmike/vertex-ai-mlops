![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fvertex-agent-engine%2Fdeploy&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/vertex-agent-engine/deploy/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/vertex-agent-engine/deploy/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/vertex-agent-engine/deploy/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/vertex-agent-engine/deploy/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/vertex-agent-engine/deploy/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/vertex-agent-engine/deploy/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/vertex-agent-engine/deploy/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Deployment Deep-Dive

This document explains how the deployment works in detail — what gets packaged, why the entrypoint wrapper exists, how environment variables flow, and what Agent Engine gives you automatically.

---

## Contents

- [How Source-File Deployment Works](#how-source-file-deployment-works)
- [The Entrypoint Wrapper](#the-entrypoint-wrapper)
- [What Gets Packaged](#what-gets-packaged)
- [Environment Variable Flow](#environment-variable-flow)
- [Class Methods Spec](#class-methods-spec)
- [Deployment State](#deployment-state)
- [Deploy Script Commands](#deploy-script-commands)
- [Using Deployed Agents](#using-deployed-agents)
- [What Agent Engine Provides](#what-agent-engine-provides)
- [Extending to Multiple Deployments](#extending-to-multiple-deployments)
- [Prerequisites](#prerequisites)

---

## How Source-File Deployment Works

Source-file deployment ([introduced in SDK v1.112.0](https://docs.cloud.google.com/agent-builder/deprecations/agent-engine-migration)) uploads your Python source code directly to Agent Engine. No pickle serialization, no GCS staging bucket.

At deploy time, the script:

1. Collects all `agent_*` packages plus `deploy/`
2. Generates `requirements.txt` from `pyproject.toml`
3. Uploads everything as a tarball (must be under 8 MB)
4. Agent Engine builds a container, installs requirements, and starts serving

```python
client.agent_engines.create(config={
    "source_packages": ["agent_greeter", "agent_router", "agent_tools", "deploy", "requirements.txt"],
    "entrypoint_module": "deploy.entrypoint",
    "entrypoint_object": "app",
    "requirements_file": "requirements.txt",
    "class_methods": ADK_CLASS_METHODS,
    ...
})
```

---

## The Entrypoint Wrapper

Agent Engine requires an [`AdkApp`](https://cloud.google.com/agent-builder/agent-engine/adk) instance as the entrypoint — not a raw ADK `Agent`. The `AdkApp` wrapper registers the API methods (`stream_query`, `create_session`, etc.) that Agent Engine exposes as HTTP endpoints.

```python
# deploy/entrypoint.py
from vertexai.agent_engines import AdkApp
from agent_router.agent import root_agent

app = AdkApp(agent=root_agent, enable_tracing=True)
```

**Why a separate file?** This keeps deployment concerns out of your agent code. `agent_router/agent.py` works identically with `adk web` locally and Agent Engine in production. The entrypoint is just a thin bridge.

The deploy script tells Agent Engine where to find it:
- `entrypoint_module`: `deploy.entrypoint` (Python import path)
- `entrypoint_object`: `app` (the `AdkApp` instance)

---

## What Gets Packaged

The deploy script auto-discovers source packages by scanning for `agent_*` directories with `__init__.py`:

```python
def _get_source_packages() -> list[str]:
    packages = []
    for item in sorted(PROJECT_ROOT.iterdir()):
        if item.is_dir() and item.name.startswith("agent_") and (item / "__init__.py").exists():
            packages.append(item.name)
    packages.append("deploy")  # includes entrypoint.py
    return packages
```

Dependencies come from `pyproject.toml`, written to a temporary `requirements.txt`:

```python
def _write_requirements_file() -> Path:
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    deps = data["project"]["dependencies"]
    req_path = PROJECT_ROOT / "requirements.txt"
    req_path.write_text("\n".join(deps) + "\n")
    return req_path
```

**Important:** The `config.py` file at the project root is also included because `agent_*` packages import from it. Any `.py` file at the root that agents import must be in the upload.

---

## Environment Variable Flow

```
.env (local file)
  │
  ├──→ config.py (local development via python-dotenv)
  │
  └──→ deploy.py reads .env
         │
         ├── Filters out reserved vars (GOOGLE_CLOUD_PROJECT, PORT, etc.)
         ├── Adds telemetry vars
         │
         └──→ Agent Engine env_vars
                │
                └──→ config.py (deployed — reads os.environ, same code)
```

The key insight: `config.py` uses `os.getenv()` with defaults. Locally, `python-dotenv` loads the `.env` file. In Agent Engine, the deploy script passes the same values as container environment variables. Same code, both environments.

**Reserved variables** that Agent Engine sets automatically (filtered out to avoid conflicts):

| Variable | Set by |
|----------|--------|
| `GOOGLE_CLOUD_PROJECT` | Agent Engine |
| `GOOGLE_CLOUD_LOCATION` | Agent Engine |
| `GOOGLE_APPLICATION_CREDENTIALS` | Agent Engine |
| `PORT` | Cloud Run (underlying runtime) |
| `K_SERVICE`, `K_REVISION`, `K_CONFIGURATION` | Cloud Run |

### Infrastructure location vs. model location

This is the most subtle part of deployment. There are three location variables, and they serve different purposes:

| Variable | What it controls | Set by | Passed to agent? |
|----------|-----------------|--------|------------------|
| `GOOGLE_CLOUD_LOCATION` | Agent Engine deployment region | Agent Engine (reserved) | No — filtered out, Agent Engine sets it automatically |
| `AGENT_MODEL_LOCATION` | API endpoint for ADK agent model calls | `.env` → deploy script | Yes — passes through to deployed agent |
| `TOOL_MODEL_LOCATION` | API endpoint for direct `google-genai` calls in tools | `.env` → deploy script | Yes — passes through to deployed agent |

**Why they differ:** Agent Engine runs in a specific region (e.g., `us-central1`), and sets `GOOGLE_CLOUD_LOCATION` accordingly. But ADK uses `GOOGLE_CLOUD_LOCATION` as the API endpoint for Gemini calls too. If a preview model like `gemini-3-flash-preview` is only available on `global`, the agent would 404 trying to reach it at `us-central1`.

**How it's solved:**

1. **ADK agents** — The root agent overrides `GOOGLE_CLOUD_LOCATION` with `AGENT_MODEL_LOCATION` at import time:
   ```python
   # agent_router/agent.py
   if AGENT_MODEL_LOCATION:
       os.environ["GOOGLE_CLOUD_LOCATION"] = AGENT_MODEL_LOCATION  # "global"
   ```
   This runs before any agent makes a model call, so all ADK agents hit the `global` endpoint.

2. **Direct Gemini calls in tools** — The `google-genai` client takes location in its constructor, independent of `GOOGLE_CLOUD_LOCATION`:
   ```python
   # agent_tools/tools.py
   _client = genai.Client(vertexai=True, location=TOOL_MODEL_LOCATION)  # "global"
   ```

Both `AGENT_MODEL_LOCATION` and `TOOL_MODEL_LOCATION` are not in `RESERVED_ENV_VARS`, so they pass through to the deployed agent and the same code works in both local and deployed environments.

---

## Class Methods Spec

Source-file deployment requires an explicit list of API methods. These tell Agent Engine which methods on your `AdkApp` to expose as HTTP endpoints:

| Method | API Mode | Purpose |
|--------|----------|---------|
| `async_stream_query` | async_stream | Stream responses (primary query method) |
| `stream_query` | stream | Synchronous streaming |
| `create_session` / `async_create_session` | sync / async | Create a new session |
| `get_session` / `async_get_session` | sync / async | Retrieve session state |
| `list_sessions` / `async_list_sessions` | sync / async | List sessions for a user |
| `delete_session` / `async_delete_session` | sync / async | Delete a session |
| `async_add_session_to_memory` | async | Add session to memory service |
| `async_search_memory` | async | Search memory |

These are the same for every ADK agent deployment — copy the `ADK_CLASS_METHODS` list from `deploy.py` as-is.

---

## Deployment State

The deploy script tracks deployment metadata in `deploy/app/deployment.json`:

```json
{
  "resource_name": "projects/123/locations/us-central1/reasoningEngines/456",
  "deployed_at": "2026-03-30T10:00:00.000000",
  "display_name": "vertex-agent-engine-tutorial",
  "description": "Tutorial multi-agent system deployed to Vertex AI Agent Engine."
}
```

This file is how the script knows whether to create a new deployment or update an existing one. It's safe to commit to version control.

---

## Deploy Script Commands

| Command | What it does |
|---------|-------------|
| `deploy.py` | Run local smoke test, then create a new deployment |
| `deploy.py --update` | Update existing deployment with latest code and env vars |
| `deploy.py --delete` | Delete the deployment and clear `deployment.json` |
| `deploy.py --info` | Show resource name, timestamps, and Console URL |
| `deploy.py --test` | Create a session, send a query, print response, clean up |
| `deploy.py --skip-local-test` | Deploy without running the local smoke test first |

---

## Using Deployed Agents

### Python SDK

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
    message="Tell me about Saturn",
):
    content = event.get("content")
    if content:
        print(content)
```

### REST API

```bash
BASE="https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT/locations/us-central1/reasoningEngines/RESOURCE_ID"
TOKEN=$(gcloud auth print-access-token)

# Create session
curl -s -X POST "${BASE}:query" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"class_method": "async_create_session", "input": {"user_id": "user-123"}}'

# Stream a query
curl -s -X POST "${BASE}:streamQuery?alt=sse" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "user-123",
      "session_id": "SESSION_ID",
      "message": "Tell me about Saturn"
    }
  }'
```

### ADK Web UI with Agent Engine Sessions

Run the ADK dev UI locally but connect to Agent Engine for persistent sessions:

```bash
uv run adk web \
  --session_service_uri="agentengine://projects/PROJECT/locations/LOCATION/reasoningEngines/RESOURCE_ID"
```

See [interact.ipynb](interact.ipynb) for a hands-on tutorial with runnable examples.

---

## What Agent Engine Provides

When deployed, the following are automatically available:

| Feature | What it provides |
|---------|-----------------|
| **Persistent sessions** | Cloud-based session storage — conversations survive restarts |
| **Cloud Monitoring** | Metrics dashboard for request counts, latencies, errors |
| **Cloud Logging** | Runtime event logs for debugging |
| **Cloud Trace** | Distributed tracing across agent calls and tool invocations |
| **Prompt/response logging** | Full GenAI content capture for audit and debugging |

Cloud Trace and prompt logging are enabled by the telemetry env vars the deploy script sets automatically.

---

## Extending to Multiple Deployments

This tutorial deploys a single agent. To support multiple deployments (like [data-onboarding](../../data-onboarding/) does with `orchestrator` and `chat`):

1. **Add an `AGENT_CONFIGS` dict** mapping deployment names to their entrypoint modules, display names, and deployment file paths
2. **Create separate entrypoint files** per deployment (e.g., `entrypoint_a.py`, `entrypoint_b.py`)
3. **Add a positional CLI argument** to select which agent: `deploy.py agent_a` / `deploy.py agent_b`
4. **Store deployment state in subfolders**: `deploy/agent_a/deployment.json`, `deploy/agent_b/deployment.json`

See [data-onboarding/deploy/deploy.py](../../data-onboarding/deploy/deploy.py) for a working example.

---

## Prerequisites

- [Vertex AI API](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com) enabled
- [Cloud Telemetry API](https://console.cloud.google.com/apis/library/telemetry.googleapis.com) enabled (for tracing)
- Authenticated: `gcloud auth application-default login`

---

## References

- [Vertex AI Agent Engine overview](https://docs.cloud.google.com/agent-builder/agent-engine/overview)
- [Deploy ADK agents to Agent Engine](https://google.github.io/adk-docs/deploy/agent-engine/deploy/)
- [SDK migration guide (v1.112.0+)](https://docs.cloud.google.com/agent-builder/deprecations/agent-engine-migration)
- [Agent Engine troubleshooting](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/troubleshooting/deploy)
