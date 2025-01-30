![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FApplied+GenAI%2FEvaluation&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Applied%20GenAI/Evaluation/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# Evaluation
> You are here: `vertex-ai-mlops/Applied GenAI/Evaluation/readme.md`

This directory contains workflows that demonstrate how to evaluate and optimize generative AI models using Vertex AI.  Evaluating the quality of responses from generative AI models is crucial for ensuring they meet the desired performance standards for tasks such as summarization, question answering, and code generation.  These workflows leverage the Vertex AI platform to streamline this process.

**Workflows:**

- **[Evaluation For GenAI](./Evaluation%20For%20GenAI.ipynb):** This notebook provides a comprehensive guide to evaluating generative AI responses using the Vertex AI SDK. It covers the fundamentals of GenAI evaluation, explaining how to assess model outputs against baselines or ground truths using various task-specific metrics. The notebook explores different types of evaluation methods, including:
    - **Model-Based Pairwise:** Comparing two responses using a model as a judge to determine the better one based on defined criteria.
    - **Model-Based Pointwise:** Evaluating a single response against a set of criteria, with a model assigning a rating based on the specified metric.
    - **Computation-based:** Directly comparing text using metrics like Exact Match, BLEU, ROUGE for similarity, or classification metrics like F1-score and accuracy on aggregated results. It also includes embedding based comparisons like distance.
    This workflow is essential for understanding the basics of evaluating the quality of your GenAI model's outputs.

- **[Optimize Prompts Using Evaluation Metrics](./Optimize%20Prompts%20Using%20Evaluation%20Metrics.ipynb):** This notebook demonstrates how to use evaluation metrics to automatically optimize prompt performance by rewriting system instructions. It leverages the Vertex AI Prompt Optimization service, which provides tools for refining system instructions with or without the use of multi-shot prompting (demonstrations). Key aspects covered include:
    - Initializing a prompt optimization job as a Vertex AI Custom Training Job.
    - Preparing inputs, including system instructions, prompt templates (with optional placeholders for ground truth or model-generated responses), input data files (JSONL or CSV), and configuration parameters specifying metrics, target, and source LLMs.
    - Understanding the outputs: optimized system instructions and evaluation results for each step taken during the optimization process.
    - Using official documentation and provided code examples to get started with prompt optimization.
This workflow is ideal for improving your GenAI models iteratively by fine-tuning the instructions provided to the model.