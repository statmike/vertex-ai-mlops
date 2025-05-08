# Agents

Build an agent workflow using the [Agent Development Kit (ADK)](https://google.github.io/adk-docs/) from Google.  This agent workflow will:
- load document for evaluation as an artifact for agents to use
- extract content from the document using the custom data extractor we created in [step 1](../1-custom-extractor.ipynb) and used in [step 2](../2-document-extraction.ipynb)
- compare the document to each vendors document to show similarity and verify classification like we showed in [step 4](../4-document-similarity.ipynb)
- assess the document for anomalies like we did in [step 5](../5-document-anomalies.ipynb)
- compare the document to a known good doucment from the same vedor to highlight in key difference in formatting like we did in [step 6](../6-document-comparison.ipynb)

## Environment Setup

This project uses a Python environment.  You can replicate the exact environment with `pyenv` and the `venv` library (included in Python >= 3.3):

```
pyenv install 3.13.3
pyenv local 3.13.3
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run The Agents Locally

To test this agent you can use the `adk web` command from inside the `document_agent` folder.  This will start the test user interface and you can `ctrl+click` on the `http://localhost:8000` address:

<div align="center">
  <img src="../resources/images/adk/adk_web.png" alt="Document Processing" width="80%"/>
</div>

The test UI will open in a local browser:

<div align="center">
  <img src="../resources/images/adk/adk_web_ui.png" alt="Document Processing" width="80%"/>
</div>

