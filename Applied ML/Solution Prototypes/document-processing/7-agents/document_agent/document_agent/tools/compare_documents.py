from google.adk import tools
from google import genai
from ..config import GCP_PROJECT, GCP_LOCATION

client = genai.Client(vertexai=True, project = GCP_PROJECT, location = GCP_LOCATION)

async def compare_documents(
    original_document_artifact_key: str,
    template_document_artifact_key: str,
    tool_context: tools.ToolContext
) -> str:
    """
    
    """

    prompt = """
You are specialized in comparing two documents, an 'original document' and a 'vendor template', for formatting differences.
You are provided two documents here for the comparisions:
- the first is the orginal document
- the second is a vendor template from a known authentic document from the same vendor.

Your tasks are:
1.  **Visually analyze** the image content of both `Part` objects provided to you.
2.  Based on this visual analysis, identify and report any differences in formatting between the original document and the vendor template.
    Focus on aspects such as:
    - Fonts (type, size, style, color)
    - Positioning and alignment of elements (text blocks, images, tables, logos, headers, footers)
    - Overall layout and structure (margins, columns, spacing between elements)
    - Use of colors, branding elements, and visual styles.
3.  Provide a clear and detailed overview of these **visual formatting differences**. 
    """

    try:
        # 1. Load the artifacts
        original_doc_artifact = await tool_context.load_artifact(filename = original_document_artifact_key)
        template_doc_artifact = await tool_context.load_artifact(filename = template_document_artifact_key)

        # 2. request
        response = client.models.generate_content(
            model = 'gemini-2.0-flash',
            contents = [original_doc_artifact, template_doc_artifact, prompt],
            config = genai.types.GenerateContentConfig(
                system_instruction = """You are specialized in comparing two documents, an 'original document' and a 'vendor template', for formatting differences."""
            )
        )

        return response.text



    except Exception as e:
        return f"An error occurred comparing the doucments: {str(e)}"
