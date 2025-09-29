# Vertex AI RAG Engine

In RAG applications, the tasks for ingesting, chunking, embedding, indexing, retrieval, ranking, and generation all have great services and options within Vertex AI and Google Cloud. The [Vertex AI RAG Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview) is an SDK approach to automating these steps. The SDK makes opinionated choices for many of the services while surfacing important configuration parameters for the user. It also offers a direct entry point to the individual services in some cases for manually overriding the workflow when necessary.

Here we will show two paths with RAG Engine. A simple path using as many defaults as possible to illustrate the simplicity the service offers. Then, a more customized path where the vector database is independently set up and configured to augment the RAG engine with hybrid search enabled by [Vertex AI Vector Search](https://cloud.google.com/vertex-ai/docs/vector-search/overview).


RAG Engine Setup:
1. Create Corpus
2. Import Documents
3. Retrieval Points: 
   1. Matching Chunks
   2. Re-Ranked Matching Chunks
4. Generated Answers with a Tool to Retrieve

Workflows
- [Simple RAG Engine Workflow](./rag-engine-simple.py): This workflow demonstrates an end-to-end RAG implementation using the RAG Engine SDK with its default managed vector database. It covers creating a corpus, importing a PDF document form GCS, and then demonstrates multiple retrieval strategies: retrieval with basic vector search, retrieval with re-ranking, and using an LLM as a re-ranker. Finally, it shows how to use the RAG corpus and retrieval settings as a tool for a generative model to answer questions based on the document with a single call.
- Customizable RAG Engine usage With Vertex AI Vector Search
- Augmenting Vertex AI Vector Search For Hybrid Search
