![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2FApplied+GenAI%2FVertex+AI+Search&dt=readme.md)

# /Applied GenAI/Vertex AI Search/readme.md

This series of notebooks highlights the use over Vertex AI Search for workflows that includes using Google's foundational large generative AI models. These don't need to be trained or hosted - just called with via API. Read more about these exciting new features of Vertex AI Search (FKA) Generative AI App Builder Enterprise Search [here](https://cloud.google.com/enterprise-search)


## About Vertex AI Search
Vertex AI Search is a part of the Vertex AI suite of tools offered by Google Cloud.

Vertex AI Search lets developers, even those with limited machine learning skills, quickly and easily tap into the power of Google’s foundation models and search expertise to create enterprise-grade generative AI applications. Vertex AI Search lets organizations quickly build generative AI powered search engines for customers and employees. The solution is provided within the Google Cloud UI and also via API for integration with enterprise workflows or large language models.

## Using Vertex AI Search
Vertex AI Search is generally available in Google Cloud.

Upload data in the form of unstructued documents, web sites or relational databases and the users can retrieve the most relevant document chunks using natural language queries. The API is provided with specific configuration options which are designed to work well in conjunction with LLMs, such as choosing different document chunk types.

Vertex AI Search can provide search [snippets, extractive answers, and extractive segments](https://cloud.google.com/generative-ai-app-builder/docs/snippets#extractive-segments) with each search response to enhance your results.

## Combining Vertex AI Search with LLMs

As LLMs continue to explode in power and popularity, it has become increasingly clear that tools for information retrieval are an essential part of the stack to unlock many of Gen AI's most valuable use cases. These retrieval tools allow you to efficiently fetch information from your own data and insert the most relevant extracts directly into LLM prompts. This allows you to ground Generative AI output in data that you know to be relevant, validated and up to date.

Most approaches to retrieval typically require the creation of embeddings from documents and the set up of a vector search engine. Custom solutions such as these are time consuming and complex to create, maintain and host. In contrast, Vertex AI Search is a turnkey search engine which provides Google-quality results as a managed service.



## Getting Started

**Install**

The Vertex AI [Python Client](https://cloud.google.com/python/docs/reference/aiplatform/latest) will need to be updated to at least the 1.25.0 release.

Th Vertex AI Search [Python Client](https://cloud.google.com/generative-ai-app-builder/docs/libraries#client-libraries-install-python) will need to be installed.

## Notebooks For Document Q&A Examples:

This [Notebook](Applied GenAI/Vertex AI Search/Vertex AI Search Document Q&A Using Extractive Segments - MLB Rules For Baseball.ipynb) demonstrates the use of **Vertex AI Search with Extractive Segments**.

 Ask any questions related to the MLB Baseball rules and get text generated answers using the combination of both Vertex AI Search and Vertex GenAI LLMs.

 ## Vertex AI Search Setup:

Vertex AI Search Setup can be found [here](./vertex_search_setup.md)