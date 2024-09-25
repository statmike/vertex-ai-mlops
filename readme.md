![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main//readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Vertex AI for Machine Learning Operations

>**2024 UPDATE:**  This repository is evolving from end-to-end workflows for various frameworks into an MLOps focused approach for development of predictive and generative AI operations.  The new approach is being developed in the [MLOps](./MLOps/readme.md) folder.  Once it nears completion, the content in this repository will be rearranged into the following structure:
>- MLOps
>    - Pipelines
>    - Experiments
>    - Feature Store
>    - Model Monitoring
>    - ...
>- Applied Examples
>    - Forecasting
>    - GenAI
>    - ...
>- Framework Workflows
>    - BigQuery ML
>    - TensorFlow
>    - scikit-learn
>    - ...
> - ...







---
> This is the original readme from prior to the shift in this repository.  After the content rearrangement is complete and this information is incorporate above it will be removed.  

## 👋 I'm Mike

I want to share and enable [Vertex AI](https://cloud.google.com/vertex-ai/docs/start/introduction-unified-platform) from [Google Cloud](https://cloud.google.com/vertex-ai) with you.  The goal here is to share a comprehensive set of end-to-end workflows for machine learning that each cover the range of data to model to serving and managing - even automating the flow.  Regardless of your data type, skill level or framework preferences you will find something helpful here.  You can even ask for what you need and I might be able to work it into updates! 

<p align="center" width="100%"><center>
    <a href="https://youtu.be/snUEwsft1wY" target="_blank" rel="noopener noreferrer">
      <kbd><img width="50%" src="architectures/thumbnails/playbutton/readme.png"></kbd>
    </a>
</center></p>
<p align="center">Click to watch on YouTube</p>
<p align="center">Click <a href="https://youtube.com/playlist?list=PLgxF613RsGoUuEjJJxJW2JYyZ8g1qOUou" target="_blank" rel="noopener noreferrer">here</a> to see current playlist for this repository</p>

---
## Tracking

To better understand which content is most helpful to users, this repository uses tracking pixels in each markdown (`.md`) and notebook (`.ipynb`) file.  **No user or location data is collected.**  The only information captured is that the content was rendered/viewed which gives us a daily count of usage.  Please share any concerns you have with this in [repositories discussion board](https://github.com/statmike/vertex-ai-mlops/discussions) and I am happy to also provide a branch without the tracking.  

A script is provided to remove this tracking from your local copy of this repository in the file `pixel_remove.py` in the folder [pixel](./architectures/tracking/setup/pixel/readme.md).  This readme also has the complete code for creating the tracking in case you want to use replicate it or just understand it in greater detail.

---
## Approach Used In This Repository

This repository is presented as workflows using, primarily, interactive python notebooks `.ipynb`.  Why?  These are easy to review, share, and move.  They contain elements for both code and narrative. The narrative can be written with plain text, Markdown and/or HTML which makes providing visual explanations easy.  This reinforces the goal of this repository: information that is easily accessible, portable, and great for starting points in your own work.

In notebooks, execution is driven from the locally attached compute.  In this repository that means the Python code is currently running in the notebooks compute.  The code in this repository heavily leans on orchestrating services in GCP rather than doing data compute in the local environment to the notebook.  That means these notebooks are designed to run on minimal machine sizes, like `n1-standard2` even.  The heavy work of training and serving is done on Vertex AI, BigQuery, and other Google Cloud services.  You will even find notebooks that author code, and then deploy the code in services like Vertex AI Custon Training and Vertex AI Pipelines.  

There are sections that use other languages, like R, as well as creating files that are external to the notebooks: `dockerfile`, `.py` scripts and modules, etc.

The code in this repository is opinionated.  It is not completely production ready as well as not simply ad-hoc exploration.  It aims to the right of the continum of exploration to deployment: 'hello-world' to CI/CD/CT.  In our data science daily work we might think of the process as:

<p align="center" width="100%"><center>
    <img src="./architectures/architectures/images/readme/code_progression.png">
</center></p>

In **explore**, everything is code as you go.  At some point in this exploration ideas find value and need to be developed.

In **develop**, the approach is usually something like:
- make it work
    - get a working end to end flow
- clean it up
    - revisit the code and remove parts that are no longer needed and reorder based on what is learned
- generalize it
    - parameterize
    - use functions
    - control flow: start using logic to check for out of bound conditions
- optimize it
    - better use of data structures to handle data usage during execution
    - consider execution timing and optimize for the simoultaneous goal of readability (= maintainability) and compute time

In many cases, getting from development to **deployment** is simple:
- schedule a notebook - a lot like skipping the **develop** stage
- deploy a pipeline
- create a cloud function

But, inevitably, as a workflow proves value it requires more effort before you **deploy**:
- error handling
- unit testing
- move from specialized code to generalized code: 
    - use classes
    - control environment handling

So where does the code in the repository fall? In the late **develop** phase with strong readability and adaptibility.

<p align="center" width="100%"><center>
    <img src="./architectures/architectures/images/readme/code_progression_star.png">
</center></p>

---
## Table of Contents
- [Considerations](#considerations)
- [Overview](#overview)
- [Vertex AI](#vertex)
- [Interacting With Vertex AI](#vertexsdk)
- [Setup](#setup)
- [Helpful Sections](#helpful)
- [More Resources](#resources)

---
<a id = 'considerations'></a>
## Considerations

### Data Type

-  Tables: Tabular, structured data in rows and columns
-  Language: Text for translation and/or understanding
-  Vision: Images
-  Video

### Convenience Level

-  Use Pre-Trained APIs
-  Automate building Custom Models
-  End-to-end Custom ML with core tools in the framework of your choice

### Framework Preferences

-  [Scikit-learn](https://scikit-learn.org/stable/index.html)
-  [XGBoost](https://xgboost.readthedocs.io/en/latest/)
-  [Tensorflow](https://www.tensorflow.org/)
-  [Pytorch](https://pytorch.org/)
-  [Spark MLlib](https://spark.apache.org/docs/latest/ml-guide.html)
-  [R](https://www.r-project.org/)
-  [Julia](https://julialang.org/)
-  More!

---
<a id = 'overview'></a>
## Overview

This is a series of workflow demonstrations that use the same data source to build and deploy the same machine learning model with different frameworks and automation.  These are meant to help get started in understanding and learning Vertex AI and provide starting points for new projects.  

The demonstrations focus on workflows and don't delve into the specifics of ML frameworks other than how to integrate and automate with Vertex AI. Let me know if you have ideas for more workflows or details to include!

To understand the contents of this repository, the following charts uncover the groupings of the content.

| Direction |
:-------------------------:
![](./architectures/architectures/images/readme/decision_training.png)

### Pre-Trained APIs
<table style='text-align:center;vertical-align:middle' width="100%" cellpadding="1" cellspacing="0">
    <tr>
        <th colspan='4'>Pre-Trained Models</th>
        <th rowspan='2'>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl/v1/32px.svg">
            <a href="https://cloud.google.com/vertex-ai/docs/beginner/beginners-guide" target="_blank">AutoML</a>
        </th>
    </tr>
    <tr>
        <th>Data Type</th>
        <th>Pre-Trained Model</th>
        <th>Prediction Types</th>
        <th>Related Solutions</th>
    </tr>
    <tr>
        <td rowspan='2'>
            <img src="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/text_snippet/default/40px.svg">
            <br>Text
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/cloud_translation_api/v1/32px.svg">
            <br><a href="https://cloud.google.com/translate/docs/overview" target="_blank">Cloud Translation API</a>
        </td>
        <td>Detect, Translate</td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/text-to-speech/v1/32px.svg">
            <br><a href="https://cloud.google.com/text-to-speech/docs/basics" target="_blank">Cloud Text-to-Speech</a>
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl_translation/v1/32px.svg">
            <br><a href="https://cloud.google.com/translate/automl/docs" target="_blank">AutoML Translation</a>
        </td>
    </tr>
            <tr>
                <td>
                   <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/cloud_natural_language_api/v1/32px.svg">
                   <br><a href="https://cloud.google.com/natural-language/docs/quickstarts" target="_blank">Cloud Natural Language API</a>
                </td>
                <td>
                    Entities (Identify and label), Sentiment, Entity Sentiment, Syntax, Content Classification
                </td>
                <td>
                    <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/healthcare_nlp_api/v1/32px.svg">
                    <br><a href="https://cloud.google.com/healthcare-api/docs/how-tos/nlp" target="_blank">Healthceare Natural Language API</a>
                </td>
                <td>
                    <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl_natural_language/v1/32px.svg">
                    <br><a href="https://cloud.google.com/vertex-ai/docs/training-overview#text_data" target="_blank">AutoML Text</a>
            </tr>
    <tr>
        <td>
            <img src="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/image/default/40px.svg">
            <br>Image
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/cloud_vision_api/v1/32px.svg">
            <br><a href="https://cloud.google.com/vision/docs/features-list" target="_blank">Cloud Vision API</a>
        </td>
        <td>
            Crop Hint, OCR, Face Detect, Image Properties, Label Detect, Landmark Detect, Logo Detect, Object Localization, Safe Search, Web Detect
        </td>
        <td>
            <table>
                <tr>
                    <td>
                        <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/document_ai/v1/32px.svg">
                        <br><a href="https://cloud.google.com/document-ai/docs/processors-list" target="_blank">Document AI</a>
                    </td>
                    <td>
                        <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/visual_inspection/v1/32px.svg">
                        <br><a href="" taget="_blank">Visual Inspection AI</a>
                    </td>
                </tr>
            </table>
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl_vision/v1/32px.svg">
            <br><a href="https://cloud.google.com/vertex-ai/docs/training-overview#image_data" target="_blank">AutoML Image</a>
        </td>
    </tr>
    <tr>
        <td>
            <img src="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/mic/default/40px.svg">
            <br>Audio
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/media_translation_api/v1/32px.svg">
            <br><a href="https://cloud.google.com/media-translation" target="_blank">Cloud Media Translation API</a>
        </td>
        <td>Real-time speech translation</td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/speech-to-text/v1/32px.svg">
            <br><a href="https://cloud.google.com/speech-to-text/docs/basics" target="_blank">Cloud Speech-to-Text</a>
        </td>
        <td></td>
    </tr>
    <tr>
        <td>
            <img src="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/videocam/default/40px.svg">
            <br>Video
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/video_intelligence_api/v1/32px.svg">
            <br><a href="https://cloud.google.com/video-intelligence/docs/quickstarts" target="_blank">Cloud Video Intelligence API</a>
        </td>
        <td>
            Label Detect*, Shot Detect*, Explicit Content Detect*, Speech Transcription, Object Tracking*, Text Detect, Logo Detect, Face Detect, Person Detect, Celebrity Recognition
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/cloud_vision_api/v1/32px.svg">
            <br><a href="https://cloud.google.com/vision-ai/docs/overview" target="_blank">Vertex AI Vision</a>
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl_video_intelligence/v1/32px.svg">
            <br><a href="https://cloud.google.com/vertex-ai/docs/training-overview#video_data" target="_blank">AutoML Video</a>
        </td>
    </tr>
</table>


### AutoML
<table style='text-align:center;vertical-align:middle' width="100%" cellpadding="1" cellspacing="0">
    <tr>
        <th colspan='3'>AutoML</th>
    </tr>
    <tr>
        <th>Data Type</th>
        <th>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl/v1/32px.svg">
            <br><a href="https://cloud.google.com/vertex-ai/docs/beginner/beginners-guide" target="_blank">AutoML</a>
        </th>
        <th>Prediction Types</th>
    </tr>
    <tr>
        <td>
            <img src="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/table/default/40px.svg">
            <br>Table
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl_tables/v1/32px.svg">
            <br><a href="https://cloud.google.com/vertex-ai/docs/training-overview#tabular_data" target="_blank">AutoML Tables</a>
        </td>
        <td>
            <dl>
                <dt>Classification</dt>
                    <dd>Binary</dd>
                    <dd>Multi-class</dd>
                <dt>Regression</dt>
                <dt>Forecasting</dt>
            </dl>
        </td>
    </tr>
    <tr>
        <td>
            <img src="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/image/default/40px.svg">
            <br>Image
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl_vision/v1/32px.svg">
            <br><a href="https://cloud.google.com/vertex-ai/docs/training-overview#image_data" target="_blank">AutoML Image</a>
        </td>
        <td>
            <dl>
                <dt>Classification</dt>
                    <dd>Single-label</dd>
                    <dd>Multi-label</dd>
                <dt>Object Detection</dt>
            </dl>
        </td>
    </tr>
    <tr>
        <td>
            <img src="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/videocam/default/40px.svg">
            <br>Video
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl_video_intelligence/v1/32px.svg">
            <br><a href="https://cloud.google.com/vertex-ai/docs/training-overview#video_data" target="_blank">AutoML Video</a>
        </td>
        <td>
            <dl>
                <dt>Classification</dt>
                <dt>Object Detection</dt>
                <dt>Action Recognition</dt>
            </dl>
        </td>
    </tr>
    <tr>
        <td>
            <img src="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/text_snippet/default/40px.svg">
            <br>Text
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl_natural_language/v1/32px.svg">
            <br><a href="https://cloud.google.com/vertex-ai/docs/training-overview#text_data" target="_blank">AutoML Text</a>
        </td>
        <td>
            <dl>
                <dt>Classification</dt>
                    <dd>Single-label</dd>
                    <dd>Multi-label</dd>
                <dt>Entity Extraction</dt>
                <dt>Sentiment Analysis</dt>
            </dl>
        </td>
    </tr>
    <tr>
        <td>
            <img src="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/text_snippet/default/40px.svg">
            <br>Text
        </td>
        <td>
            <img src="https://fonts.gstatic.com/s/i/gcpiconscolors/automl_translation/v1/32px.svg">
            <br><a href="https://cloud.google.com/translate/automl/docs" target="_blank">AutoML Translation</a>
        </td>
        <td>
            Translation
        </td>
    </tr>
</table>

### With Training Data

This work focuses on cases where you have training data:

| Overview |
:-------------------------:
![](./architectures/overview/high_level.png)

|AutoML|BigQuery ML|Vertex AI| Forecasting with AutoML, BigQuery ML, OSS Prophet |
:---:|:---:|:---:|:---:
![](./architectures/overview/02_overview.png)|![](./architectures/overview/03_overview.png)|![](./architectures/overview/05_overview.png)|![](./architectures/overview/forecasting_overview.png)

### Vertex AI For ML Training

<p align="center" width="100%">
    <img src="./architectures/overview/training.png" width="45%">
    &nbsp; &nbsp; &nbsp; &nbsp;
    <img src="./architectures/overview/training2.png" width="45%">
</p>

---
<a id = 'vertex'></a>
## Vetex AI

Vetex AI is a platform for end-to-end model development.  It consist of core components that make the processes of MLOps possible for design patterns of all types.

<p align="center">
  <img alt="Components" src="architectures/slides/readme_arch.png" width="45%">
&nbsp; &nbsp; &nbsp; &nbsp;
  <img alt="Console" src="architectures/slides/readme_console.png" width="45%">
</p>

---
<a id = 'vertexsdk'></a>
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

The notebooks in this repository primarily use the Python client `aiplatform`.  There is occasional use of `aiplatform.gapic`,  `aiplatform_v1` and `aiplatform_v1beta1`.

For the full details on the APIs versions and layers and how/when to use each, [see this helpful note](./Tips/aiplatform_notes.md).

**Install the Vertex AI Python Client**
```python
pip install google-cloud-aiplatform
```

**Example Usage: Listing all Models in Vertex AI Model Registry**
```python
PROJECT = 'statmike-mlops-349915'
REGION = 'us-central1'

# List all models for project in region with: aiplatform
from google.cloud import aiplatform
aiplatform.init(project = PROJECT, location = REGION)

model_list = aiplatform.Model.list()
```

---
<a id = 'setup'></a>
## Setup

The demonstrations are presented in a series of notebooks that are best run in JupyterLab. These can be reviewed directly in [this repository on GitHub](https://github.com/statmike/vertex-ai-mlops) or cloned to your Jupyter instance on [Vertex AI Workbench Instances](https://cloud.google.com/vertex-ai/docs/workbench/instances/introduction).

### Option 1: Review And Use Individual Files

Select the files and review them directly in the browser or IDE of your choice.  This can be helpful for general understanding and selecting sections to copy/paste to your project.  Some options to get a local copy of this repositories content:
- use git: `git clone https://github.com/statmike/vertex-ai-mlops`
- use `wget` to copy individual files directly from GitHub:
    - Go to the notebook on GitHub.com and right-click the download link. Then select copy link address.
    - Alternatively, click the Raw button on GitHub and then copy the URL that loads.
    - Run the following from a notebook cell or directly from a terminal (without the !). Note the slightly different address that points directly to raw content on GitHub.
        - `!wget "https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/<path and filename>.ipynb"`
- Use [Colab](https://colab.research.google.com/) (and soon [Vetex AI Enterprise Colab](https://cloud.google.com/vertex-ai/docs/colab/create-console-quickstart)) to open the notebooks. Many of the notebooks have section at the top with buttons for opening directly in Colab.  Some notebooks don't yet have this feature and some use local Docker which is not available on Colab.  

### Option 2: Run These Notebooks in a Vertex AI Workbench based Notebook 

TL;DR
> In Google Cloud Console, Select/Create a Project then go to Vertex AI > Workbench > Instances
> - Create a new notebook and Open JupyterLab
> - Clone this repository using Git Menu, Open and run `00 - Environment Setup.ipynb`

1. Create a Project
   1. [Link](https://console.cloud.google.com/cloud-resource-manager), Alternatively, go to: Console > IAM & Admin > Manage Resources
   1. Click "+ Create Project"
   1. Provide: name, billing account, organization, location
   1. Click "Create"
1. Enable the APIs: Vertex AI API and Notebooks API
   1. [Link](https://console.cloud.google.com/flows/enableapi?apiid=aiplatform.googleapis.com,notebooks.googleapis.com)
      1. Alternatively, go to: 
         1. Console > Vertex AI, then enable API
         1. Then Console > Vertex AI > Workbench, then enable API
1. Create A Notebook with [Vertex AI Workbench Instances](https://cloud.google.com/vertex-ai/docs/workbench/instances/introduction):
    1. Go to: Console > Vertex AI > Workbench > Instances - [direct link](https://console.cloud.google.com/vertex-ai/workbench/instances)
    1. Create a new instance - [instructions](https://cloud.google.com/vertex-ai/docs/workbench/instances/create)    
    1. Once it is started, click the `Open JupyterLab` link.
    1. Clone this repository to the JupyterLab instance:
        1. Either:
            1. Go to the `Git` menu and choose `Clone a Repository`
            1. Choose the Git icon on the left toolbar and click `Clone a Repository`
        1. Provide the Clone URI of this repository: [https://github.com/statmike/vertex-ai-mlops.git](https://github.com/statmike/vertex-ai-mlops.git)
        1. In the File Browser you will now have the folder "vertex-ai-mlops" that contains the files from this repository
1. Setup the Notebook Environment for these workflows
   1. Open the notebook vertex-ai-mlops/00 - Environment Setup
   1. Follow the instructions and run the cells

Resources on these items:
- [Google Cloud Projects](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
- [Vertex AI environment](https://cloud.google.com/vertex-ai/docs/start/cloud-environment)
- [Introduction to Vertex AI Workbench](https://cloud.google.com/vertex-ai/docs/workbench/introduction)
- [Create a Vetex AI Workbench Instance](https://cloud.google.com/vertex-ai/docs/workbench/instances/create-console-quickstart)

---
<a id = 'helpful'></a>
## Helpful Sections
- [Learning Machine Learning](./Learn%20ML/readme.md)
    - I often get asked "How do I learn about ML?".  There are lots of good answers. ....
- [Explorations](./Explorations/readme.md)
    - This is a series of projects for exploring new, new-to-me, and emerging tools in the ML world!
- [Tips](./Tips/readme.md)
    - Tips for using the repository and notebooks with examples of core skills like building containers, parameterizing jobs and interacting with other GCP services. These tips help with scaling jobs and developing them with a focus on CI/CD.

---
<a id = 'resources'></a>
## More Resources Like This Repository

This is my personal repository of demonstrations I use for learning and sharing Vertex AI.  There are many more resources available.  Within each notebook I have included a resources section and a related training section. 

- GitHub [Many Examples For Real World Scenarios!](https://github.com/jchavezar/vertex-ai-samples) by [@jcavezar](https://github.com/jchavezar)
- GitHub [GoogleCloudPlatform/vertex-ai-samples](https://github.com/GoogleCloudPlatform/vertex-ai-samples)
- GitHub [GoogleCloudPlatform/mlops-with-vertex-ai](https://github.com/GoogleCloudPlatform/mlops-with-vertex-ai)
- [Overview of Data Science on Google Cloud](https://cloud.google.com/data-science)


