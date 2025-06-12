from google.adk import tools
from google import genai
from . import utils

async def get_user_file(
    tool_context: tools.ToolContext
) -> str:
    """
    Processes a newly uploaded user file, making it available for other tools.

    This tool MUST be called as the first step immediately after a user uploads a file.
    It accesses the file data from the user's message, converts it to a standard
    PNG format (if it's a PDF), and saves it as a session artifact with the key
    'user_uploaded_file'. All other document processing tools depend on this
    artifact being created first.

    Args:
        tool_context: The execution context for the tool, which contains the user's
                      uploaded file content.
    Returns:
        A string confirming the successful creation of the file artifact and its
        details, or a clear error message if the file cannot be processed.
    """

    try:
        #parts = tool_context.user_content.parts
        parts = [p for p in tool_context.user_content.parts if p.inline_data is not None]
        if parts:
            part = parts[-1] # take the most recent file
            artifact_key = 'user_uploaded_file'
            file_bytes = part.inline_data.data
            file_type = part.inline_data.mime_type

            # confirm file_type is pdf or png, else error
            if file_type is None or file_type not in ['application/pdf', 'image/png']:
                return f"Error: Expected File type not found. Found type {file_type}."
            
            # convert pdf to png
            if file_type == 'application/pdf':
                file_type, file_bytes = utils.pdf_to_png(file_type, file_bytes)

            file_part = genai.types.Part.from_bytes(data = file_bytes, mime_type = file_type)

            # add info to tool_context as artifact
            version = await tool_context.save_artifact(filename = artifact_key, artifact = file_part)

            return f"The file of type {file_type} and size {len(file_bytes)} bytes was loaded as an artifact with artifact_key = {artifact_key} and version = {version}.\nNote that pdf files are internally converted to png images (first page)."

        else:
            return f"Did not find file data in the user context."
    except Exception as e:
        return f"Error looking for user file: {str(e)}"