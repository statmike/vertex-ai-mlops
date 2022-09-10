# BigQuery Machine Learning (BQML)

## This series of notebooks will introduce BigQuery ML (BQML) with a focus on classification methods.  
- 03 - Introduction to BigQuery ML (BQML)
- 03a - BQML Logistic Regression
- 03b - BQML Boosted Trees
- 03c - BQML Random Forest
- 03d - BQML Deep Neural Network (DNN)
- 03e - BQML Wide-And-Deep Networks
- 03f - BQML Logistic Regression With Hyperparameter Tuning
- 03Tools - Prediction
- 03Tools - Pipelines Example 1
- 03Tools - Pipelines Example 2
- 03Tools - Pipelines Example 3

**Notes:**
- Each of the notebooks=experiments `03a` through `03f` create a model in BigQuery with BQML and register the model in Vertex AI Model Registry.  Rerunning the notebook will create a new model version in the Vertex AI Model Registry.  All version of the model persist in BigQuery and a timestamp is used to maintain naming uniqueness in BigQuery.
- `03Tools - Prediction` allow you to specify any experiments in this series and it will upload the latest version of the model to a Vertex AI Endpoint and demonstrate requesting predictions with Python, REST, and the GCLOUD CLI.
- Each of the `03Tools Pipelines ...` notebooks demonstrate an ML Workflow with Vertex AI Pipelines
    - `Example 1`: Deploy The Best Model To An Endpoint
    - `Example 2`: Conditionally Update Endpoint
    - `Example 3`: Retraining Tournament

## Additional BQML techniques are explored throughout this repository:
- Applied Forecasting/
    - 1 - Time Series Forecasting - Data Review in BigQuery
    - 2 - BQML Univariate Forecasting with ARIMA+
