# Time Series Chat

a helpful codelab: https://codelabs.developers.google.com/travel-agent-mcp-toolbox-adk#0


## MCP Toolbox for Databases

A solution that makes connecting to, authorizing to, and querying data simple!

Install [MCP Toolbox for Databases](https://googleapis.github.io/genai-toolbox/getting-started/introduction/).  I prefer to do this once in the home folder and reuse the toolbox for all projects during development.

```bash
cd ~
export OS="linux/amd64" # one of linux/amd64, darwin/arm64, darwin/amd64, or windows/amd64
curl -O https://storage.googleapis.com/genai-toolbox/v0.7.0/$OS/toolbox

chmod +x toolbox
./toolbox --version
```

### Test The MCP Toolbox Server

Start the MCP server locally on port 7000:

```bash
~/toolbox --tools-file="./mcp/tools.yaml" --port 7000
```

Check the server by using a browser and going to `http://localhost:7000/`.  You should see 'Hello, World!'.

A futher check is reviewing the hosted toolsets on the server that were loaded form this project by going to `http://localhost:7000/api/toolset`.  You should see:

```json
{
    "serverVersion": "0.7.0+binary.linux.amd64.714d990c34ee990e268fac1aa6b89c4883ae5023",
    "tools": {
        "sum-by-day": {
            "description": "Use this tool to get daily totals for bike stations",
            "parameters": [],
            "authRequired": []
        }
    }
}
```

Stop the lcoal server with `ctrl+c`.

other uses: 
- MCP Inspector: https://googleapis.github.io/genai-toolbox/how-to/connect_via_mcp/#using-the-mcp-inspector-with-toolbox
- With IDE Chat: https://cloud.google.com/blog/products/ai-machine-learning/new-mcp-integrations-to-google-cloud-databases?e=48754805
  - Like BQ: https://cloud.google.com/bigquery/docs/pre-built-tools-with-mcp-toolbox#configure-your-mcp-client
  - Full List: https://googleapis.github.io/genai-toolbox/how-to/connect-ide/


## Environent Setup

Start my initializing the Python environment for the ADK agents to utilize locally.

```bash
cd 'Applied ML/Solution Prototypes/time-series'
pyenv local 3.13.3
python -m venv .venv
pip install -r requirements.txt
```





