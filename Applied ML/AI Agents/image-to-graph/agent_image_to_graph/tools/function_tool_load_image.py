import os
from google.adk import tools
from PIL import Image
import io


async def load_image(file_path: str, tool_context: tools.ToolContext) -> str:
    """
    Load an image from a file path and store it in state for subsequent analysis.

    Reads the image file, validates it with Pillow, and stores the raw bytes
    and dimensions in tool_context.state for use by other tools (analyze, crop, etc.).
    Also initializes an empty graph structure in state.

    Args:
        file_path: The absolute or relative path to the image file to load.
        tool_context: The ADK tool context for accessing shared state.

    Returns:
        A message confirming the image was loaded with its dimensions,
        or an error message if loading fails.
    """
    try:
        expanded_path = os.path.expanduser(file_path)

        if not os.path.exists(expanded_path):
            return f"Error: File not found at '{file_path}'."

        with open(expanded_path, 'rb') as f:
            image_bytes = f.read()

        # Validate with Pillow and get dimensions
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        image_format = img.format or 'UNKNOWN'

        # Determine MIME type
        mime_map = {
            'JPEG': 'image/jpeg',
            'PNG': 'image/png',
            'GIF': 'image/gif',
            'BMP': 'image/bmp',
            'TIFF': 'image/tiff',
            'WEBP': 'image/webp',
        }
        mime_type = mime_map.get(image_format, 'image/png')

        # Store in state
        # Note: storing bytes as base64 string for JSON-serializable state
        import base64
        tool_context.state['source_image'] = base64.b64encode(image_bytes).decode('utf-8')
        tool_context.state['source_image_mime_type'] = mime_type
        tool_context.state['image_dimensions'] = {'width': width, 'height': height}
        tool_context.state['image_format'] = image_format

        # Initialize empty graph state
        tool_context.state['graph'] = {
            'diagram_type': None,
            'nodes': [],
            'edges': [],
            'metadata': {
                'source_file': file_path,
                'image_width': width,
                'image_height': height,
            }
        }
        tool_context.state['cropped_regions'] = {}
        tool_context.state['schema'] = None

        return (
            f"Image loaded successfully.\n"
            f"  File: {file_path}\n"
            f"  Format: {image_format}\n"
            f"  Dimensions: {width} x {height} pixels\n"
            f"  MIME type: {mime_type}\n"
            f"Graph state initialized (empty). Ready for analysis."
        )

    except Exception as e:
        return f"Error loading image: {str(e)}"
