# Conversational Analytics API

An agent at an API.  It works with BigQuery, Looker, and Looker Studio sources.  It retrieves, derives, and presents answers.  

**Resources:**
- Blog: https://cloud.google.com/blog/products/data-analytics/understanding-lookers-conversational-analytics-api
- Documentation: https://cloud.google.com/gemini/docs/conversational-analytics-api/overview
  - Key walkthrough: https://cloud.google.com/gemini/docs/conversational-analytics-api/build-agent-sdk
- Python API: https://cloud.google.com/python/docs/reference/google-cloud-geminidataanalytics/latest

**How it works:**
- Objects:
  - **Data Source Definition:** The soure BigQuery, Looker, or Looker Studio sources
  - **Context** for the using the data source
  - **Agent** that uses the context
  - **Conversation** that is a session with the agent
  - **Chat** message within the conversation
- Notes on use:
  - An agent can be used for multiple conversations
  - A conversation.... talk about stateless here

My steps to document:
- created this folder and make sure gcloud setup
- setup poetry environment and added packages
- created notebook

