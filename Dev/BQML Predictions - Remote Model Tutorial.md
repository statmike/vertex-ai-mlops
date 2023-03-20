![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2FDev&dt=BQML+Predictions+-+Remote+Model+Tutorial.md)

# BQML Remote Model Tutorial
# {IN DRAFT DEVELOPMENT}

**Notes For Development**
- [X] https://www.tensorflow.org/text/tutorials/classify_text_with_bert
- [X] large BERT model: bert_en_cased_L-12_H-768_A-12
- [X] (Modified it last layer activation function to sigmoid so that it can generate scores between 0-1)
- [X] deploy it with n1-standard-4 CPU (autoscaling 1-10)
- [X] It took around 40min to run on 10K dataset with batch size 64
- [X] Try T4 GPU to train and serve
- Next Draft
    - use bigquery public.imdb.reviews for serving demo
    - [X] make sections: setup, create model, deploy on vertex, BQ Remote Model
    - for setup: actually bring step in from other tutorials
    - move bq remote connection setup into BQ Remote Model setup
    - Make parameters for Project, region, using colab
    - 128 is default batch size - just note this in description
    - Make adaptable so user could start tutorial with model already saved in GCS

## Overview

BigQuery ML (BQML) allows you to use `SQL` to constuct an ML workflow.  This is a great leap in productivity and flexibility when the data source is BigQuery and users are already familiar with `SQL`. Using just `SQL` multiple techniques can be used for model training and even include hyperparameter tuning.  Predictions can be served directly in BigQuery which also include explainability. Models can be exported or even directly registered to Vertex AI model registry for online predictions on Vertex AI Endpoints.

BigQuery ML has had the capability to import TensorFlow models for inference within BigQuery.  Now you can register remote models and serve prediction within BigQuery.  This means a Vertex AI Prediction endpoint can be registered as a remote model and called directly from BigQuery with ML.Predict!

This can be incredibly helpful when a model is too large to import into BigQuery, you want to use a single point of inference for online, batch, and micro-batches.  

## Tutorial

This tutorial uses a customized sentiment analysis model by fine-tuning a BERT model with plain-text IMDB movie reviews.  The resulting model uses text input (movie reviews) and returns sentiment scores between (0, 1).  The model will be registered in Vertex AI Model Registry and served on a Vertex AI Prediction Endpoint.  From there the model will be added to BigQuery as a remote model.  Within BigQuery we will use the remote model to get sentiment predictions for a text column.

Contents:
- [Tutorial Setup](#Tutorial-Setup)
- [Create Model](#Create-Model)
- [Deploy Model on Vertex AI](#Deploy-Model-on-Vertex-AI)
- [BigQuery ML Remote Model](#BigQuery-ML-Remote-Model)
- [Clean Up](#Clean-Up)

### Tutorial Setup
This tutorial will use the following billable components of Google Cloud: Google Cloud Storage, Vertex AI, BigQuery and BigQuery Cloud Resource Connection.  At then end of the tutorial the billable components will be removed.

1. Click [here to Enable APIs](https://console.cloud.google.com/flows/enableapi?apiid=aiplatform.googleapis.com,storage-component.googleapis.com,bigqueryconnection.googleapis.com) for Vertex AI, Google Cloud Storage, and BigQuery Cloud Resource Connections.
2. Vertex AI: Ensure that tasks 1-3 are completed from [Set up a Google Cloud Project and development environment](https://cloud.google.com/vertex-ai/docs/pipelines/configure-project#project)
3. Google Cloud Storage: Create a Bucket in the default `US` multi-region [following these instructions](https://cloud.google.com/storage/docs/creating-buckets)


### Create Model

**Classify Text with BERT**

TensorFlow tutorials include a sentiment analysis prediction model created by [fine-tuning a BERT model](https://www.tensorflow.org/text/tutorials/classify_text_with_bert) while adding a classification layer.  Start by going to this tutorials [notebook on GitHub](https://github.com/tensorflow/text/blob/master/docs/tutorials/classify_text_with_bert.ipynb) and clicking 'Run in Google Colab' - or directly here [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tensorflow/text/blob/master/docs/tutorials/classify_text_with_bert.ipynb).

**Two Options:**
1. Use a pre-saved result of this tutorial to continue without recreating the model (skip to [Deploy Model on Vertex AI](#Deploy-Model-on-Vertex-AI))
2. Run the tutorial with modification described here - it takes about an hour to run
    - Proceed with the tutorial and make modification and additions as indicated in this tutorial:
        - Before starting to run the cells change the compute
            - On the 'Runtime' menu select 'View Resources'
            - In the 'Resources' tab that appears select 'Change runtime type'
            - In the menu that appears change 'Hardware accelerator' from `None` to `GPU`
            - Click `Save`
            - Proceed with running the cells of the notebook
        - In the section "Choose a BERT model to fine-tune" use the dropdown to change the selection to `bert_en_cased_L-12_H-768_A-12`.  This version:
            - has 12 hidden layers (L)
            - creates an encoding with length 768 (H)
            - and 12 attention heads (the core of BERT) to have 12 unique attention patterns for each input
        - In the section "Define your model" change the last layer to better map the output to a probability (0, 1):
            - from `net = tf.keras.layers.Dense(1, activation=None, name='classifier')(net)`
            - to `net = tf.keras.layers.Dense(1, activation='sigmoid', name='classifier')(net)`.
        - In the section "Export for inference" the lines that create results need to be modified now that the activation function has been changed:
            - from:
                - `reloaded_results = tf.sigmoid(reloaded_model(tf.constant(examples)))`
                - `original_results = tf.sigmoid(classifier_model(tf.constant(examples)))`
            - to:
                - `reloaded_results = reloaded_model(tf.constant(examples))`
                - `original_results = classifier_model(tf.constant(examples))`
    - Note that training and evaluation will take about 1 hour.  The results achieve > 87% accuracy.

### Deploy Model on Vertex AI

At the bottom of the notebook the model is saved to the disk of the Colab notebook.  In these steps we will add code cell to the bottom of the notebook to (step 1) move the saved model to Google Cloud Storage, (step 2) register the model in the Vertex AI Model Registry and (step 3) deploy the model to a Vertex AI Prediction Endpoint.

First, install Vertex AI SDK and restart kernel:
```python
# install Vertex AI SDK and restart kernel
!pip install google.cloud.aiplatform -q -U

import IPython

app = IPython.Application.instance()
app.kernel.do_shutdown(True)
```

Second, add a new code cell that defines parameters:
```
# Define parameters
REGION = 'us-central1'
PROJECT_ID = 'statmike-mlops-349915'
BUCKET = PROJECT_ID
saved_model_path = './imdb_bert' # redefine due to kernel restart
```

Then, add a code cell that authenticates to Google Cloud:
```python
# authenticate to Google Cloud and set project
from google.colab import auth
auth.authenticate_user()
!gcloud config set project {PROJECT_ID}
```

#### Step 1: Move the model to Google Cloud Storage (GCS)

If you chose to skip running the notebook and use a pre-built version of the model then the next step is to add this code cell:

Copy the model to Google Cloud Storage:
```python
# copy the model files to GCS
!gsutil cp -r gs://bucket/path/to/prebuilt/model gs://$PROJECT_ID/bqml/remote_model_tutorial
```

If you ran the tutorial notebook and created a model then continue by adding these code cells:

Copy the model to Google Cloud Storage:
```python
# copy the model files to GCS
!gsutil cp -r $saved_model_path gs://$PROJECT_ID/bqml/remote_model_tutorial
```

#### Step 2: Register the Model In Vertex AI Model Registry

This step will register the model in the [Vertex AI Model Registry](https://cloud.google.com/vertex-ai/docs/model-registry/introduction).

Import and Initialize the Vertex AI SDK:
```python
# initialize Vertex AI SDK
from google.cloud import aiplatform
aiplatform.init(project = PROJECT_ID, location=REGION)
```

Register the model in the [Vertex AI Model Registry](https://cloud.google.com/vertex-ai/docs/model-registry/introduction) and specify a [Pre-built container for prediction](https://cloud.google.com/vertex-ai/docs/predictions/pre-built-containers#preview) using the Vertex AI Python SDK [Model.upload](https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform.Model#google_cloud_aiplatform_Model_upload) method:
```python
# Register Model in Vertex AI Model Registry
model = aiplatform.Model.upload(
    display_name = 'BERT Sentiment',
    serving_container_image_uri = 'us-docker.pkg.dev/vertex-ai-restricted/prediction/tf_opt-gpu.nightly:latest',
    artifact_uri = f'gs://{PROJECT_ID}/bqml/remote_model_tutorial'        
)
```

Review the models Information:
```python
# Review the Models information:
model.display_name, model.name, model.uri
```

#### Step 3: Deploy the Model to Vertex AI Prediction Endpoint

This step will deploy the model from the Vertex AI Model Registry (Step 3) to a [Vertex AI Prediction Endpoint](https://cloud.google.com/vertex-ai/docs/predictions/get-predictions#get_online_predictions).

Deploy the model using the Vertex AI Python SDK [Model.deploy](https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform.Model#google_cloud_aiplatform_Model_deploy) method:

```python
# Deploy model to new endpoint
endpoint = model.deploy(
    min_replica_count = 1,
    max_replica_count = 5,
    accelerator_type = 'NVIDIA_TESLA_T4',
    accelerator_count = 1,
    machine_type = 'n1-standard-4'
)
```

```python
# redefine the examples from tutorial
examples = [
    'this is such an amazing movie!',  # this is the same sentence tried earlier
    'The movie was great!',
    'The movie was meh.',
    'The movie was okish.',
    'The movie was terrible...'
]
```

```python
# test endpoint with examples
endpoint.predict(instances = examples).predictions
```

### BigQuery ML Remote Model

Creating a BigQuery ML Remote Model has two components: a BigQuery Cloud Resource Connection and a remote model that uses the connection.

#### Step 1: Create a BigQuery Cloud Resource Connection

```python
# create BigQuery Cloud Resource Connection
!bq mk --connection --location={REGION[0:2]} --project_id={PROJECT_ID} --connection_type=CLOUD_RESOURCE bqml_remote_model_tutorial
```

```python
# retrieve the service account for the BigQuery Cloud Resource Connection
import json

bqml_connection = !bq show --format prettyjson --connection {PROJECT_ID}.{REGION[0:2]}.bqml_remote_model_tutorial
bqml_connection = json.loads(''.join(bqml_connection))
service_account = bqml_connection['cloudResource']['serviceAccountId']
service_account
```

```python
# assign vertex ai user role to the service account of the BigQuery Cloud Resource Connection
!gcloud projects add-iam-policy-binding {PROJECT_ID} --member=serviceAccount:{service_account} --role=roles/aiplatform.user
```

#### Step 2: Create a BigQuery Dataset and Remote Model

Import and Initialize BigQuery Client
```python
# BigQuery Client
from google.cloud import bigquery
bq = bigquery.Client(project = PROJECT_ID)
```

Create a BigQuery Dataset:
```python
# Create A BigQuery Dataset
query = f"""
CREATE SCHEMA IF NOT EXISTS `{PROJECT_ID}.bqml_remote_model_tutorial`
    OPTIONS(location = '{REGION[0:2]}')
"""
job = bq.query(query = query)
job.result()
job.state
```

Create Model Using Remote Connection
```python
# Create Remote Model In BigQuery
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.bqml_remote_model_tutorial.bert_sentiment`
    INPUT (text STRING)
    OUTPUT(classifier FLOAT64)
    REMOTE WITH CONNECTION `{PROJECT_ID}.{REGION[0:2]}.bqml_remote_model_tutorial`
    OPTIONS(endpoint = 'https://{REGION}-aiplatform.googleapis.com/v1/{endpoint.resource_name}')
"""
job = bq.query(query = query)
job.result()
job.state
```

#### Step 3: Get Predictions with BigQuery ML.PREDICT

```python
query = f"""
SELECT *
FROM ML.PREDICT (
    MODEL `{PROJECT_ID}.bqml_remote_model_tutorial.bert_sentiment`,
    (
        SELECT review as text
        FROM `bigquery-public-data.imdb.reviews`
        LIMIT 10
    )
)
"""
bq.query(query = query).to_dataframe()
```


```python
query = f"""
SELECT *
FROM ML.PREDICT (
    MODEL `{PROJECT_ID}.bqml_remote_model_tutorial.bert_sentiment`,
    (
        SELECT review as text
        FROM `bigquery-public-data.imdb.reviews`
        LIMIT 10000
    )
)
"""
job = bq.query(query = query)
```
About 5.5 Minutes, scales up to 2 nodes at peak



### Clean Up

To avoid incurring ongoing charges to your Google Cloud account for the resoruces used in this tutorial, either delete the project that contains the resources, or keep the project and delete the individual resources.

```python
# remove Vertex AI Prediction Endpoint
endpoint.delete(force = True)

# remove model in Vertex AI Model Registry
model.delete()

# remove model files in GCS
#!gsutil rm -r gs://$PROJECT_ID/bqml/remote_model_tutorial

# remove BigQuery Dataset (holds model definition)
# bq data

# remove BigQuery Cloud Resource Connection
!bq rm --connection {PROJECT_ID}.{REGION[0:2]}.bqml_remote_model_tutorial
```