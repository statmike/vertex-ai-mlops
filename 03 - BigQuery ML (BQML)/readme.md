# 03 - BigQuery ML (BQML)
Machine Learning with SQL using [BigQuery ML (BQML)](https://cloud.google.com/bigquery-ml/docs/introduction).

**Prerequisites**
- [00 - Setup.ipynb](../00%20-%20Setup/00%20-%20Environment%20Setup.ipynb)
- [01 - BigQuery - Table Data Source.ipynb](../01%20-%20Data%20Sources/01%20-%20BigQuery%20-%20Table%20Data%20Source.ipynb)

## This series of notebooks will introduce BigQuery ML (BQML) with a focus on classification methods.
- [03 - Introduction to BigQuery ML (BQML)](03%20-%20Introduction%20to%20BigQuery%20ML%20(BQML).ipynb)
- [03a - BQML Logistic Regression](03a%20-%20BQML%20Logistic%20Regression.ipynb)
- [03b - BQML Boosted Trees](03b%20-%20BQML%20Boosted%20Trees.ipynb)
- [03c - BQML Random Forest](03c%20-%20BQML%20Random%20Forest.ipynb)
- [03d - BQML Deep Neural Network (DNN)](03d%20-%20BQML%20Deep%20Neural%20Network%20(DNN).ipynb)
- [03e - BQML Wide-And-Deep Networks](03e%20-%20BQML%20Wide-And-Deep%20Networks.ipynb)
- [03f - BQML Logistic Regression With Hyperparameter Tuning](03f%20-%20BQML%20Logistic%20Regression%20With%20Hyperparameter%20Tuning.ipynb)
- [03Tools - Predictions](03Tools%20-%20Predictions.ipynb)
- [03Tools - Pipelines Example 1](03Tools%20-%20Pipelines%20Example%201.ipynb)
- [03Tools - Pipelines Example 2](03Tools%20-%20Pipelines%20Example%202.ipynb)
- [03Tools - Pipelines Example 3](03Tools%20-%20Pipelines%20Example%203.ipynb)

**Notes:**
- Each of the notebooks=experiments `03a` through `03f` create a model in BigQuery with BQML and register the model in Vertex AI Model Registry.  Rerunning the notebook will create a new model version in the Vertex AI Model Registry.  All versions of the model persist in BigQuery and a timestamp is used to maintain naming uniqueness in BigQuery.
- `03Tools - Prediction` allows you to specify any experiment in this series and it will upload the latest version of the model to a Vertex AI Endpoint and demonstrate requesting predictions with Python, REST, and the GCLOUD CLI.
- Each of the `03Tools Pipelines ...` notebooks demonstrate an ML Workflow using BQML models with Vertex AI Pipelines
    - `Example 1`: Deploy The Best Model To An Endpoint
    - `Example 2`: Conditionally Update Endpoint
    - `Example 3`: Retraining Tournament

## Additional BQML techniques are explored throughout this repository:
- [Applied Forecasting](../Applied%20Forecasting/readme.md)/
    - [1 - BigQuery Time Series Forecasting Data Review and Preparation](../Applied%20Forecasting/1%20-%20BigQuery%20Time%20Series%20Forecasting%20Data%20Review%20and%20Preparation.ipynb)
    - [2 - BQML Univariate Forecasting with ARIMA+](../Applied%20Forecasting/2%20-%20BQML%20Univariate%20Forecasting%20with%20ARIMA+.ipynb)
    - [8 - Vertex AI Pipelines - Forecasting Tournament - BQML + AutoML + Prophet](../Applied%20Forecasting/8%20-%20Vertex%20AI%20Pipelines%20-%20Forecasting%20Tournament%20-%20BQML%20+%20AutoML%20+%20Prophet.ipynb)

---
ToDo:
- [X] add prereq to readme
- [X] Update references to Service Account and check for permissions - reference the 00 notebooks new section for correct setup
- [X] Hyperlinks to prediction notebook in each of 03a-03f
- [X] export model: GCS and Vertex AI Model Registry use series_experiment naming convention and storage locations
- [X] fix references to data in GCS in the Tools - Predictions notebook: bucket/series/experiment
- [ ] Add Experiment tracking
- [ ] update pipeline examples
    - [ ] New version of pipeline 1 that uses experiment tracking - call it 1b
    - [X] update pipeline 2 - same flow but updated to match the series
    - [ ] create pipeline 3
- [ ] add kmeans, pca, autoencoder for anomaly detection using fraud data (maybe in applied section)