# Data Onboarding: From URL to Conversational Analytics with AI Agents

**Give it a URL. Get queryable BigQuery tables. Then chat with your data.**

[Data Onboarding](https://github.com/statmike/vertex-ai-mlops/tree/main/Applied%20ML/AI%20Agents/data-onboarding) is a multi-agent system built with [Google ADK](https://google.github.io/adk-docs/) and [Gemini](https://cloud.google.com/vertex-ai/generative-ai/docs/gemini-overview) that automates the full lifecycle of data — from raw files on the web to production BigQuery tables you can query in plain English.

## The Problem

Getting external data into BigQuery means downloading files, figuring out schemas, writing DDL, casting types, documenting columns. Then when someone asks "what does this column mean?" you're digging through source docs, and "compare volumes across exchanges" means writing SQL by hand. This project replaces that entire workflow with two AI agents.

## Two Agents

**Onboarding** — Point the orchestrator at a URL and it crawls the site, downloads every data file it finds (CSV, Excel, Parquet, JSON, XML, and more), reads the documentation alongside them (PDFs, READMEs, data dictionaries), uses that context to design BigQuery tables with meaningful names and descriptions, creates them, publishes end-to-end lineage to Dataplex, and validates — all autonomously through a pipeline of seven coordinating sub-agents.

**Chat** — Ask questions about the onboarded data in plain English. A three-persona router classifies each question and delegates to the right specialist:

- *"Compare the total short sale volume across the four Cboe equity exchanges"* → **Data Analyst** — generates SQL, runs queries, returns tables and charts via the [Conversational Analytics API](https://cloud.google.com/gemini/docs/conversational-analytics-api/overview)
- *"Show me the processing log for this source"* → **Data Engineer** — queries pipeline metadata, lineage, and schema decisions
- *"What does PRVDR_NUM mean?"* → **Catalog Explorer** — semantic search over auto-generated documentation using BigQuery `AI.SEARCH`

## What Gets Created

The onboarding agent doesn't just dump data into a single dataset — it builds a structured BigQuery layer architecture:

| Dataset | Purpose |
|---------|---------|
| **Staging** (`*_staging`) | External tables pointing at raw files in GCS |
| **Bronze** (`*_bronze`) | Materialized tables with enriched column names, types, descriptions, partitioning, and auto-generated documentation |
| **Meta** (`*_meta`) | Pipeline metadata — source manifest, processing log, lineage, schema decisions, web provenance, data catalog |
| **Context** (`*_context`) | Semantic search index with vector embeddings for the Catalog Explorer agent |
| **ADK** (`*_adk`) | Agent event log — every LLM call, tool invocation, and agent transfer for debugging and analysis |

The bronze layer's `table_documentation` is what connects the two agents: the onboarding agent writes it, and the chat agent reads it to find the right tables for each question. Onboard once, chat immediately.

The chat agent deploys to [Vertex AI Agent Engine](https://docs.cloud.google.com/agent-builder/agent-engine/overview) as a managed service with persistent sessions, distributed tracing, and auto-scaling. The orchestrator runs locally as a batch pipeline — onboard once, then query the data through the deployed chat agent. When multiple sources are onboarded, set `CHAT_SCOPE` to the dataset you want to query and update the deployment — this keeps the agent focused on the right tables.

## Dive In

| | |
|---|---|
| [**Project README**](https://github.com/statmike/vertex-ai-mlops/tree/main/Applied%20ML/AI%20Agents/data-onboarding/readme.md) | Full architecture, all 12 agents, configuration, what gets created in BigQuery |
| [**Deployment Guide**](https://github.com/statmike/vertex-ai-mlops/tree/main/Applied%20ML/AI%20Agents/data-onboarding/deploy/readme.md) | Deploy to Agent Engine — packaging, entrypoints, IAM, querying deployed agents |
| [**Interaction Tutorial**](https://github.com/statmike/vertex-ai-mlops/tree/main/Applied%20ML/AI%20Agents/data-onboarding/deploy/interact.ipynb) | Query deployed agents via Python SDK and REST API |
| [**Cboe Example**](https://github.com/statmike/vertex-ai-mlops/tree/main/Applied%20ML/AI%20Agents/data-onboarding/examples/cboe/cboe.md) | End-to-end walkthrough with financial data, questions run locally |
| [**Medicare Example**](https://github.com/statmike/vertex-ai-mlops/tree/main/Applied%20ML/AI%20Agents/data-onboarding/examples/medicare-provider/readme.md) | Full cycle with CMS healthcare data, questions run against deployed Agent Engine |
