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

- **Custom Python Tools:**
  - Used to execute simple, pre-defined SQL queries.
- **MCP Toolbox for Databases:**
  - [kind: bigquery_sql](https://googleapis.github.io/genai-toolbox/resources/tools/bigquery-sql/): Executes pre-defined SQL statements that can include parameters for dynamic filtering.
  - [kind: bigquery-execute-sql](https://googleapis.github.io/genai-toolbox/resources/tools/bigquery-sql/): Executes an LLM-generated SQL query.
  - [kind: bigqueryget-table-info](https://googleapis.github.io/genai-toolbox/resources/tools/bigquery-get-table-info/): Retrieves table metadata, which is provided to the LLM as context to help it write accurate SQL queries.
- **Built-in tools for BigQuery:**
  - Built-in tools used to interact with BigQuery that fetch metadata and execute SQL queries.

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
curl -O https://storage.googleapis.com/genai-toolbox/v0.7.0/$OS/toolbox

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
poetry install --no-root
```

>The `--no-root` flag is used because this project is a collection of scripts and not an installable package itself.
</details>
<details>
<summary>🐍 Option 2: Using `venv` and `pip`</summary>

If you prefer to use Python's built-in tools, you can use `venv` and `pip` with the `requirements.txt` file.

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
~/toolbox --tools-file="./tools.yaml" --port 7000
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
#   --port 8000

# Run the ADK web interface with one of:

# venv:
adk web --reload

# poetry:
poetry run adk web --reload
```

This will start the test user interface and you can `ctrl+click` on the `http://localhost:8000` address.

When finished, stop the service with `ctrl+c` in the terminal.

---
### Example Questions

Some example questions that trigger the different types of tools:

These trigger the funtion tools:

1.  What years had the most hurricanes?
2.  How many hurricanes were in 2015?

These trigger the MCP Toolbox tools `bigquery-sql`

3.  What were the biggest hurricanes by wind speed?
4.  What was the biggest hurricane by wind speed in 2015?

These force the dynamic creation of SQL and execute it with MCP Toolbox tools `bigquery-execute-sql`

5. What was the last hurricane of 2008?
6. What was the first hurricane of the 2009 year in the North Atlantic Basin?
7. What was the last hurricane of 2008 in the North Atlantic Basin?

These trigger the more general sub-agent that uses built-in BigQuery tools to find tables and generate SQl to answer the users questions:

8. Are there any weather datasets other than hurricanes?
9. What does the tsunami dataset have?
10. Do Tsunami's have names and seasons/years?
11. How many tsunamis across what date range is information available for?
12. How many records are from BC years?
13. Describe one of these based on available data.

