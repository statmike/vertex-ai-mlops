"""Tool to return pre-loaded Knowledge Context capsules from the shared cache.

The context is populated once at startup by the ``context_cache`` module.
Every ``initialize_context`` tool call returns instantly from that cache.
"""

from google.adk import tools

from context_cache import get_all_detailed


async def initialize_context(
    tool_context: tools.ToolContext,
) -> str:
    """Return pre-loaded Knowledge Context capsules for all tables in scope.

    The context is populated once at startup by the shared ``context_cache``
    module (when ``adk web`` or ``adk run`` starts).  This tool returns the
    cached result instantly.

    Returns:
        The full knowledge context string for all tables in scope.
    """
    return get_all_detailed()
