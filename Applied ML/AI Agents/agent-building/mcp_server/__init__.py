"""Host theLook's agent tools as a Model Context Protocol (MCP) server.

This is the *hosting* side of MCP: it takes the same function tools the ADK
agents already use (``search_docs``, ``analyze_sales``, ``search_catalog``) and
re-publishes them over the MCP wire protocol, so **any** MCP client — Claude
Desktop, another team's agent, an IDE — can call theLook's capabilities without
importing our Python. The consuming side (an ADK agent that *calls* an MCP
server via ``McpToolset``) lives in ``agent_mcp_client/``.

Nothing here re-implements a tool: :mod:`mcp_server.registry` wraps each existing
ADK tool, exposes its schema via ``adk_to_mcp_tool_type``, and executes the very
same coroutine. :mod:`mcp_server.server` mounts that registry on a low-level MCP
server served over stdio (local dev) or Streamable-HTTP (the production
transport an Agent-Runtime or Cloud-Run-hosted server would use).
"""
