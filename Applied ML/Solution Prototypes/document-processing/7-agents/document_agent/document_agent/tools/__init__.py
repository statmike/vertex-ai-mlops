from .get_gcs_file import get_gcs_file
from .doc_extraction import document_extraction
from .get_doc_embedding import get_doc_embedding
from .bq_query_to_classify import bq_query_to_classify


DOCUMENT_PROCESSING_TOOLS = [
    get_gcs_file,
    document_extraction,
    get_doc_embedding,
    bq_query_to_classify
]