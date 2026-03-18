from .function_tool_assess_image import assess_image
from .function_tool_detect_connections import detect_connections
from .function_tool_detect_elements import detect_elements
from .function_tool_label_elements import label_elements
from .function_tool_report_results import report_results

TOOLS = [
    assess_image,
    detect_elements,
    detect_connections,
    label_elements,
    report_results,
]
