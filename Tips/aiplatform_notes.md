## Interacting with Vertex AI
Many Vertex AI resources can be viewed and monitored directly in the [GCP Console](https://console.cloud.google.com/vertex-ai).  Vertex AI resources are primarily created, and modified with the [Vertex AI API](https://cloud.google.com/vertex-ai/docs/reference).  

The API is accessible from:
- the command line with [`gcloud ai`](https://cloud.google.com/sdk/gcloud/reference/ai), 
- [REST](https://cloud.google.com/vertex-ai/docs/reference/rest),
- [gRPC](https://cloud.google.com/vertex-ai/docs/reference/rpc), 
- or the [client libraries](https://cloud.google.com/vertex-ai/docs/start/client-libraries) (built on top of gRPC) for
    - [Python](https://cloud.google.com/python/docs/reference/aiplatform/latest), 
    - [Java](https://cloud.google.com/java/docs/reference/google-cloud-aiplatform/latest/overview), and 
    - [Node.js](https://cloud.google.com/nodejs/docs/reference/aiplatform/latest).  

There are [levels](https://cloud.google.com/vertex-ai/docs/start/client-libraries#client_libraries):
- high-level `aiplatform`
    - The Vertex AI SDK, publically available features. Easiest to use, concise, and designed to simplify common tasks in workflows.
- low-level `aiplatform.gapic`
    - auto-generated from Google's sevice proto files.  GAPIC stands for Google API CodeGen.

There are [versions](https://cloud.google.com/vertex-ai/docs/reference#versions) for `aiplatform.gapic`: 
- `aiplatform_v1`: stable,
    - all the production features of the platform
- `aiplatform_v1beta1`: latest preview features.
    - includes additional features of the platform in beta phase

**Python**

The [Google Cloud Python Client](https://github.com/googleapis/google-cloud-python) has a library for Vertex AI called [aiplatform](https://github.com/googleapis/python-aiplatform) which is called the Vertex AI SDK for Python.
- [Python Cloud Client Libraries](https://cloud.google.com/python/docs/reference)
    - [google-cloud-aiplatform](https://cloud.google.com/python/docs/reference/aiplatform/latest)
        - [`aiplatform` package](https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform)
- Another helpful version of the Vertex AI SDK for Python documentation can be [found here](https://googleapis.dev/python/aiplatform/latest/index.html#)
- Also helpful: [Getting started with Python](https://cloud.google.com/python/docs/getting-started) in Google Cloud


The notebooks in this repository primarily use the Python client `aiplatform`.  There is occasional use of `aiplatform.gapic`,  `aiplatform_v1` and `aiplatform_v1beta1`.

**Install the Vertex AI Python Client**
```python
pip install google-cloud-aiplatform
```

**Example of All Client Versions/Layers with Python Client**

This example shows the process of listing all models for a Vertex AI Model Registry in a project in a region:
```python
PROJECT = 'statmike-mlops-349915'
REGION = 'us-central1'

# List all models for project in region with: aiplatform
from google.cloud import aiplatform
aiplatform.init(project = PROJECT, location = REGION)
model_list = aiplatform.Model.list()

# List all models for project in region with: aiplatform.gapic
from google.cloud import aiplatform
model_client_gapic = aiplatform.gapic.ModelServiceClient(client_options = {"api_endpoint": f"{REGION}-aiplatform.googleapis.com"})
model_list = list(model_client_gapic.list_models(parent = f'projects/{PROJECT}/locations/{REGION}'))

# List all models for project in region with: aiplatform_v1
from google.cloud import aiplatform_v1
model_client_v1 = aiplatform_v1.ModelServiceClient(client_options = {"api_endpoint": f"{REGION}-aiplatform.googleapis.com"})
model_list = list(model_client_v1.list_models(parent = f'projects/{PROJECT}/locations/{REGION}'))

# List all models for project in region with: aiplatform_v1beta1
from google.cloud import aiplatform_v1beta1
model_client_v1beta1 = aiplatform_v1beta1.ModelServiceClient(client_options = {"api_endpoint": f"{REGION}-aiplatform.googleapis.com"})
model_list = list(model_client_v1beta1.list_models(parent = f'projects/{PROJECT}/locations/{REGION}'))
```