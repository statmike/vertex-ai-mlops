from google.adk import tools
import base64

async def display_images_side_by_side(
    original_document_artifact_key: str,
    template_document_artifact_key: str,
    tool_context: tools.ToolContext
) -> str:
    """
    Loads two image artifacts (expected to be PNGs) and returns an HTML string
    to display them side-by-side. The ADK Workbench can render this HTML.

    Args:
        original_document_artifact_key: The key of the original document image artifact.
        template_document_artifact_key: The key of the template document image artifact.
        tool_context: The execution context for the tool.

    Returns:
        An HTML string to display the images, or an error message.
    """
    try:
        # 1. Load the artifacts
        # These artifacts should contain the PNG image bytes from your PDF conversion
        original_doc_artifact = await tool_context.load_artifact(filename = original_document_artifact_key)
        template_doc_artifact = await tool_context.load_artifact(filename = template_document_artifact_key)

        # 2. Get image bytes (assuming they are PNGs) and base64 encode them
        # The genai.types.Part object stores bytes in inline_data.data
        original_img_bytes = original_doc_artifact.inline_data.data
        template_img_bytes = template_doc_artifact.inline_data.data

        original_img_base64 = base64.b64encode(original_img_bytes).decode('utf-8')
        template_img_base64 = base64.b64encode(template_img_bytes).decode('utf-8')

        # 3. Construct HTML for side-by-side display
        # This HTML can be rendered by the ADK Workbench in the tool output.
        html_output = f"""
        <div style="text-align: center;">
            <p><strong>Visual Comparison: Original Document vs. Template</strong></p>
            <table style="width:100%; border-collapse: collapse;">
                <thead>
                    <tr>
                        <th style="width:50%; padding: 8px; border: 1px solid #ddd; background-color: #f2f2f2;">Original Document ({original_document_artifact_key})</th>
                        <th style="width:50%; padding: 8px; border: 1px solid #ddd; background-color: #f2f2f2;">Template Document ({template_document_artifact_key})</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="vertical-align:top; padding:5px; border: 1px solid #ddd;">
                            <img src="data:image/png;base64,{original_img_base64}" alt="Original Document" style="max-width:100%; height:auto; display:block; margin-left:auto; margin-right:auto;">
                        </td>
                        <td style="vertical-align:top; padding:5px; border: 1px solid #ddd;">
                            <img src="data:image/png;base64,{template_img_base64}" alt="Template Document" style="max-width:100%; height:auto; display:block; margin-left:auto; margin-right:auto;">
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
        return html_output
    except Exception as e:
        return f"Error generating HTML for image comparison display: {str(e)}"