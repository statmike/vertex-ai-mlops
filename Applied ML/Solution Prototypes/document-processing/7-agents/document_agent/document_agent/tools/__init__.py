from .get_gcs_file import get_gcs_file
from .get_user_file import get_user_file
from .doc_extraction import document_extraction
from .get_doc_embedding import get_doc_embedding
from .bq_query_to_classify import bq_query_to_classify
from .bq_query_to_predict_classification import bq_query_to_predict_classification
from .load_vendor_template import load_vendor_template
from .diplay_images_side_by_side import display_images_side_by_side
from .compare_documents import compare_documents

DOCUMENT_PROCESSING_TOOLS = [
    get_gcs_file,
    get_user_file,
    document_extraction,
    get_doc_embedding,
    bq_query_to_classify,
    load_vendor_template,
    display_images_side_by_side,
    compare_documents
]

DOCUMENT_CLASSIFICATION_TOOLS = [
    bq_query_to_predict_classification
]