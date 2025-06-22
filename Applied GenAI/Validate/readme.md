![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+GenAI%2FValidate&file=readme.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Validate/readme.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Validate/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Validate/readme.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Validate/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Validate/readme.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
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
# Validate
> You are here: `vertex-ai-mlops/Applied GenAI/Validate/readme.md`

<p align="center"><center>
    <img src="../resources/images/created/applied-genai/overview-build-validate.png" width="75%">
</center></p>

Large language models (LLMs) are powerful tools for generating human-like text, but they can sometimes generate inaccurate information. To ensure your LLM provides grounded and factual responses, you need to provide it with relevant context. Retrieval augmented generation (RAG) helps find the relevant context, and ranking can help filter and sort the retrieved context. But how can you be sure the LLM is actually using that context effectively?

This is where validation comes in - it allows you to assess how well an LLM's response is grounded in the context provided to the prompt.

## Vertex AI Agent Builder Check Grounding API

This API helps you analyze how well an LLM's response is grounded in the context you provided.

Here's how it works:

- **Input:** You provide the Check Grounding API with the LLM's response and the context chunks you included in the prompt.
- **Analysis:** The API breaks down the LLM's response and maps phrases to supporting evidence within the context.
- **Output:** The API returns a detailed report, including:
    - **Citations:** Links between specific phrases in the response and the supporting context.
    - **Support Score:** An overall score (0 to 1) indicating how well the response is supported by the context.

**Workflow:**

- [Vertex AI Agent Builder Check Grounding API](../Validate/Vertex%20AI%20Agent%20Builder%20Check%20Grounding%20API.ipynb)
