![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2F03+-+BigQuery+ML+%28BQML%29&dt=readme.md)

# /03 - BigQuery ML (BQML)/readme.md

This series of notebooks will introduce [BigQuery ML (BQML)](https://cloud.google.com/bigquery/docs/bqml-introduction) with a focus on classification methods.

**BigQuery ML (BQML) Overview**

[BigQuery ML](https://cloud.google.com/bigquery/docs/bqml-introduction) allows you to use `SQL` to constuct an ML workflow.  This is a great leap in productivity and flexibility when the data source is [BigQuery](https://cloud.google.com/bigquery/docs/introduction) and users are already familiar with `SQL`. Using just `SQL`, [multiple techniques](https://cloud.google.com/bigquery/docs/bqml-introduction#model_selection_guide) can be used for model training and even include [hyperparameter tuning](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-hp-tuning-overview).  It includes serverless [training, evaluation, and inference](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-e2e-journey) techniques for supervised, unsupervised, time series methods, even recommendation engines.  [Predictions](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-inference-overview) can be served directly in BigQuery which also include explainability measures. Predictive models can be [exported to their native framework](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-export-model) for portability, or even directly [registered to Vertex AI model registry](https://cloud.google.com/bigquery/docs/managing-models-vertex) for online predictions on Vertex AI Endpoints.  You can [import models into BigQuery ML](https://cloud.google.com/bigquery/docs/reference/standard-sql/inference-overview#inference_using_imported_models) from many common framework, or [connect to remotely hosted models](https://cloud.google.com/bigquery/docs/reference/standard-sql/inference-overview#inference_using_remote_models) on Vertex AI Endpoints. You can even directly use many [pre-trained models](https://cloud.google.com/bigquery/docs/reference/standard-sql/inference-overview#pretrained-models) in Vertex AI Like Cloud Vision API, Cloud Natural Language API, and Cloud Translate API.

A great starting point for seeing the scope of available methods is the [user journey for models](https://cloud.google.com/bigquery-ml/docs/reference/standard-sql/bigqueryml-syntax-e2e-journey).  This repository also has a series of notebook based workflows for many BigQuery ML methods that can be reviewed here: [../03 - BigQuery ML (BQML)](../03%20-%20BigQuery%20ML%20(BQML)/readme.md).

**Prerequisites**
- [00 - Setup.ipynb](../00%20-%20Setup/00%20-%20Environment%20Setup.ipynb)
- [01 - BigQuery - Table Data Source.ipynb](../01%20-%20Data%20Sources/01%20-%20BigQuery%20-%20Table%20Data%20Source.ipynb)

## Notebooks:
This list is in the suggested order of review for anyone getting an overview and learning about BigQuery ML.  It is also ok to pick a particular notebook of interest and if there are dependencies on prior notebooks they will be listed in the **prerequisites** section at the top of the notebook.  

>The notebooks are designed to be editable for trying with other data sources.  The same parameter names are used across the notebooks to also help when trying multiple methods on a custom data source.

- 1 - [Introduction to BigQuery ML (BQML)](Introduction%20to%20BigQuery%20ML%20(BQML).ipynb)
- Supervised Learning: Classification Methods
    - [03a - BQML Logistic Regression](03a%20-%20BQML%20Logistic%20Regression.ipynb)
    - [03b - BQML Boosted Trees](03b%20-%20BQML%20Boosted%20Trees.ipynb)
    - [03c - BQML Random Forest](03c%20-%20BQML%20Random%20Forest.ipynb)
    - [03d - BQML Deep Neural Network (DNN)](03d%20-%20BQML%20Deep%20Neural%20Network%20(DNN).ipynb)
    - [03e - BQML Wide-And-Deep Networks](03e%20-%20BQML%20Wide-And-Deep%20Networks.ipynb)
    - [03f - BQML Logistic Regression With Hyperparameter Tuning](03f%20-%20BQML%20Logistic%20Regression%20With%20Hyperparameter%20Tuning.ipynb)
- Unsupervised Learning
    - [03g - BQML - PCA with Anomaly Detection](03g%20-%20BQML%20-%20PCA%20with%20Anomaly%20Detection.ipynb)
    - [03h - BQML k-means with Anomaly Detection](03h%20-%20BQML%20k-means%20with%20Anomaly%20Detection.ipynb)
    - [03i - BQML Autoencoder with Anomaly Detection](03i%20-%20BQML%20Autoencoder%20with%20Anomaly%20Detection.ipynb)
- Feature Engineering
    - [BQML Feature Engineering](BQML%20Feature%20Engineering.ipynb)
    - [BQML Feature Engineering - v2](BQML%20Feature%20Engineering%20-%20v2.ipynb)
- Enhanced Examples - more than one model
    - [BQML Cross-validation Example](BQML%20Cross-validation%20Example.ipynb)
    - [BQML Ensemble Example](BQML%20Ensemble%20Example.ipynb)
- Import Models
    - [BQML Import Model - scikit-learn](BQML%20Import%20Model%20-%20scikit-learn.ipynb)
    - [BQML Import Model - TensorFlow](BQML%20Import%20Model%20-%20TensorFlow.ipynb)
- Use Remote Models
    - [BQML Remote Model on Vertex AI Endpoint](BQML%20Remote%20Model%20on%20Vertex%20AI%20Endpoint.ipynb)
    - [BQML Remote Model Tutorial](BQML%20Remote%20Model%20Tutorial.md)
        - [BQML Remote Model Tutorial - Notebook](BQML%20Remote%20Model%20Tutorial%20-%20Notebook.ipynb) (Run as a Colab - see header for instructions)
- Other Topics
    - [03Tools - Predictions](03Tools%20-%20Predictions.ipynb)
    - [03Tools - Pipelines Example 1](03Tools%20-%20Pipelines%20Example%201.ipynb)
    - [03Tools - Pipelines Example 2](03Tools%20-%20Pipelines%20Example%202.ipynb)
    - [03Tools - Pipelines Example 3](03Tools%20-%20Pipelines%20Example%203.ipynb)


**Notes:**
- Each of the notebooks=experiments `03a` through `03i` create a model in BigQuery with BQML and register the model in Vertex AI Model Registry.  Rerunning the notebook will create a new model version in the Vertex AI Model Registry.  All versions of the model persist in BigQuery and a timestamp is used to maintain naming uniqueness in BigQuery.
    - This recent integration between BQML models and Vertex AI Model Registry will result in an update to this work.
- `03Tools - Prediction` allows you to specify any experiment in this series and it will upload the latest version of the model to a Vertex AI Endpoint and demonstrate requesting predictions with Python, REST, and the GCLOUD CLI.
- Each of the `03Tools Pipelines ...` notebooks demonstrate an ML Workflow using BQML models with Vertex AI Pipelines
    - `Example 1`: Deploy The Best Model To An Endpoint
    - `Example 2`: Conditionally Update Endpoint
    - `Example 3`: Retraining Tournament

## Additional BQML techniques are explored throughout this repository:
- [AutoML](../02%20-%20Vertex%20AI%20AutoML)/
    - [BQML AutoML](../02%20-%20Vertex%20AI%20AutoML/BQML%20AutoML.ipynb)
- [Applied Forecasting](../Applied%20Forecasting/readme.md)/
    - [BigQuery Time Series Forecasting Data Review and Preparation](../Applied%20Forecasting/BigQuery%20Time%20Series%20Forecasting%20Data%20Review%20and%20Preparation.ipynb)
    - [BQML Univariate Forecasting with ARIMA+](../Applied%20Forecasting/BQML%20Univariate%20Forecasting%20with%20ARIMA+.ipynb)
    - [BQML Multivariate Forecasting with ARIMA+ XREG](../Applied%20Forecasting/BQML%20Multivariate%20Forecasting%20with%20ARIMA+%20XREG.ipynb)
    - [BQML Regression Based Forecasting](../Applied%20Forecasting/BQML%20Regression%20Based%20Forecasting.ipynb)
    - [Vertex AI Pipelines - BQML ARIMA+](./Vertex%20AI%20Pipelines%20-%20BQML%20ARIMA+.ipynb)
    - [8 - Vertex AI Pipelines - Forecasting Tournament - BQML + AutoML + Prophet](../Applied%20Forecasting/8%20-%20Vertex%20AI%20Pipelines%20-%20Forecasting%20Tournament%20-%20BQML%20+%20AutoML%20+%20Prophet.ipynb)

---

ToDo:
- [ ] Next Update Pass
    - [ ] correct language for 'This Run' sections print statment: with > will
    - [ ] add colab link and code - update bq client to set project for colab use
    - [ ] add code to lookup existing model to each notebook so it can be run without retraining
    - [ ] rename experiment in 03g, h, i to match notebook name
    - [ ] 03h kmeans add silhouette plot
    - [ ] add experiment tracking
    - [ ] directly register BQML models in Vertex AI [link](https://cloud.google.com/bigquery-ml/docs/managing-models-vertex)
    - [ ] create an example of ML.PREDICT for patial dependence plot
- [ ] update pipeline examples
    - [ ] pipelines 1 and 2 break if models form 03g, 03h, or 03i are deployed - unsupervised methods
    - [ ] New version of pipeline 1 that uses experiment tracking - call it 1b
    - [X] update pipeline 2 - same flow but updated to match the series
    - [ ] create pipeline 3
- [ ] Predictions
    - [ ] Online Predictions notebooks like 05
    - [ ] Batch Predictions In Vertex
    - [ ] Cloud Run
    - [ ] Local
    - [ ] DataFlow

