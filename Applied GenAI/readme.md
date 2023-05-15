![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2FApplied+GenAI&dt=readme.md)

# /Applied GenAI/readme.md

This series of notebooks highlights the use over Vertex AI Generative AI for workflows that include using Google's large generative AI models.  Read more about these exciting new features of Vertex AI [here](https://cloud.google.com/vertex-ai/docs/generative-ai/learn/overview).

---
**Install**

The Vertex AI [Python Client](https://cloud.google.com/python/docs/reference/aiplatform/latest) will need to be updated to at least the 1.25.0 release.

```Python
!pip install google.cloud.aiplatform -U -q --user
```

If you installed a `.whl` directly during the early preview then you might need to also use the `--force-reinstall` tag.  You can check the version to make sure it is >1.25.0 or higher with:

```Python
import google.cloud.aiplatform as aiplatform
aiplatform.__version__
```

**Authorization**

If you are in a Vertex AI Workbench instance then you are already authenticated to a GCP project.  You can retrive the current project into a variable using:

```Python
project = !gcloud config get-value project
PROJECT_ID = project[0]
PROJECT_ID
```

If you need to first authenticate to your GCP project from a Colab, use the following:

```Python
from google.colab import auth

auth.authenticate_user()
!gcloud config set project {PROJECT_ID}
```

**Setup**

```Python
PROJECT_ID = 'your project here'
REGION = 'us-central1'

import vertexai.preview.language_models

vertexai.init(project = PROJECT_ID, location = REGION)


```

**Use**

Example for a text generation request with a specific model - [reference](https://cloud.google.com/python/docs/reference/aiplatform/latest/vertexai.preview.language_models.TextGenerationModel):

```Python
textgen_model = vertexai.preview.language_models.TextGenerationModel.from_pretrained('text-bison@001')

textgen_model.predict('What are the rules of baseball?')
```

>Baseball is a bat-and-ball game played between two teams of nine players on a field in the shape of a diamond. The game is played with a hard, round ball and a bat. The object of the game is for a team to score more runs than the opposing team.
>
>A run is scored when a player advances around all four bases in the correct order. The bases are located at first, second, third, and home plate. A player can advance to the next base by hitting the ball and running, or by being walked or hit by a pitch.

---
## Notebooks:

**Prerequisites**

These notebook include direct installs of several supporting packages.  

**Document Q&A Examples**:

Ask complex scenario based questions and get text generated answers with references to relative sections of the documents.
- [Vertex AI GenAI For Document Q&A - MLB Rules](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20-%20MLB%20Rules.ipynb)
    - This parses a PDF document from GCS or URL
    - gets embeddings for the elements
    - creates a local vector search function with ScaNN
    - creates a function to generate Generative AI prompts with document contexts retrieved by vector search of the question (embedding) and the documents elements
    - Saves the document parsing and embeddings to GCS and/or BigQuery for retrieval on future runs - saves repeat cost and time
- [Vertex AI Matching Engine For Document Q&A](./Vertex%20AI%20Matching%20Engine%20For%20Document%20Q&A.ipynb)
- coming soon - Use Vertex AI Matching Engine for stateful, low latency, vector searches
    - Use Vertex AI Matchng Engine to Create and Deploy an index
    - Perform online queries with hosted index
    - Recreate the document bot from [Vertex AI GenAI For Document Q&A - MLB Rules](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20-%20MLB%20Rules.ipynb) using online queries
- coming soon - A Cloud Function for running our document bot

## More Resources
- Examples for Prompt Design and Tuning of Foundational Models: [github.com/GoogleCloudPlatform/generative-ai](https://github.com/GoogleCloudPlatform/generative-ai)