![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FSolution+Prototypes%2Fdocument-processing%2F7-agents&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/document-processing/7-agents/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Agents

Build an agent workflow using the [Agent Development Kit (ADK)](https://google.github.io/adk-docs/) from Google.  This agent workflow will:
- load document for evaluation as an artifact for agents to use
- extract content from the document using the custom data extractor we created in [step 1](../1-custom-extractor.ipynb) and used in [step 2](../2-document-extraction.ipynb)
- compare the document to each vendors document to show similarity and verify classification like we showed in [step 4](../4-document-similarity.ipynb)
- assess the document for anomalies like we did in [step 5](../5-document-anomalies.ipynb)
- compare the document to a known good doucment from the same vedor to highlight in key difference in formatting like we did in [step 6](../6-document-comparison.ipynb)

## Environment Setup

This project uses a Python environment.  You can replicate the exact environment with `pyenv` and the `venv` library (included in Python >= 3.3):

> **Note:** This code does assume you have [git](https://github.com/git-guides/install-git) installed and relies on having installed the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) and [initialized](https://cloud.google.com/sdk/docs/initializing) it with `gcloud init`.

```
# 1. Clone the repository
git clone https://github.com/statmike/vertex-ai-mlops.git

# 2. Change into the cloned repository directory
cd 'vertex-ai-mlops/Applied ML/Solution Prototypes/document-processing/7-agents'

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

# 7. Change to the specific agent subfolder
cd document_agent
```

## Run The Agents Locally With A Test UI

To test this agent you can use the `adk web` command from inside the `document_agent` folder.  

```
# 8. Run the ADK web interface
adk web
```

This will start the test user interface and you can `ctrl+click` on the `http://localhost:8000` address:

<div align="center">
  <img src="../resources/images/adk/adk_web.png" alt="Document Processing" width="80%"/>
</div>

The test UI will open in a local browser:

<div align="center">
  <img src="../resources/images/adk/adk_web_ui.png" alt="Document Processing" width="80%"/>
</div>

Stop the service with `ctrl+c` in the terminal.

## Deploy Agents: Locally for testing, Vertex AI Agent Engine for productions

Deployment code is included in the included notebook workflow [deploy-vertex-ai-agent-engine](./document_agent/deploy-vertex-ai-agent-engine.ipynb).  This workflow shows how to use the Vertex AI SDK to deploy the agent as a local application for testing and then to Vertex AI Agent Engine for a scalable production hosting.

The deployment created here is directly used in the following example UI Applications:

---

> The following UI Applicaiton need updating to point to hosted versions of the agent on Vetex AI Agent Engine. (optionally local)

---

### An Example User UI: Gradio

With `adk web` running in one terminal window open another terminal window to execute:

```
cd 'vertex-ai-mlops/Applied ML/Solution Prototypes/document-processing/7-agents'
source .venv/bin/activate
cd document_agent/apps
python gradio_app.py
```

Open the Gradio app at the address reported in the terminal with a `ctrl+click`.

<div align="center">
  <img src="../resources/images/adk/gradio.png" alt="Document Processing App: Gradio" width="80%"/>
</div>

### An Example User UI: Streamlit

With `adk web` running in one terminal window open another terminal window to execute:

```
cd 'vertex-ai-mlops/Applied ML/Solution Prototypes/document-processing/7-agents'
source .venv/bin/activate
cd document_agent/apps
streamlit run streamlit_app.py
```

Open the Streamlit app at the address reported in the terminal with a `ctrl+click` - it will most likely auto-open in the system browser.

<div align="center">
  <img src="../resources/images/adk/streamlit.png" alt="Document Processing App: Streamlit" width="80%"/>
</div>

### An Example User UI: Mesop

With `adk web` running in one terminal window open another terminal window.  

```
cd 'vertex-ai-mlops/Applied ML/Solution Prototypes/document-processing/7-agents'
source .venv/bin/activate
cd document_agent/apps
mesop mesop_app.py
```

Open the Mesop app at the address reported in the terminal with a `ctrl+click`.

<div align="center">
  <img src="../resources/images/adk/mesop.png" alt="Document Processing App: Mesop" width="80%"/>
</div>

