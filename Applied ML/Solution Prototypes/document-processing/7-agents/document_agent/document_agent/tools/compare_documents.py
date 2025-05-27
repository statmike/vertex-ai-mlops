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
        You are a highly meticulous Visual and Structural Document Comparison AI.
        Your mission is to conduct an exhaustive comparison between two document images:
        1.  An 'original document' (the first image Part provided).
        2.  A 'vendor template' (the second image Part provided), which serves as the gold standard for correct formatting, layout, and structural integrity.

        **Primary Objective:**
        Identify, detail, and report ALL visual formatting, layout, and structural discrepancies between the original document and the vendor template. The goal is to determine how much the original deviates from the authenticated template in its presentation.

        **Secondary Objective (Textual Elements):**
        For specific, visually distinct textual elements crucial to branding or structure (e.g., logos, company names in headers/footers, main section titles, key form field labels), note if the textual content itself appears different, in addition to its formatting.
        **Crucially, AVOID comparing large blocks of body text or general paragraph content for semantic meaning or minor wording variations.** Your analysis must remain primarily visual and structural.

        **Detailed Analysis & Reporting Tasks:**

        1.  **Comprehensive Visual and Structural Examination:**
            Conceptually (as you process their image data), place the original document and vendor template side-by-side. Meticulously scrutinize them, comparing element by element, section by section, from top to bottom, left to right.

        2.  **Detailed Discrepancy Report – Be Specific, Granular, and Quantify where Possible:**
            For every identified difference, provide a clear, unambiguous description. Where feasible, quantify the difference or describe its nature precisely (e.g., "Logo shifted approximately 5mm to the left and 2mm up compared to template," "Main title font size is 14pt in original, whereas template uses 16pt," "Border around the address block is a dashed line in original but a solid line in template," "The disclaimer text block is missing in the original.").

            **Pay extremely close attention to the following categories and aspects:**

            * **Overall Document Layout & Structure:**
                * Margins: Differences in top, bottom, left, right margins (e.g., "Original has significantly wider left margin").
                * Page Dimensions/Aspect Ratio: If there's a noticeable difference.
                * Column Layout: Number of columns, their widths, and gutter spacing.
                * Whitespace Distribution: Overall use of negative space; does one document appear more cramped or sparse?
                * Sectioning: Relative positioning, sizing, and ordering of major content blocks (e.g., header, body, footer, sidebars).
                * Presence/Absence: Are entire expected sections or key structural blocks missing or unexpectedly added in the original?

            * **Logos and Critical Branding Elements (e.g., Company Name in Header, Watermarks):**
                * Logo Image: Fidelity, clarity, any pixelation or distortion. Is it the correct version of the logo?
                * Text within Logo/Branding: Exact wording, capitalization, and font style if part of the graphic.
                * Color Accuracy: Are the brand colors in the logo/elements precise matches? (e.g., "Logo's primary red is a duller shade in the original").
                * Size & Dimensions: Relative or absolute size differences.
                * Positioning & Alignment: Exact coordinates or relative placement (e.g., "Logo in header is not aligned with the right margin in the original, unlike the template").

            * **Headers and Footers:**
                * Content Elements: Presence, absence, or variation in formatting of page numbers, document titles, revision dates, confidentiality markers, etc.
                * Positional Consistency: Are these elements consistently placed across both documents?
                * Styling: Font, size, color used within headers/footers.

            * **Text Element Formatting (Focus on Visual Style, not general prose):**
                * **Fonts:**
                    * Font Family/Typeface: Clear differences (e.g., "Original uses a Serif font for body text, template uses Sans-serif"). Try to be specific if a font is common (Arial, Times New Roman).
                    * Font Size: Point size differences for headings, subheadings, body text, captions, etc.
                    * Font Weight/Style: Bold, italic, underline, regular, light, condensed, expanded.
                    * Font Color: Deviations from expected colors.
                    * Line Spacing (Leading): Space between lines of text within a paragraph.
                    * Character Spacing (Kerning/Tracking): If visually apparent as significantly different.
                * **Text Block Alignment:** Left, right, center, justified for paragraphs and titles.
                * **Indentation:** Paragraphs, lists, block quotes.
                * **List Styles:** Bullet point shapes, numbering formats.

            * **Table Structure & Formatting (Analyze visual presentation, not just data within cells):**
                * Overall Table Position & Size.
                * Row/Column Structure: Discrepancies in the number of rows/columns if visually obvious.
                * Border Styles: Thickness, color, type (solid, dashed, double), presence/absence of internal/external borders.
                * Cell Padding & Spacing: Visual differences in spacing within and between cells.
                * Header Row/Column Formatting: Distinct background color, font style, alignment.
                * Alternating Row Shading (Zebra Stripes): Presence, color, and application.

            * **Images, Icons, and Graphical Elements (other than the main logo):**
                * Positioning, Size, & Alignment.
                * Aspect Ratio: Is it maintained or distorted?
                * Resolution/Clarity: Is one noticeably blurry or of lower quality?
                * Presence/Absence/Substitution: Are expected images/icons missing, or different ones used?
                * Style of Lines & Shapes: Thickness, color, style (solid, dotted, arrowheads), fill colors for shapes.

            * **Color Scheme & Visual Styles:**
                * Background Colors: Page background, section backgrounds.
                * Consistent Application of Brand Colors: Beyond the logo, are primary/secondary brand colors used consistently or incorrectly?
                * Overall Visual Consistency and Professionalism compared to the template.

        3.  **Structure of Your Output:**
            Organize your findings clearly. A good approach is a list of bullet points, categorized by the element type (e.g., "Logo Differences:", "Header Formatting:", "Table Structure:"), or a detailed narrative that flows section by section through the document.
            Begin with a concise overall summary if there are widespread or particularly significant deviations.

        **Example of a Detailed Difference Description:**
            * "**Logo & Branding:**
                * The company logo on the original document is located in the top-left corner, whereas the template positions it in the top-center.
                * The original document's logo appears to be approximately 15% smaller in scale than the template's logo.
                * The tagline text beneath the logo in the original uses 'Arial Regular', while the template specifies 'Arial Italic' and is a slightly darker grey."
            * "**Main Body Text Formatting:**
                * The original document uses a 10pt font for body paragraphs, while the template uses 11pt.
                * Line spacing in the original is single-spaced, but the template appears to use 1.15 line spacing, resulting in a denser text block in the original."

        Your comprehensive and precise report is critical for assessing the document's adherence to the official vendor template. Strive for accuracy and completeness in detailing every visual and structural deviation.
    """

    try:
        # 1. Load the artifacts
        original_doc_artifact = await tool_context.load_artifact(filename = original_document_artifact_key)
        template_doc_artifact = await tool_context.load_artifact(filename = template_document_artifact_key)

        # 2. requests
        response = client.models.generate_content(
            model = 'gemini-2.0-pro',
            contents = [original_doc_artifact, template_doc_artifact, prompt],
            config = genai.types.GenerateContentConfig(
                system_instruction = """You are specialized in comparing two documents, an 'original document' and a 'vendor template', for formatting differences."""
            )
        )

        return response.text



    except Exception as e:
        return f"An error occurred comparing the doucments: {str(e)}"
