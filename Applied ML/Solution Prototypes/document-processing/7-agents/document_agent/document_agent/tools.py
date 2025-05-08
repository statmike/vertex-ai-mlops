import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from google.adk import tools
from google import genai
from google.cloud import storage
from google.cloud import documentai
from . import config

def _generate_artifact_key(gcs_bucket: str, gcs_file_path: str) -> str:
    """Generates a unique key for storing and retrieving the GCS file artifact."""
    return f"gcsfile_{gcs_bucket}_{gcs_file_path.replace('/', '_')}"

def get_gcs_file(gcs_bucket: str, gcs_file_path: str, tool_context: tools.ToolContext) -> str:
    """
    Checks if a file from GCS is already loaded as an artifact. If so, returns its details.
    Otherwise, downloads the file, saves it as an artifact in the ADK session,
    and returns its details.

    Args:
        gcs_bucket: The name of the GCS bucket.
        gcs_file_path: The full path to the file within the GCS bucket.
        tool_context: The execution context for the tool.
    Returns:
        A string confirming the file status (already loaded or newly loaded) and its details,
        or an error message.
    """

    # a key for the artifact to be stored as:
    file_name = gcs_file_path.split('/')[-1]
    artifact_key = _generate_artifact_key(gcs_bucket, gcs_file_path)

    try:
        # does this file already exists as an artifact?
        existing_artifact = tool_context.load_artifact(filename = artifact_key)

        # it already exists:
        if existing_artifact and isinstance(existing_artifact, genai.types.Part):
            file_type = existing_artifact.inline_data.mime_type
            file_size = len(existing_artifact.inline_data.data)
            message = f"The file {file_name} (from gs://{gcs_bucket}/{gcs_file_path}) is already loaded as an artifact. Type: {file_type}, Size: {file_size} bytes, artifact_key = {artifact_key}."
            return message

        # retrieve file as bytes
        gcs = storage.Client()
        bucket = gcs.bucket(gcs_bucket)
        blob = bucket.blob(gcs_file_path)

        if not blob.exists():
            return f"Error: File not found in GCS at gs://{gcs_bucket}/{gcs_file_path}"

        file_bytes = blob.download_as_bytes()
        file_type = blob.content_type
        if file_type is None: file_type = 'application/octet-stream'
        file_name = blob.name.split('/')[-1]
        file_part = genai.types.Part.from_bytes(data = file_bytes, mime_type = file_type)
        
        # add info to tool_context as artifact
        version = tool_context.save_artifact(filename = artifact_key, artifact = file_part)
        
        return f"The file {file_name} of type {file_type} and size {len(file_bytes)} bytes was loaded as an artifact with artifact_key = {artifact_key} and version = {version}"
    
    except Exception as e:

        return f"Error downloading the file: {str(e)}"


def get_document_extraction(artifact_key: str, tool_context: tools.ToolContext) -> str:
    """
    Processes a previously loaded document artifact using Google Document AI for text extraction,
    then summarizes the extracted text using an LLM.

    Args:
        artifact_key: The key of the artifact previously loaded by get_gcs_file.
        tool_context: The execution context for the tool.

    Returns:
        A string containing the summary of the document's extracted text, or an error message.
    """

    try:
        # 1. Get the artifact
        artifact = tool_context.load_artifact(filename = artifact_key)

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
                name = config.DOCUMENT_PARSER,
                inline_document = documentai.Document(content = file_bytes, mime_type = file_mime_type)
            )
        )

        # 3. Extract Details From Reponse
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
        return result  
      
    except Exception as e:
        return f"An error occurred during document extraction or summarization for '{artifact_key}': {str(e)}"

DOCUMENT_PROCESSING_TOOLS = [
    get_gcs_file,
    get_document_extraction
]