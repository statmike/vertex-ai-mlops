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
* **Table**: `attractions_list`

The `search-places` tool queries the `attractions_list` table. The table schema is inferred to have at least a `place` column, as shown in the SQL statement `SELECT place FROM...`. You will need to create this dataset and table in your BigQuery project with the appropriate schema before running the application.

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

1.  Make sure you have the required dependencies installed from `pyproject.toml`.
2.  Set up the environment variables in a `.env` file.
3.  Launch the remote agents from their respective directories. Each agent is configured to run on a different port (8001, 8002, 8003, 8004).

    `uvicorn a2a_root_agent.remote_a2a.travel_brainstormer_agent.agent:a2a_app1 --host localhost --port 8001`

    `uvicorn a2a_root_agent.remote_a2a.attractions_planner_agent.agent:a2a_app2 --host localhost --port 8002`

    `uvicorn a2a_root_agent.remote_a2a.travel_history_agent.agent:a2a_app3 --host localhost --port 8003`
    
    `uvicorn a2a_root_agent.remote_a2a.places_of_interest_agent.agent:a2a_app4 --host localhost --port 8004`
    
4.  Launch the main `a2a_root_agent` to start the application using `adk web`.