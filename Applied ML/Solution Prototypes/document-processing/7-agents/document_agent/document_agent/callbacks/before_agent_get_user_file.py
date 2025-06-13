# ./callbacks/before_agent_get_user_file.py

from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google import genai
from ..tools import utils

async def before_agent_get_user_file(
    callback_context: CallbackContext
) -> Optional[genai.types.Content]:
    """
    Checks for a user-uploaded file before the agent runs.

    If a file is found in the user's message, this callback processes it,
    converts it to a PNG (if it's a PDF), and saves it as an artifact named
    'user_uploaded_file'. It then returns a direct confirmation message to the
    user and halts further agent processing for the current turn.

    If no file is found, it returns None, allowing the agent to proceed normally.
    """

    parts = []
    if callback_context.user_content and callback_context.user_content.parts:
        parts = [p for p in callback_context.user_content.parts if p.inline_data is not None]

    # if no file then continue to agent by returning empty
    if not parts:
        return None
    
    # if file then save as artifact
    part = parts[-1]
    artifact_key = 'user_uploaded_file'
    file_bytes = part.inline_data.data
    file_type = part.inline_data.mime_type

    # confirm file_type is pdf or png, else let user know the expected type
    if file_type is None or file_type not in ['application/pdf', 'image/png']:
        issue_message = f"The file you provided is of type {file_type} which is not supported here.  Please provide either a PDF or PNG."
        response = genai.types.Content(
            parts = [genai.types.Part(text = issue_message)],
            role = 'model'
        )
        return response
                                                                                    
    # convert pdf to png
    if file_type == 'application/pdf':
        file_type, file_bytes = utils.pdf_to_png(file_type, file_bytes)

    # create artifact
    artifact = genai.types.Part.from_bytes(data = file_bytes, mime_type = file_type)

    # save artifact
    version = await callback_context.save_artifact(filename = artifact_key, artifact = artifact)

    # Formulate a confirmation message
    confirmation_message = (
        f"Thank you! I've successfully processed your uploaded file.\n\n"
        f"It's now ready for the next step and is stored as artifact with key "
        f"'{artifact_key}' (version: {version}, size: {len(file_bytes)} bytes).\n\n"
        f"What would you like to do with it? For example: 'Extract the contents', "
        f"'Classify this document', or 'Redact sensitive info'."
    )
    response = genai.types.Content(
        parts = [genai.types.Part(text = confirmation_message)],
        role = 'model'
    )

    return response




