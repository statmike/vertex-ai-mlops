![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fagent-building&file=README.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/agent-building/README.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/README.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/agent-building/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/agent-building/README.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/agent-building/README.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Agent Building — A Tour of the Gemini Enterprise Agent Platform

One multi-agent retail workflow, built with [Google ADK](https://adk.dev/) and run through **every pillar** of the [Gemini Enterprise Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform) — Build, Scale, Govern, Optimize. It is a *learner*: read it top to bottom to see how the platform's parts fit together, or run it to watch a fleet of agents answer real questions over live BigQuery data, unstructured documents, and a data catalog.

> **Naming note:** In April 2026 **Vertex AI** was rebranded to the **Gemini Enterprise Agent Platform**. This is largely a branding change — the SDKs and API namespaces are unchanged (`google-cloud-aiplatform`, `vertexai`, `dataplex_v1`). Several components were renamed too: **Agent Engine → Agent Runtime** (SDK module still `agent_engines`), and **Dataplex Universal Catalog → Knowledge Catalog** (`dataplex` namespace unchanged). This project uses the new names in prose and keeps the stable identifiers in code.

## What you get

- **A realistic multi-agent system** for a fictional retailer, *theLook*, that answers three distinct kinds of question and routes each to the right specialist.
- **Model variety on purpose** — Gemini 3 Pro, Flash, and Flash-Lite *and* Claude on Vertex, so you see how a mixed-model fleet is wired.
- **Both composition styles a Google developer reaches for** — tightly-coupled in-process sub-agents *and* an independently-deployable agent consumed over the **A2A protocol**.
- **A clean setup/agent boundary** — every bit of provisioning lives in [`scripts/`](scripts/), so the agent code reads the way it would at a company that *already has its data*.
- **Textbook structure** — one agent per folder, one file per tool, shared code in `utils/`, no spiderweb imports.

> **Delivery is phased, and all phases are complete.** This document and the code cover **Phase 1 (Build)** — the full local workflow — **Phase 2 (Scale + Govern)** — deploying both agents to Agent Runtime with Sessions + Memory Bank (see [`deploy/`](deploy/)) — **Phase 3 (Optimize)** — two evaluation engines plus observability over the event log (see [`optimize/`](optimize/)) — **Phase 4 (Build helpers)** — mapping this hand-built project onto the platform's [Studio/Garden/CLI on-ramps](#build-helpers-phase-4) — and **Phase 5 (full-platform coverage)** — interop (MCP, web grounding, A2A skills), managed Example Store + RAG Engine, Model Armor, the Skill Registry, the Agent Optimizer, and a map of the [console/policy-only features](#platform-features-you-configure-not-code). See the [Roadmap](#roadmap).

## The platform, in four pillars

The Agent Platform organizes the agent lifecycle into four pillars. This project touches all four; the table links each to its docs and to where it shows up here.

| Pillar | What it covers | Key components | Where in this project |
|---|---|---|---|
| **[Build](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build)** | Author agents and their tools | [ADK](https://adk.dev/), [Agent Garden](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/agent-garden) & [Studio](https://docs.cloud.google.com/gemini-enterprise-agent-platform/agent-studio), [Agents CLI](https://google.github.io/agents-cli/guide/getting-started/), [RAG Engine](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview), [MCP](https://modelcontextprotocol.io/), [Skill Registry](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/skill-registry) | `agent_concierge/`, `agent_discovery/`, `agent_web/`, `mcp_server/`, `agent_mcp_client/`, `skills/` (Phase 1 ✅) + [Build helpers](#build-helpers-phase-4) |
| **[Scale](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)** | Deploy and run in production | [Agent Runtime](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview), [Sessions](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/overview), [Memory Bank](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/memory-bank/overview) | [`deploy/`](deploy/) (Phase 2 ✅) |
| **[Govern](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern)** | Identity, registry, safety | [Agent Identity](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-identity-overview), [Agent Registry](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-registry), [Agent Gateway](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview) / [Model Armor](https://docs.cloud.google.com/security-command-center/docs/model-armor-overview) | [`deploy/`](deploy/) + README (Phase 2 ✅) |
| **[Optimize](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview)** | Evaluate, simulate, observe | [Gen AI Evaluation](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview), Simulation, [Observability](https://adk.dev/integrations/bigquery-agent-analytics/) | [`optimize/`](optimize/) (Phase 3 ✅) |

## The workflow: theLook's concierge

The domain is a fictional online retailer with a big catalog. A shopper, merchant, or analyst asks one front-door agent anything; it routes to the specialist that owns the answer.

```
User ─▶ agent_concierge ............... root router      (Gemini 3 Pro)
          │
          ├─(in-process sub-agent)──▶ agent_catalog ..... policy & how-to Q&A from documents   (Gemini 3 Flash)
          │                                               unstructured docs in a BigQuery object table (AI.GENERATE)
          │
          ├─(in-process sub-agent)──▶ agent_analytics ... numbers from live BigQuery data       (Gemini 3 Flash-Lite)
          │                                               Conversational Analytics API, inline tables
          │
          └─(A2A remote agent)──────▶ agent_discovery ... "what data do you have about X?"       (Claude on Vertex)
                                                          Knowledge Catalog semantic search
                                                          — its own deployable, reached over A2A
```

Three questions, three data modalities, four models:

| Ask | Routed to | Data it uses |
|---|---|---|
| *"What's your return window?"* | `agent_catalog` | Unstructured docs (object table + `AI.GENERATE`) |
| *"Which product category sold the most last quarter?"* | `agent_analytics` | Live BigQuery theLook tables (Conversational Analytics API) |
| *"What tables do you have about orders?"* | `agent_discovery` | Knowledge Catalog metadata (semantic `search_entries`) |

### Why two composition styles?

A developer optimizing for flexibility uses **both**, so this project shows both deliberately:

- **In-process sub-agents** (`agent_catalog`, `agent_analytics`) — tight coupling, low latency, one deployable. Wired with ADK `sub_agents=[...]`. Best when the specialists share a lifecycle and owner.
- **A2A remote agent** (`agent_discovery`) — its own service with an independent lifecycle, scaling, and (often) team. The concierge [consumes](https://google.github.io/adk-docs/a2a/quickstart-consuming/) it as a `RemoteA2aAgent` pointed at the agent's card URL. Locally it is [exposed](https://google.github.io/adk-docs/a2a/quickstart-exposing/) via `to_a2a()` + uvicorn; in production it deploys separately to Agent Runtime.

### Few-shot steering with an Example Store

The analytics agent doesn't hard-code a fixed few-shot block in its prompt. Instead it draws from a managed [Example Store](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/example-stores/overview) — a semantically-searchable set of curated `(question → ideal answer)` pairs — and injects the *few most similar* examples for each incoming question. A "top categories by revenue" question is steered by a revenue example; an "average order value" question by a formatting example. `scripts/setup.py` provisions and seeds the store; the agent attaches it via ADK's `VertexAiExampleStore` wrapped in an `ExampleTool` (see [`agent_analytics/examples.py`](agent_concierge/sub_agents/agent_analytics/examples.py)), which searches the store on every turn and prepends the matches. Vertex assigns the store a numeric resource id, so setup, cleanup, and the agent all resolve it by its deterministic *display name* (or an explicit `EXAMPLE_STORE_NAME` override). Fully guarded: with no store provisioned the tool is `None` and the agent runs unsteered.

### Two retrieval paths for the catalog agent: hand-built vs. managed RAG

The catalog agent answers policy/help questions from the same set of unstructured retail docs *two* ways, side by side, so you can compare the platform's managed retrieval against a hand-built one:

- **Hand-built** — a BigQuery **object table** over the GCS docs plus `AI.GENERATE` (`search_docs`). You own the retrieval SQL and the grounding prompt.
- **Managed** — Vertex's [RAG Engine](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview): `scripts/setup.py` creates a **corpus** backed by a managed vector database (the "Vector Search" storage) and imports the *same* GCS docs, letting the platform handle chunking, embedding, indexing, and semantic retrieval. The agent attaches it via ADK's `VertexAiRagRetrieval` (see [`agent_catalog/rag.py`](agent_concierge/sub_agents/agent_catalog/rag.py)). As with the Example Store, Vertex assigns the corpus a numeric id, so setup, cleanup, and the agent all resolve it by its deterministic *display name* (or an explicit `RAG_CORPUS_NAME` override). Fully guarded: with no corpus provisioned the tool is `None` and the agent falls back to `search_docs` alone.

> **Serverless-mode note:** the corpus uses the `RagManagedVertexVectorSearch` backend — the older `RagManagedDb` backend is rejected in serverless projects. Provisioning goes through the `agentplatform` client (the successor to the deprecated `vertexai.preview.rag`, whose embedding-config path is broken in the current SDK); the runtime resolver still reads it through either SDK since it's the same resource.

### Interoperability: tools over MCP, web grounding, and A2A skills

Beyond the three specialists, the project carries a few small **standalone** components (each its own top-level folder, run directly with `uv run adk web <folder>`) that round out the *tool* story — how an agent sources capabilities. They're kept separate on purpose, so they don't perturb the concierge topology the [optimize](optimize/) harness pins.

- **Publishing tools over [MCP](https://modelcontextprotocol.io/)** — [`mcp_server/`](mcp_server/) re-publishes the same three ADK tools (catalog, analytics, discovery) as a [Model Context Protocol](https://modelcontextprotocol.io/) server, over both **stdio** (how a desktop client launches a server) and **Streamable-HTTP** (the production transport; deploy behind Cloud Run). `adk_to_mcp_tool_type` derives each tool's MCP schema straight from its ADK signature.
- **Consuming tools over MCP** — [`agent_mcp_client/`](agent_mcp_client/) is an agent whose *entire* toolset comes from a remote MCP server via ADK's `McpToolset` — no tools are defined in the package; ADK calls the server's `list_tools` at runtime and turns each into a callable. This is the client counterpart to `mcp_server/`.
- **Web grounding** — [`agent_web/`](agent_web/) carries ADK's built-in `google_search` tool: where the other agents read theLook's *internal* documents and data, this one grounds answers in the *public web* with citations. (Built-in grounding tools can't be mixed with ordinary function tools in one agent, so it stands alone; to offer it alongside the others, add it as an in-process `sub_agent`.)
- **Explicit A2A skills** — the discovery agent's card advertises rich [`AgentSkill`](https://google.github.io/adk-docs/a2a/) entries (see [`agent_discovery/skills.py`](agent_discovery/skills.py)), so an A2A consumer can discover *what it can do* — distinct from the Skill Registry below (a shared, searchable catalog of reusable skill bundles).

### Publishing reusable skills to the Skill Registry

Where A2A `AgentCard.skills` describe *one agent's* advertised capabilities, the platform's [Skill Registry](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/skill-registry) is a **shared, semantically-searchable catalog** of reusable skill *bundles* that any agent or team can discover and pull. [`skills/`](skills/) publishes bundles to it over `client.skills` (`publish | list | retrieve | delete`), reusing the sibling `agent-skills/` project's `SKILL.md` bundles as-is. The registry is regional-only (us-central1 / europe-west4 / us-east5) and always ships a built-in `gcp-skill-registry` alongside yours; a semantic `retrieve("forecast sales in BigQuery")` ranks the matching bundle first.

## Project layout

Opinionated and flat to trace: an agent is a folder, its tools are one-file-each under `tools/`, its sub-agents nest under `sub_agents/`, shared helpers live in `utils/`, and `__init__.py` wires the modules.

```
agent-building/
├── README.md                      # you are here — platform tour + Phase 1
├── config.py                      # ALL settings (per-agent model + location split)
├── .env.example                   # every env var, documented
├── pyproject.toml                 # uv project; ruff + pytest config
├── Makefile                       # install / setup / run / discovery / test / lint
│
├── scripts/                       # *** provisioning — run once; skip if you have data ***
│   ├── setup.py                   # APIs, IAM, BQ views, profile scans, GCS docs, object table,
│   │                              #   Model Armor, Example Store, RAG corpus
│   ├── cleanup.py                 # tears it all down (mirrors setup via shared ids)
│   └── resources.py               # deterministic resource-id helpers (no drift)
│
├── deploy/                        # *** Phase 2: Scale + Govern → Agent Runtime ***
│   ├── deploy.py                  # multi-target CLI: concierge | discovery
│   ├── entrypoint_concierge.py    # AdkApp(app=...) — source mode, ships the observability plugin
│   ├── entrypoint_discovery.py    # A2aAgent(...) — object mode, native A2A on Runtime
│   └── interact.ipynb             # sessions + Memory Bank walkthrough on a deployment
│
├── optimize/                      # *** Phase 3: Optimize — eval, simulation, observability ***
│   ├── harness/                   # tested offline library (traces, scoring, report, SQL)
│   ├── run_local.py / judge_local.py       # local eval engine
│   ├── simulate_platform.py / evaluate_platform.py  # managed Simulation + AutoRaters
│   └── observe_events.py          # summarize the BigQuery event log
│
├── skills/                        # *** Build: publish reusable skills to the Skill Registry ***
│   ├── bundles.py                 # discover bundles + parse SKILL.md (offline, tested)
│   └── registry.py                # publish | list | retrieve | delete over client.skills
│
├── agent_concierge/               # ROOT router (Gemini 3 Pro)
│   ├── agent.py                   # root_agent + App(plugins=[observability])
│   ├── prompts.py                 # global_instructions + agent_instructions
│   ├── bq_plugin.py               # BigQuery Agent Analytics plugin (observability)
│   ├── guard.py                   # Model Armor prompt/response callbacks (Govern)
│   ├── utils/                     # a2a card URL, authed A2A client, Memory Bank wiring
│   ├── sub_agents/
│   │   ├── agent_catalog/         # unstructured search  (Gemini 3 Flash)
│   │   │   └── rag.py             # RAG Engine managed-retrieval tool (Build)
│   │   └── agent_analytics/       # BigQuery Q&A          (Gemini 3 Flash-Lite)
│   │       └── examples.py        # Example Store few-shot tool (Build)
│   └── tests/
│
├── agent_discovery/               # INDEPENDENT A2A agent (Claude on Vertex)
│   ├── agent.py                   # root_agent + to_a2a(...) app for uvicorn
│   ├── prompts.py
│   ├── skills.py                  # explicit A2A AgentCard.skills (Build)
│   └── tools/                     # Knowledge Catalog search (one file per tool)
│
│   # --- standalone interop demos (own folders; not concierge sub-agents) ---
├── agent_web/                     # built-in google_search grounding    (Gemini 3 Flash)
├── mcp_server/                    # publishes theLook's tools over MCP (stdio + HTTP)
│   ├── server.py                  # low-level MCP server (list_tools / call_tool)
│   └── registry.py                # wraps the 3 ADK tools as MCP tools
└── agent_mcp_client/              # an agent whose whole toolset is an McpToolset
```

## Quickstart (Phase 1, local)

**Prerequisites:** [`uv`](https://docs.astral.sh/uv/), the [`gcloud` CLI](https://cloud.google.com/sdk/docs/install) authenticated (`gcloud auth application-default login`), and a Google Cloud project with billing. Claude on Vertex must be [enabled in Model Garden](https://cloud.google.com/products/model-garden/claude).

```bash
# 1. Install
make install                       # uv sync --extra dev

# 2. Configure
cp .env.example .env               # then set GOOGLE_CLOUD_PROJECT

# 3. Provision the demo data (once). A real company skips this — it already
#    has its data — and just points config.py at existing resources.
make setup                         # BQ views, GCS docs, object table, Model Armor,
                                   #   Example Store, RAG corpus, IAM (see scripts/)

# 4. Run. The discovery agent is a separate service, so start it first…
make discovery                     # serves agent_discovery over A2A on :8001
#    …then, in a second terminal, launch the concierge web UI:
make run                           # uv run adk web .
```

Open the ADK web UI, pick **agent_concierge**, and try one question of each kind (see the table above). Watch the event stream: you'll see in-process `transfer_to_agent` calls for catalog/analytics, and an **A2A hop** out to the discovery service.

```bash
make test                          # offline unit tests (cloud clients mocked)
make check                         # lint + test
make cleanup                       # remove everything setup.py created
```

## The setup / agent boundary

This is the project's central discipline: **agents never provision.** All dataset creation, IAM, API enablement, and demo-data seeding live in [`scripts/`](scripts/). The agent packages assume their resources already exist — exactly the situation at a company with an established data estate. The one deliberate exception is the observability plugin ([`bq_plugin.py`](agent_concierge/bq_plugin.py)), which get-or-creates its own tiny *event-log* table: that is the agent's own telemetry, not domain data, and it is fully guarded so the agent runs fine without it. `scripts/cleanup.py` still removes it.

Because every resource name derives from `RESOURCE_PREFIX` (via [`scripts/resources.py`](scripts/resources.py)), `setup.py` and `cleanup.py` reconstruct identical names — no drift, clean teardown.

## Scale + Govern (Phase 2)

Phase 1 runs everything locally. **Phase 2 deploys** both agents to [Agent Runtime](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview) — the managed runtime formerly called Agent Engine — which turns on the platform features that only exist once an agent ships. Full details are in [`deploy/`](deploy/); the shape:

```bash
make deploy-discovery      # deploy the standalone A2A agent first (it's the dependency)
# set DISCOVERY_A2A_URL in .env to discovery's Runtime A2A endpoint, then:
make deploy-concierge      # deploy the router + in-process specialists
```

The two composition styles become **two separate Runtime resources** — deployed two different ways. The concierge ships in **source mode** as an `AdkApp` (its Python is uploaded and it exposes `stream_query`). Discovery ships in **object mode** as an [`A2aAgent`](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview), which Agent Runtime serves as a real, native **A2A** endpoint. The concierge's `RemoteA2aAgent` wiring is unchanged from local — only discovery's URL differs, and the hop is now authenticated (a token-refreshing client for the `googleapis.com` endpoint, `None` for localhost; see [`utils/auth.py`](agent_concierge/utils/auth.py)).

> **Why this project runs on google-adk 2.x.** Serving native A2A on Agent Runtime uses the `A2aAgent` template, which requires A2A protocol **v1.0** types that ship only in `a2a-sdk` 1.x — and ADK lifts its `a2a-sdk` cap to allow that only at **2.5.0+**. The deployed cross-Runtime A2A hop is therefore a 2.x capability; on ADK 1.x it cannot be served. Locally, the v0.3 well-known card URL still works; deployed, the card is embedded in the resource (the Runtime serves no fetchable card), so the consumer reads it from there. See [`deploy/readme.md`](deploy/readme.md) for the wiring.

**Scale** — deployment gives you, with no extra code:

- **Managed [Sessions](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/overview)** — persistent cloud conversation state.
- **[Memory Bank](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/memory-bank/overview)** — long-term user facts across sessions. `AdkApp` uses it by default when deployed; the concierge only supplies the *recall* tools (`PreloadMemoryTool`/`LoadMemoryTool`) and a *persist* callback (`add_session_to_memory`) in [`utils/memory.py`](agent_concierge/utils/memory.py). Both no-op locally, so behavior is identical either way.

**Govern** — deploying is also what engages the Govern pillar, largely for free:

- **[Agent Registry](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-registry)** — deployed agents auto-register in a central, queryable catalog (version, framework = ADK, capabilities).
- **[Agent Identity](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-identity-overview)** — each agent gets a strongly-attested cryptographic **SPIFFE ID** tied to its lifecycle — stronger isolation than a shared service account.
- **[Agent Gateway](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview)** — central enforcement (mTLS, least-privilege policy, and AI guardrails via [Model Armor](https://docs.cloud.google.com/security-command-center/docs/model-armor-overview)) for agent↔agent and agent↔tool traffic.
- **[Model Armor](https://docs.cloud.google.com/security-command-center/docs/model-armor-overview) guardrails** — this project wires Model Armor *in code*: `scripts/setup.py` provisions a policy template (prompt-injection / jailbreak, malicious-URI, and responsible-AI filters), and the concierge screens every prompt and response against it via `before_model_callback` / `after_model_callback` (see [`agent_concierge/guard.py`](agent_concierge/guard.py)). Callbacks — not an `App` plugin — because `adk web` doesn't apply plugins, so the guard is active locally *and* deployed. It's fully guarded: with no template configured the callbacks are no-ops. A blocked prompt never reaches the model; a blocked answer is replaced with a safe refusal.

The [`deploy/interact.ipynb`](deploy/interact.ipynb) notebook connects to a live deployment and demonstrates sessions and cross-session memory end to end.

## Platform features you configure, not code

Some of the platform is enforced by the org — set up in the Cloud console or by an administrator's policy, not reproduced in an agent's Python. A complete tour still owes you an honest map of them: what each does, and how it would wrap the system this project already deploys. None require changes to the agent code here; they sit *around* it.

| Feature | What it does | How it wraps this project |
|---|---|---|
| **[Agent Gateway](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview)** | The platform's networking layer for agentic traffic — Client-to-Agent (ingress) and Agent-to-Anywhere (egress) — mediating HTTP protocols including **MCP** and **A2A**, and enforcing access via IAM, Identity-Aware Proxy, and Model Armor. | Would front the concierge↔discovery **A2A hop** and the [`mcp_server`](mcp_server/) traffic with central mTLS + policy, instead of the per-call authed client this project wires by hand. (Limits: no VPC-SC support; ~5,000 resources per gateway.) |
| **[Semantic Governance](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/policies/semantic-governance-overview)** *(Preview)* | An LLM-based runtime layer that evaluates an agent's *proposed tool calls* against plain-English **Natural Language Constraints** before execution, allowing only calls that match trusted-user intent. Enforced through the Agent Gateway. | Would gate each `transfer_to_agent` / tool call (e.g. "analytics may read theLook tables but never DELETE") as a policy — a complement to the in-code [Model Armor](https://docs.cloud.google.com/security-command-center/docs/model-armor-overview) prompt/response screening. Run dry-run first; verdicts are probabilistic. |
| **[Agent Platform Threat Detection](https://docs.cloud.google.com/security-command-center/docs/agent-platform-threat-detection-overview)** *(Preview)* | A built-in Security Command Center service that monitors agents on **Agent Runtime** for runtime threats (malicious binaries, container escapes, reverse shells) and control-plane threats (data exfiltration, suspicious token generation). | Would watch the two deployed Runtime engines (concierge, discovery) and raise SCC findings — zero agent code; enabled at the SCC/project level. |
| **[AI Protection](https://docs.cloud.google.com/security-command-center/docs/ai-protection-overview)** | The broader SCC posture capability: inventory AI assets, find vulnerabilities and over-privileged agents, centralize AI risk. | Would flag, e.g., an over-broad role on the Runtime service agent — the least-privilege grants in [`scripts/setup.py`](scripts/setup.py) are the code-side counterpart. Advanced features need SCC Premium/Enterprise. |
| **[Managed Agents API](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/managed-agents)** *(Pre-GA)* | Build autonomous, fully-managed agents with a single API call (the "Antigravity" harness): each runs in an isolated sandbox that reasons, plans, executes code, searches, and reads/writes files. Configure via the Agents API, drive at runtime via the Interactions API. | An alternative *authoring model* to the hand-built ADK agents here — you'd describe an agent rather than assemble it. Not for production/sensitive data yet. |

Two Govern features this project *does* engage automatically on deploy — **[Agent Registry](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-registry)** (auto-registration) and **[Agent Identity](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-identity-overview)** (SPIFFE-based per-agent identity) — are covered in [Scale + Govern](#scale--govern-phase-2) above.

> **SDK naming in flux.** The platform is mid-rename at the SDK layer too. `vertexai.Client` now emits a deprecation warning pointing to **`agentplatform.Client`**, and `vertexai.preview.rag` likewise points to `agentplatform`'s RAG surface. This project uses `agentplatform.Client` where the older path is broken (RAG provisioning; see [Two retrieval paths](#two-retrieval-paths-for-the-catalog-agent-hand-built-vs-managed-rag)) and the stable `vertexai`/`google-cloud-aiplatform` identifiers elsewhere, since both resolve to the same resources during the transition.

## Models

| Agent | Model | Why |
|---|---|---|
| `agent_concierge` | `gemini-3-pro-preview` | Strongest reasoning — routing is the hardest decision |
| `agent_catalog` | `gemini-3-flash-preview` | Fast, capable grounded document Q&A |
| `agent_analytics` | `gemini-3-flash-lite-preview` | Cheapest — the Conversational Analytics API does the heavy lifting |
| `agent_discovery` | `claude-opus-5` (Vertex) | Model variety; strong at synthesizing catalog metadata |

Each agent's model **and** its serving location are set independently in [`config.py`](config.py). Preview Gemini models are served from the `global` endpoint; Claude is served from Model Garden. Keeping model-location separate from infra-location (where Agent Runtime deploys) is what lets the same code run locally and deployed without endpoint 404s.

## Build helpers (Phase 4)

This project writes agents in **ADK by hand** so every moving part is visible — that is the point of a learner. The Build pillar also offers higher-level on-ramps that get you to the same place faster; here is where each fits, and how this project maps onto them.

- **[Agent Studio](https://docs.cloud.google.com/gemini-enterprise-agent-platform/agent-studio)** — a low-code visual canvas in the Cloud console for designing and testing an agent's reasoning loop. Prototype a router like `agent_concierge` visually, then **export to ADK** to continue in full code — exactly the code shape in this repo.
- **[Agent Garden](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/agent-garden)** — a curated library of prebuilt, source-available agent samples (RAG, analysis, multi-agent patterns) wired to RAG Engine, Vector Search, and Gemini. A faster start than a blank folder when your use case matches a template.
- **[Agents CLI](https://google.github.io/agents-cli/guide/getting-started/)** — `uvx` CLI (successor to the agent-starter-pack) that scaffolds, evaluates, deploys, and publishes ADK agents, and ships skills for AI coding assistants. It is the tooling counterpart to this project's hand-written [`Makefile`](Makefile) + [`deploy/`](deploy/) + [`optimize/`](optimize/): `agents-cli deploy` targets Agent Runtime (Python only), and `agents-cli publish gemini-enterprise` registers the deployment. See the [ADK + Agents CLI quickstart](https://docs.cloud.google.com/gemini-enterprise-agent-platform/agents/quickstart-adk) and [deploy an agent](https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/deploy-an-agent).
- **[RAG Engine](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview)** — managed retrieval (chunking, embeddings, vector storage). This project **ships it**: `agent_catalog` runs it alongside its hand-built object-table + `AI.GENERATE` tool over the same docs, so you can compare the two paths directly (see [Two retrieval paths](#two-retrieval-paths-for-the-catalog-agent-hand-built-vs-managed-rag)).

The trade-off is deliberate: the helpers optimize for speed to a working agent; this repo optimizes for *seeing* how an agent is assembled. Once you understand the hand-built version here, the Studio/Garden/CLI paths are the same components with the boilerplate removed.

## Roadmap

- **Phase 1 — Build** ✅ — local multi-agent workflow, provisioning scripts, tests.
- **Phase 2 — Scale + Govern** ✅ — deploy concierge and discovery separately to Agent Runtime; Sessions + Memory Bank; a walkthrough notebook; Agent Registry / Identity / Gateway notes. See [`deploy/`](deploy/).
- **Phase 3 — Optimize** ✅ — the Platform Simulation & Evaluation API *and* a local offline harness + judge + report; Observability over the BigQuery event log. See [`optimize/`](optimize/).
- **Phase 4 — Build helpers** ✅ — [Agent Studio, Agent Garden, Agents CLI, and RAG Engine](#build-helpers-phase-4) references mapping the hand-built project onto the platform's higher-level on-ramps; final docs pass with all links verified.
- **Phase 5 — Full-platform coverage** ✅ — closed the remaining feature gaps so the tour spans the whole platform: interop ([MCP](#interoperability-tools-over-mcp-web-grounding-and-a2a-skills) server/client, web grounding, A2A skills), managed [few-shot Example Store](#few-shot-steering-with-an-example-store) and [RAG Engine](#two-retrieval-paths-for-the-catalog-agent-hand-built-vs-managed-rag), in-code [Model Armor](https://docs.cloud.google.com/security-command-center/docs/model-armor-overview) guardrails, the [Skill Registry](#publishing-reusable-skills-to-the-skill-registry), the [Agent Optimizer](optimize/) loss-cluster pass, and an honest map of the [console/policy-only features](#platform-features-you-configure-not-code).

## References

- [Gemini Enterprise Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform)
- [Agent Development Kit (ADK)](https://adk.dev/)
- [Agent Studio](https://docs.cloud.google.com/gemini-enterprise-agent-platform/agent-studio) · [Agent Garden](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/agent-garden) · [Agents CLI](https://google.github.io/agents-cli/guide/getting-started/)
- [ADK A2A: exposing](https://google.github.io/adk-docs/a2a/quickstart-exposing/) & [consuming](https://google.github.io/adk-docs/a2a/quickstart-consuming/) remote agents
- [Agent Runtime overview](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
- [Conversational Analytics API](https://docs.cloud.google.com/gemini/docs/conversational-analytics-api/overview)
- [Knowledge Catalog (Dataplex) — discovery agent](https://docs.cloud.google.com/dataplex/docs/use-discovery-agent)
- [BigQuery `AI.GENERATE` over object tables](https://docs.cloud.google.com/bigquery/docs/analyze-multimodal-data)
- [Claude on Vertex AI](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/partner-models/claude)
- [BigQuery Agent Analytics (observability)](https://adk.dev/integrations/bigquery-agent-analytics/)
- [RAG Engine](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview) · [Example Store](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/example-stores/overview) · [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Skill Registry](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/skill-registry) · [Managed Agents API](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/managed-agents)
- Govern: [Agent Gateway](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview) · [Semantic Governance](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/policies/semantic-governance-overview) · [Agent Identity](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-identity-overview) · [Agent Registry](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-registry)
- Security: [Model Armor](https://docs.cloud.google.com/security-command-center/docs/model-armor-overview) · [Agent Platform Threat Detection](https://docs.cloud.google.com/security-command-center/docs/agent-platform-threat-detection-overview) · [AI Protection](https://docs.cloud.google.com/security-command-center/docs/ai-protection-overview)
