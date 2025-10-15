![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Ftravel-planner&file=README.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/travel-planner/README.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/travel-planner/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/travel-planner/README.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/travel-planner/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/travel-planner/README.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# Travel Planner Agent

This repository contains a multi-agent system designed to help users plan their travels. The system is built using the ADK framework and orchestrates several specialized sub-agents to provide a cohesive conversational experience.

***

### Overview

The **Travel Planner Agent** is a steering agent that directs the user to one of its sub-agents based on their needs. The main goal is to assist users in deciding where to travel, planning attractions, and viewing their past travel history.

The system includes the following remote agents:
* **Travel Brainstormer Agent**: Helps users pick a country to visit based on their travel goals, such as adventure, leisure, or learning.
* **Attractions Planner Agent**: Assists in building a list of attractions to visit within a chosen country.
* **Travel History Agent**: Shows the user a list of places they have visited in the past.
* **Places of Interest Agent**: Gathers and stores user-picked attractions and countries in a BigQuery table.

***

### Functionality

The main agent, `steering`, listens to the user's request and delegates to the appropriate sub-agent.

* If the user needs help deciding on a country, they are sent to the `travel_brainstormer_agent`.
* If the user already knows the country, they are sent to the `attractions_planner_agent`.
* If the user wants to see their past travel history, they are sent to the `travel_history_agent`.
* If the user picks an attraction or wants to view their list of picked attractions, they are sent to the `places_of_interest_agent`.

The system uses tools to interact with a BigQuery database to manage travel data.

***

### Agent to Agent (A2A) Protocol and MCP Server

This project uses the **Agent to Agent (A2A) protocol** and a **MCP server** to manage the multi-agent system and its tools.

The core of the multi-agent system is the `steering` agent, which acts as a central orchestrator. This root agent uses the **`RemoteA2aAgent`** class to define its sub-agents, each of which is a separate, remote application. These sub-agents are served as web services on different ports using the **`to_a2a`** function from the ADK framework. This setup allows the agents to communicate with each other, fulfilling the A2A design pattern.

The **MCP server** (**Model Context Protocol**) is a key component for providing tools to the agents. The `pyproject.toml` file lists `mcp` as a dependency. Within each sub-agent's code, a `ToolboxSyncClient` is initialized to connect to the MCP server at `http://localhost:5000`. The agents then load a specific toolset, `my_bq_toolset`, from the server. The `tools.yaml` file defines the tools provided by the MCP server, such as `search-places` and `execute_sql_tool`, and specifies their connection to a BigQuery source.

***

### Tools

The agents use a toolbox to perform specific actions. These tools are defined in `tools.yaml` and interact with a BigQuery source named `my-bq-source`.

* **`search-places`**: A BigQuery SQL tool that lists places previously visited by the user.
* **`execute_sql_tool`**: A BigQuery tool that executes SQL statements. This is used by the `places_of_interest_agent` to store new attractions.
* **`bigquery_get_table_info`**: A tool to get metadata about a BigQuery table. The `places_of_interest_agent` uses this to get the schema for the `attractions` table before writing a query.
* **`save_attractions_to_state`**: A local tool used by the `attractions_planner` agent to save a list of attractions to the session state.

***

### Setup and Running

#### BigQuery Setup

This project requires a BigQuery dataset and table to store and retrieve travel data. The `tools.yaml` file specifies the project, dataset, and table to be used.

* **Project ID**: `vertexai-demo-ltfpzhaw`
* **Dataset ID**: `bq_adk_ds`
* **Table**: `attractions` and `travel_history`

The `search_places` tool queries the `travel_history` table. The table schema is inferred to have `country` column, as shown in the SQL statement in `tools.yaml` file. 
The `execute_sql_tool` tool questions the `attractions` table using the sql that's dynamically generated based on the user's request.
You will need to create this dataset and tables in your BigQuery project with the appropriate schema before running the application.

SQL for creating the dataset bq_adk_ds:

```sql
CREATE SCHEMA IF NOT EXISTS `vertexai-demo-ltfpzhaw`.`bq_adk_ds`;
```

SQL for attractions Table: 

```sql
CREATE TABLE
  `vertexai-demo-ltfpzhaw`.`bq_adk_ds`.`attractions`( attraction_name STRING,
    country STRING);
```

SQL for travel_history Table:

```sql
CREATE TABLE 
`vertexai-demo-ltfpzhaw`.`bq_adk_ds`.`travel_history`( country STRING);
```
Insert following sample countries into travel_history table:

```sql
INSERT INTO
  `vertexai-demo-ltfpzhaw`.`bq_adk_ds`.`travel_history` (country)
VALUES
  ('Germany'),
  ('Japan'),
  ('France');
```

#### Prerequisites

The following dependencies are required to run the project. They are listed in the `pyproject.toml` file.

* `a2a-sdk`
* `google-genai`
* `google-cloud-aiplatform`
* `dotenv`
* `uvicorn`
* `mcp`
* `google-adk`
* `toolbox-core`

Download the [MCP Toolbox for Databases](https://github.com/googleapis/genai-toolbox) by following the instruction in the link.

If you are using VS Code as IDE, following the steps in the link to configure the [MCP Server](https://code.visualstudio.com/docs/copilot/chat/mcp-servers#_add-an-mcp-server)

#### Setup with `uv`

This project uses `uv` for dependency management. You can use the `pyproject.toml` file to install all the necessary packages in a new virtual environment.

1.  Create and activate a new virtual environment: `uv venv` and then `source .venv/bin/activate`.
2.  Install the dependencies listed in `pyproject.toml`: `uv sync`
3.  To create a `requirements.txt` file from the `pyproject.toml`, run the following command: `uv pip compile --output-file requirements.txt pyproject.toml`

#### Environment Configuration

The project uses environment variables defined in the `.env` file.

* `GOOGLE_GENAI_USE_VERTEXAI=TRUE`
* `GOOGLE_CLOUD_PROJECT=<your-google-cloud-project>`
* `GOOGLE_CLOUD_LOCATION=us-central1`
* `MODEL=gemini-2.5-flash`

#### Note: 
- Update `<your-gcp-project>` in `prompts.py` and `tools.yaml` file with your project id.
- Rename the `example.tools.yaml` to `tools.yaml`.

#### How to Run

1.  Make sure you have the required dependencies installed from `pyproject.toml` and at `travel_planner_a2a_mcp_demo` folder level.
2.  Set up the environment variables in a `.env` file.
3.  Run MCP Toolbox using the following:

    `./toolbox --tools-file="tools.yaml"`

4.  Launch the remote agents from their respective directories. Each agent is configured to run on a different port (8001, 8002, 8003, 8004).

    `uvicorn a2a_root_agent.remote_a2a.travel_brainstormer_agent.agent:a2a_app1 --host localhost --port 8001`

    `uvicorn a2a_root_agent.remote_a2a.attractions_planner_agent.agent:a2a_app2 --host localhost --port 8002`

    `uvicorn a2a_root_agent.remote_a2a.travel_history_agent.agent:a2a_app3 --host localhost --port 8003`
    
    `uvicorn a2a_root_agent.remote_a2a.places_of_interest_agent.agent:a2a_app4 --host localhost --port 8004`

    
5.  Launch the main `a2a_root_agent` to start the application using `adk web`.

#### How to invoke remote agents via JSON RPC

1. Launch the remote agents from their respective directories. I am using travel_brainstormer_agent as an example here:

 `uvicorn a2a_root_agent.remote_a2a.travel_brainstormer_agent.agent:a2a_app1 --host localhost --port 8001`

2. Open a new terminal window and run the following curl command which uses JSON RPC:

```curl --request POST --url http://localhost:8001 --header 'content-type: application/json' --data '{"jsonrpc": "2.0","id": 33,"method": "message/send","params": {"message": {"role": "user","parts": [{ "type": "text", "text": "I need help deciding where to travel." }],"messageId":"foo4","kind": "message"}}}'```

3. Here is the sample response:

```{"id":33,"jsonrpc":"2.0","result":{"artifacts":[{"artifactId":"d2ddbe71-336c-46da-9555-8a0ada99639c","parts":[{"kind":"text","text":"I can help with that! To narrow down the options, what are your primary goals for this trip? Are you looking for adventure, relaxation, learning, shopping, or experiencing art and culture?"}]}],"contextId":"39ca1a61-2521-4a9c-bcf0-0e3e42a4cfd0","history":[{"contextId":"39ca1a61-2521-4a9c-bcf0-0e3e42a4cfd0","kind":"message","messageId":"foo4","parts":[{"kind":"text","text":"I need help deciding where to travel."}],"role":"user","taskId":"2a1d5699-8e7c-4efa-8af0-ea8a6e340705"},{"contextId":"39ca1a61-2521-4a9c-bcf0-0e3e42a4cfd0","kind":"message","messageId":"foo4","parts":[{"kind":"text","text":"I need help deciding where to travel."}],"role":"user","taskId":"2a1d5699-8e7c-4efa-8af0-ea8a6e340705"},{"kind":"message","messageId":"2d304b6a-8407-4ecb-bd56-9855e9c7650e","parts":[{"kind":"text","text":"I can help with that! To narrow down the options, what are your primary goals for this trip? Are you looking for adventure, relaxation, learning, shopping, or experiencing art and culture?"}],"role":"agent"}],"id":"2a1d5699-8e7c-4efa-8af0-ea8a6e340705","kind":"task","metadata":{"adk_app_name":"travel_brainstormer","adk_user_id":"A2A_USER_39ca1a61-2521-4a9c-bcf0-0e3e42a4cfd0","adk_session_id":"39ca1a61-2521-4a9c-bcf0-0e3e42a4cfd0","adk_invocation_id":"e-7c7bfa15-9413-489b-8411-9400a9c81483","adk_author":"travel_brainstormer","adk_usage_metadata":{"candidatesTokenCount":39,"candidatesTokensDetails":[{"modality":"TEXT","tokenCount":39}],"promptTokenCount":324,"promptTokensDetails":[{"modality":"TEXT","tokenCount":324}],"thoughtsTokenCount":78,"totalTokenCount":441,"trafficType":"ON_DEMAND"}},"status":{"state":"completed","timestamp":"2025-08-28T14:21:50.289022+00:00"}}} ```
