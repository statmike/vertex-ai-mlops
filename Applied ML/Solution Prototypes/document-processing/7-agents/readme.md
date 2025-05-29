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

# 8. Run the ADK web interface
adk web
```

## Run The Agents Locally With A Test UI

To test this agent you can use the `adk web` command from inside the `document_agent` folder.  This will start the test user interface and you can `ctrl+click` on the `http://localhost:8000` address:

<div align="center">
  <img src="../resources/images/adk/adk_web.png" alt="Document Processing" width="80%"/>
</div>

The test UI will open in a local browser:

<div align="center">
  <img src="../resources/images/adk/adk_web_ui.png" alt="Document Processing" width="80%"/>
</div>

Stop the service with `ctrl+c` in the terminal.

## An Example User UI

With `adk web` running in one terminal window open another terminal window.  

```
cd 'vertex-ai-mlops/Applied ML/Solution Prototypes/document-processing/7-agents'
source .venv/bin/activate
cd document_agent/gradio_app
python gradio_app.py
```

Open the Gradio app at the address reported in the terminal with a `ctrl+click`.



