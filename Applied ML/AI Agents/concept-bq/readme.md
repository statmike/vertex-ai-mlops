![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fconcept-bq&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/concept-bq/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/concept-bq/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/concept-bq/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/concept-bq/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/concept-bq/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# Concept: Agentic Retrieval With BigQuery

This project demonstrates how an [ADK](https://google.github.io/adk-docs/) agent can interact with Google BigQuery using three distinct methods: executing pre-defined SQL, using parameterized SQL queries, and leveraging an LLM to dynamically generate SQL based on table metadata.

> **Why do this?** Retrieving context for an LLM goes beyond standard retrieval-augmented generation (RAG) and semantic search. With **agentic retrieval**, the LLM gets access to tools (via function calling) that allow it to translate a user's request directly into a structured query. This enables the agent to filter, aggregate, and transform data during retrieval and unlocks real-time access to operational databases that are constantly changing.

The agent uses a combination of [function tools](https://google.github.io/adk-docs/tools/function-tools/) (custom Python tools), the [built-in tools for BigQuery](https://google.github.io/adk-docs/tools/built-in-tools/#bigquery), and the [MCP Toolbox for Databases](https://googleapis.github.io/genai-toolbox/getting-started/introduction/):

- **Python Function Tools:**
  - Custom Python functions that use the BigQuery client library to execute pre-defined, non-parameterized or parameterized SQL queries.
- **Conversational Analytics API via Python Function Tool:**
  - A custom Python function that calls the powerful Conversational Analytics API, enabling rich, stateful conversations about data, including the generation of summaries and charts.
    - Check out the stand-alone deep dive into this offering in [Conversational Analytics API](../conversational-analytics-api/readme.md) which offers a notebook overview of all three usage modes of the API along with all the steps to setup and connect to it.
- **MCP Toolbox for Databases (Pre-defined SQL):**
  - [kind: bigquery-sql](https://googleapis.github.io/genai-toolbox/resources/tools/bigquery-sql/): Executes pre-defined SQL statements from the `tools.yaml` file, which can include parameters for dynamic filtering.
- **MCP Toolbox for Databases (Dynamic SQL Generation):**
  - [kind: bigquery-get-table-info](https://googleapis.github.io/genai-toolbox/resources/tools/bigquery-get-table-info/): Retrieves table metadata, which is provided to the LLM as context to help it write accurate SQL queries.
  - [kind: bigquery-execute-sql](https://googleapis.github.io/genai-toolbox/resources/tools/bigquery-execute-sql/): Executes an LLM-generated SQL query.
- **ADK Built-in Tools for BigQuery:**
  - General-purpose tools that are part of the ADK for interacting with BigQuery, capable of fetching metadata and executing SQL queries.
- **BigQuery Forecasting with Python Function Tool:**
  - A custom Python function that creates visualizations of BigQuery forecast results, combining the built-in ADK forecast tool with custom plotting capabilities for time series analysis.

**More Resources:**
- Excellent blog: [BigQuery meets ADK: 10 tips to safeguard your data (and wallet) from agents](https://medium.com/google-cloud/bigquery-meets-adk-10-tips-to-safeguard-your-data-and-wallet-from-agents-8c8ea72a9d4e)
- DevRel Blog Series on ADK Agents for BigQuery:
  - [Part 1: Build a baseline agent for BigQuery with ADK](https://medium.com/google-cloud/adk-agents-for-bigquery-series-40de8cf4e3ca)
  - [Part 2: Evaluate your agent](https://medium.com/google-cloud/adk-agents-for-bigquery-series-fcd237452898)
  - [Part 3: Optimize the agent’s environment and model](https://medium.com/google-cloud/adk-agents-for-bigquery-series-part-3-optimize-the-agents-environment-and-model-552cad1d53a3)
  - [Part 4: System Instructions and beyond](https://medium.com/google-cloud/adk-agents-for-bigquery-series-part-4-system-instructions-and-beyond-934aa769db4a)

---
## Environment Setup

Install the prerequisite tools and setup the Python environment.

### 🧰 MCP Toolbox For Databases

This is a solution that makes connecting to, authorizing to, and querying data simple!

Install [MCP Toolbox for Databases](https://googleapis.github.io/genai-toolbox/getting-started/introduction/).  I prefer to do this once in the home folder and reuse the toolbox for all projects during development.

```bash
# detect the environment OS and Architecture:
uname -s -m

# install in home folder
cd ~
export OS="linux/amd64" # one of linux/amd64, darwin/arm64, darwin/amd64, or windows/amd64
curl -O https://storage.googleapis.com/genai-toolbox/v0.17.0/$OS/toolbox

# make toolbox executable
chmod +x toolbox
./toolbox --version
```

### ⚙️ Python Environment Setup

This guide provides two methods for setting up the Python environment. Follow the "Initial Steps" first, then choose **one** of the two options to install the dependencies.

> **Note:** This project requires [Git](https://github.com/git-guides/install-git), the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) (initialized via `gcloud init`), and [pyenv](https://github.com/pyenv/pyenv) for managing Python versions.

---
### Initial Steps (Required for both methods)

#### 1. Clone the Repository
Open your terminal and run the following commands to clone the repository and navigate into the project directory.
```bash
# Navigate to the directory where you store your projects
cd ~/repos # Or your preferred location

# Clone the repository from GitHub
git clone https://github.com/statmike/vertex-ai-mlops.git

# Change into the correct project sub-directory
cd 'vertex-ai-mlops/Applied ML/AI Agents/concept-bq'
```

#### 2. Set the Python Version
This project is standardized on Python 3.13.3. Use pyenv to install and activate this version for the project.

```bash
# Install Python 3.13.3 if it's not already installed
pyenv install --skip-existing 3.13.3

# Set the local Python version for this directory
pyenv local 3.13.3
```

#### Install Dependencies (Choose One Option)
Now, choose your preferred method to install the Python packages.

<details>
<summary>✅ Option 1: Using Poetry (Recommended)</summary>

This is the simplest method if you have Poetry installed. It uses the poetry.lock file to perfectly replicate the development environment.

```bash
# Install all project dependencies
poetry install
```

</details>
<details>
<summary>🐍 Option 2: Using `venv` and `pip`</summary>

If you prefer to use Python's built-in tools, you can use `venv` and `pip` with the `requirements.txt` file.
> **Note:** In an ephemeral environment, you might choose to bypass `venv` and install packages directly with `pip`.

```bash
# 1. Create a virtual environment folder named .venv
python -m venv .venv

# 2. Activate the virtual environment
# On macOS and Linux:
source .venv/bin/activate

# On Windows (Command Prompt):
# .venv\Scripts\activate

# 3. Install the required packages from requirements.txt
pip install -r requirements.txt
```
</details>

---
## Running The Agent

Running the agent requires first running the MCP Toolbox Server, locally in this case, and then starting the ADK test UI, also locally.

### 1 - Start The MCP Toolbox Server

Use a new terminal window to start the MCP server locally on port 7000.

> **Note:** The Python `venv` is not needed for toolbox to run.

```bash
# from inside the project folder:
TOOL_FILES=$(echo ./agent_*/toolbox_tools.yaml | tr ' ' ',')
  ~/toolbox --port 7000 --tools-files="$TOOL_FILES"
```

Check the server by using a browser and going to `http://localhost:7000/`.  You should see 'Hello, World!'.

A futher check is reviewing the hosted toolsets on the server that were loaded form this project by going to `http://localhost:7000/api/toolset`.  You should see JSON formatted specs for the tools defined in the `tools.yaml` file.

When done, **but not yet**, you can stop the local server with `ctrl+c`.

### 2 - Run The Agents Locally With A Test UI

Edit the `.env` file to include the name of your GCP project.

To test this agent you can use the `adk web` command from inside the `concept-bq` folder.

```bash
# adk web options include:
#   --reload
#   --port 8000 # the default port

# Run the ADK web interface with one of:

# venv:
adk web --reload

# poetry:
poetry run adk web --reload
```

This will start the test user interface and you can `ctrl+click` on the `http://localhost:8000` address.

When finished, stop the service with `ctrl+c` in the terminal.

### 3 - Test Deployed Agents Locally (Optional)

If you have deployed an agent to Vertex AI Agent Engine, you can test it locally using the same ADK web interface with sessions managed by the deployed instance:

```bash
# Get the agent_engine_id from the deployment.json file:
# agent_convo_api: cat agent_convo_api/deploy/deployment.json
# agent_bq_forecast: cat agent_bq_forecast/deploy/deployment.json

# Run with deployed session service:
poetry run adk web --session_service_uri=agentengine://${agent_engine_id}

# Example for agent_convo_api:
poetry run adk web --session_service_uri=agentengine://projects/1026793852137/locations/us-central1/reasoningEngines/YOUR_ENGINE_ID
```

This allows you to:
- Test the deployed agent without redeploying
- Use production session management locally
- Debug deployed agent behavior
- Verify deployed agent permissions and tool access

---
### Example Questions

When you run the ADK web interface, you can interact with the agents. In the top-left corner of the window, there is a dropdown menu to select the agent you want to interact with.

#### Router Agent: `agent_concept_bq`

If you select the `agent_concept_bq`, you can ask any of the questions below and observe how it delegates the task to the appropriate sub-agent. This is a great way to see the routing logic in action.  Do this and ask the questions in the order they are presented below to see the routing as well as the memory between questions within the agents.

**Notes On Behavior of Sub-Agents**
- The first question for a new topic will trigger a handoff to the appropriate sub-agent. That sub-agent will then remain engaged to handle follow-up questions on the same topic.
- If a sub-agent cannot answer a question, it will pass the task back to the parent router agent. This behavior is controlled by the `disallow_transfer_to_parent=False` and `disallow_transfer_to_peers=True` parameters in the agent's configuration.
- To switch topics and trigger a different sub-agent during the demo, you can explicitly ask the current agent to "pass the task back to the parent."
- > **Remember**: This project is a demonstration of various data interaction methods. In a real-world application, you would likely choose the single best method for your use case rather than combining all of them.

#### Sub-Agent: `agent_bq_python_tools` (Python Function Tools)

This agent uses custom Python functions to query BigQuery. It is specialized for questions about the number of hurricanes.

- What years had the most hurricanes?
- How many hurricanes were in 2015?

#### Sub-Agent: `agent_mcp_toolbox_prewritten` (MCP Toolbox - Pre-written SQL)

This agent uses pre-defined SQL queries from the `tools.yaml` file. It is specialized for questions about hurricane wind speeds.

- What were the biggest hurricanes by wind speed?
- What was the biggest hurricane by wind speed in 2015?

#### Sub-Agent: `agent_mcp_toolbox_dynamic` (MCP Toolbox - Dynamic SQL)

This agent can dynamically generate SQL queries based on the table metadata. It is designed to handle more complex or custom questions about hurricanes.

- What was the last hurricane of 2008?
- What was the first hurricane of the 2009 year in the North Atlantic Basin?
- What was the last hurricane of 2008 in the North Atlantic Basin?

#### Sub-Agent: `agent_bq_builtin` (ADK Built-in Tools)

This agent is best for showing the step-by-step process of building and executing a SQL query. It is triggered when a question for a non-hurricane topic explicitly mentions `SQL` or `query`.

- I want to use SQL to query but first, are there any weather datasets other than hurricanes?
- Are there any datasets or tables about tsunamis?
- What does the tsunami dataset have?
- Do Tsunami's have names and seasons/years?
- How many tsunamis across what date range is information available for?
- How many records are from BC years?
- Describe one of these based on available data.

#### Sub-Agent: `agent_bq_forecast` (BigQuery Forecasting)

This agent specializes in time series forecasting using BigQuery's built-in forecast capabilities. It works with the NYC Citibike trips dataset and can generate forecasts with visualizations. Use this agent for questions about predicting future trends or patterns.

**Deployment:** This agent has been prepared for production deployment. See the [Deployment Guide](#deployment) below and [agent_bq_forecast/deploy/readme.md](./agent_bq_forecast/deploy/readme.md) for full deployment instructions.

- What is the 30 day forecast for trip volume overall?
- How about for just the stations with names incluing 72 st?
- And now for each of these stations.

#### Sub-Agent: `agent_convo_api` (Conversational Analytics API)

For any other general or conversational question **not about hurricanes**, this agent will be used. It is best for answering questions conversationally and can create tables and charts as well.

**Deployment:** This agent has been prepared for production deployment. See the [Deployment Guide](#deployment) below and [agent_convo_api/deploy/readme.md](./agent_convo_api/deploy/readme.md) for full deployment instructions.

- Pass back to the parent agent
- What is the average number of earthquakes that occur each year?
- Over what range of years did these occur?
- Make a table of the top 10 years with most earthquakes.
- What is the average number of earthquakes for the years 1900 through most recent dates?
- Make a time series chart of the count of earthquakes by year.
- Make an updated chart for only the year 1940 through most recent dates.

---
## Deployment

After developing and testing agents locally, the next step is deploying them to production environments. This project includes a complete deployment workflow for deploying ADK agents to **Vertex AI Agent Engine** and optionally registering them with **Gemini Enterprise**.

### Deployment Architecture

Agents are deployed to [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview), which provides:
- **Managed Infrastructure** - Serverless deployment with automatic scaling
- **Session Management** - Built-in user session tracking and state management
- **Integration** - Direct SDK and REST API access
- **Observability** - Integrated logging, tracing, and monitoring
- **Gemini Enterprise** - Optional registration for access through Gemini interface

### Deployment Structure

Each agent that is prepared for deployment has a dedicated `deploy/` folder with everything needed:

```
agent_name/
├── agent.py              # Agent implementation
├── tools/                # Agent-specific tools
└── deploy/               # Deployment resources
    ├── deployment.json   # Deployment metadata (auto-managed)
    ├── deploy-vertex-ai-agent-engine.ipynb
    ├── use-vertex-ai-agent-engine.ipynb
    ├── register-adk-on-agent-engine-with-gemini-enterprise.ipynb
    └── readme.md         # Agent-specific deployment guide
```

### Deployment Workflow

The deployment process consists of three notebooks that should be run in order:

1. **Deploy to Vertex AI Agent Engine**
   - Local testing before deployment
   - Creates/updates deployment on Vertex AI
   - Configures IAM permissions
   - Stores deployment metadata

2. **Use the Deployed Agent**
   - Test via Python SDK
   - Test via REST API
   - Manage sessions
   - View conversation history

3. **Register with Gemini Enterprise** (Optional)
   - Makes agent available in Gemini interface
   - Enables user access through Gemini Enterprise

### Currently Deployed Agents

| Agent | Status | Deployment Guide |
|-------|--------|-----------------|
| `agent_convo_api` | ✅ Ready | [Deploy Guide](./agent_convo_api/deploy/readme.md) |
| `agent_bq_forecast` | ✅ Ready | [Deploy Guide](./agent_bq_forecast/deploy/readme.md) |

### Quick Start: Deploy an Agent

To deploy the `agent_convo_api` (or any prepared agent):

```bash
# 1. Navigate to the agent's deployment folder
cd agent_convo_api/deploy

# 2. Open the deployment notebook in Jupyter or your IDE
# 3. Run: deploy-vertex-ai-agent-engine.ipynb
# 4. Run: use-vertex-ai-agent-engine.ipynb
# 5. (Optional) Run: register-adk-on-agent-engine-with-gemini-enterprise.ipynb
```

**The notebooks are fully templated and auto-configure based on their location** - no code changes required!

### Prerequisites for Deployment

Before deploying any agent, ensure you have:

1. **Google Cloud Project Setup**
   - Active GCP project with billing enabled
   - Vertex AI API enabled
   - Agent Engine API enabled

2. **Configuration**
   - Main `.env` file configured with:
     - `GOOGLE_CLOUD_PROJECT`
     - `GOOGLE_CLOUD_LOCATION`
     - `GOOGLE_CLOUD_STORAGE_BUCKET`

3. **Authentication**
   - Authenticated via `gcloud auth login`
   - Application default credentials configured

4. **Required Permissions**
   - `roles/aiplatform.user` or `roles/aiplatform.admin`
   - `roles/storage.objectAdmin` (for GCS staging)
   - Additional permissions based on agent tools

### Deployment Configuration

The deployment notebooks automatically:
- **Detect the agent** by importing from `../agent.py`
- **Load project config** from `../../.env`
- **Use shared dependencies** from `../../requirements.txt`
- **Store deployment state** in `./deployment.json`

No manual path configuration needed!

### Deploying Additional Agents

To prepare a new agent for deployment:

```bash
# 1. Create the deploy folder
mkdir -p path/to/new_agent/deploy

# 2. Copy the deployment templates
cp agent_convo_api/deploy/*.ipynb path/to/new_agent/deploy/
cp agent_convo_api/deploy/deployment.json path/to/new_agent/deploy/
cp agent_convo_api/deploy/readme.md path/to/new_agent/deploy/

# 3. Run the notebooks from the new agent's deploy folder
# That's it! The templates auto-configure for the new agent.
```

### Key Features

- **Template-Based** - Copy deployment notebooks to any agent, no changes needed
- **Auto-Discovery** - Notebooks automatically find and import the agent
- **Metadata Tracking** - Deployment state stored in `deployment.json`
- **Shared Configuration** - Uses project-level `.env` and `requirements.txt`
- **Update-Friendly** - Easy to update deployed agents with code changes
- **Permission Management** - Guided setup for agent service account permissions

### Documentation

- **Project-Level Guide** - This section (you are here)
- **Agent-Specific Guides** - Each agent's `deploy/readme.md`
- **Official Docs**:
  - [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
  - [ADK Deployment Guide](https://google.github.io/adk-docs/deploy/)

### Troubleshooting

Common deployment issues and solutions are documented in each agent's deployment guide. For general help:

- Review the [agent_convo_api deployment guide](./agent_convo_api/deploy/readme.md) for detailed examples
- Check [Vertex AI Agent Engine docs](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
- Verify all prerequisites are met
- Ensure APIs are enabled in your GCP project

---