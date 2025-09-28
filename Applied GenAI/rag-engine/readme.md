# Vertex AI Rag Engine

In RAG applicaiton the tasks for ingesting, chunking, embedding, indexing, retrieval , ranking, and generation all have great services and options within Vertex AI and Google Cloud.  The [Vertex AI RAG Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview) is an SDK approach to automating these steps.  The SDK makes opinionate choices for many of the services while surfacing important configuration parameters for the user.  It also offers a directly entry point to the individual serivces in some cases for manually overriding the workflow when necessary.  

Here we will show two path with RAG Engine.  A simple path using as many defaults as possible to illustrate the simplicity the service offers.  Then, more customized path where even the vector database is indepedently setup and continually configured to augument RAG engine with hybrid search enabled by [Vertex AI Vector Search](https://cloud.google.com/vertex-ai/docs/vector-search/overview).


RAG Engine Setup:
1. Create Corpus
2. Import Documents
3. Retrieval Points: 
   1. Matching Chunks
   2. Ranked Chunks
   3. Generated Answers with Matching Chunks
   4. Generated Answers with Ranked Chunks

Workflows
- RAG in seconds
- Customizable RAG Engine usage