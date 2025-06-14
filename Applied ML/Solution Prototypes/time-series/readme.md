# Time Series Chat

```bash
cd ~
export OS="linux/amd64" # one of linux/amd64, darwin/arm64, darwin/amd64, or windows/amd64
curl -O https://storage.googleapis.com/genai-toolbox/v0.7.0/$OS/toolbox

chmod +x toolbox
./toolbox --version
```

```bash
cd 'Applied ML/Solution Prototypes/time-series'
pyenv local 3.13.3
python -m venv .venv
pip install -r requirements.txt
```

```bash
~/toolbox --tools-file="./mcp/tools.yaml" --port 7000
```

go to: http://localhost:7000/

see: Hello, World!

go to: http://localhost:7000/api/toolset

see:
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


