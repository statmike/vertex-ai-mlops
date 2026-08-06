"""agent_mcp_client — an agent whose tools come entirely from an MCP server.

This is the *consuming* side of MCP, and the counterpart to ``mcp_server/`` (which
publishes theLook's tools). Where the other agents import Python tool functions
directly, this agent is handed an ``McpToolset`` pointed at a remote MCP server:
at runtime ADK connects, calls the server's ``list_tools``, and turns each into a
callable tool. So the tools you see here are literally *the MCP server's tools* —
none are defined in this package.

Transport is **Streamable-HTTP**, the production MCP transport: the server is a
separate process (locally ``python -m mcp_server.server --transport http``; in
production a Cloud Run service), not an in-process import and not a stdio
subprocess. That's the pattern Google recommends for MCP servers consumed from
Agent Runtime — it scales independently and avoids shipping a Node/npx subprocess
inside the agent container.

Run locally:
    # 1. start the MCP server
    uv run python -m mcp_server.server --transport http --port 8009
    # 2. run this agent (adk web, or import root_agent)
    uv run adk web agent_mcp_client
"""

import os

from config import MCP_CLIENT_MODEL, MCP_CLIENT_MODEL_LOCATION

# Pick the inference endpoint before importing ADK (same pattern as the concierge).
if MCP_CLIENT_MODEL_LOCATION:
    os.environ["GOOGLE_CLOUD_LOCATION"] = MCP_CLIENT_MODEL_LOCATION

from google.adk.agents import Agent  # noqa: E402
from google.adk.tools.mcp_tool import McpToolset  # noqa: E402
from google.adk.tools.mcp_tool.mcp_session_manager import (  # noqa: E402
    StreamableHTTPConnectionParams,
)

from config import MCP_SERVER_URL  # noqa: E402

from . import prompts  # noqa: E402

# The whole toolset is remote: ADK fetches the tool list from the MCP server at
# the URL below. Nothing here enumerates the tools — that's the point of MCP.
mcp_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url=MCP_SERVER_URL),
)

root_agent = Agent(
    model=MCP_CLIENT_MODEL,
    name="agent_mcp_client",
    description=(
        "Answers theLook retail questions using tools discovered from a remote "
        "MCP server (documents, sales analytics, data catalog)."
    ),
    global_instruction=prompts.global_instructions,
    instruction=prompts.agent_instructions,
    tools=[mcp_toolset],
)
