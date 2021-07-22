# ReadMe

Welcome to this repository of [Vertex AI](https://cloud.google.com/vertex-ai) Notebooks.  

New to Vetex AI? I suggest starting [here](https://cloud.google.com/architecture/ml-on-gcp-best-practices).

The purpose of these [notebooks](https://cloud.google.com/vertex-ai/docs/general/notebooks) is to showcase using Vertex AI platform core functionality for efficiency of ML operations.  These notebooks use a [BigQuery table](https://cloud.google.com/bigquery/docs/tables-intro) as a data source and train a very simple model in multiple ways ([BQML](https://cloud.google.com/bigquery-ml/docs/introduction), [AutoML](https://cloud.google.com/vertex-ai/docs/start/automl-users), [TensorFlow Keras](https://www.tensorflow.org/api_docs/python/tf/keras)).  The goal is to focus on options available for operations rather than get into the details of modeling.   

These notebooks span from external models, like BigQuery ML and TensorFlow, to managed pipelines of TFX and KFP orchestrated TensorFlow.  

---

## Get Started
These are the GCP resources needed to get started:
- A GCP Project.
    - These examples use `PROJECT_ID='statmike-mlops'` which can be updated at the top of each notebook.
- An [Vertex AI Notebook Instance](https://cloud.google.com/vertex-ai/docs/general/notebooks).
    - These examples are not compute intensive and it is suggested that you use TensorFlow 2.4 without GPU's with all extentions enabled.

---

## How to Use These Files:
- Open JupyterLab for your Notebook Instance:
    - Clone this repository to your notebook instance
        - https://github.com/statmike/vertex-ai-mlops.git

---     
     