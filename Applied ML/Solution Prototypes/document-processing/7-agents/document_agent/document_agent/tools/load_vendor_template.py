from google.adk import tools
from google import genai
from google.cloud import storage
from . import utils

async def load_vendor_template(most_likely_class: str, tool_context: tools.ToolContext) -> str:
    """
    Checks if a file from GCS is already loaded as an artifact. If so, returns its details.
    Otherwise, downloads the file, saves it as an artifact in the ADK session,
    and returns its details.

    Args:
        most_likely_class: The name of the vendor that the users document was classified as by the classification_insights_agent
        tool_context: The execution context for the tool.
    Returns:
        A string confirming the file status (already loaded or newly loaded) and its details,
        or an error message.
    """

    gcs_file_path = f"applied-ml-solution-prototypes/document-processing/{most_likely_class.lower()}/template/template.png"
    gcs_bucket = 'statmike-mlops-349915'

    # a key for the artifact to be stored as:
    file_name = gcs_file_path.split('/')[-1]
    artifact_key = f"gcsfile_{gcs_bucket}_{gcs_file_path.replace('/', '_')}"

    try:
        # does this file already exists as an artifact?
        existing_artifact = await tool_context.load_artifact(filename = artifact_key)

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
        file_ext = file_name.split('.')[-1]

        # confirm file_type is pdf or png, else error
        if file_type is None or file_type not in ['application/pdf', 'image/png']:
            if file_ext == 'pdf':
                file_type = 'application/pdf'
            elif file_ext == 'png':
                file_type = 'image/png'
            else: 
                # file_type = 'application/octet-stream'
                return f"Error: Expected File type not found in GCS at gs://{gcs_bucket}/{gcs_file_path}. Found type {file_type}."
        
        # convert pdf to png
        if file_type == 'application/pdf':
            file_type, file_bytes = utils.pdf_to_png(file_type, file_bytes)

        file_part = genai.types.Part.from_bytes(data = file_bytes, mime_type = file_type)
        
        # add info to tool_context as artifact
        version = await tool_context.save_artifact(filename = artifact_key, artifact = file_part)
        
        return f"The file {file_name} of type {blob.content_type} and size {len(file_bytes)} bytes was loaded as an artifact with artifact_key = {artifact_key} and version = {version}.\nNote that pdf files are internally converted to png images (first page)."
    
    except Exception as e:

        return f"Error downloading the file: {str(e)}"