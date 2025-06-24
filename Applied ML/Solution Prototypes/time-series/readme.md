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

This project uses a Python environment.  You can replicate the exact environment with `pyenv` and the `venv` library (included in Python >= 3.3):

> **Note:** This code does assume you have [git](https://github.com/git-guides/install-git) installed and relies on having installed the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) and [initialized](https://cloud.google.com/sdk/docs/initializing) it with `gcloud init`.

```bash
# 0. change to the directory where you want to store the git repository:
cd ~/repos # change to your preference

# 1. Clone the repository
git clone https://github.com/statmike/vertex-ai-mlops.git

# 2. Change into the cloned repository directory
cd 'vertex-ai-mlops/Applied ML/Solution Prototypes/time-series'

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

### Start The MCP Toolbox Server

Use a new terminal window to start the MCP server locally on port 7000.  

> **Note:** The Python `venv` is not needed for toolbox to run.

```bash
cd 'Applied ML/Solution Prototypes/time-series'
~/toolbox --tools-file="./mcp/tools.yaml" --port 7000
```

Check the server by using a browser and going to `http://localhost:7000/`.  You should see 'Hello, World!'.

A futher check is reviewing the hosted toolsets on the server that were loaded form this project by going to `http://localhost:7000/api/toolset`.  You should see:

```json
{
  "serverVersion": "0.7.0+binary.linux.amd64.714d990c34ee990e268fac1aa6b89c4883ae5023",
  "tools": {
    "forecast-sum-by-day-overall": {
      "description": "Use this tool to get overall daily totals with forecasts",
      "parameters": [],
      "authRequired": []
    },
    "forecast-sum-by-day-stations": {
      "description": "Use this tool to get daily totals for bike stations with forecasts",
      "parameters": [
        {
          "name": "locator",
          "type": "string",
          "description": "Part of a start_station_name value, a wildcard",
          "authSources": []
        }
      ],
      "authRequired": []
    },
    "sum-by-day-overall": {
      "description": "Use this tool to get overall daily totals",
      "parameters": [],
      "authRequired": []
    },
    "sum-by-day-stations": {
      "description": "Use this tool to get daily totals for bike stations",
      "parameters": [
        {
          "name": "locator",
          "type": "string",
          "description": "Part of a start_station_name value, a wildcard",
          "authSources": []
        }
      ],
      "authRequired": []
    }
  }
}
```

When done, **but not yet**, you can stop the local server with `ctrl+c`.

### Run The Agents Locally With A Test UI

To test this agent you can use the `adk web` command from inside the `time-series` folder. 

```bash
# 7. Run the ADK web interface
adk web
```

This will start the test user interface and you can `ctrl+click` on the `http://localhost:8000` address.

Stop the service with `ctrl+c` in the terminal.

### Example Questions

Some example questions:
1.  What are the recent daily totals?
2.  What are the numer like for stations along 72 st?
3.  What are the expected values for stations near central park?

Example results:

Question 1 will trigger the tool for visualizing the overall daily totals from the past:
<div style="text-align: center;">
  <img src="./resources/overall.gif" style="border: 2px solid black; width: auto; height: 600px;">
  <a href="./resources/plot-from-response-from-sum-by-day-overall.html" target="_blank" rel="noopener noreferrer">
    <p style="margin-top: 12px; font-size: 0.9em; font-style: italic; text-aign: center;">Right-Click and open in new tab for interactive view</p>
  </a>
</div><br><br>
Question 2 will trigger the tool for visualizing the station level daily totals from the past for the subset of stations where the name includes '72 St':
<div style="text-align: center;">
  <img src="./resources/stations.gif" style="border: 2px solid black; width: auto; height: 600px;">
  <a href="./resources/plot-from-response-from-sum-by-day-stations.html" target="_blank" rel="noopener noreferrer">
    <p style="margin-top: 12px; font-size: 0.9em; font-style: italic; text-aign: center;">Right-Click and open in new tab for interactive view</p>
  </a>
</div><br><br>
Question 3 will trigger the tool for visualizing the station level daily totals with forecast for the stations where the name includes 'Central Park':
<div style="text-align: center;">
  <img src="./resources/stations_forecast.gif" style="border: 2px solid black; width: auto; height: 600px;">
  <a href="./resources/plot-from-response-from-forecast-sum-by-day-stations.html" target="_blank" rel="noopener noreferrer">
    <p style="margin-top: 12px; font-size: 0.9em; font-style: italic; text-aign: center;">Right-Click and open in new tab for interactive view</p>
  </a>
</div><br><br>


---
Thoughts to include later:

other uses: 
- MCP Inspector: https://googleapis.github.io/genai-toolbox/how-to/connect_via_mcp/#using-the-mcp-inspector-with-toolbox
- With IDE Chat: https://cloud.google.com/blog/products/ai-machine-learning/new-mcp-integrations-to-google-cloud-databases?e=48754805
  - Like BQ: https://cloud.google.com/bigquery/docs/pre-built-tools-with-mcp-toolbox#configure-your-mcp-client
  - Full List: https://googleapis.github.io/genai-toolbox/how-to/connect-ide/


Todo:
- add environment setup
- mcp setup
- adk setup
- mcp tools
- adk agents
- plot relationships
- how to run


a helpful codelab: https://codelabs.developers.google.com/travel-agent-mcp-toolbox-adk#0