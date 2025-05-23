from .get_gcs_file import get_gcs_file
from .doc_extraction import document_extraction

DOCUMENT_PROCESSING_TOOLS = [
    get_gcs_file,
    document_extraction
]