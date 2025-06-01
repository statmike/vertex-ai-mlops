![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

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



