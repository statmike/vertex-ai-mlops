from google.adk import tools
from google import genai
import io, base64
from PIL import Image, ImageDraw, ImageFont

async def display_images_side_by_side(
    original_document_artifact_key: str,
    template_document_artifact_key: str,
    tool_context: tools.ToolContext
) -> str:
    """
    Loads two image artifacts (expected to be PNGs) and returns a composite PNG of these side-by-side for comparison.

    Args:
        original_document_artifact_key: The key of the original document image artifact.
        template_document_artifact_key: The key of the template document image artifact.
        tool_context: The execution context for the tool.

    Returns:
        "Successfully create comparison image artifact with key 'latest_comparison'"
    """
    # constants for layout
    BORDER_THICKNESS = 5
    PADDING_BETWEEN_IMAGES = 30
    OUTER_MARGIN = 20
    LABEL_AREA_HEIGHT = 60  # Height for the label text area above images
    FONT_SIZE = 24
    BACKGROUND_COLOR = "white"
    BORDER_COLOR = "black"
    TEXT_COLOR = "black"

    try:
        # 1. Load the artifacts
        original_doc_artifact = await tool_context.load_artifact(filename = original_document_artifact_key)
        template_doc_artifact = await tool_context.load_artifact(filename = template_document_artifact_key)

        # 2. Get image bytes and load into Pillow objects:
        original_img_bytes = original_doc_artifact.inline_data.data
        template_img_bytes = template_doc_artifact.inline_data.data

        img_orig = Image.open(io.BytesIO(original_img_bytes))
        img_template = Image.open(io.BytesIO(template_img_bytes))

        # 3. Cacluate dimension for composite image:
        img_orig_width, img_orig_height = img_orig.size
        img_template_width, img_template_height = img_template.size

        total_content_width = img_orig_width + img_template_width + PADDING_BETWEEN_IMAGES
        max_content_height = max(img_orig_height, img_template_height)

        canvas_width = total_content_width + 2 * OUTER_MARGIN + 2 * BORDER_THICKNESS # one border per image
        canvas_height = max_content_height + LABEL_AREA_HEIGHT + 2 * OUTER_MARGIN + BORDER_THICKNESS # one border for image area

        # 4. Create the new image canvas
        composite_image = Image.new('RGB', (canvas_width, canvas_height), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(composite_image)

        try:
            font = ImageFont.truetype("arial.ttf", FONT_SIZE)
        except IOError:
            font = ImageFont.load_default()

        # 5. Draw labels
        label_orig_text = "Original Document"
        label_template_text = "Classified Vendor's Template"

        # Calculate text size for centering (Pillow 9.2.0+ has getbbox, older has textsize)
        if hasattr(draw, 'textbbox'):
            label_orig_bbox = draw.textbbox((0,0), label_orig_text, font=font)
            label_template_bbox = draw.textbbox((0,0), label_template_text, font=font)
            label_orig_width = label_orig_bbox[2] - label_orig_bbox[0]
            label_template_width = label_template_bbox[2] - label_template_bbox[0]
        else: # Fallback for older Pillow
            label_orig_width, _ = draw.textsize(label_orig_text, font=font)
            label_template_width, _ = draw.textsize(label_template_text, font=font)

        x_orig_label = OUTER_MARGIN + BORDER_THICKNESS + (img_orig_width / 2) - (label_orig_width / 2)
        x_template_label = OUTER_MARGIN + BORDER_THICKNESS + img_orig_width + PADDING_BETWEEN_IMAGES + (img_template_width / 2) - (label_template_width / 2)
        y_label = OUTER_MARGIN + (LABEL_AREA_HEIGHT - FONT_SIZE) / 3 # Adjusted for better vertical centering

        draw.text((x_orig_label, y_label), label_orig_text, fill=TEXT_COLOR, font=font)
        draw.text((x_template_label, y_label), label_template_text, fill=TEXT_COLOR, font=font)

        # 6. Define positions and draw borders and paste images
        y_images_top = OUTER_MARGIN + LABEL_AREA_HEIGHT

        # Original Image
        x_orig_start = OUTER_MARGIN
        draw.rectangle(
            (x_orig_start, y_images_top, x_orig_start + img_orig_width + 2 * BORDER_THICKNESS, y_images_top + img_orig_height + 2 * BORDER_THICKNESS),
            outline=BORDER_COLOR, width=BORDER_THICKNESS
        )
        composite_image.paste(img_orig, (x_orig_start + BORDER_THICKNESS, y_images_top + BORDER_THICKNESS))

        # Template Image
        x_template_start = x_orig_start + img_orig_width + 2 * BORDER_THICKNESS + PADDING_BETWEEN_IMAGES
        draw.rectangle(
            (x_template_start, y_images_top, x_template_start + img_template_width + 2 * BORDER_THICKNESS, y_images_top + img_template_height + 2 * BORDER_THICKNESS),
            outline=BORDER_COLOR, width=BORDER_THICKNESS
        )
        composite_image.paste(img_template, (x_template_start + BORDER_THICKNESS, y_images_top + BORDER_THICKNESS))

        # 7. Save the composite image to bytes
        img_byte_arr = io.BytesIO()
        composite_image.save(img_byte_arr, format='PNG')
        png_bytes = img_byte_arr.getvalue()

        # 8. Store as a new artifact
        comparison_part = genai.types.Part.from_bytes(data = png_bytes, mime_type="image/png")
        version = await tool_context.save_artifact(filename = "latest_comparison", artifact = comparison_part)

        return "Successfully created comparison image artifact with key 'latest_comparison' and it has version {version}."

    except Exception as e:
        return f"Error creating and storing comparison image artifact: {str(e)}"