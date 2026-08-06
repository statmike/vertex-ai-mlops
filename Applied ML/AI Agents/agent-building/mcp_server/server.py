"""A low-level MCP server that publishes theLook's tools.

Run it one of two ways:

    # stdio — how a desktop MCP client (Claude Desktop, an IDE) launches a server
    uv run python -m mcp_server.server --transport stdio

    # Streamable-HTTP — the production transport; the ADK McpToolset consumer
    # (agent_concierge/sub_agents/agent_web) connects to this over HTTP
    uv run python -m mcp_server.server --transport http --port 8009

The server wires the :mod:`mcp_server.registry` tools into MCP's two required
handlers — ``list_tools`` (advertise schemas) and ``call_tool`` (execute) — using
``adk_to_mcp_tool_type`` so the advertised schema is exactly the ADK tool's,
minus the context parameter.

Deploying this for real: package the Streamable-HTTP app behind a Cloud Run
service (set ``stateless=True`` so it scales horizontally) and point the consumer
at its URL. That sidesteps the stdio/subprocess path entirely, which is the
pattern Google recommends for MCP servers consumed by Agent Runtime.
"""

from __future__ import annotations

import argparse
import contextlib
from collections.abc import AsyncIterator

import mcp.types as mcp_types
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type
from mcp.server.lowlevel import Server

from mcp_server.registry import HOSTED_TOOLS, hosted_tools_by_name

SERVER_NAME = "thelook-tools"


def build_server() -> Server:
    """Build the MCP server with theLook's tools mounted."""
    app: Server = Server(SERVER_NAME)
    by_name = hosted_tools_by_name()

    @app.list_tools()
    async def list_tools() -> list[mcp_types.Tool]:
        # Advertise each ADK tool's MCP schema (name, description, inputSchema).
        return [adk_to_mcp_tool_type(t.function_tool) for t in HOSTED_TOOLS]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[mcp_types.ContentBlock]:
        tool = by_name.get(name)
        if tool is None:
            return [mcp_types.TextContent(type="text", text=f"Unknown tool: {name}")]
        answer = await tool.run(arguments or {})
        return [mcp_types.TextContent(type="text", text=answer)]

    return app


async def _run_stdio(app: Server) -> None:
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def _http_app(app: Server):
    """A Starlette ASGI app serving the MCP server over Streamable-HTTP."""
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.routing import Mount

    # stateless=True: no server-side session affinity, so the service scales
    # horizontally behind Cloud Run — the recommended production posture.
    manager = StreamableHTTPSessionManager(app=app, stateless=True)

    async def handle(scope, receive, send):
        await manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncIterator[None]:
        async with manager.run():
            yield

    return Starlette(routes=[Mount("/mcp", app=handle)], lifespan=lifespan)


def main() -> None:
    parser = argparse.ArgumentParser(description="theLook MCP tool server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8009)
    args = parser.parse_args()

    app = build_server()

    if args.transport == "stdio":
        import anyio

        anyio.run(_run_stdio, app)
    else:
        import uvicorn

        print(f"Serving MCP over Streamable-HTTP at http://{args.host}:{args.port}/mcp")
        uvicorn.run(_http_app(app), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
