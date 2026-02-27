import os
from google.adk import tools


def get_results_dir(tool_context: tools.ToolContext) -> str | None:
    """Return the absolute path to the results directory next to the source image.

    The directory name depends on whether a schema was provided:
    - ``results-with-schema/``    when ``input_schema`` is set
    - ``results-without-schema/`` otherwise

    The directory is created if it does not already exist.

    Returns ``None`` when the graph or its ``source_file`` metadata is missing,
    allowing callers to fall back to artifact-only behaviour.
    """
    graph = tool_context.state.get('graph')
    if not graph:
        return None

    source_file = graph.get('metadata', {}).get('source_file')
    if not source_file:
        return None

    parent_dir = os.path.dirname(os.path.expanduser(source_file))
    subfolder = (
        'results-with-schema'
        if tool_context.state.get('input_schema')
        else 'results-without-schema'
    )

    results_dir = os.path.join(parent_dir, subfolder)
    os.makedirs(results_dir, exist_ok=True)
    return os.path.abspath(results_dir)
