![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/readme.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/Applied%20ML/AI%20Agents/readme.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Applied AI Agents
> You are here: `vertex-ai-mlops/Applied ML/AI Agents/readme.md`

Putting ML and Generative AI to work with Agents.

**Agents**

An **AI Agent** uses models (like LLMs) to understand goals, make decisions, and take actions to get things done.

Agent purposes often fit into these categories:

* **LLM-based Agents:** Interpret input to generate outputs that create action.
* **Workflow Agents:** Control execution: sequential steps, parallel actions, or loops.
* **Custom Agents:** Allow implementing custom code, even for non-LLM or model-based tasks.

Agents need:

* **Tools:** To interact with outside services, APIs, or execute code.
* **Callbacks:** Hooks for checks, logging, and redirection during execution.
* **Session Management:** For handling session history, state, and memory (including save/load of files).
* **Planning:** Breaking down inputs into steps and planning the execution order.
* **Model Access:** Connection to the underlying AI models.
* **Runtime:** To manage agent execution and coordinate with services.
* **Deployment:** An environment to run and scale agent invocations.
* **Evaluation:** Logic to compare expected results to actual results for testing.

This is made easier by the Google [Agent Development Kit (ADK)](https://google.github.io/adk-docs/). Check out the sample applications in [adk-samples](https://github.com/google/adk-samples). It enables flexible agent creation and addresses advanced needs like:
* **[Deploying agents](https://google.github.io/adk-docs/deploy/)** to execution environments
    * Directly to [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview) for fully managed scaling. Vertex AI Agent Engine also supports deploying agents built with other frameworks (like LangChain, LangGraph, AG2 (AutoGen), and LlamaIndex).
* **Connecting agents to services via Model Context Protocol (MCP)**
    * Use existing MCP servers with ADK ([ADK as an MCP Client](https://google.github.io/adk-docs/tools/mcp-tools/#1-using-mcp-servers-with-adk-agents-adk-as-an-mcp-client)).
    * Build an [MCP server exposing ADK Tools](https://google.github.io/adk-docs/tools/mcp-tools/).
    * Use Google Cloud Databases with [MCP Toolbox for Databases](https://googleapis.github.io/genai-toolbox/getting-started/introduction/)

Learn More about ADK:
- [Agent Developement Kit](https://google.github.io/adk-docs/) has excellent documentation
- [Bo Yang (Author and Tech Lead) on Medium](https://medium.com/me/following-feed/writers/5e6030bc9788) has excellent short blogs on key functionality of ADK

Sometimes agents need to interact across boundaries (departments, companies, networks). The need for a standard protocol for agent-to-agent communication is met by the [A2A protocol](https://google.github.io/A2A/#/?id=unlock-collaborative-agent-to-agent-scenarios-with-a-new-open-protocol).

## Solution Based Workflows In This Repository

The [Solution Prototypes](../Solution%20Prototypes/readme.md) folder has examples that cover full user workflows that incorporate multiple GCP services. Here are some example that can be found over there: 

[Document Processing Agent](../Solution%20Prototypes/document-processing/7-agents/readme.md)
- Upload files or provide GCS URI to load documents (PNG or PDF)
- Agent can:
  - Redact Content
  - Extract Content
  - Classify the document based on warehouse of known vendors
    - First based on document similarity to known vendors document
    - Then, if needed, with a predictive classification model training on known good documents
  - Compare a document to the classified vendor or any other vendors template
    - Get a side-by-side view along with list of different detected by a model

[Time Series Forecasting Agent](../Solution%20Prototypes/time-series/readme.md)
- An agent that uses MCP Toolbox for databases to retrieve data, context, from BigQuery
  - Multiple tools that retrieve history of daily demand and can also use `AI.FORECAST` to create on-demand forecast for daily demand going forward
  - The agent also has tools the prepare the data in interactive visuals

## Example Concepts In This Folder

This folder has examples based on core functionality of agents interacting with GCP services.  These are meant to help learn and explore core concepts.

- **[BigQuery Context Discovery](./bigquery-context/readme.md)**
  - Multi-agent system comparing five parallel approaches to discovering the best BigQuery tables for answering user questions
  - **BQ Metadata Tools**: LLM-driven tool calls using ADK BigQueryToolset
  - **Dataplex Search**: Semantic search with Dataplex SDK
  - **Dataplex Context**: Zero per-query API calls using cached metadata from Dataplex `lookupContext`
  - **Context Pre-Filter**: LLM reviews briefs, reranker evaluates with full metadata
  - **Semantic Context**: Dataplex search combined with cached context
  - Shared Gemini-based reranker produces structured output with confidence scores, key columns, SQL hints, and join suggestions
  - Automated benchmark with recall/precision scoring across test questions

- **[Agentic Retrieval with BigQuery](./concept-bq/readme.md)**
  - Demonstrates multiple methods for agents to interact with BigQuery data
  - **Python Function Tools**: Custom functions using BigQuery client library for pre-defined and parameterized SQL queries
  - **MCP Toolbox for Databases**: Pre-defined SQL execution and dynamic SQL generation using table metadata
  - **ADK Built-in Tools**: General-purpose BigQuery tools for step-by-step metadata and query execution
  - **Conversational Analytics API**: Stateful conversations with automatic chart and summary generation
  - **BigQuery Forecasting**: Time series forecasting with interactive visualizations using AI.FORECAST
  - Router agent pattern delegating to specialized sub-agents based on question type
  - BigQuery Agent Analytics Plugin for logging all events to BigQuery
  - Complete deployment workflows to Vertex AI Agent Engine with templated notebooks

- **[Conversational Analytics API](./conversational-analytics-api/readme.md)**
  - Overview and walkthrough of Google's Conversational Analytics API for building conversational experiences on top of data
  - Clear hierarchy: Data Source → Context → Agent → Conversation → Chat
  - Support for BigQuery tables, Looker, and Looker Studio reports
  - Three usage modes: stateful sessions, stateless with agent, and inline on-demand queries
  - Comprehensive Jupyter notebook walkthrough covering all usage modes

- **[Data Onboarding](./data-onboarding/readme.md)**
  - Two multi-agent systems that automate the full data lifecycle: **onboard** data from URLs into BigQuery, then **chat** with it using natural language
  - **Onboarding pipeline** with sub-agents for acquire → discover → understand → design → implement → validate
    - Supports CSV, TSV, JSON, Excel, Parquet, Avro, ORC, XML, and ZIP archives
    - Cross-references data with context documents (PDFs, READMEs, data dictionaries)
    - Auto-generates meaningful column names, types, and descriptions
    - Publishes end-to-end lineage to Dataplex and triggers data profile scans
  - **Chat agent** with three personas for querying onboarded data:
    - Data Analyst queries actual data via Conversational Analytics API
    - Data Engineer explores processing logs and lineage
    - Catalog Explorer performs semantic search over documentation with AI.SEARCH
  - Deployable to Vertex AI Agent Engine

- **[Image to Graph](./image-to-graph/readme.md)**
  - Converts complex diagram images (flowcharts, electrical schematics, network diagrams, UML) into structured graph representations
  - Iterative visual thinking: full-image scan, region identification with bounding boxes, crop and re-examine at detail
  - Supports local files, HTTPS URLs, GCS paths, and PDF files as input
  - Optional OpenCV-based preprocessing for structured diagrams (shape detection, contour analysis)
  - Schema support: auto-generate JSON Schema or provide a custom Pydantic schema
  - Interactive HTML visualization with linked highlighting, flow subgraphs, and Mermaid diagrams
  - Q&A sub-agent for answering questions about the extracted graph

- **[Travel Planner Agent](./travel-planner/README.md)**
  - Multi-agent travel planning system using Agent-to-Agent (A2A) protocol for cross-agent communication
  - Four specialized remote agents: Travel Brainstormer, Attractions Planner, Travel History, Places of Interest
  - Steering agent pattern for intelligent request delegation
  - MCP server integration with custom BigQuery tools for travel data management
  - Remote agents served as web services communicating via A2A protocol
  - Session state management for tracking user-selected attractions

- **[Vertex AI Agent Engine Deployment](./vertex-agent-engine/readme.md)**
  - Minimal multi-agent deployment tutorial demonstrating how to deploy ADK agents to Vertex AI Agent Engine
  - Source-file deployment pattern (under 8 MB limit) with each agent as its own package
  - AdkApp entrypoint wrapper for Agent Engine with environment variable passthrough
  - Infrastructure vs. model location separation (`GOOGLE_CLOUD_LOCATION` vs `AGENT_MODEL_LOCATION`)
  - Complete deployment lifecycle management: create, update, delete, and test
  - Example agents: router, greeter, and tools agent with math, lookup, and direct Gemini calls

