![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FAI+Agents%2Fconversational-analytics-api&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/AI%20Agents/conversational-analytics-api/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/conversational-analytics-api/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/conversational-analytics-api/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/conversational-analytics-api/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/AI%2520Agents/conversational-analytics-api/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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