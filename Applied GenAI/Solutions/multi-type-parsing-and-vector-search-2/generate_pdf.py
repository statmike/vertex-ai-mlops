"""Fetch web pages and save as PDF files using WeasyPrint."""

from weasyprint import HTML
from pathlib import Path
from urllib.parse import urlparse
import re

# --- URLs to convert (replace with your real URLs) ---

urls = [
    "https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series",
    "https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-multivariate-time-series",
    "https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-forecast",
    "https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-detect-anomalies",
    "https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-evaluate",
    "https://docs.cloud.google.com/bigquery/docs/auto-preprocessing",
    "https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-arima-coefficients",
    "https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-arima-evaluate",
    "https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-holiday-info",
    "https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-forecast",
    "https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-detect-anomalies",
    "https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-explain-forecast",
]

# --- Output ---

output_dir = Path("generated_pdf")
output_dir.mkdir(exist_ok=True)

# --- Convert each URL to PDF ---

def slugify(url: str) -> str:
    """Turn a URL path into a safe filename."""
    path = urlparse(url).path.strip("/")
    return re.sub(r"[^a-zA-Z0-9]+", "_", path).strip("_")

for url in urls:
    filename = slugify(url) + ".pdf"
    output_file = output_dir / filename
    HTML(url=url).write_pdf(output_file)
    print(f"Created: {output_file}")
