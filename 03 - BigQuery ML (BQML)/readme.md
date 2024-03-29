![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2F03+-+BigQuery+ML+%28BQML%29&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/03%20-%20BigQuery%20ML%20%28BQML%29/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# vertex-ai-mlops/03 - BigQuery ML (BQML)/readme.md

This series of notebooks will introduce [BigQuery ML (BQML)](https://cloud.google.com/bigquery/docs/bqml-introduction) with a focus on classification methods.

**BigQuery ML (BQML) Overview**

[BigQuery ML](https://cloud.google.com/bigquery/docs/bqml-introduction) allows you to use `SQL` to constuct an ML workflow.  This is a great leap in productivity and flexibility when the data source is [BigQuery](https://cloud.google.com/bigquery/docs/introduction) and users are already familiar with `SQL`. Using just `SQL`, [multiple techniques](https://cloud.google.com/bigquery/docs/bqml-introduction#model_selection_guide) can be used for model training and even include [hyperparameter tuning](https://cloud.google.com/bigquery/docs/hp-tuning-overview).  It includes serverless [training, evaluation, and inference](https://cloud.google.com/bigquery/docs/e2e-journey) techniques for supervised, unsupervised, time series methods, even recommendation engines.  [Predictions](https://cloud.google.com/bigquery/docs/inference-overview) can be served directly in BigQuery which also include explainability measures. Predictive models can be [exported to their native framework](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-export-model) for portability, or even directly [registered to Vertex AI model registry](https://cloud.google.com/bigquery/docs/create_vertex) for online predictions on Vertex AI Endpoints.  You can [import models into BigQuery ML](https://cloud.google.com/bigquery/docs/inference-overview#inference_using_imported_models) from many common frameworks, or [connect to remotely hosted models](https://cloud.google.com/bigquery/docs/inference-overview#inference_using_remote_models) on Vertex AI Endpoints. You can even directly use many [pre-trained models](https://cloud.google.com/bigquery/docs/inference-overview#pretrained-models) in Vertex AI Like Cloud Vision API, Cloud Natural Language API, Cloud Translate API, and Generative AI with Vertex AI hosted LLMs.

A great starting point for seeing the scope of available methods is the [user journey for models](https://cloud.google.com/bigquery/docs/e2e-journey).  This repository also has a series of notebook based workflows for many BigQuery ML methods that can be reviewed here: [../03 - BigQuery ML (BQML)](../03%20-%20BigQuery%20ML%20(BQML)/readme.md).

**BigFrames**

A new way to interact with BigQuery and BigQuery ML is [BigQuery DataFrames](https://cloud.google.com/python/docs/reference/bigframes/latest).  A new Pythonic DataFrame with modules for BigQuery (`bigframes.pandas`) that is pandas-compatible and BigQuery ML (`bigframes.ml`) that is scikit-learn like.  This series of notebooks will be expanded to offer workflow examples in the choice of SQL or BigFrames!

**Prerequisites**
- [00 - Setup.ipynb](../00%20-%20Setup/00%20-%20Environment%20Setup.ipynb)
- [01 - BigQuery - Table Data Source.ipynb](../01%20-%20Data%20Sources/01%20-%20BigQuery%20-%20Table%20Data%20Source.ipynb)

## Notebooks:
This list is in the suggested order of review for anyone getting an overview and learning about BigQuery ML.  It is also ok to pick a particular notebook of interest and if there are dependencies on prior notebooks they will be listed in the **prerequisites** section at the top of the notebook.  

>These notebooks are designed to be editable for trying with other data sources.  The same parameter names are used across the notebooks to also help when trying multiple methods on a custom data source.

<table style='text-align:left;vertical-align:middle;border:1px solid black' width="80%" cellpadding="1" cellspacing="0">
<!--...........................................................................................................................................................................-->
    <tr style='text-align:center;vertical-align:middle'>
        <th>SQL With <a href = "https://cloud.google.com/python/docs/reference/bigquery/latest" target="_blank">BigQuery API</a></th>
        <th>DataFrame With <a href = "https://cloud.google.com/python/docs/reference/bigframes/latest" target="_blank">BigFrames API</a></th>
    </tr>
<!--...........................................................................................................................................................................-->
    <tr style='text-align:center;vertical-align:middle'>
        <th colspan='2'>Setup And Introduction</th>
    </tr>
    <tr>
        <td><a href = "./Introduction%20to%20BigQuery%20ML%20%28BQML%29.ipynb" target="_blank">Introduction to BigQuery ML (BQML)</a></td>
        <td></td>
    </tr>
<!--...........................................................................................................................................................................-->
    <tr style='text-align:center;vertical-align:middle'>
        <th colspan='2'>Supervised Learning: Classification Methods</th>
    </tr>
    <tr>
        <td><a href = "./03a%20-%20BQML%20Logistic%20Regression.ipynb" target="_blank">03a - BQML Logistic Regression</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./03b%20-%20BQML%20Boosted%20Trees.ipynb" target="_blank">03b - BQML Boosted Trees</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./03c%20-%20BQML%20Random%20Forest.ipynb" target="_blank">03c - BQML Random Forest</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./03d%20-%20BQML%20Deep%20Neural%20Network%20(DNN).ipynb" target="_blank">03d - BQML Deep Neural Network (DNN)</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./03e%20-%20BQML%20Wide-And-Deep%20Networks.ipynb" target="_blank">03e - BQML Wide-And-Deep Networks</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./03f%20-%20BQML%20Logistic%20Regression%20With%20Hyperparameter%20Tuning.ipynb" target="_blank">03f - BQML Logistic Regression With Hyperparameter Tuning</a></td>
        <td></td>
    </tr>
<!--...........................................................................................................................................................................-->
    <tr style='text-align:center;vertical-align:middle'>
        <th colspan='2'>Unsupervised Learning</th>
    </tr>
    <tr>
        <td><a href = "./03g%20-%20BQML%20-%20PCA%20with%20Anomaly%20Detection.ipynb" target="_blank">03g - BQML - PCA with Anomaly Detection</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./03h%20-%20BQML%20k-means%20with%20Anomaly%20Detection.ipynb" target="_blank">03h - BQML k-means with Anomaly Detection</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./03i%20-%20BQML%20Autoencoder%20with%20Anomaly%20Detection.ipynb" target="_blank">03i - BQML Autoencoder with Anomaly Detection</a></td>
        <td></td>
    </tr>
<!--...........................................................................................................................................................................-->
    <tr style='text-align:center;vertical-align:middle'>
        <th colspan='2'>Feature Engineering</th>
    </tr>
    <tr>
        <td>Depricated (see following notebooks) <a href = "./BQML%20Feature%20Engineering.ipynb" target="_blank">BQML Feature Engineering</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./BQML%20Feature%20Engineering%20-%20Create%20Model%20With%20Transpose.ipynb" target="_blank">BQML Feature Engineering - Create Model With Transpose</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./BQML%20Feature%20Engineering%20-%20preprocessing%20functions.ipynb" target="_blank">BQML Feature Engineering - preprocessing functions</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./BQML%20Feature%20Engineering%20-%20reusable%20and%20modular.ipynb" target="_blank">BQML Feature Engineering - reusable and modular</a></td>
        <td></td>
    </tr>
<!--...........................................................................................................................................................................-->
    <tr style='text-align:center;vertical-align:middle'>
        <th colspan='2'>Enhanced Examples - more than one model</th>
    </tr>
    <tr>
        <td><a href = "./BQML%20Cross-validation%20Example.ipynb" target="_blank">BQML Cross-validation Example</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./BQML%20Ensemble%20Example.ipynb" target="_blank">BQML Ensemble Example</a></td>
        <td></td>
    </tr>
<!--...........................................................................................................................................................................-->
    <tr style='text-align:center;vertical-align:middle'>
        <th colspan='2'>Import Models</th>
    </tr>
    <tr>
        <td><a href = "./BQML%20Import%20Model%20-%20scikit-learn.ipynb" target="_blank">BQML Import Model - scikit-learn</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./BQML%20Import%20Model%20-%20TensorFlow.ipynb" target="_blank">BQML Import Model - TensorFlow</a></td>
        <td></td>
    </tr>
<!--...........................................................................................................................................................................-->
    <tr style='text-align:center;vertical-align:middle'>
        <th colspan='2'>Use Remote Models</th>
    </tr>
    <tr>
        <td><a href = "./BQML%20Remote%20Model%20on%20Vertex%20AI%20Endpoint.ipynb" target="_blank">BQML Remote Model on Vertex AI Endpoint</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./BQML%20Remote%20Model%20Tutorial.md" target="_blank">BQML Remote Model Tutorial</a>
            <ul>
                    <li><a href = "./BQML%20Remote%20Model%20Tutorial%20-%20Notebook.ipynb" target="_blank">BQML Remote Model Tutorial - Notebook</a> (Run as a Colab - see header for instructions)</li>
            </ul>
        </td>
        <td></td>
    </tr>
<!--...........................................................................................................................................................................--> 
    <tr style='text-align:center;vertical-align:middle'>
        <th colspan='2'>Generative AI</th>
    </tr>
    <tr>
        <td><a href = "./BQML%20For%20Generative%20AI%20With%20SQL.ipynb" target="_blank">BQML For Generative AI With SQL</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "../Applied%20GenAI/readme.md" target="_blank">Applied GenAI</a>
            <ul>
                <li><a href = "../Applied%20GenAI/Vertex%20AI%20GenAI%20For%20Rewriting%20-%20BigQuery%20Advisor%20With%20Codey.ipynb" target = "_blank">Vertex AI GenAI For Rewriting - BigQuery Advisor With Codey</a></li>
                <li><a href = "../Applied%20GenAI/Vertex%20AI%20GenAI%20For%20BigQuery%20Q&A%20-%20Overview.ipynb" target = "_blank">Vertex AI GenAI For BigQuery Q&A - Overview</a></li>
            </ul>
        </td>
        <td><a href = "../Applied%20GenAI/readme.md" target="_blank">Applied GenAI</a>
            <ul>
                <li><a href = "../Applied%20GenAI/Vertex%20AI%20GenAI%20Embeddings%20-%20As%20Features%20For%20Hierarchical%20Classification.ipynb" target = "_blank">Vertex AI GenAI Embeddings - As Features For Hierarchical Classification</a></li>
            </ul>
        </td>
    </tr>
<!--...........................................................................................................................................................................-->
    <tr style='text-align:center;vertical-align:middle'>
        <th colspan='2'>Other Topics</th>
    </tr>
    <tr>
        <td><a href = "./03Tools%20-%20Predictions.ipynb" target="_blank">03Tools - Predictions</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./03Tools%20-%20Pipelines%20Example%201.ipynb" target="_blank">03Tools - Pipelines Example 1</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./03Tools%20-%20Pipelines%20Example%202.ipynb" target="_blank">03Tools - Pipelines Example 2</a></td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "./03Tools%20-%20Pipelines%20Example%203.ipynb" target="_blank">03Tools - Pipelines Example 3</a></td>
        <td></td>
    </tr>
<!--...........................................................................................................................................................................-->
    <tr style='text-align:center;vertical-align:middle'>
        <th colspan='2'>Additional BQML techniques are explored throughout this repository</th>
    </tr>
    <tr>
        <td><a href = "../02%20-%20Vertex%20AI%20AutoML/readme.md" target="_blank">AutoML</a>
            <ul>
                <li><a href = "../02%20-%20Vertex%20AI%20AutoML/BQML%20AutoML.ipynb" target="_blank">BQML AutoML</a></li>
            </ul>
        </td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "../Working%20With/Document%20AI/readme.md" target="_blank">Document AI</a>
            <ul>
                <li><a href = "../Working%20With/Document%20AI/Document%20AI%20-%20From%20BigQuery.ipynb" target="_blank">Document AI - From BigQuery</a></li>
            </ul>
        </td>
        <td></td>
    </tr>
    <tr>
        <td><a href = "../Applied%20Forecasting/readme.md" target="_blank">Applied Forecasting</a>
            <ul>
                <li><a href = "../Applied%20Forecasting/BigQuery%20Time%20Series%20Forecasting%20Data%20Review%20and%20Preparation.ipynb" target="_blank">BigQuery Time Series Forecasting Data Review and Preparation</a></li>
                <li><a href = "../Applied%20Forecasting/BQML%20Univariate%20Forecasting%20with%20ARIMA+.ipynb" target="_blank">BQML Univariate Forecasting with ARIMA+</a></li>
                <li><a href = "../Applied%20Forecasting/BQML%20Multivariate%20Forecasting%20with%20ARIMA+%20XREG.ipynb" target="_blank">BQML Multivariate Forecasting with ARIMA+ XREG</a></li>
                <li><a href = "../Applied%20Forecasting/BQML%20Regression%20Based%20Forecasting.ipynb" target="_blank">BQML Regression Based Forecasting</a></li>
                <li><a href = "../Applied%20Forecasting/Vertex%20AI%20Pipelines%20-%20BQML%20ARIMA+.ipynb" target="_blank">Vertex AI Pipelines - BQML ARIMA+</a></li>
                <li><a href = "../Applied%20Forecasting/Vertex%20AI%20Pipelines%20-%20Forecasting%20Tournament%20with%20Kubeflow%20Pipelines%20(KFP).ipynb" target="_blank">Vertex AI Pipelines - Forecasting Tournament with Kubeflow Pipelines (KFP)</a></li>
            </ul>
        </td>
        <td><a href = "../Applied%20Forecasting/readme.md" target="_blank">Applied Forecasting</a>
            <ul>
                <li><a href = "../Applied%20Forecasting/Vertex%20AI%20Prediction%20Endpoints%20for%20Online%20Forecasting%20With%20Prophet.ipynb" target="_blank">Vertex AI Prediction Endpoints for Online Forecasting With Prophet</a></li>
            </ul>
        </td>
    </tr>
<!--...........................................................................................................................................................................-->    
</table>


**Notes:**
- Each of the notebooks=experiments `03a` through `03i` create a model in BigQuery with BQML and register the model in Vertex AI Model Registry.  Rerunning the notebook will create a new model version in the Vertex AI Model Registry.  All versions of the model persist in BigQuery and a timestamp is used to maintain naming uniqueness in BigQuery.
    - This recent integration between BQML models and Vertex AI Model Registry will result in an update to this work.
- `03Tools - Prediction` allows you to specify any experiment in this series and it will upload the latest version of the model to a Vertex AI Endpoint and demonstrate requesting predictions with Python, REST, and the GCLOUD CLI.
- Each of the `03Tools Pipelines ...` notebooks demonstrate an ML Workflow using BQML models with Vertex AI Pipelines
    - `Example 1`: Deploy The Best Model To An Endpoint
    - `Example 2`: Conditionally Update Endpoint
    - `Example 3`: Retraining Tournament
