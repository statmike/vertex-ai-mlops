import json

from google.adk import tools
from google import genai
from google.cloud import documentai
from ..config import DOCUMENT_PARSER

async def document_extraction(artifact_key: str, tool_context: tools.ToolContext) -> str:
    """
    Processes a previously loaded document artifact using Google Document AI for text extraction.

    Args:
        artifact_key: The key of the artifact previously loaded by get_gcs_file.
        tool_context: The execution context for the tool.

    Returns:
        A string containing the documents extration results, or an error message.
    """

    try:
        # 1. Get the artifact
        artifact = await tool_context.load_artifact(filename = artifact_key)

        if not artifact:
            return f"Error: Artifact with key '{artifact_key}' not found. Please load the file first."
        if not isinstance(artifact, genai.types.Part):
            return f"Error: Artifact '{artifact_key}' is not of the expected type (google_genai.types.Part)."

        file_bytes = artifact.inline_data.data
        file_mime_type = artifact.inline_data.mime_type

        # 2. Call Document AI
        docai_client = documentai.DocumentProcessorServiceClient(
            client_options = dict(api_endpoint = f"us-documentai.googleapis.com")
        )
        response = docai_client.process_document(
            request = documentai.ProcessRequest(
                name = DOCUMENT_PARSER,
                inline_document = documentai.Document(content = file_bytes, mime_type = file_mime_type)
            )
        )

        # 3a. testing entities to JSON and let LLM handle
        dict_result = documentai.Document.to_dict(response.document, use_integers_for_enums = False)
        json_result = json.dumps(dict_result['entities'])

        # 3b. Extract Details From Reponse
        result = ""
        for e, entity in enumerate(response.document.entities):
            a = entity.type_
            if entity.normalized_value:
                b = entity.normalized_value
            else:
                b = entity.mention_text.strip()
            result += f"{a}\n{b}\n"
            
            if entity.properties:
                for prop in entity.properties:
                    if prop.normalized_value:
                        c = prop.normalized_value
                    else:
                        c = prop.mention_text
                    result += f"{prop.type_} = {c}\n"

        # 3. Return either the json extract of the entities or the prepared string of entity data:
        return json_result  
      
    except Exception as e:
        return f"An error occurred during document extraction or summarization for '{artifact_key}': {str(e)}"
