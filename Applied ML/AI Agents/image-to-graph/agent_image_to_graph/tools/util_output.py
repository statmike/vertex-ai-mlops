import os
import re
from urllib.parse import urlparse

from google.adk import tools

# Project-level examples directory (sibling to agent_image_to_graph/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_EXAMPLES_DIR = os.path.join(_PROJECT_ROOT, "examples")


def get_results_dir(tool_context: tools.ToolContext) -> str | None:
    """Return the absolute path to the results directory for the current run.

    Resolution order:
    1. If the source file is a **local path inside the project's examples/**
       directory, results go next to the file (existing behaviour).
    2. Otherwise (GCS path, URL, or local file outside examples/), a folder
       is created under ``<project>/examples/<folder-name>/`` derived from
       the source reference.

    Within the chosen parent directory, a sub-folder is created:
    - ``results-with-schema/``    when ``input_schema`` is set
    - ``results-without-schema/`` otherwise

    Returns ``None`` when the graph or its ``source_file`` metadata is missing,
    allowing callers to fall back to artifact-only behaviour.
    """
    graph = tool_context.state.get("graph")
    if not graph:
        return None

    source_file = graph.get("metadata", {}).get("source_file")
    if not source_file:
        return None

    subfolder = (
        "results-with-schema"
        if tool_context.state.get("input_schema")
        else "results-without-schema"
    )

    # Determine parent directory for results
    parent_dir = _resolve_parent_dir(source_file)

    results_dir = os.path.join(parent_dir, subfolder)
    os.makedirs(results_dir, exist_ok=True)
    return os.path.abspath(results_dir)


def _resolve_parent_dir(source_file: str) -> str:
    """Decide where results should live based on the source file reference.

    - Local files already under ``examples/`` → directory containing the file.
    - Everything else → a new folder under ``<project>/examples/``.
    """
    # Check if it's a local path (not GCS/URL)
    is_remote = source_file.startswith(("gs://", "http://", "https://"))

    if not is_remote:
        local_abs = os.path.abspath(os.path.expanduser(source_file))
        examples_abs = os.path.abspath(_EXAMPLES_DIR)
        if local_abs.startswith(examples_abs + os.sep):
            # Already under examples/ — use the file's own directory
            return os.path.dirname(local_abs)

    # Remote or local-outside-examples: create a folder under examples/
    folder_name = _folder_name_from_source(source_file)
    parent = os.path.join(_EXAMPLES_DIR, folder_name)
    os.makedirs(parent, exist_ok=True)
    return parent


def _folder_name_from_source(source: str) -> str:
    """Derive a filesystem-safe folder name from a source reference.

    Examples:
        gs://my-bucket/diagrams/arch.png  → gcs-my-bucket-arch
        https://example.com/path/flow.png → url-example-com-flow
        /home/user/docs/diagram.png       → local-diagram
    """
    # Extract the meaningful filename (without extension)
    if source.startswith("gs://"):
        path_part = source[5:]  # strip gs://
        bucket = path_part.split("/")[0]
        basename = os.path.splitext(os.path.basename(path_part))[0]
        raw = f"gcs-{bucket}-{basename}"
    elif source.startswith(("http://", "https://")):
        parsed = urlparse(source)
        host = parsed.hostname or "unknown"
        basename = os.path.splitext(os.path.basename(parsed.path))[0] or "download"
        raw = f"url-{host}-{basename}"
    else:
        basename = os.path.splitext(os.path.basename(source))[0]
        raw = f"local-{basename}"

    # Sanitize: lowercase, replace non-alphanumeric with hyphens, collapse
    sanitized = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    return sanitized or "unknown-source"
