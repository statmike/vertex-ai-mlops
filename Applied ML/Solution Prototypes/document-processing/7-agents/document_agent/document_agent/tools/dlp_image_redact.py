from google.adk import tools
from google import genai
from google.cloud import dlp_v2
from ..config import GCP_PROJECT, GCP_LOCATION

dlp_client = dlp_v2.DlpServiceClient()

async def dlp_image_redact(
    artifact_key: str,
    tool_context: tools.ToolContext
) -> str:
    """
    Redacts sensitive information from a document image using Google Cloud DLP.

    This tool loads an image from the specified artifact key, sends it to the
    DLP API to redact predefined sensitive info_types (e.g., PERSON_NAME,
    PHONE_NUMBER), and then saves the redacted image back to the same artifact,
    creating a new version.

    Args:
        artifact_key: The key of the image artifact to be redacted. This artifact
                      will be overwritten with the redacted version.
        tool_context: The execution context for the tool, used to load and save
                      the artifact.
    Returns:
        A string confirming that the image was redacted and the artifact was
        updated with a new version number. If no sensitive information was
        found, it returns a message indicating no changes were made.
        Returns an error message if the process fails.
    """

    try:
        # 1. Get the document from artifacts
        document = await tool_context.load_artifact(filename = artifact_key)

        # 2. Setup DLP Processing Parameters
        info_types = ['PERSON_NAME', 'PHONE_NUMBER']
        byte_item = {
            "type_" : document.inline_data.mime_type.upper().replace('/', '_'),
            "data" : document.inline_data.data
        }
        inspect_config = {
            "info_types" : [{"name": info_type} for info_type in info_types]
        }
        request = dlp_v2.RedactImageRequest(
            parent = f"projects/{GCP_PROJECT}",
            inspect_config = inspect_config,
            byte_item = byte_item,
            include_findings = True
        )

        # 3. Make redaction request with dlp clinet
        response = dlp_client.redact_image(request = request)

        # 4. Get redacted image and update the artifact
        if response.redacted_image:
            redacted_image = response.redacted_image
            file_part = genai.types.Part.from_bytes(data = redacted_image, mime_type = document.inline_data.mime_type)
            version = await tool_context.save_artifact(filename = artifact_key, artifact = file_part)
            return f"The document image was redacted and saved back as version={version} for artifact_key: {artifact_key}"
        else:
            redacted_image = None
            return f"There were no redactions to perform on this document and the artifact remains unchanged with artifact_key: {artifact_key}"

    except Exception as e:

        return f"Error processing the document embedding: {str(e)}"
