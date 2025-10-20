![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# Applied ML
> You are here: `vertex-ai-mlops/Applied ML/readme.md`

Applying models to enhance workflows is Applied ML – often referred to as AI.

**Applied ML**

In some cases, a workflow requires model output, which might seem related to the serving topic covered in [MLOps/Serving](../MLOps/Serving/readme.md). However, it's actually the next step: what you do with the response. For instance, in forecasting, you might use the forecasted horizon to change how you interact with your customers or your supply chain. A great example of applied ML is generative AI, where a very general model serves many purposes and can be coerced into conducting actions, such as agents. Another area of applied ML involves combining or specifically applying techniques to achieve an objective. This is the purpose of this area of the repository.

The work in this part of the repository will make use of:
- Multiple Frameworks which are covered directly in [Framework Workflows](../Framework%20Workflows/readme.md)
- MLOps techniques which are covered in detail in [MLOps](../MLOps/readme.md)

**Application Areas:**

- **[Forecasting](./Forecasting/readme.md)**
  - Time series analysis with trend exploration, seasonality, holidays, and special events
  - BigQuery ML hierarchical forecasting models with bottom-up and top-down approaches
  - Forecast disaggregation using forecast proportions
  - Integration with Vertex AI and open source frameworks

- **[Generative AI (GenAI)](./GenAI/readme.md)**
  - Large language models (LLMs) with Vertex AI Generative AI
  - Retrieval Augmented Generation (RAG) for grounding responses in personal data
  - Prompt optimization with evaluation metrics
  - Supervised tuning for targeted response types
  - Controlled generation with JSON structures and function calling
  - Business use cases: search with citations, classification, summarization, schema-based extraction

- **[AI Agents](./AI%20Agents/readme.md)**
  - Agent Development Kit (ADK) for building LLM-based, workflow, and custom agents
  - Tools for API integration, code execution, and external service interaction
  - Deployment to Vertex AI Agent Engine for fully managed scaling
  - Model Context Protocol (MCP) integration including MCP Toolbox for Google Cloud Databases
  - Agent-to-Agent (A2A) protocol for cross-boundary communication
  - Concept examples: Agentic retrieval with BigQuery, Conversational Analytics API, Travel Planner
  - Production examples: Document Processing Agent, Time Series Forecasting Agent (see Solution Prototypes)

- **[Anomaly Detection](./Anomaly%20Detection/readme.md)**
  - Model-based recognition of anomalous patterns in data
  - Custom autoencoder models built with Keras for anomaly detection
  - BigQuery ML anomaly detection with PCA, k-means, and autoencoder models
  - Time series forecasting-based anomaly detection (univariate and multivariate ARIMA+)
  - Identification of data points driving anomalous indicators
  - Examples for detecting precursors to system failures

- **[Optimization](./Optimization/readme.md)**
  - Systematic optimization of decision variables to maximize/minimize objective functions
  - Vertex AI Vizier for black-box optimization and hyperparameter tuning
  - Multi-objective optimization with Pareto-optimal solutions
  - Safety thresholds and constraint handling
  - Contextual bandits and conditional optimization
  - Comprehensive documentation with parameter specs, metrics, trials, and advanced configurations
  - Integration with scipy.optimize for continuous problems and Google OR-Tools for discrete/combinatorial problems

**Solution Prototypes**

Some workflows require complex applications or the combination of multiple applications.  These **solutions** can solve complex business scenarios.

- **[Solution Prototypes](./Solution%20Prototypes/readme.md)**
  - **Document Processing**: End-to-end invoice processing with variable vendor formats
    - Custom Document AI extraction for key information across formats
    - Multimodal embeddings for document similarity analysis
    - Nearest neighbor search to detect format changes and potential fraud
    - Conditional GenAI comparison for human review of dissimilar documents
    - Automated processing with BigQuery Object Tables
    - Agentic workflow using ADK with deployment to Vertex AI Agent Engine
  - **Time Series Forecasting Agent**: Interactive forecasting with conversational interface
    - ADK-based agent with MCP Toolbox integration for BigQuery data retrieval
    - On-demand forecasting using BigQuery's AI.FORECAST function
    - Interactive visualization of historical demand and forecasts
    - Natural language queries for time series data exploration
