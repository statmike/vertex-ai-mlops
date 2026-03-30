# Deploying ADK Agents to Vertex AI Agent Engine — A Hands-On Tutorial

**Build a multi-agent system. Deploy it to production. Query it from anywhere.**

[This tutorial](https://github.com/statmike/vertex-ai-mlops/tree/main/Applied%20ML/AI%20Agents/vertex-agent-engine) walks through deploying [Google ADK](https://google.github.io/adk-docs/) agents to [Vertex AI Agent Engine](https://docs.cloud.google.com/agent-builder/agent-engine/overview) using source-file deployment — no pickle, no GCS staging, no infrastructure to manage.

## What It Covers

The agents are intentionally simple (a router, a greeter, a tools agent with a solar system knowledge base). The focus is on the **deployment patterns** that are hard to find in docs:

- **Project structure** — each agent as its own Python package, shared config from `.env`, thin `AdkApp` entrypoint wrapper that keeps deployment concerns out of your agent code
- **Source-file deployment** — packaging source code, generating `requirements.txt` from `pyproject.toml`, the `class_methods` spec Agent Engine requires
- **Infrastructure location vs. model location** — Agent Engine runs in `us-central1`, but preview models live on `global`. How to separate deployment region from API endpoint so your agents don't 404
- **Two model configs** — a routing model and a tool model, each with its own API location. Tools that call Gemini directly via `google-genai` alongside ADK's agent reasoning
- **Environment variable flow** — from `.env` through the deploy script to Agent Engine, filtering reserved vars, enabling telemetry
- **Full lifecycle CLI** — deploy, update, delete, info, test, local smoke test
- **Interacting with deployed agents** — Python SDK and REST API with sessions and streaming

## Why This Exists

Deploying ADK agents to Agent Engine involves several non-obvious steps — the `AdkApp` wrapper, the class methods spec, the model location override, reserved env vars. This project puts all the pieces together in one runnable example so you can see how they connect, then apply the same patterns to your own agents.

These are the same patterns used in [data-onboarding](https://github.com/statmike/vertex-ai-mlops/tree/main/Applied%20ML/AI%20Agents/data-onboarding), a production multi-agent system with 12 agents that onboards data from URLs into BigQuery and lets you chat with it.

## Dive In

| | |
|---|---|
| [**Project README**](https://github.com/statmike/vertex-ai-mlops/tree/main/Applied%20ML/AI%20Agents/vertex-agent-engine/readme.md) | Key patterns explained with code, setup, run locally, deploy |
| [**Deployment Guide**](https://github.com/statmike/vertex-ai-mlops/tree/main/Applied%20ML/AI%20Agents/vertex-agent-engine/deploy/readme.md) | Deep-dive: source packaging, env var flow, class methods, location handling |
| [**Interaction Tutorial**](https://github.com/statmike/vertex-ai-mlops/tree/main/Applied%20ML/AI%20Agents/vertex-agent-engine/deploy/interact.ipynb) | Query the deployed agent via Python SDK and REST API |
| [**Data Onboarding**](https://github.com/statmike/vertex-ai-mlops/tree/main/Applied%20ML/AI%20Agents/data-onboarding) | Production example using these same patterns at scale |
