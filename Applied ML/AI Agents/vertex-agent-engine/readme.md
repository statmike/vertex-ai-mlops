![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fvertex-agent-engine&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/vertex-agent-engine/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/vertex-agent-engine/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/vertex-agent-engine/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/vertex-agent-engine/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/vertex-agent-engine/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/vertex-agent-engine/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/vertex-agent-engine/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Vertex AI Agent Engine — Deployment Tutorial

A minimal multi-agent system built with [Google ADK](https://google.github.io/adk-docs/) that demonstrates how to deploy ADK agents to [Vertex AI Agent Engine](https://docs.cloud.google.com/agent-builder/agent-engine/overview) using source-file deployment.

The agents are intentionally simple — the focus is on the **deployment patterns**: how to structure your project, wrap agents for deployment, pass environment variables, and interact with deployed agents.

## Contents

- [What You'll Learn](#what-youll-learn)
- [Project Structure](#project-structure)
- [The Agents](#the-agents)
- [Key Patterns](#key-patterns)
- [Setup](#setup)
- [Run Locally](#run-locally)
- [Deploy](#deploy)
- [Interact with Deployed Agents](#interact-with-deployed-agents)

---

## What You'll Learn

1. **Project layout** — each agent as its own Python package, shared config from `.env`
2. **AdkApp entrypoint** — why Agent Engine needs a wrapper and how to keep it separate from your agent code
3. **Source-file deployment** — packaging source code, generating `requirements.txt` from `pyproject.toml`, staying under the 8 MB limit
4. **Environment variables** — reading from `.env`, filtering reserved vars, passing model locations to deployed agents
5. **Deployment lifecycle** — create, update, delete, test, and track state in `deployment.json`
6. **Interacting with deployed agents** — Python SDK and REST API with sessions and streaming

---

## Project Structure

```
vertex-agent-engine/
│
├── .env.example                  # Template — copy to .env and fill in
├── config.py                     # Shared config loaded from .env
├── pyproject.toml                # Dependencies and project metadata
│
├── agent_router/                 # Root agent — routes to sub-agents
│   ├── __init__.py
│   └── agent.py                  #   defines root_agent
│
├── agent_greeter/                # Sub-agent — greetings and introductions
│   ├── __init__.py
│   ├── agent.py                  #   defines greeter_agent
│   └── tools.py                  #   get_greeting tool
│
├── agent_tools/                  # Sub-agent — facts and calculations
│   ├── __init__.py
│   ├── agent.py                  #   defines tools_agent
│   └── tools.py                  #   lookup and calculate tools
│
└── deploy/                       # Deployment infrastructure
    ├── __init__.py               #   package marker (needed for imports)
    ├── deploy.py                 #   CLI for deploy/update/delete/info/test
    ├── entrypoint.py             #   AdkApp wrapper for Agent Engine
    ├── readme.md                 #   Deployment deep-dive
    ├── interact.ipynb            #   Tutorial: query deployed agents
    └── app/
        └── deployment.json       #   Tracks deployment state
```

---

## The Agents

```
User message ──→ agent_router ──┬──→ agent_greeter (greetings, introductions)
                    (router)    │
                                └──→ agent_tools (facts, calculations)
```

| Agent | Role | Tools |
|-------|------|-------|
| `agent_router` | Routes each message to the right sub-agent | *(none — delegates only)* |
| `agent_greeter` | Welcomes users, explains capabilities | `get_greeting` — time-appropriate greeting |
| `agent_tools` | Answers questions, does math, explains topics | `lookup` — solar system knowledge base |
| | | `calculate` — evaluate math expressions |
| | | `explain` — calls Gemini directly for deeper answers |

The `explain` tool demonstrates an important pattern: **tools that make their own LLM calls** via `google-genai`, separate from the agent's reasoning. This uses `TOOL_MODEL` from config — the same model configuration that flows through `.env` → deploy script → Agent Engine.

**Try these questions:**
- *"Hello!"* → routes to greeter
- *"Tell me about Jupiter"* → routes to tools → lookup
- *"What is 149.6 * 1000?"* → routes to tools → calculate
- *"Why is Mars red?"* → routes to tools → explain (calls Gemini directly)

---

## Key Patterns

### 1. Shared Config from `.env`

All configuration lives in a single `.env` file at the project root. A shared `config.py` module loads it with `python-dotenv`:

```env
# .env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1          # deployment region (Agent Engine infra)

AGENT_MODEL=gemini-3-flash-preview
AGENT_MODEL_LOCATION=global                # API endpoint for model calls
TOOL_MODEL=gemini-3-flash-preview
TOOL_MODEL_LOCATION=global                 # API endpoint for direct Gemini calls
```

#### Infrastructure location vs. model location

This is a critical distinction:

| Variable | Purpose | Example |
|----------|---------|---------|
| `GOOGLE_CLOUD_LOCATION` | Where Agent Engine runs (deployment region) | `us-central1` |
| `AGENT_MODEL_LOCATION` | Which API endpoint ADK agents call for model inference | `global` |
| `TOOL_MODEL_LOCATION` | Which API endpoint tools use for direct Gemini calls | `global` |

These are often different. Agent Engine deploys to a specific region (`us-central1`), but preview models like `gemini-3-flash-preview` may only be available on the `global` endpoint. If you don't separate them, your deployed agent will 404 when trying to call the model at `us-central1`.

#### How each call type handles location

**ADK agents** use just the model name — you cannot use `location/model` format (ADK interprets `/` as a litellm provider prefix). ADK reads `GOOGLE_CLOUD_LOCATION` for the API endpoint, so the root agent overrides it with `AGENT_MODEL_LOCATION` at import time:

```python
# agent_router/agent.py — overrides the API endpoint for model calls
from config import AGENT_MODEL, AGENT_MODEL_LOCATION
if AGENT_MODEL_LOCATION:
    os.environ["GOOGLE_CLOUD_LOCATION"] = AGENT_MODEL_LOCATION  # e.g., "global"

root_agent = Agent(model=AGENT_MODEL, ...)  # just the model name, no location prefix
```

Sub-agents inherit this setting — no override needed in each one:

```python
# agent_tools/agent.py
from config import TOOL_MODEL
tools_agent = Agent(model=TOOL_MODEL, ...)
```

**Direct Gemini calls in tools** use the `google-genai` client, which takes location in its constructor — independent of `GOOGLE_CLOUD_LOCATION`:

```python
# agent_tools/tools.py — tool that calls Gemini directly
from google import genai
from config import TOOL_MODEL, TOOL_MODEL_LOCATION

_client = genai.Client(vertexai=True, location=TOOL_MODEL_LOCATION)

def explain(topic: str) -> dict:
    response = _client.models.generate_content(model=TOOL_MODEL, contents=...)
    return {"explanation": response.text}
```

**The deploy script** reads `GOOGLE_CLOUD_LOCATION` to know which region to deploy to, but filters it from the env vars passed to the agent (Agent Engine sets it automatically). `AGENT_MODEL_LOCATION` and `TOOL_MODEL_LOCATION` pass through to the deployed agent, so the override and direct client calls work identically in both local and deployed environments.

**Why this matters:** Change models or locations in `.env` and both environments update — one source of truth.

### 2. AdkApp Entrypoint Wrapper

Agent Engine requires an [`AdkApp`](https://cloud.google.com/agent-builder/agent-engine/adk) instance, not a raw ADK `Agent`. The `AdkApp` registers API methods (`stream_query`, `create_session`, etc.) that Agent Engine exposes as HTTP endpoints.

A thin wrapper in `deploy/entrypoint.py` keeps this concern separate from your agent code:

```python
# deploy/entrypoint.py
from vertexai.agent_engines import AdkApp
from agent_router.agent import root_agent

app = AdkApp(agent=root_agent, enable_tracing=True)
```

Your `agent.py` files stay clean — they work with both `adk web` locally and Agent Engine in production without any changes.

### 3. Source-File Deployment

The deploy script collects all `agent_*` directories plus `deploy/`, generates a `requirements.txt` from `pyproject.toml`, and uploads everything to Agent Engine:

```python
# What gets uploaded:
source_packages = ["agent_greeter", "agent_router", "agent_tools", "deploy", "requirements.txt"]
```

No pickle serialization, no GCS staging bucket. Total size must be under 8 MB.

### 4. Environment Variable Passthrough

The deploy script reads your `.env`, filters out reserved variables that Agent Engine sets automatically (`GOOGLE_CLOUD_PROJECT`, `PORT`, etc.), and passes the rest:

```python
# deploy/deploy.py — simplified
env_vars = dotenv.dotenv_values(".env")
for key in RESERVED_ENV_VARS:
    env_vars.pop(key, None)
env_vars["GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"] = "true"
```

This means your `AGENT_MODEL` and `AGENT_MODEL_LOCATION` values flow from `.env` → deploy script → Agent Engine → deployed agent → `config.py` → agent code. One source of truth.

---

## Setup

### Prerequisites

- Python 3.13+
- A Google Cloud project with the [Vertex AI API](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com) enabled
- Authenticated: `gcloud auth application-default login`
- [Cloud Telemetry API](https://console.cloud.google.com/apis/library/telemetry.googleapis.com) enabled (for Agent Engine tracing)

### Install

```bash
# Clone and navigate
cd "Applied ML/AI Agents/vertex-agent-engine"

# Install dependencies
uv sync

# Jupyter kernel (for deploy/interact.ipynb)
uv pip install ipykernel
uv run python -m ipykernel install --user --name vertex-agent-engine --display-name "Vertex Agent Engine"

# Configure
cp .env.example .env
# Edit .env — set GOOGLE_CLOUD_PROJECT
```

---

## Run Locally

Before deploying, run the agents locally to see how they work:

```bash
uv run adk web
```

Select **`agent_router`** from the dropdown in the ADK web UI. Try these questions to exercise each sub-agent and tool:

| Question | Route | What happens |
|----------|-------|-------------|
| *"Hello!"* | `agent_greeter` → `get_greeting` | Returns a time-appropriate greeting and introduces the system |
| *"Tell me about Jupiter"* | `agent_tools` → `lookup` | Searches the in-memory knowledge base for planet facts |
| *"Why is Mars red?"* | `agent_tools` → `explain` | Calls Gemini directly via `google-genai` for a detailed explanation |
| *"What is 149.6 * 1000?"* | `agent_tools` → `calculate` | Evaluates the math expression |
| *"How far is the Moon compared to Mars as a percentage?"* | `agent_tools` → `lookup` + `calculate` | Multi-tool: looks up distances, then calculates the ratio |
| *"What can you do?"* | `agent_greeter` → `get_greeting` | Explains available capabilities |

Watch the event stream in the ADK UI to see agent transfers, tool calls, and responses in real time.

---

## Deploy

```bash
# Deploy to Agent Engine
uv run python deploy/deploy.py

# Manage the deployment
uv run python deploy/deploy.py --info     # show deployment info + console URL
uv run python deploy/deploy.py --test     # send a test query
uv run python deploy/deploy.py --update   # push latest code
uv run python deploy/deploy.py --delete   # tear down
```

See [deploy/readme.md](deploy/readme.md) for the full deployment deep-dive.

---

## Interact with Deployed Agents

See [deploy/interact.ipynb](deploy/interact.ipynb) for a runnable tutorial covering:
- Connecting to a deployed agent via the Python SDK
- Creating and managing sessions
- Streaming queries
- Using the REST API directly

---

## References

- [Google ADK documentation](https://google.github.io/adk-docs/)
- [Vertex AI Agent Engine overview](https://docs.cloud.google.com/agent-builder/agent-engine/overview)
- [Deploy ADK agents to Agent Engine](https://google.github.io/adk-docs/deploy/agent-engine/deploy/)
- [SDK migration guide (v1.112.0+)](https://docs.cloud.google.com/agent-builder/deprecations/agent-engine-migration)
- [data-onboarding](../data-onboarding/) — a production example using these same patterns at scale
