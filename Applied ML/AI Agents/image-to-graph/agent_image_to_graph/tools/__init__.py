from .function_tool_load_image import load_image
from .function_tool_load_schema import load_schema
from .function_tool_analyze_image import analyze_image
from .function_tool_crop_and_examine import crop_and_examine
from .function_tool_trace_connections import trace_connections
from .function_tool_update_graph import update_graph
from .function_tool_get_graph import get_graph
from .function_tool_generate_schema import generate_schema
from .function_tool_validate_graph import validate_graph
from .function_tool_generate_description import generate_description
from .function_tool_export_result import export_result
from .function_tool_generate_visualization import generate_visualization

TOOLS = [
    load_image,
    load_schema,
    analyze_image,
    crop_and_examine,
    trace_connections,
    update_graph,
    get_graph,
    generate_schema,
    validate_graph,
    generate_description,
    export_result,
    generate_visualization,
]
