![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fagent-building%2Fdeploy&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/agent-building/deploy/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/deploy/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/deploy/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/deploy/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/deploy/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/agent-building/deploy/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/agent-building/deploy/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Deploy to Agent Runtime (Scale + Govern)

Phase 1 ran the whole system locally. This folder is **Phase 2**: it ships the two
agents to [**Agent Runtime**](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
— the platform's managed runtime (formerly Agent Engine) — and turns on the
**Scale** and **Govern** pillars that only exist once an agent is deployed.

Agent Runtime gives every deployed ADK agent, with no extra code:

- **Managed [Sessions](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/overview)** — persistent, cloud-based conversation state.
- **[Memory Bank](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/memory-bank/overview)** — long-term user facts, on the same Runtime instance.
- **Cloud Monitoring, Logging, and Trace** — metrics, logs, and distributed traces.
- **[Agent Registry](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-registry) auto-registration** and an **[Agent Identity](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-identity-overview)** (Govern).

---

## Two deployables, on purpose

This is the same hybrid architecture from Phase 1, now at Runtime scale. The two
composition styles map onto **two separate Runtime resources**:

| Target | What deploys | Deploy mode | Reached how |
|---|---|---|---|
| **`discovery`** | `agent_discovery` (Claude on Vertex) + its catalog tool, wrapped in an `A2aAgent` | **object** (cloudpickled) | native **A2A** — Runtime serves the agent card + protocol on `.../a2a` |
| **`concierge`** | router + in-process `agent_catalog` / `agent_analytics` + observability, wrapped in an `AdkApp` | **source** (uploaded `.py`) | `stream_query` API / ADK web |

Deploy **discovery first** — it's the dependency. Then point the concierge at
discovery's A2A endpoint and deploy it. The concierge's `RemoteA2aAgent` wiring is
unchanged from local; only the URL (and now, authentication + protocol version)
differs.

```
   Phase 1 (local)                          Phase 2 (deployed)
   ───────────────                          ──────────────────
   concierge  (adk web)                     concierge  ── Agent Runtime resource (AdkApp)
     └─A2A→ localhost:8001                     └─authed A2A→ discovery Runtime resource
              discovery (uvicorn, to_a2a)                    (A2aAgent, native A2A on .../a2a)
```

> **Why ADK 2.x here.** Building this deployed hop is exactly why the project
> runs on **google-adk 2.6+ / a2a-sdk 1.x**. Native A2A on Agent Runtime uses the
> `vertexai.agent_engines.templates.a2a.A2aAgent` template, which requires A2A
> protocol **v1.0** types (`supported_interfaces`, `TransportProtocol`,
> `PROTOCOL_VERSION_CURRENT`) that only ship in `a2a-sdk` 1.x — and ADK only
> lifts its `a2a-sdk<0.4` cap at 2.5.0+. On ADK 1.x the deployed cross-Runtime A2A
> hop cannot be served at all. Locally, `to_a2a()` still serves a v0.3 card at the
> well-known path; the consumer branches on the URL to pick the right card path.

---

## Quick start

```bash
# 0. One-time: make sure the demo data exists (Phase 1).
make setup

# 1. Deploy discovery first (it's the A2A dependency).
make deploy-discovery                       # = uv run python deploy/deploy.py discovery
uv run python deploy/deploy.py discovery --info      # copy the resource name / A2A endpoint

# 2. Point the concierge at the deployed discovery agent.
#    Set DISCOVERY_A2A_URL in .env to discovery's A2A endpoint:
#      https://{region}-aiplatform.googleapis.com/v1beta1/{resource_name}/a2a
#    (leave blank to keep using a local discovery on localhost:8001)

# 3. Deploy the concierge.
make deploy-concierge                       # = uv run python deploy/deploy.py concierge

# Manage either agent
uv run python deploy/deploy.py concierge --test      # send a test query to the deployed agent
uv run python deploy/deploy.py concierge --update    # push latest code
uv run python deploy/deploy.py concierge --info      # resource name + console URL
make deploy-delete                          # tear down both
```

Each deploy runs a **local smoke test** first (against the exact object that
ships — the concierge's `AdkApp`, discovery's in-memory runner). Skip it with
`--skip-local-test`.

---

## How it works

The two agents ship in **two different deploy modes**, each the natural fit for
what it exposes. `deploy.py` picks the mode per target from `AGENT_CONFIGS`.

### Concierge — source mode (`AdkApp`)

The concierge uses the [source-file deployment method](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/deploy)
of the client-based SDK (`google-cloud-aiplatform` v1.112.0+): your Python source
is uploaded directly — no pickling. Agent Runtime needs an
[`AdkApp`](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/develop/adk)
so it can expose `stream_query`, `create_session`, and the Memory Bank methods as
API endpoints. A thin entrypoint module builds it without touching the `agent.py`
that also serves `adk web`:

```python
# deploy/entrypoint_concierge.py
from vertexai.agent_engines import AdkApp
from agent_concierge.agent import app as concierge_app   # the ADK App (carries the plugin)
app = AdkApp(app=concierge_app, enable_tracing=True)
```

The concierge wraps its ADK **`App`** so the observability plugin ships too. At
deploy time `deploy.py`:

1. Collects the source to ship — every `agent_*` package, the `deploy/` package,
   **and the root `config.py`** (this project shares one root config across all
   agents, so it must travel with the source).
2. Generates a `requirements.txt` from `pyproject.toml` (removed afterward).
3. Uploads it with the entrypoint, [class-methods spec](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/manage-with-adk), and env vars.

### Discovery — object mode (`A2aAgent`)

The discovery agent doesn't expose `stream_query`; it speaks **native A2A**. That
comes from the `vertexai.agent_engines.templates.a2a.A2aAgent` template, which
Agent Runtime serves as a real A2A endpoint (agent card + JSON protocol) at
`.../reasoningEngines/{id}/a2a`. `entrypoint_discovery.py` builds one:

```python
# deploy/entrypoint_discovery.py (sketch)
from vertexai.agent_engines.templates.a2a import A2aAgent
# 1. Build the ADK agent card, then retarget its primary interface to the
#    template's required binding — AgentCardBuilder emits JSONRPC, but A2aAgent
#    requires HTTP+JSON / protocol v1.0 or it raises ValueError.
# 2. Wrap the discovery Runner in an A2aAgentExecutor(use_legacy=False).
app = A2aAgent(agent_card=..., agent_executor_builder=...)
```

Because `A2aAgent` is a live template object (not just source), discovery deploys
in **object mode**: `client.agent_engines.create(agent=<A2aAgent>, config={...})`
cloudpickles the object and ships `agent_discovery` + `config.py` as extra
packages. `A2aAgent.set_up()` rewrites the card's URL to the live Runtime endpoint
at deploy time, and `register_operations()` publishes the A2A surface — no
class-methods spec.

### Sessions + Memory Bank — mostly automatic

Once deployed, `AdkApp` uses **managed cloud sessions** and
**`VertexAiMemoryBankService`** (on this same Runtime instance) by default — no
builder needed. The agent's only jobs, wired in `agent_concierge/`:

- **Recall** — `PreloadMemoryTool` + `LoadMemoryTool` on the root agent surface
  stored memories to the model (`utils/memory.py`).
- **Persist** — an `after_agent_callback` calls `add_session_to_memory` to distill
  each finished turn into Memory Bank (generation is **not** automatic). It's a
  no-op locally, so behavior is identical with or without a memory service.

See the [ADK Memory Bank quickstart](https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/adk-quickstart).

### The authenticated A2A hop

Local discovery is plain HTTP on `localhost`, and `to_a2a()` serves its card at
the **well-known path** (`/.well-known/agent-card.json`, protocol v0.3). A
**deployed** discovery agent lives under `*-aiplatform.googleapis.com`, speaks
protocol **v1.0**, and serves an *authenticated* card at `.../a2a/v1/card` — not
the well-known path. So the concierge adapts on both axes:

- **Card path** — `agent_concierge/utils/a2a.py` branches on `googleapis.com` in
  the base URL: `/v1/card` for a deployed Runtime, well-known for localhost.
- **Auth** — `agent_concierge/utils/auth.py` returns a token-refreshing `httpx`
  client for a `googleapis.com` URL and `None` for localhost.
- **Protocol** — the `RemoteA2aAgent` is built with `use_legacy=False` so it
  talks v1.0 to both ends (requires a2a-sdk 1.x / ADK 2.x).

The same `RemoteA2aAgent` wiring works in both places. (An A2A consumer configured
this way is best run from `adk web` or Cloud Run; see the
[walkthrough notebook](interact.ipynb).)

---

## Govern — what deployment turns on

Deploying to Agent Runtime is also how the **Govern** pillar engages, with little
to no extra work:

- **[Agent Registry](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-registry)** — deployed agents are auto-registered in a central, queryable catalog (versions, framework = ADK, capabilities). Both `concierge` and `discovery` show up automatically.
- **[Agent Identity](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-identity-overview)** — each agent gets a strongly-attested, cryptographic **SPIFFE ID** tied to its lifecycle — stronger isolation than a shared service account, and it brokers outbound tool auth.
- **[Agent Gateway](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview)** — the central enforcement point for agent↔agent and agent↔tool traffic: mTLS, least-privilege policy, and AI guardrails via [Model Armor](https://docs.cloud.google.com/security-command-center/docs/model-armor-overview). Registry membership is a prerequisite for connectivity.

See the platform [Govern overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern).

---

## Files

```
deploy/
├── deploy.py                 # multi-target CLI: concierge | discovery
├── entrypoint_concierge.py   # AdkApp(app=concierge App) — source mode, ships the plugin
├── entrypoint_discovery.py   # A2aAgent(agent_card, executor) — object mode, native A2A
├── interact.ipynb            # sessions + memory walkthrough (SDK) against a deployment
├── concierge/deployment.json # written by deploy.py (resource name, timestamps)
└── discovery/deployment.json
```
