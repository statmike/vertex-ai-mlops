![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+ML%2FSolution+Prototypes&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20ML/Solution%20Prototypes/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/Solution%2520Prototypes/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/Solution%2520Prototypes/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/Solution%2520Prototypes/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%2520ML/Solution%2520Prototypes/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# Solution Prototypes
> You are here: `vertex-ai-mlops/Applied ML/Solution Prototypes/readme.md`

This folder contains solution prototypes that integrate multiple aspects of Applied ML. These solutions are more complex and use-case specific than the examples found in other folders within this section.

**Solutions**

- **[Document Processing](./document-processing/readme.md)** - End-to-end invoice processing with fraud detection
  - **Challenge**: Variable invoice formats across vendors with potential fraud detection needs
  - **Step 1: Custom Document Extraction**
    - Document AI Custom Extractor with generative AI for zero-shot, few-shot, and fine-tuned parsing
    - Extract structured data from variable format documents (invoices, forms, etc.)
    - Online and batch processing capabilities with BigQuery integration
  - **Step 2: Document Preparation**
    - BigQuery Object Tables for managing documents in Google Cloud Storage
    - `ML.PROCESS_DOCUMENT` function for SQL-based extraction at scale
    - Structured storage of extracted invoice data and metadata
  - **Step 3: Multimodal Embeddings**
    - Vertex AI multimodal embedding models for document representation
    - `ML.GENERATE_EMBEDDING` function in BigQuery for batch embedding generation
    - Vector representations enabling similarity search and classification
  - **Step 4: Document Similarity & Classification**
    - `VECTOR_SEARCH` function for nearest neighbor analysis
    - PCA-based 2D visualization of document relationships
    - ML-based vendor classification using embedding features
  - **Step 5: Anomaly Detection**
    - Statistical analysis to identify potentially fraudulent or mislabeled documents
    - Detection of format changes and unusual patterns
    - Flagging system for human review
  - **Step 6: Document Comparison**
    - Gemini multimodal prompts for automated fraud indicator identification
    - Side-by-side document comparison highlighting formatting differences
    - Descriptive analysis of layout and content anomalies
  - **Step 7: Agent Workflow**
    - ADK-based agent orchestrating the complete fraud analysis workflow
    - Integration of extraction, classification, anomaly detection, and comparison
    - Deployment to Vertex AI Agent Engine with application integration examples
    - Interactive UI for fraud analysts to review and investigate flagged documents

- **[Time Series](./time-series/readme.md)** - Conversational forecasting with interactive visualizations
  - **Agentic Retrieval**: Natural language queries for time series data stored in BigQuery
  - **MCP Toolbox Integration**: Pre-defined tools for querying historical data and generating forecasts
  - **BigQuery AI.FORECAST**: On-demand time series forecasting using BigQuery's built-in ML capabilities
  - **Interactive Visualizations**: Python-based plotting tools creating interactive charts from query results
  - **Station-Level Analysis**: Drill-down capabilities for analyzing specific locations or subsets
  - **ADK Web UI**: Local testing environment with example questions and visual outputs
  - **Use Cases**: Daily totals analysis, station-specific trends, forecast generation with historical context

