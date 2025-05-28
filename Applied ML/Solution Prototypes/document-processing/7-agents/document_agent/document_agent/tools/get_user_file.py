from google.adk import tools
from google import genai

import fitz #pymupdf

async def get_user_file(
    tool_context: tools.ToolContext
) -> str:
    """
    Find a user uploaded file in the context and saves it as an artifact and returns the artifact key as part of the response.
    If the detected file is a PDF then it converts the first page to a PNG to use as the artifact.

    Args:
        tool_context: The execution context for the tool
    Returns:
        A string confirming the file status and its details, or an error message.
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
                #file_bytes = convert_to_png(file_bytes)
                doc = fitz.open(filetype ="pdf", stream = file_bytes)
                page = doc.load_page(0)
                pix = page.get_pixmap(dpi=300)
                file_bytes = pix.tobytes(output = 'png')                
                file_type = 'image/png'

            file_part = genai.types.Part.from_bytes(data = file_bytes, mime_type = file_type)

            # add info to tool_context as artifact
            version = await tool_context.save_artifact(filename = artifact_key, artifact = file_part)

            return f"The file of type {file_type} and size {len(file_bytes)} bytes was loaded as an artifact with artifact_key = {artifact_key} and version = {version}.\nNote that pdf files are internally converted to png images (first page)."

        else:
            return f"Did not find file data in the user context."
    except Exception as e:
        return f"Error looking for user file: {str(e)}"