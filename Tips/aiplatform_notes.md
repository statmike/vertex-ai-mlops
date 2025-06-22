![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FTips&file=aiplatform_notes.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Tips/aiplatform_notes.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Tips/aiplatform_notes.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Tips/aiplatform_notes.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Tips/aiplatform_notes.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https%3A//github.com/statmike/vertex-ai-mlops/blob/main/Tips/aiplatform_notes.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
</table><br/><br/>

---
## Interacting with Vertex AI
Many Vertex AI resources can be viewed and monitored directly in the [GCP Console](https://console.cloud.google.com/vertex-ai).  Vertex AI resources are primarily created, and modified with the [Vertex AI API](https://cloud.google.com/vertex-ai/docs/reference).  

Also see [Introduction to the Vertex AI SDK for Python](https://cloud.google.com/vertex-ai/docs/python-sdk/use-vertex-ai-python-sdk).

The API is accessible from:
- the command line with [`gcloud ai`](https://cloud.google.com/sdk/gcloud/reference/ai), 
- [REST](https://cloud.google.com/vertex-ai/docs/reference/rest),
- [gRPC](https://cloud.google.com/vertex-ai/docs/reference/rpc), 
- or the [client libraries](https://cloud.google.com/vertex-ai/docs/start/client-libraries) (built on top of gRPC) for
    - [Python](https://cloud.google.com/python/docs/reference/aiplatform/latest), 
    - [Java](https://cloud.google.com/java/docs/reference/google-cloud-aiplatform/latest/overview), and 
    - [Node.js](https://cloud.google.com/nodejs/docs/reference/aiplatform/latest).  

There are [levels](https://cloud.google.com/vertex-ai/docs/start/client-libraries#client_libraries):
- high-level `aiplatform` - referred to as Vertex AI SDK
    - The Vertex AI SDK, publically available features. Easiest to use, concise, and designed to simplify common tasks in workflows.
- low-level `aiplatform.gapic` - referred to as Vertex AI client library
    - auto-generated from Google's sevice proto files.  GAPIC stands for Google API CodeGen.

There are [versions](https://cloud.google.com/vertex-ai/docs/reference#versions) for `aiplatform.gapic`: 
- `aiplatform_v1`: stable,
    - all the production features of the platform
- `aiplatform_v1beta1`: latest preview features.
    - includes additional features of the platform in beta phase

**Python**

The [Google Cloud Python Client](https://github.com/googleapis/google-cloud-python) has a library for Vertex AI called [aiplatform](https://github.com/googleapis/python-aiplatform) which is called the Vertex AI SDK for Python.
- All [Python Cloud Client Libraries](https://cloud.google.com/python/docs/reference)
    - Vertex AI: [google-cloud-aiplatform](https://cloud.google.com/python/docs/reference/aiplatform/latest)
        - Package: [`aiplatform` package](https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform)
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