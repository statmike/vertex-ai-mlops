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

- [Agentic Retrieval with BigQuery](./concept-bq/readme.md)
  - Use tools to retrieval contectual data from Google BigQuery
  - This example shows multiple ways of using and creating tools that execute SQL to retrieve data from BigQuery

- [Conversational Analytics API](./conversational-analytics-api/readme.md)
  - An overview of using the Conversational Analytics API to build conversational experiences on top of your data.

- [Travel Planner Agent](./travel-planner/README.md)
  - A multi-agent system that helps users plan their travels, built using the ADK framework.

