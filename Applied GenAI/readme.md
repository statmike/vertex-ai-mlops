![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2FApplied+GenAI&dt=readme.md)

# /Applied GenAI/readme.md

This series of notebooks highlights the use over Vertex AI Generative AI for workflows that include using Google's foundational large generative AI models.  These dont't need to be trained or hosted - just called with via API.  Read more about these exciting new features of Vertex AI [here](https://cloud.google.com/vertex-ai/docs/generative-ai/learn/overview).

**More Resources**

- Examples for Prompt Design and Tuning of Foundational Models: [github.com/GoogleCloudPlatform/generative-ai](https://github.com/GoogleCloudPlatform/generative-ai)
- [Enterprise Search](https://cloud.google.com/enterprise-search) on Generative AI App Builder

---
## Getting Started

This section cover the basics for getting started with the Python Client. 

>For a complete getting started overview of all the foundation models in use along with tips for managing asynchronous and streaming request as well as handling all requests within quota please check out this notebook:
>- [Getting Started - Vertex AI GenAI Python Client](Getting%20Started%20-%20Vertex%20AI%20GenAI%20Python%20Client.ipynb)

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

import vertexai.language_models

vertexai.init(project = PROJECT_ID, location = REGION)
```

**Use**

Example for a text generation request with a specific model - [reference](https://cloud.google.com/python/docs/reference/aiplatform/latest/vertexai.language_models.TextGenerationModel):

```Python
textgen_model = vertexai.language_models.TextGenerationModel.from_pretrained('text-bison@001')

prediction = textgen_model.predict('What are the rules of baseball?')

predition.text
```

>Baseball is a bat-and-ball game played between two teams of nine players on a field in the shape of a diamond. The game is played with a hard, round ball and a bat. The object of the game is for a team to score more runs than the opposing team.
>
>A run is scored when a player advances around all four bases in the correct order. The bases are located at first, second, third, and home plate. A player can advance to the next base by hitting the ball and running, or by being walked or hit by a pitch.

You can also look at the `safety_attibute` part of the [prediction response](https://cloud.google.com/python/docs/reference/aiplatform/latest/vertexai.language_models.TextGenerationResponse).  It is empty in this example indicating no strong association with any of the potentially sensitive topics.  [Description of attributes](https://cloud.google.com/vertex-ai/docs/generative-ai/learn/responsible-ai#safety_attribute_descriptions)

```Python
prediction.safety_attribute
```

> {}


```Python
textgen_model.predict('What are the rules of baseball?', max_output_tokens = 500)
```

>Baseball is a bat-and-ball game played between two teams of nine players on a field in the shape of a diamond. The game is played with a hard, round ball and a bat. The object of the game is for a team to score more runs than the opposing team.
>
>A run is scored when a player advances around all four bases in the correct order. The bases are located at first, second, third, and home plate. A player can advance to the next base by hitting the ball and running to the next base before the ball is thrown to the fielder covering that base.
>
>The game is played in innings. Each inning consists of two halves, with one team batting in each half. In the first half of the inning, the batting team tries to score runs by hitting the ball and running the bases. In the second half of the inning, the fielding team tries to prevent the batting team from scoring runs by throwing the ball to the bases before the runners can reach them.
>
>The game ends when one team has scored more runs than the other team. The team with the most runs at the end of the game wins.
>
>Here are some of the basic rules of baseball:
>
>* The game is played between two teams of nine players.
>* The game is played on a field in the shape of a diamond.
>* The object of the game is to score more runs than the opposing team.
>* A run is scored when a player advances around all four bases in the correct order.
>* The game is played in innings. Each inning consists of two halves, with one team batting in each half.
>* In the first half of the inning, the batting team tries to score runs by hitting the ball and running the bases.
>* In the second half of the inning, the fielding team tries to prevent the batting team from scoring runs by throwing the ball to the bases before the runners can reach them.
>* The game ends when one team has scored more runs than the other team.
>* The team with the most runs at the end of the game wins.

---
## LLMs

Large Language Models (LLMs) are models that have been trained on enormous amounts of text samples and then fine tuned for tasks like summarization, extraction, and/or classification.  Today, these fine-tuned models have emerged as generative AI, also called GenAI.  

I like to say GenAI stands for "General AI" as these models are now like opinionated bots that can do many tasks that previously required custom fit-for-purpose ML models.  Those fit-for-purpose models needed training data, labeling, and iterative training to get to the necesssary accuracy for a single task.  Now the processes has reversed a bit.  These general models can be asked, called prompting, to do the a new task and then the prompt can be iteratively adjusted to attempt achieving a desired accuracy.  This prompt iteration takes on stages:
- Adjusting prompts iteratively = Single Shot Prompt Engineering
- Informing prompts with examples = Multi-Shot Prompt Engineering
- Adaptive tuning with limited input:output sample pairs = Tuning 

>See more in [Introduction to prompt design](https://cloud.google.com/vertex-ai/docs/generative-ai/learn/introduction-prompt-design).

Before jumping into use cases it is a good idea to think about what LLMs are doing.  The prompt is followed with an output.  The LLM is generating an output based on setting that guide it through picking likely next word, then next word, then next word, then next word, ... until it has either created a response that fits or hit the limit of it's output size.

A good way to "see" this is to pick a popular passage of public domain text. Like the opening paragraph/sentence of "A Tale of Two Cites" by Charles Dickens and Harvey Dunn.  "It was the best of times, it was the worst of times, ...".  How many input/prompt words before the LLM picks the correct next word?  How many before it can fill in the remainder of the passage?  What is the input/prompt starts mid-sentence?  

Expore all of these questions interatively with the notebook:
- [Understanding LLMs](./Understanding%20LLMs.ipynb)

---
## GenAI Use Cases

**Designing Prompts**

Reference - [Overview of text prompt design](https://cloud.google.com/vertex-ai/docs/generative-ai/text/text-overview)

While using an LLM basically comes down to text input and text output, it can be helpful to understand how to frame the text input to achieve a desired output.  This is known as prompting.  Experimenting with prompting is called prompt tuning.  How the input prompt is framed can solve different types of tasks like summarization, classification and various extraction tasks (generate text, rewrite text, answer questions).  A high level overview of prompt design for these tasks is depicted below:

<p align="center" width="100%"><center>
    <img align="center" alt="Overview Chart" src="../architectures/notebooks/applied/genai/prompting.png" width="45%">
</center></p>
    
An incredibly useful task for LLMs is answering questions - the far right extraction tasks depicted above.  There are several approaches to constructing prompts for this type of tasks.  The simplest is just asking the question - single shot.  This relies on the LLMs pre-trained data to construct an answer.  LLMs can have vast knowledge of many topics but are probably are unaware of you private and/or newly created information.  

**Tuning Language Models**

Reference - [Tune language models](https://cloud.google.com/vertex-ai/docs/generative-ai/models/tune-models)

When the answers need to be tailored for format, length or tone then it can be helpful to try multi-shot prompting.  This includes examples of questions with answers in the prompt followed by the new question as a way of coercing the type of answer.  Another way to acomplish this is to create a tuned adaptor for the model that formats a single shot prompt in a way that coerces the answer based on a set of tuning examples.

>**Sidebar:**
>
>Tuning a language model does not actually change the model. Instead, it enhances the model for a specific task.  This helps the model learn to perform a task as desired from a set of examples - tuning examples.  This can be thought of as an adaptor model.  I like to think of this as a pair of glasses for an LLM.  These glasses focus the light (input text) onto the eye (the LLM input) in an alignment that optimizes on doing the task well.

**Contextual Awareness**

When the LLM needs additional information related to the question in order to answer it, the information can also be supplied in the prompt as context.  This avoids the need to customize or retrain an LLM for specific new or private information.

>**Sidebar:**
>
>When an LLM is used to generate an answer, it is drawing from the input prompt and the learned information (parameters).  I like to think of an LLM like a professional researcher.  The researcher has read many articles, books, papers and more and is very knowledgeable.  The researcher is likely very good at reading new documents as well because it has a lot of transferable skills from already vast knowledge.  When you give context to the LLM it is like giving the researcher a new article.  They are likely very good at reading and understanding this new information as long as it is similar in style, topic, and format to what they have spent its career doing (training).
>
>Extending this analogy, if the new context is too brief or off topic then the researcher likely needs to fill in the gaps and might misinterpret what you are asking.  Also, if you give too much context that veers off into other topics then the researcher may also go too far off topic when trying to answer.  This sometimes gets called hallucination but I like to think of it as the researcher getting off topic from not being well informed, guided, and focused on the topic at hand.

Prompting approaches for question answering are shown in the diagram below:
    
<p align="center" width="100%"><center>
    <img align="center" alt="Overview Chart" src="../architectures/notebooks/applied/genai/qa.png" width="45%">
</center></p>

**Retrieving Context**

Ultimately, the LLM needs contextual information about the question in order to answer it.  Rather than needing your custom or private information as part of the LLM you could supply relevant context from your library or warehouse of information along with a question so that the LLM is tasked with reading, and determining how to answer using the supplied context.  The core to this approach is retrieving the context.  The chart below shows many sources that can be used to retrieve context for the question.

<p align="center" width="100%"><center>
    <img align="center" alt="Overview Chart" src="../architectures/notebooks/applied/genai/context.png" width="45%">
</center></p>

The key is retrieving context relevant to the specific question being asked.  Not too much context, not off topic context, but specific relevant context.  A great advantage of this approach is that the LLM does not necessary need specific training or parameters to understand your private or new text because the text is being supplied in the prompt - as context to the question.

**Input/Output Sizes: Tokens**

Large language models have limit for the size of input then can receive and output they can return.  While we think of these as words, maybe even characters, the models are actually using a codified version of language where the coding process is called tokenization.  It is not as simple as a `unique_word = unique_token` because models use a data compression mechanism like [Byte-Pair Encoding (BPE)](https://en.wikipedia.org/wiki/Byte_pair_encoding).

>**Sidebar:**
>
> Languages are enormous.  Many words and many versions and variations of words.  Words are made up of characters and it turns out there are actually fewer grouping of unique characters than there are unique words.  Byte-Pair Encoding groups common/frequent sets of characters into unique encodings.  This process is a big part of mapping languages to machine learning and is a core part of the research.  Modern LLMs dont just take a "bag" of unique words, or encoded character groupings.  They also consider all the combinations of these with lengths that can be very long.  The longer the considered length the more the more semantic meaning and nuance can be learned from passages of text.

Without getting into to much detail about the mechanics of the LLMs we want to know why these token limits exists.  First, computational performance.  Handling more means needing more memory and more computational complexity.  There are models designed for larger input and/or output.  These models have architectures designed to handle longer text during their training phase.  Models are typically priced based on the input+output size so we should always try to focus the interaction with LLMs on the specific task with optimal information.  Semantic retrieval in the next section will help a lot with this!

>**Sidebar:**
>
>Input and output limits for LLMs can be described in the analogy of interacting with a researcher as we have before in this document.  The LLM is the researcher.  We can bring new information to the researcher - context in the prompt.  The researcher may limit what they are willing to consider when we ask each question - input tokens.  The researcher may also limit the response they give - output tokens.

**Token and Pricing - Control and Transparency**

LLMs hosted as API's are typically priced by a combination of the input+output and the model itself.  Large general models might cost more while smaller topical models (think code completion) are cheaper.  Models with highly focused areas of knowledge might have very special pricing - think medical or legal with specific domains covered in the pre-training data.

One mechanism to control cost is limiting the input and output size.  To control output sizes model have parameters like [`max_output_token`](https://cloud.google.com/python/docs/reference/aiplatform/latest/vertexai.language_models.TextGenerationModel#vertexai_language_models_TextGenerationModel_predict).  Input size can be controlled and to create smaller, more optimal chunks of input the technique of the next section will help - semantic retrieval.

With Vertex AI, [pricing](https://cloud.google.com/vertex-ai/pricing#generative_ai_models) for LLMs is based on the model and the character count of the input + output. This makes pricing easy and transparent.  Since the models measure input and output in tokens it can be helpful to use the `countTokens` method provided for models ([details here](https://cloud.google.com/vertex-ai/docs/generative-ai/get-token-count)).

**Semantic Retrieval**

A type of LLM is an embedding LLM which returns a vector of numbers to represent the input text, image, or combination (multimodal).  These numbers relate to the words, their order, their meaning, and their cooperation - in other words semantic meaning of the input.  These embeddings lead to an amazing general approach to identifying context for a question that can been automated without a lot of customization.

By computing the distance between embeddingins for questions and pieces of information, sometimes called chunks (think lines, paragraphs, ...), a filtered list of most relevant content can be retrieve as context.

**Examples**

The following sections link to many notebook based examples of using LLMs as described here!

---
## Summarization

Text can come in the form of audio.  This requires a conversion to text, transcription.  Google Cloud provides a Speech-To-Text API with multiple methods to handle this process depending on the needs, length of audio, and file/streaming application.  

- [Summarize Conversations - Text and Audio](./Summarize%20Conversations%20-%20Text%20and%20Audio.ipynb)
    - Start with history of a chat transcription in text
    - Continue the chat using a Chat LLM as an agent
    - Uses an LLM to Summarize the combined chat transcription with the added agent interaction
    - Converts the transcript to an audio file with multiple voices using the Text-To-Speech API
    - Converts the audio file to a conversation transcript will also recognizing the different speakers
    - Use DLP to redact person information like Names, Account numbers, and URLs.
    - Summarizes the chat transcript overall and from the perspective of each speaker
    - Use the LLM to label the speaker by their role as either "Agent" or "Customer"

---
## Notebooks For BigQuery Q&A Examples:

These notebooks use code generation LLMs to first query BigQuery to retrieve context for users questions.  Then the response is provided to text generation LLMs to answer the question.

<p align="center" width="100%"><center>
    <img align="center" alt="Overview Chart" src="../architectures/notebooks/applied/genai/bq_qa.png" width="45%">
</center></p>

- [Vertex AI GenAI For BigQuery Q&A - Overview](./Vertex%20AI%20GenAI%20For%20BigQuery%20Q&A%20-%20Overview.ipynb)

**Coming Soon! [Vertex AI Extensions](https://cloud.google.com/vertex-ai/docs/generative-ai/extensions/overview)** Simplify the process of connecting to and retrieving relevant data from sources like BigQuery!

**Extended concepts:**

Similar to the Document Q&A examples below, embedding based content retrieval can also benefit BigQuery Q&A.  

By creating embeddings for table descriptions, the question can be embedded and used to find the best matching table to use for the query.  

By creating embeddings for column descriptions, the question can be embedded and used to find the best matching columns to include in the schema supplied as context.  This allows narrowing the context down to a subset of columns rather than full tables.  The list of columns should always be checked for the inclusing of any key columns for the table and those added if not directly identified in the embedding search.  

A further enhancement is to use a text LLM along with a code LLM.  First ask the text LLM to list the steps needed to answer the question.  Then, the prompt for the code llm would include the steps retrieved from the text LLM along with the matching table and column schema retrieved.  

### Automate BigQuery Metadata With LLMs

Using LLMs to query data in BigQuery highlight the need for descriptive metadata like:
- better column names
- better table and column descriptions

This example workflow shows how to use an LLM to generate better naming and descriptions through interpretation of the content of tables. 

- [Vertex AI GenAI For BigQuery Metadata - Make Better Tables](./Vertex%20AI%20GenAI%20For%20BigQuery%20Metadata%20-%20Make%20Better%20Tables.ipynb)

---
## Working with Code as A Language

Code is a language.  A common syntax is SQL.  BigQuery runs GoogleSQL and a common question is "Is my code efficient?".

Using BigQuery and Vertex AI Codey APIs it is possible to build a BigQuery Advisory!

[Vertex AI GenAI For Rewriting - BigQuery Advisor With Codey](./Vertex%20AI%20GenAI%20For%20Rewriting%20-%20BigQuery%20Advisor%20With%20Codey.ipynb)
- Use the BigQuery Information Schema to find potentially inefficient queries.  In this case identify the queries with longest syntax as an example.
- Use BigQuery ML to directly connect to Vertex AI Generative AI APIs and get descriptions of long SQL statements
- Use Vertex AI Codey APIs to rewrite long code with a target of shorter syntax
    - The example runs on an environment that has run all the code in this GitHub repository.  It find a query with more than 7k character and shrinks it by 54% and then submits it to check that it runs successfully!

---
## Notebooks For Document Q&A Examples:

**Prerequisites**

These notebooks include direct installs of several supporting packages.  They use Vertex AI and Document AI services for processing data while also using Google Cloud Storage And Google BigQuery for data storage and retrieval.  If you are running these notebooks from Colab or another environment where your user id is authenticated then your account will need roles/permissions that allow working with these services.  If you are running these from a Vertex AI Workbench Notebook instance then it is running as a service account which will need the roles/permission that allow working with these services. 


### Document Q&A - Version 1

Ask complex scenario based questions and get text generated answers with references to relative sections of the documents.
- These parse a PDF document from GCS or URL into the documents elements: tables, paragraphs
- gets embeddings for the elements
- creates a local vector search function with ScaNN
- creates a function to generate Generative AI prompts with document contexts retrieved by vector search of the question (embedding) and the documents elements
- Saves the document parsing and embeddings to GCS and/or BigQuery for retrieval on future runs - saves repeat cost and time

<p align="center" width="100%"><center>
    <img align="center" alt="Overview Chart" src="../architectures/notebooks/applied/genai/doc_qa.png" width="45%">
</center></p>

    
**Sports Rules:**
- [Vertex AI GenAI For Document Q&A - MLB Rules For Baseball](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20-%20MLB%20Rules%20For%20Baseball.ipynb)
- [Vertex AI GenAI For Document Q&A - USGA Rule For Golf](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20-%20USGA%20Rules%20For%20Golf.ipynb)
- [Vertex AI GenAI For Document Q&A - IFAB Laws For Football](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20-%20IFAB%20Laws%20For%20Football.ipynb)
- [Vertex AI GenAI For Document Q&A - MCC Laws For Cricket](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20-%20MCC%20Laws%20For%20Cricket.ipynb)
- [Vertex AI GenAI For Document Q&A - NBA Rules For Basketball](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20-%20NBA%20Rules%20For%20Basketball.ipynb)
- [Vertex AI GenAI For Document Q&A - NFL Rules For Football](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20-%20NFL%20Rules%20For%20Football.ipynb)
- [Vertex AI GenAI For Document Q&A - NHL Rules For Hockey](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20-%20NHL%20Rules%20For%20Hockey.ipynb)

**Business Documents:**
- [Vertex AI GenAI For Document Q&A - FAA Regulations](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20-%20FAA%20Regulations.ipynb)
- [Vertex AI GenAI For Document Q&A - Municipal Securities](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20-%20Municipal%20Securities.ipynb)
- [Vertex AI GenAI For Document Q&A - Annual Report](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20-%20Annual%20Report.ipynb)


Use Vertex AI Matching Engine to host low-latency vector search:
- [Vertex AI Matching Engine For Document Q&A](./Vertex%20AI%20Matching%20Engine%20For%20Document%20Q&A.ipynb)
    - Use [Vertex AI Matching Engine](https://cloud.google.com/vertex-ai/docs/matching-engine/overview) for stateful, low latency, vector searches
        - Create and Deploy an index
        - Perform online queries with hosted index
        - Recreate the document bot using online queries
        - Rerunning for multiple `EXPERIMENT` values will deploy multiple indexes to the same index endpoint

### Document Q&A - Version 2
    
Enhacements compared to Version 1:
- multiple documents
- better context configuation with multi-level search
- ouput include visual of all pages that include context to the question with bounding boxes
- better data formatting for scaling in services outside the notebook environment: datastore, Vetex AI Matching Engine, BigQuery, ...
- ability to overwrite previous runs saved data when needed

**Sports Rules:**
- [Vertex AI GenAI For Document Q&A v2 - MLB Rules For Baseball](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20v2%20-%20MLB%20Rules%20For%20Baseball.ipynb)
    
**Business Documents:**   
- [Vertex AI GenAI For Document Q&A - Local Government Trends](./Vertex%20AI%20GenAI%20For%20Document%20Q&A%20-%20Local%20Government%20Trends.ipynb)    

---
## Embeddings

A number of the techniques covered here use embeddings. Embeddings are vector representations of text or images or both.  These are vectors of floating point numbers that come from a model that has been trained to embed content in a way that efficiently represents the content. See how to get embeddings from text, images and both with the notebook:
- [Vertex AI GenAI Embeddings](./Vertex%20AI%20GenAI%20Embeddings.ipynb)

Embeddings can be used:
- To find similar content with vector similarity searches - as show in Q&A examples above
- Clutering content in groups with similiar attributes
- Detect anomaly or outlier observations
- Classification models - use embeddings as features to predict classes

Embeddings as features is a lot like a compact, lower dimension representation of content.  One idea for using embeddings as features is to categorize content.  Stores have catalogs.  Products in the catelog have descriptions (text) and maybe even images.  Using embeddings of the product information make it possible to train a classifier for complex product catalogs - even with hierarchys.  Check out this notebook to see an example of this:
- [Vertex AI GenAI Embeddings - As Features For Hierarchical Classification](./Vertex%20AI%20GenAI%20Embeddings%20-%20As%20Features%20For%20Hierarchical%20Classification.ipynb)


---
## More Resources
- Examples for Prompt Design and Tuning of Foundational Models: [github.com/GoogleCloudPlatform/generative-ai](https://github.com/GoogleCloudPlatform/generative-ai)
- [Enterprise Search](https://cloud.google.com/enterprise-search) on Generative AI App Builder