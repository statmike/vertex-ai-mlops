![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2FDev&dt=BQML+Predictions+-+Remote+Model+Tutorial.md)

# BQML Remote Model Tutorial
# {IN DRAFT DEVELOPMENT}

**Notes For Development**
- https://www.tensorflow.org/text/tutorials/classify_text_with_bert
- large BERT model: bert_en_cased_L-12_H-768_A-12
- (Modified it last layer activation function to sigmoid so that it can generate scores between 0-1)
- deploy it with n1-standard-4 CPU (autoscaling 1-10)
- It took around 40min to run on 10K dataset with batch size 64
- Try T4 GPU to train and server



## Overview

BigQuery ML (BQML) allows you to use `SQL` to constuct an ML workflow.  This is a great leap in productivity and flexibility when the data source is BigQuery and users are already familiar with `SQL`. Using just `SQL` multiple techniques can be used for model training and even include hyperparameter tuning.  Predictions can be served directly in BigQuery which also include explainability. Models can be exported or even directly registered to Vertex AI model registry for online predictions on Vertex AI Endpoints.

BigQuery ML has had the capability to import TensorFlow models for inference within BigQuery.  Now you can register remote models and serve prediction within BigQuery.  This means a Vertex AI Prediction endpoint can be registered as a remote model and called directly from BigQuery with ML.Predict!

This can be incredibly helpful when a model is too large to import into BigQuery, you want to use a single point of inference for online, batch, and micro-batches.  

## Tutorial

This tutorial will build a custom sentiment analysis model by fine-tuning a BERT model in plain-text IMDB movie reviews.  The resulting model take text as input and return sentiment scores between (0, 1).  The model will be registered in Vertex AI Model Registry and served on a Vertex AI Prediction Endpoint.  From there model will be added to BigQuery as a remote model.  Finally, within BigQuery we will use the model to get sentiment predictions for a text column.

## Before You Begin
This tutorial will use the following billable components of Google cloud: Google Cloud Storage, Vertex AI, BigQuery and and a BigQuery Cloud Resource Connection.  Set these up if they are not already prepared:

1. Vertex AI: Ensure that tasks 1-3 are completed from [Set up a Google Cloud Project and development environment](https://cloud.google.com/vertex-ai/docs/pipelines/configure-project#project)
2. Google Cloud Storage: Create a Bucket in the default `US` multi-region [following these instructions](https://cloud.google.com/storage/docs/creating-buckets)
3. BigQuery: Create a dataset for this tutorial [following these instructions](https://cloud.google.com/bigquery/docs/datasets#create-dataset)
4. BigQuery Cloud Resource Connection: Follow the instuctions for [Create and setup a Cloud resource connection](https://cloud.google.com/bigquery/docs/create-cloud-resource-connection)
    - When you get to the step for [Grant access to the service account](https://cloud.google.com/bigquery/docs/create-cloud-resource-connection#access-storage) assign the [Vertex AI User IAM role](https://cloud.google.com/vertex-ai/docs/general/access-control#aiplatform.user) (`roles/aiplatform.user`)

## Step 1: Classify Text with BERT

TensorFlow tutorials include a sentiment analysis prediction model created by [fine-tuning a BERT model](https://www.tensorflow.org/text/tutorials/classify_text_with_bert) with a classification layer.  Start by going to this tutorials [notebook on GitHub](https://github.com/tensorflow/text/blob/master/docs/tutorials/classify_text_with_bert.ipynb) and clicking Run in Google Colab - or directly here [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tensorflow/text/blob/master/docs/tutorials/classify_text_with_bert.ipynb).

Proceed with the tutorial and make modification and additions as indicated in this tutorial:
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
    
Note that training and evaluation will take about 1 hour.  The results achieve > 87% accuracy.

## Step 2: Move the model to Google Cloud Storage (GCS)

**Prerequisites**

Add the bottom of the notebook the model is saved to the disk of the Colab notebook.  In this step we will add code cells to the notebook to authenticate to Google Cloud and copy the model to a storage bucket.

View the size of the model:
```python
# review model size
!du -sh $saved_model_path
```
Shows the final model is around 433MB.

Authenticate to Google Cloud:
```python
# authenticate to Google Cloud
from google.colab import auth
auth.authenticate_user()
```

Set The Google Cloud Project:
```python
# set the Google Cloud Project
PROJECT_ID = 'statmike-mlops-349915'
!gcloud config set project {PROJECT_ID}
```

Copy the model to Google Cloud Storage:
```python
# copy the model files to GCS
!gsutil cp -r $saved_model_path gs://$PROJECT_ID/bqml/remote_model_tutorial
```

## Step 3: Register the Model In Vertex AI Model Registry

This step will register the model in the [Vertex AI Model Registry](https://cloud.google.com/vertex-ai/docs/model-registry/introduction).

**DOES THIS NEED RUNTIME RESTART - IF YES, THEN WHAT IS IMPACT TO RUNNING FOLLOWING CODE - any prereqs?**
Install Vertex AI SDK:
```python
!pip install google.cloud.aiplatform -q
```

Import and Initialize the Vertex AI SDK:
```python
# initialize Vertex AI SDK
REGION = 'us-central1'
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

## Step 4: Deploy the Model to Vertex AI Prediction Endpoint

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
# test endpoint
endpoint.predict(instances = examples)
```


## Step 5: Create A Remote Model in BigQuery

Import and Initialize BigQuery Client
```python
# BigQuery Client
from google.cloud import bigquery
bq = bigquery.Client(project = PROJECT_ID)
```

Create Model Using Remote Connection
```python
# Create Remote Model In BigQuery
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.bert_sentiment.bert_sentiment` AS
    INPUT (test STRING)
    OUTPUT(sentiment FLOAT64)
    REMOTE WITH CONNECTION `{PROJECT_ID}.US.vertex_connect`
    OPTIONS(endpoint = 'https://{REGION}-aiplatform.googleapis.com/v1/{endpoint.resource_name}')
"""
job = bq.query(query = query)
job.result()
job.state
```

## Step 6: Get Predictions!

```python
query = f"""

"""
bq.query(query = query)
```

## Step 7: Clean Up

To avoid incurring ongoing charges to your Google Cloud account for the resoruces used in this tutorial, either delete the project that contains the resources, or keep the project and delete the individual resources.

- endpoint
- model
- gcs
- bq dataset
- bq connection

```python
endpoint.delete(force = True)
model.delete()
#!gsutil rm -r gs://$PROJECT_ID/bqml/remote_model_tutorial
# bq data
# bq connection
```