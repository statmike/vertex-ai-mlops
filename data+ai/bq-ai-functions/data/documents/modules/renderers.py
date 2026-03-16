"""HTML-to-PDF renderers for receipts and invoices.

Uses Jinja2 for HTML templating and weasyprint for PDF conversion.
Each function returns raw PDF bytes — the caller decides where to save.

An optional ``style`` dict controls visual appearance (fonts, colors,
separators, layout).  When omitted, a default style is used.  See
``modules/styles.py`` for the style generators.
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML


def _render_template(template_name: str, context: dict, template_dir: Path) -> bytes:
    """Render an HTML template to PDF bytes.

    Args:
        template_name: Filename of the Jinja2 template (e.g. 'receipt.html').
        context: Template context dictionary (data + style).
        template_dir: Path to the directory containing templates.

    Returns:
        PDF file contents as bytes.
    """
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template(template_name)
    html_str = template.render(**context)
    return HTML(string=html_str).write_pdf()


def render_receipt(data: dict, template_dir: Path, style: dict | None = None) -> bytes:
    """Render receipt data to PDF bytes.

    Args:
        data: Receipt dictionary (store_name, items, total, etc.).
        template_dir: Path to the templates/ directory.
        style: Visual style dict from styles.receipt_style().
               Uses default style when omitted.

    Returns:
        PDF file contents as bytes.
    """
    if style is None:
        from modules.styles import receipt_style
        style = receipt_style()
    template_name = style.get('template', 'receipt_thermal.html')
    context = {**data, 'style': style}
    return _render_template(template_name, context, template_dir)


def render_invoice(data: dict, template_dir: Path, style: dict | None = None) -> bytes:
    """Render invoice data to PDF bytes.

    Args:
        data: Invoice dictionary (company_name, line_items, total_due, etc.).
        template_dir: Path to the templates/ directory.
        style: Visual style dict from styles.invoice_style().
               Uses default style when omitted.

    Returns:
        PDF file contents as bytes.
    """
    if style is None:
        from modules.styles import invoice_style
        style = invoice_style()
    template_name = style.get('template', 'invoice_corporate.html')
    context = {**data, 'style': style}
    return _render_template(template_name, context, template_dir)
