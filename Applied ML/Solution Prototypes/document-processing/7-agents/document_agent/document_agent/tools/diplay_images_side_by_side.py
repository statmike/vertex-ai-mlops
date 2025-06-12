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
    Loads two image artifacts (expected to be PNGs), resizes them to the height of the smaller image
    while maintaining aspect ratio, and returns a composite PNG of these side-by-side for comparison.

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
    LABEL_AREA_HEIGHT = 100  # Height for the label text area above images
    FONT_SIZE = 56
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

        # 3. Determine target height (height of the smaller image) and resize images
        img_orig_width, img_orig_height = img_orig.size
        img_template_width, img_template_height = img_template.size

        target_height = min(img_orig_height, img_template_height)

        try:
            resampling_method = Image.Resampling.LANCZOS
        except AttributeError:  # For older Pillow versions
            resampling_method = Image.ANTIALIAS

        # Resize original image
        if img_orig_height != target_height:
            ratio_orig = target_height / img_orig_height
            new_orig_width = int(img_orig_width * ratio_orig)
            img_orig = img_orig.resize((new_orig_width, target_height), resampling_method)
            img_orig_width, img_orig_height = img_orig.size # Update dimensions

        # Resize template image
        if img_template_height != target_height:
            ratio_template = target_height / img_template_height
            new_template_width = int(img_template_width * ratio_template)
            img_template = img_template.resize((new_template_width, target_height), resampling_method)
            img_template_width, img_template_height = img_template.size # Update dimensions

        # 4. Calculate dimension for composite image using new (potentially resized) dimensions:
        total_content_width = img_orig_width + img_template_width + PADDING_BETWEEN_IMAGES
        max_content_height = max(img_orig_height, img_template_height)

        canvas_width = total_content_width + 2 * OUTER_MARGIN + 2 * BORDER_THICKNESS # one border per image
        canvas_height = max_content_height + LABEL_AREA_HEIGHT + 2 * OUTER_MARGIN + BORDER_THICKNESS # one border for image area

        # 5. Create the new image canvas
        composite_image = Image.new('RGB', (canvas_width, canvas_height), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(composite_image)

        try:
            font = ImageFont.truetype("DejaVuSans.ttf", FONT_SIZE)
        except IOError:
            font = ImageFont.load_default()

        # 6. Draw labels
        label_orig_text = "Uploaded Document"
        label_template_text = "Classified Vendor's Template"

        # Calculate text size for centering (Pillow 9.2.0+ has getbbox, older has textsize)
        if hasattr(draw, 'textbbox'):
            label_orig_bbox = draw.textbbox((0,0), label_orig_text, font=font)
            label_template_bbox = draw.textbbox((0,0), label_template_text, font=font)
            label_orig_width = label_orig_bbox[2] - label_orig_bbox[0]
            label_orig_height = label_orig_bbox[3] - label_orig_bbox[1] # Get text height
            label_template_width = label_template_bbox[2] - label_template_bbox[0]
        else: # Fallback for older Pillow
            label_orig_width, _ = draw.textsize(label_orig_text, font=font)
            label_template_width, _ = draw.textsize(label_template_text, font=font)

        x_orig_label = OUTER_MARGIN + BORDER_THICKNESS + (img_orig_width / 2) - (label_orig_width / 2)
        x_template_label = OUTER_MARGIN + BORDER_THICKNESS + img_orig_width + PADDING_BETWEEN_IMAGES + (img_template_width / 2) - (label_template_width / 2)
        y_label = OUTER_MARGIN + (LABEL_AREA_HEIGHT - FONT_SIZE) / 3 # Adjusted for better vertical centering
        y_label = OUTER_MARGIN + (LABEL_AREA_HEIGHT - label_orig_height) / 2 # Center based on actual text height

        draw.text((x_orig_label, y_label), label_orig_text, fill=TEXT_COLOR, font=font)
        draw.text((x_template_label, y_label), label_template_text, fill=TEXT_COLOR, font=font)

        # 7. Define positions and draw borders and paste images
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

        # 8. Save the composite image to bytes
        img_byte_arr = io.BytesIO()
        composite_image.save(img_byte_arr, format='PNG')
        png_bytes = img_byte_arr.getvalue()

        # 9. Store as a new artifact
        comparison_part = genai.types.Part.from_bytes(data = png_bytes, mime_type="image/png")
        version = await tool_context.save_artifact(filename = "latest_comparison", artifact = comparison_part)

        return "Successfully created comparison image artifact with key 'latest_comparison' and it has version {version}."

    except Exception as e:
        return f"Error creating and storing comparison image artifact: {str(e)}"