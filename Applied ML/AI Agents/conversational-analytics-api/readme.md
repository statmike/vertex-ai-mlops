# Conversational Analytics API

This API allows you to build conversational experiences on top of your data. It uses a clear hierarchy of components and offers multiple chat modes — **both stateful and stateless** — to cover a wide range of applications.

**Resources:**
- Blog: https://cloud.google.com/blog/products/data-analytics/understanding-lookers-conversational-analytics-api
- Documentation: https://cloud.google.com/gemini/docs/conversational-analytics-api/overview
  - Key walkthrough: https://cloud.google.com/gemini/docs/conversational-analytics-api/build-agent-sdk
- Python API: https://cloud.google.com/python/docs/reference/google-cloud-geminidataanalytics/latest

**How it Works: The Hierarchy**
1. **Data Source:** The foundation. This is your raw data, such as a BigQuery table(s), Looker, or Looker Studio reports.
2. **Context:** A layer that sits on top of a **Data Source**. It defines how the data should be interpreted, including table schemas, descriptions, and rules for querying.
3. **Agent:** A conversational entity that uses a **Context**. The Agent is the "bot" that understands the data (via its Context) and can answer questions about it.
4. **Conversation:** A specific session with an **Agent**. It tracks the history of a single, ongoing dialogue.
5. **Chat:** An individual message sent by a user within a **Conversation**.

This structure means a **Chat** happens in a **Conversation**, which is handled by an **Agent**, who understands the data through its **Context**, which is linked to a **Data Source**.

**Usage Modes**

Chats can be either **stateful** or **stateless*, depending on how you manage the conversation history.
- **Stateful (Session-based)**: For a continuous conversation, you reference a **Conversation** in each chat call. The service automatically remembers and manages the entire chat history for that session. This is best for ongoing, multi-turn interactions.
- **Stateless**: For individual queries, you must provide the full conversation history with every chat call. This is useful when you want to manage the state yourself. You can do this in two ways:
  - **With an Agent:** Send the history to a pre-configured **Agent**, which already knows its data source and context.
  - **Inline (On-demand):** Send the history and the **data source** Context together in the same call. This is ideal for quick, one-off questions where a pre-configured Agent isn't available or necessary.

## Getting Started

This repository includes a notebook, [conversational-analytics-api.ipynb](conversational-analytics-api.ipynb), to help you get started. This notebook provides a comprehensive walkthrough for using the Conversational Analytics API and can serve as a valuable resource for your own projects.