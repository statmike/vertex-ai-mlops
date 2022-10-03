# 00 - Setup

This initial notebook is used to do essential `pip install ...`, create a GCS storage bucket, and save a datasource to GCS.  This sets up the main resources for the notebooks used in tutorials with this repository.

## Setting Up the Environment
- [00 - Environment Setup.ipynb](./00%20-%20Environment%20Setup.ipynb)
    - does environment setup: creats storage bucket, installs Python packages, saves source data

---
ToDo:
- [X] Move Plotly install to notebooks that use it
- [X] Update formating to match series
- [X] Detect and modify Service Account to have GCS Admin access for Pipelines
- [X] Move Dataset creation to 01 Series
