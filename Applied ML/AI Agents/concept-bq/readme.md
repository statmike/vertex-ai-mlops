# Concept: Agentic Retrieval With BigQuery

This ADK agent concept shows tools that interact with Google BigQuery using different methods to execute pre-defined SQL, parameterized SQL, and LLM generated SQL (leverging table metadata as context):

- Custom Tools, called Function Tools, to **execute pre-defined SQL**
- MCP Toolbox for Databases
    - Uses [kind: bigquery_sql](https://googleapis.github.io/genai-toolbox/resources/tools/bigquery-sql/) to **execute pre-defined SQL**. Can **include parameters** for dynamic queries.
    - Uses [kind: bigquery-execute-sql](https://googleapis.github.io/genai-toolbox/resources/tools/bigquery-sql/) to **execute LLM generated SQL** as input. 
      - Also incorporate: [kind: bigqueryget-table-info](https://googleapis.github.io/genai-toolbox/resources/tools/bigquery-get-table-info/) to retrieve table metadata to help with LLM query writing.

---
## Environment Setup

Install the prerequisite tools and setup the Python environment.

### MCP Toolbox For Databases

This is a solution that makes connecting to, authorizing to, and querying data simple!

Install [MCP Toolbox for Databases](https://googleapis.github.io/genai-toolbox/getting-started/introduction/).  I prefer to do this once in the home folder and reuse the toolbox for all projects during development.

```bash
cd ~
export OS="linux/amd64" # one of linux/amd64, darwin/arm64, darwin/amd64, or windows/amd64
curl -O https://storage.googleapis.com/genai-toolbox/v0.7.0/$OS/toolbox

chmod +x toolbox
./toolbox --version
```

### Python Enviornment

This project uses a Python environment.  You can replicate the exact environment with [`pyenv`](https://github.com/pyenv/pyenv) and the [`venv`](https://docs.python.org/3/library/venv.html) library (included in Python >= 3.3):

> **Note:** This code does assume you have [git](https://github.com/git-guides/install-git) installed and relies on having installed the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) and [initialized](https://cloud.google.com/sdk/docs/initializing) it with `gcloud init`.  This code manages Python environments with `venv` and Python versions with `pyenv`.

```bash
# 0. change to the directory where you want to store the git repository:
cd ~/repos # change to your preference

# 1. Clone the repository
git clone https://github.com/statmike/vertex-ai-mlops.git

# 2. Change into the cloned repository directory
cd 'vertex-ai-mlops/Applied ML/AI Agents/concept-bq'

# 3. Set up the Python environment using pyenv
# (Install Python 3.13.3 if you don't have it)
pyenv install 3.13.3
# (Set Python 3.13.3 as the local version for this project)
pyenv local 3.13.3

# 4. Create a virtual environment
python -m venv .venv

# 5. Activate the virtual environment
source .venv/bin/activate

# 6. Install the required Python packages
pip install -r requirements.txt
```

---
## Running The Agent

Running the agent requires first running the MCP Toolbox Server, locally in this case, and then starting the ADK test UI, also locally.

### 1 - Start The MCP Toolbox Server

Use a new terminal window to start the MCP server locally on port 7000.  

> **Note:** The Python `venv` is not needed for toolbox to run.

```bash
cd 'Applied ML/AI Agents/concept-bq'
~/toolbox --tools-file="./tools.yaml" --port 7000
```

Check the server by using a browser and going to `http://localhost:7000/`.  You should see 'Hello, World!'.

A futher check is reviewing the hosted toolsets on the server that were loaded form this project by going to `http://localhost:7000/api/toolset`.  You should see JSON formatted specs for the tools defined in the `tools.yaml` file.

When done, **but not yet**, you can stop the local server with `ctrl+c`.

### 2 - Run The Agents Locally With A Test UI

To test this agent you can use the `adk web` command from inside the `concept-bq` folder. 

```bash
# 7. Run the ADK web interface
adk web
```

This will start the test user interface and you can `ctrl+click` on the `http://localhost:8000` address.

When finished, stop the service with `ctrl+c` in the terminal.

### Example Questions

Some example questions:
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