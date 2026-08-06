"""Tests for the MCP-client agent wiring (offline — no server contacted).

We can't list live tools without a running MCP server (that path is exercised by
an integration check), so here we pin the *contract*: the agent's toolset is an
McpToolset pointed at the configured Streamable-HTTP URL, and the agent defines
no local tools of its own — everything is remote by design.
"""

from google.adk.tools.mcp_tool import McpToolset

from agent_mcp_client.agent import mcp_toolset, root_agent


def test_agent_has_exactly_one_toolset_and_it_is_mcp():
    """The whole toolset is the MCP toolset — no hand-written tools here."""
    assert root_agent.tools == [mcp_toolset]
    assert isinstance(mcp_toolset, McpToolset)


def test_toolset_points_at_configured_streamable_http_url():
    import config

    params = mcp_toolset._mcp_session_manager._connection_params
    assert params.url == config.MCP_SERVER_URL
    # Streamable-HTTP (the production transport), not stdio/SSE.
    assert type(params).__name__ == "StreamableHTTPConnectionParams"


def test_agent_identity():
    import config

    assert root_agent.name == "agent_mcp_client"
    assert root_agent.model == config.MCP_CLIENT_MODEL
