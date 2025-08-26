![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FSolution+Prototypes%2Ftime-series&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/time-series/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/Solution%2520Prototypes/time-series/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/Solution%2520Prototypes/time-series/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/Solution%2520Prototypes/time-series/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/Solution%2520Prototypes/time-series/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# Time Series Chat

Answer users questions about data, time series data, that is stored in Google BigQuery.  This agent example interacts with tools setup with the MCP Toolbox for Databases to query BigQuery and returns data related to the users questions to the agent.  A term for this is agentic retrieval.  The results of the tool are passed to a Function tool that include Python code to create an interative visual for the data that is them passed to the user as a response.

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
cd 'vertex-ai-mlops/Applied ML/Solution Prototypes/time-series'
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

Some example questions:
1.  What are the recent daily totals?
2.  What are the numbers like for stations along 72 st?
3.  What are the expected values for stations near central park?

Example results:

Question 1 will trigger the tool for visualizing the overall daily totals from the past:
<div style="text-align: center;">
  <img src="./resources/overall.gif" style="border: 2px solid black; width: auto; height: 600px;">
  <a href="https://htmlpreview.github.io/?https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/time-series/resources/plot-from-response-from-sum-by-day-overall.html" target="_blank" rel="noopener noreferrer">
    <p style="margin-top: 12px; font-size: 0.9em; font-style: italic; text-aign: center;">Right-Click and open in new tab for interactive view</p>
  </a>
</div><br><br>
Question 2 will trigger the tool for visualizing the station level daily totals from the past for the subset of stations where the name includes '72 St':
<div style="text-align: center;">
  <img src="./resources/stations.gif" style="border: 2px solid black; width: auto; height: 600px;">
  <a href="https://htmlpreview.github.io/?https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/time-series/resources/plot-from-response-from-sum-by-day-stations.html" target="_blank" rel="noopener noreferrer">
    <p style="margin-top: 12px; font-size: 0.9em; font-style: italic; text-aign: center;">Right-Click and open in new tab for interactive view</p>
  </a>
</div><br><br>
Question 3 will trigger the tool for visualizing the station level daily totals with forecast for the stations where the name includes 'Central Park':
<div style="text-align: center;">
  <img src="./resources/stations_forecast.gif" style="border: 2px solid black; width: auto; height: 600px;">
  <a href="https://htmlpreview.github.io/?https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/time-series/resources/plot-from-response-from-forecast-sum-by-day-stations.html" target="_blank" rel="noopener noreferrer">
    <p style="margin-top: 12px; font-size: 0.9em; font-style: italic; text-aign: center;">Right-Click and open in new tab for interactive view</p>
  </a>
</div><br><br>
