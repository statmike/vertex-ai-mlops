![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2F03+-+BigQuery+ML+%28BQML%29&file=BQML+Remote+Model+Tutorial.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/03%20-%20BigQuery%20ML%20%28BQML%29/BQML%20Remote%20Model%20Tutorial.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# BQML Remote Model Tutorial

This tutorial is also part of the BigQuery Documentations Tutorials section - [view here](https://cloud.google.com/bigquery/docs/bigquery-ml-remote-model-tutorial).  In this repository there is also a pre-completed version of the notebook modifications described below.

## Overview

BigQuery ML (BQML) allows you to use `SQL` to constuct an ML workflow.  This is a great leap in productivity and flexibility when the data source is BigQuery and users are already familiar with `SQL`. Using just `SQL`, multiple techniques can be used for model training and even include hyperparameter tuning.  Predictions can be served directly in BigQuery which also includes explainability. Models can be exported or even directly registered to Vertex AI model registry for online predictions on Vertex AI Prediction Endpoints.

BigQuery ML has had the capability to import TensorFlow models for inference within BigQuery.  Now you can also register remote models and serve prediction within BigQuery.  This means a Vertex AI Prediction endpoint can be registered as a remote model and called directly from BigQuery with [`ML.Predict`](https://cloud.google.com/bigquery-ml/docs/reference/standard-sql/bigqueryml-syntax-predict).

This can be incredibly helpful when a model is too large to import into BigQuery or when you want to use a single point of inference for online, batch, and micro-batches.  

## Tutorial

This tutorial uses a customized sentiment analysis model by fine-tuning a BERT model with plain-text IMDB movie reviews.  The resulting model uses text input (movie reviews) and returns sentiment scores between (0, 1).  The model will be registered in [Vertex AI Model Registry](https://cloud.google.com/vertex-ai/docs/model-registry/introduction) and served on a [Vertex AI Prediction Endpoint](https://cloud.google.com/vertex-ai/docs/predictions/get-predictions#deploy_a_model_to_an_endpoint).  From there the model will be added to BigQuery as a remote model.  Within BigQuery we will use the remote model to get sentiment predictions for a text column (reviews of movies from the 100,000 row table `bigquery-public-data.imdb.reviews`.

Contents:
- [Tutorial Setup](#Tutorial-Setup)
- [Create Model](#Create-Model)
- [Deploy Model on Vertex AI](#Deploy-Model-on-Vertex-AI)
- [BigQuery ML Remote Model](#BigQuery-ML-Remote-Model)
- [Clean Up](#Clean-Up)

### Tutorial Setup
This tutorial will use the following billable components of Google Cloud: Google Cloud Storage, Vertex AI, BigQuery, and BigQuery Cloud Resource Connection.  At then end of the tutorial the billable components will be removed.

1. Click [here to Enable APIs](https://console.cloud.google.com/flows/enableapi?apiid=aiplatform.googleapis.com,storage-component.googleapis.com,bigqueryconnection.googleapis.com) for Vertex AI, Google Cloud Storage, and BigQuery Cloud Resource Connections.
2. Google Cloud Storage: Create a Bucket in the default `US` multi-region [following these instructions](https://cloud.google.com/storage/docs/creating-buckets)


### Create Model

**Classify Text with BERT**

TensorFlow tutorials include a sentiment analysis prediction model created by [fine-tuning a BERT model](https://www.tensorflow.org/text/tutorials/classify_text_with_bert) while adding a classification layer.  Start by going to this tutorials [notebook on GitHub](https://github.com/tensorflow/text/blob/master/docs/tutorials/classify_text_with_bert.ipynb) and clicking 'Run in Google Colab' - or directly here [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tensorflow/text/blob/master/docs/tutorials/classify_text_with_bert.ipynb).

**To view an already modified version of this notebook [click here](./BQML%20Remote%20Model%20Tutorial%20-%20Notebook.ipynb).**

**Two Options:**
1. Use a pre-saved result of this tutorial (or another model altogether) to continue without recreating the model (skip to [Deploy Model on Vertex AI](#Deploy-Model-on-Vertex-AI))
2. Run the tutorial with modifications described here - **it takes about an hour to run**
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
            - from: `net = tf.keras.layers.Dense(1, activation=None, name='classifier')(net)`
            - to: `net = tf.keras.layers.Dense(1, activation='sigmoid', name='classifier')(net)`.
        - In the section "Export for inference" the lines that create results need to be modified now that the activation function has been changed above:
            - from:
                - `reloaded_results = tf.sigmoid(reloaded_model(tf.constant(examples)))`
                - `original_results = tf.sigmoid(classifier_model(tf.constant(examples)))`
            - to:
                - `reloaded_results = reloaded_model(tf.constant(examples))`
                - `original_results = classifier_model(tf.constant(examples))`
    - Note that training and evaluation will take about 1 hour.  The results achieve > 87% accuracy.

### Deploy Model on Vertex AI

At the bottom of the notebook the model is saved to the disk of the Colab notebook.  In these steps we will add code cell to the bottom of the notebook to (step 1) move the saved model to Google Cloud Storage, (step 2) register the model in the Vertex AI Model Registry and (step 3) deploy the model to a Vertex AI Prediction Endpoint.

#### Step 1: Setup Environment and Connect to GCP

First, install Vertex AI SDK and restart kernel:
```python
# install Vertex AI SDK and restart kernel
!pip install google.cloud.aiplatform -q -U

import IPython

app = IPython.Application.instance()
app.kernel.do_shutdown(True)
```

Second, add a new code cell that defines parameters:
```python
# Define parameters
REGION = 'us-central1'
EXPERIMENT = 'remote-model-tutorial'
SERIES = 'bqml'
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

#### Step 2: Move the model to Google Cloud Storage (GCS)

If you chose to skip running the notebook and use a pre-built version of the model then the next step is to add this code cell:

Copy the model to Google Cloud Storage:
```python
# copy the model files to GCS
!gsutil cp -r gs://bucket/path/to/prebuilt/model gs://{PROJECT_ID}/{SERIES}/{EXPERIMENT}
```

If you ran the tutorial notebook and created a model then continue by adding these code cells:

Copy the model to Google Cloud Storage:
```python
# copy the model files to GCS
!gsutil cp -r $saved_model_path gs://{PROJECT_ID}/{SERIES}/{EXPERIMENT}
```

#### Step 3: Register the Model In Vertex AI Model Registry

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
    display_name = f'{SERIES}_{EXPERIMENT}',
    serving_container_image_uri = 'us-docker.pkg.dev/vertex-ai-restricted/prediction/tf_opt-gpu.nightly:latest',
    artifact_uri = f'gs://{PROJECT_ID}/{SERIES}/{EXPERIMENT}'        
)
```

Review the models Information:
```python
# Review the Models information:
model.display_name, model.name, model.uri
```

#### Step 4: Deploy the Model to Vertex AI Prediction Endpoint

This step will deploy the model from the Vertex AI Model Registry (Step 3) to a [Vertex AI Prediction Endpoint](https://cloud.google.com/vertex-ai/docs/predictions/get-predictions#get_online_predictions).

Deploy the model using the Vertex AI Python SDK [Model.deploy](https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform.Model#google_cloud_aiplatform_Model_deploy) method.  Here the replica counts are specified in a range of 1 (minimum) to 3 (maximum) and will scale based on traffic volumes and latency.
```python
# Deploy model to new endpoint
endpoint = model.deploy(
    min_replica_count = 1,
    max_replica_count = 3,
    accelerator_type = 'NVIDIA_TESLA_T4',
    accelerator_count = 1,
    machine_type = 'n1-standard-4'
)
```

Define the same examples from the tutorial above:
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

Request predictions for the examples:
```python
# test endpoint with examples
endpoint.predict(instances = examples).predictions
```

Compare to the result from the tutorial above and note that they are the same since they are served from the same model that has been relocated and deployed in Vertex AI Prediction Endpoints.

### BigQuery ML Remote Model

Creating a BigQuery ML Remote Model has two components: a [BigQuery Cloud Resource Connection](https://cloud.google.com/bigquery/docs/create-cloud-resource-connection) and a BigQuery Remote Model that uses the connection.

#### Step 1: Create a BigQuery Cloud Resource Connection

Create the cloud resource connection:
```python
# create BigQuery Cloud Resource Connection
!bq mk --connection --location={REGION[0:2]} --project_id={PROJECT_ID} --connection_type=CLOUD_RESOURCE {SERIES}_{EXPERIMENT}
```

Retrieve the service account associated with the cloud resource connection:
```python
# retrieve the service account for the BigQuery Cloud Resource Connection
import json

bqml_connection = !bq show --format prettyjson --connection {PROJECT_ID}.{REGION[0:2]}.{SERIES}_{EXPERIMENT}
bqml_connection = json.loads(''.join(bqml_connection[[r for r, row in enumerate(bqml_connection) if row == '{'][0]:]))
service_account = bqml_connection['cloudResource']['serviceAccountId']
service_account
```

Assign the service account [Vertex AI user role](https://cloud.google.com/vertex-ai/docs/general/access-control#aiplatform.user):
```python
# assign vertex ai user role to the service account of the BigQuery Cloud Resource Connection
!gcloud projects add-iam-policy-binding {PROJECT_ID} --member=serviceAccount:{service_account} --role=roles/aiplatform.user
```

#### Step 2: Create a BigQuery Dataset and Remote Model

Import and initialize a BigQuery Client:
```python
# BigQuery Client
from google.cloud import bigquery
bq = bigquery.Client(project = PROJECT_ID)
```

Create a BigQuery Dataset:
```python
# Create A BigQuery Dataset
query = f"""
CREATE SCHEMA IF NOT EXISTS `{PROJECT_ID}.{SERIES}`
    OPTIONS(location = '{REGION[0:2]}')
"""
job = bq.query(query = query)
job.result()
job.state
```

To see the input and output specification for the TensorFlow model use the [SavedModel CLI](https://www.tensorflow.org/guide/saved_model#details_of_the_savedmodel_command_line_interface):
```python
# Inspect model inputs and outpus with SavedModel CLI
!saved_model_cli show --dir {model.uri} --all
```

Create Model Using Remote Connection
```python
# Create Remote Model In BigQuery
query = f"""
CREATE OR REPLACE MODEL `{PROJECT_ID}.{SERIES}.{EXPERIMENT.replace('-', '_')}`
    INPUT (text STRING)
    OUTPUT(classifier ARRAY<FLOAT64>)
    REMOTE WITH CONNECTION `{PROJECT_ID}.{REGION[0:2]}.{SERIES}_{EXPERIMENT}`
    OPTIONS(endpoint = 'https://{REGION}-aiplatform.googleapis.com/v1/{endpoint.resource_name}')
"""
job = bq.query(query = query)
job.result()
job.state
```

#### Step 3: Get Predictions with BigQuery ML.PREDICT

Get predictions from the remote model within BigQuery using the `ML.PREDICT` function.  This sends records from the query statment to the remote model for serving prediction back to BigQuery as a single function call.

```python
query = f"""
SELECT *
FROM ML.PREDICT (
    MODEL `{PROJECT_ID}.{SERIES}.{EXPERIMENT.replace('-', '_')}`,
    (
        SELECT review as text
        FROM `bigquery-public-data.imdb.reviews`
        LIMIT 10
    )
)
"""
bq.query(query = query).to_dataframe()
```


Use the remote model to server a large batch of prediction.  Here 10k records are selected and sent for prediction.  The remote model defaults to a batch size of 128 instances for its requests.
```python
query = f"""
SELECT *
FROM ML.PREDICT (
    MODEL `{PROJECT_ID}.{SERIES}.{EXPERIMENT.replace('-', '_')}`,
    (
        SELECT review as text
        FROM `bigquery-public-data.imdb.reviews`
        LIMIT 10000
    )
)
"""
job = bq.query(query = query)
job.result()
print(job.state, f'in {(job.ended-job.started).seconds/60} minutes')
```

### Clean Up

To avoid incurring ongoing charges to your Google Cloud account for the resoruces used in this tutorial, either delete the project that contains the resources, or keep the project and delete the individual resources.

```python
# remove Vertex AI Prediction Endpoint
endpoint.delete(force = True)

# remove model in Vertex AI Model Registry
model.delete()

# remove model files in GCS
#!gsutil rm -r gs://{PROJECT_ID}/{SERIES}/{EXPERIMENT}

# remove BigQuery Dataset (holds model definition)
#!bq rm -r -f -d {PROJECT_ID}.{SERIES}

# remove BigQuery Cloud Resource Connection
!bq rm --connection {PROJECT_ID}.{REGION[0:2]}.{SERIES}_{EXPERIMENT}
```
