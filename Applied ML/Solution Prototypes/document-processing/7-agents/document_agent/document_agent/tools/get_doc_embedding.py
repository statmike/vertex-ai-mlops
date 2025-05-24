from google.adk import tools
import vertexai.vision_models
from ..config import GCP_PROJECT, GCP_LOCATION

vertexai.init(project = GCP_PROJECT, location = GCP_LOCATION)

async def get_doc_embedding(artifact_key: str, tool_context: tools.ToolContext) -> str:
    """
    Calls the Vertex AI Embedding API to generate an embedding for the document artifact that was previously loaded.
    Stores the embedding vector in the context with key 'document_embedding'.

    Args:
        artifact_key: The key of the artifact previously loaded by get_gcs_file.
        tool_context: The execution context for the tool.

    Returns:
        A string confirming the document embedding operation is completed, or an error message.
    """

    try:
        # 1. Get the document from artifacts
        document = await tool_context.load_artifact(filename = artifact_key)

        # 2. Convert genai.Part to vertexai.Part
        document = vertexai.vision_models.Image(image_bytes = document.inline_data.data)

        # 3. Connect To Vertex AI Embedding Model
        model = vertexai.vision_models.MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

        # 4. Get embedding
        embedding = model.get_embeddings(image = document).image_embedding

        # 5. Add embedding to context for the session (default, no prefix)
        tool_context.state['document_embedding'] = embedding

        return f'The document was retrieved with artifact_key {artifact_key} and sucessfully embedding and stored in the session state with key "document_embedding".'

    except Exception as e:

        return f"Error processing the document embedding: {str(e)}"