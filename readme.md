# ReadMe

Welcome to this repository of AI Platform Notebooks.  The purpose of these notebooks is to showcase using AI Platform resources for efficiency of ML operations.  These notebook use a BigQuery table as a data source and train a very simple model in multiple ways (BQML, TensorFlow Keras).  The goal is to focus on options available for operations rather than get buried in the details of modeling.   

These notebooks span from external models, like BigQuery ML and TensorFlow, to managed pipelines of TFX managed TensorFlow.  

---

## Get Started
These are the GCP resources needed to get started:
- A GCP Project.
    - These examples use `PROJECT_ID='statmike-mlops'` which can be updated at the top of each notebook.
- An AI Platform Notebook Instance.
    - These examples are not compute intensive and it is suggested that you use TensorFlow 2.4 without GPU's with all extentions enabled.

---

## How to Use These Files:
- Open JupyterLab for your Notebook Instance
    - Clone this repository to your notebook instance
        - setup authentication to git repository
            - open terminal in notebook instance
            - paste the credentials from [these instructions](https://cloud.google.com/source-repositories/docs/authentication#manually-generated-credentials)
        - open the git menu
            - clone repository
            - provide: https://source.developers.google.com/p/statmike-mlops/r/mlops
        - In the File Browser change to the `mlops` folder
        - Open `00 - Initial Setup`

---     
     