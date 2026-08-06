"""Tests for the MCP hosting registry (offline).

Verify that each ADK tool is published with a clean MCP schema (the context
parameter dropped, only ``question`` exposed), that the context shim accepts the
provenance writes the tools make, and that execution routes ``question`` through.
"""

import pytest
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

from mcp_server.registry import (
    HOSTED_TOOLS,
    HostedTool,
    _McpToolContext,
    hosted_tools_by_name,
)


def test_hosted_tools_expose_only_question():
    """adk_to_mcp_tool_type must drop tool_context — clients only send question."""
    assert {t.name for t in HOSTED_TOOLS} == {"search_docs", "analyze_sales", "search_catalog"}
    for tool in HOSTED_TOOLS:
        schema = adk_to_mcp_tool_type(tool.function_tool)
        props = schema.inputSchema.get("properties", {})
        assert list(props) == ["question"], f"{tool.name} should expose only 'question'"
        assert "tool_context" not in props


def test_by_name_maps_every_tool():
    by_name = hosted_tools_by_name()
    assert set(by_name) == {t.name for t in HOSTED_TOOLS}


def test_shim_accepts_state_writes():
    """The tools write provenance into tool_context.state; the shim must allow it."""
    ctx = _McpToolContext()
    ctx.state["catalog_last_sources"] = ["return_policy.md"]
    assert ctx.state["catalog_last_sources"] == ["return_policy.md"]


@pytest.mark.asyncio
async def test_run_routes_question_and_synthesizes_context():
    """HostedTool.run passes 'question' through and supplies a working context."""
    captured = {}

    async def fake(question, tool_context):
        captured["question"] = question
        tool_context.state["wrote"] = True  # must not raise
        return "ok"

    tool = HostedTool(fake)
    result = await tool.run({"question": "where are orders?"})
    assert result == "ok"
    assert captured["question"] == "where are orders?"
