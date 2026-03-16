"""Visual style configurations for receipt and invoice PDFs.

Provides randomized but reproducible style parameters that the Jinja2
templates use to vary fonts, colors, layout, and decorative elements.
Each function accepts a seed for deterministic output.

Usage:
    from modules.styles import receipt_style, invoice_style

    style = receipt_style(seed=7)
    pdf = render_receipt(data, template_dir, style=style)
"""

import random


def receipt_style(seed: int = 0) -> dict:
    """Generate a random receipt visual style.

    Args:
        seed: Random seed for reproducibility.

    Returns:
        Dict of style parameters consumed by receipt.html.
    """
    rng = random.Random(seed)

    fonts = [
        "'Courier New', Courier, monospace",
        "Consolas, 'Courier New', monospace",
        "'Lucida Console', Monaco, monospace",
        "'Andale Mono', monospace",
    ]

    separators = [
        {'heavy': '=' * 40, 'light': '-' * 40},
        {'heavy': '*' * 40, 'light': '. ' * 20},
        {'heavy': '#' * 40, 'light': '- ' * 20},
        {'heavy': '~' * 40, 'light': '~' * 40},
        {'heavy': '= ' * 20, 'light': '. ' * 20},
    ]

    templates = [
        'receipt_thermal.html',
        'receipt_compact.html',
        'receipt_itemized.html',
    ]

    sep = rng.choice(separators)
    width_mm = rng.randint(68, 80)

    return {
        'template': rng.choice(templates),
        'font_family': rng.choice(fonts),
        'font_size': rng.choice(['10px', '11px', '12px']),
        'line_height': rng.choice(['1.3', '1.4', '1.5']),
        'page_width': f'{width_mm + 10}mm',
        'body_width': f'{width_mm}mm',
        'header_align': rng.choice(['center', 'left']),
        'store_name_upper': rng.choice([True, False]),
        'store_name_size': rng.choice(['14px', '16px', '18px']),
        'divider_heavy': sep['heavy'],
        'divider_light': sep['light'],
        'grand_total_border': rng.choice([
            '1px dashed #000',
            '1px solid #000',
            '2px solid #000',
            '1px double #000',
        ]),
        'show_barcode': rng.choice([True, True, False]),
        'footer_message': rng.choice([
            'THANK YOU FOR SHOPPING WITH US!',
            'THANK YOU! PLEASE COME AGAIN!',
            'WE APPRECIATE YOUR BUSINESS!',
            'THANK YOU FOR YOUR PURCHASE!',
            'HAVE A GREAT DAY!',
        ]),
    }


def invoice_style(seed: int = 0) -> dict:
    """Generate a random invoice visual style.

    Args:
        seed: Random seed for reproducibility.

    Returns:
        Dict of style parameters consumed by invoice.html.
    """
    rng = random.Random(seed)

    palettes = [
        {'accent': '#2c3e50', 'accent_text': '#fff'},
        {'accent': '#1a5276', 'accent_text': '#fff'},
        {'accent': '#0e6655', 'accent_text': '#fff'},
        {'accent': '#78281f', 'accent_text': '#fff'},
        {'accent': '#1e8449', 'accent_text': '#fff'},
        {'accent': '#4a235a', 'accent_text': '#fff'},
        {'accent': '#7e5109', 'accent_text': '#fff'},
        {'accent': '#1b2631', 'accent_text': '#fff'},
        {'accent': '#c0392b', 'accent_text': '#fff'},
        {'accent': '#2471a3', 'accent_text': '#fff'},
    ]

    fonts = [
        "'Helvetica Neue', Helvetica, Arial, sans-serif",
        "Georgia, 'Times New Roman', serif",
        "'Trebuchet MS', 'Lucida Grande', sans-serif",
        "'Segoe UI', Tahoma, Geneva, sans-serif",
    ]

    templates = [
        'invoice_corporate.html',
        'invoice_banner.html',
        'invoice_minimal.html',
    ]

    palette = rng.choice(palettes)

    return {
        'template': rng.choice(templates),
        'accent_color': palette['accent'],
        'accent_text': palette['accent_text'],
        'font_family': rng.choice(fonts),
        'font_size': rng.choice(['10px', '11px']),
        'title_size': rng.choice(['24px', '28px', '32px']),
        'header_border': f"{rng.choice(['2px', '3px', '4px'])} solid {palette['accent']}",
        'table_style': rng.choice(['striped', 'bordered', 'minimal']),
        'company_name_size': rng.choice(['20px', '22px', '24px']),
    }
