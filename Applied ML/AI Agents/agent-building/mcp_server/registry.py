"""Publish the existing ADK tools as MCP tools — schema and execution.

Each entry pairs an ADK tool function with a ``FunctionTool`` wrapper. The wrapper
is only used to *derive the MCP schema* (``adk_to_mcp_tool_type`` reads the
function's signature and docstring and, notably, drops the ``tool_context``
parameter — an MCP client only ever sees ``question``). Execution calls the same
coroutine directly.

**Why a context shim.** The three tools take ``(question, tool_context)`` and use
``tool_context`` only to *write* provenance into ``tool_context.state`` (sources,
surfaced tables) for a downstream ADK agent to chain on. Over MCP there is no ADK
invocation, so a full ``ToolContext`` (which needs a live ``InvocationContext``)
would be pure overhead. :class:`_McpToolContext` supplies just the ``.state``
dict the tools touch; those writes are simply discarded after the call, which is
correct — the MCP response is the answer text, and provenance is an ADK-only
chaining concern.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from google.adk.tools.function_tool import FunctionTool

from agent_concierge.sub_agents.agent_analytics.tools import analyze_sales
from agent_concierge.sub_agents.agent_catalog.tools import search_docs
from agent_discovery.tools import search_catalog


class _McpToolContext:
    """Minimal stand-in for ADK's ToolContext over the MCP boundary.

    The hosted tools only assign to ``tool_context.state`` (see module docstring).
    A plain object with a dict ``state`` satisfies that without constructing a
    full ADK InvocationContext.
    """

    def __init__(self) -> None:
        self.state: dict[str, Any] = {}


@dataclass(frozen=True)
class HostedTool:
    """One tool exposed over MCP: its ADK function plus schema wrapper."""

    func: Callable[..., Awaitable[str]]
    function_tool: FunctionTool = field(init=False)

    def __post_init__(self) -> None:
        # FunctionTool derives name/description/inputSchema from the function.
        object.__setattr__(self, "function_tool", FunctionTool(self.func))

    @property
    def name(self) -> str:
        return self.function_tool.name

    async def run(self, arguments: dict[str, Any]) -> str:
        """Execute the tool with an MCP-supplied argument dict.

        Only ``question`` crosses the wire (adk_to_mcp_tool_type omits the
        context param); the context is synthesized locally.
        """
        question = arguments.get("question", "")
        return await self.func(question=question, tool_context=_McpToolContext())


# The tools theLook publishes over MCP — the same three the ADK agents use.
HOSTED_TOOLS: list[HostedTool] = [
    HostedTool(search_docs),
    HostedTool(analyze_sales),
    HostedTool(search_catalog),
]


def hosted_tools_by_name() -> dict[str, HostedTool]:
    return {t.name: t for t in HOSTED_TOOLS}
