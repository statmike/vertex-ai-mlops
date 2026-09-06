"""Print the real tool inventory of every MCP server this sandbox uses.

    uv run python examples/probe_tool_inventory.py [--tier 1]

**Diagnostic, not scored.** `docs/paths.md` claims the managed
servers expose a narrower surface than self-hosted Toolbox. That claim decides
which paths can answer which question categories, so it should be reproducible
on demand rather than cited from documentation that will drift.

This calls `tools/list` against each server and prints what actually comes back,
plus the per-server difference.
"""

import argparse
import asyncio
import sys

import _bootstrap  # noqa: F401 - import for the sys.path side effect
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

import config
import mcp_clients
import toolbox_server


async def tool_names(toolset: McpToolset) -> list[str]:
    """`tools/list` against one server, unfiltered."""
    tools = await toolset.get_tools()
    return sorted(tool.name for tool in tools)


async def probe_managed(url: str, tier: int) -> list[str]:
    toolset = mcp_clients._managed_toolset(url, [], tier)  # noqa: SLF001 - diagnostic, no filter
    try:
        return await tool_names(toolset)
    finally:
        await toolset.close()


async def probe_toolbox(tools: list[str], tier: int) -> list[str]:
    return await _probe_server(toolbox_server.start(tools, tier))


async def probe_prebuilt(prebuilt: str) -> list[str]:
    """What a Toolbox source actually ships, from the vendor's own config.

    `probe_toolbox` renders *our* curated tool list, so it can only ever return
    what we asked for — it cannot answer "how wide is this source", which is
    what F4 claims. This can.
    """
    return await _probe_server(toolbox_server.start_prebuilt(prebuilt))


async def _probe_server(server: toolbox_server.Server) -> list[str]:
    toolset = McpToolset(
        connection_params=mcp_clients.StreamableHTTPConnectionParams(url=server.url, timeout=60)
    )
    try:
        return await tool_names(toolset)
    finally:
        await toolset.close()
        server.stop()


def show(title: str, names: list[str]) -> None:
    print(f"\n{title}  ({len(names)} tools)")
    for name in names:
        print(f"    {name}")


async def main_async(tier: int) -> int:
    print(f"Probing MCP tool inventories (tier {tier}, project {config.require_project()})")

    managed_bq = await probe_managed(mcp_clients.MANAGED_BIGQUERY_URL, tier)
    managed_dp = await probe_managed(mcp_clients.MANAGED_DATAPLEX_URL, tier)
    show("Managed BigQuery MCP", managed_bq)
    show("Managed Knowledge Catalog MCP", managed_dp)

    prebuilt_bq = await probe_prebuilt("bigquery")
    prebuilt_dp = await probe_prebuilt("dataplex")
    show("Toolbox bigquery source, as shipped (--prebuilt)", prebuilt_bq)
    show("Toolbox dataplex source, as shipped (--prebuilt)", prebuilt_dp)

    toolbox_bq = await probe_toolbox(mcp_clients.TOOLBOX_BIGQUERY_TOOLS, tier)
    toolbox_dp = await probe_toolbox(mcp_clients.TOOLBOX_DATAPLEX_TOOLS, tier)
    show("Toolbox bigquery source, as this sandbox configures it", toolbox_bq)
    show("Toolbox dataplex source, as this sandbox configures it", toolbox_dp)

    if config.looker_configured():
        try:
            show("Looker instance MCP", await probe_managed(mcp_clients.looker_mcp_url(), tier))
        except Exception as e:  # noqa: BLE001 - a diagnostic must report, not crash
            print(f"\nLooker instance MCP: UNREACHABLE — {type(e).__name__}: {e}")
            print("    In preview an admin must pre-register this agent as an OAuth client app.")
    else:
        print("\nLooker instance MCP: SKIPPED (LOOKER_BASE_URL is unset or still the placeholder)")

    print("\nDifference — what Toolbox ships that managed does not (docs/paths.md):")
    print(f"    bigquery: {sorted(set(prebuilt_bq) - set(managed_bq)) or 'nothing'}")
    print(f"    dataplex: {sorted(set(prebuilt_dp) - set(managed_dp)) or 'nothing'}")
    print("\nWhat managed has that Toolbox does not:")
    print(f"    bigquery: {sorted(set(managed_bq) - set(prebuilt_bq)) or 'nothing'}")
    print(f"    dataplex: {sorted(set(managed_dp) - set(prebuilt_dp)) or 'nothing'}")
    print("\nShipped but NOT wired into this sandbox's Path 3 (see TOOLBOX_DATAPLEX_TOOLS):")
    print(f"    bigquery: {sorted(set(prebuilt_bq) - set(toolbox_bq)) or 'nothing'}")
    print(f"    dataplex: {sorted(set(prebuilt_dp) - set(toolbox_dp)) or 'nothing'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", type=int, default=1, choices=config.TIERS)
    args = parser.parse_args()
    return asyncio.run(main_async(args.tier))


if __name__ == "__main__":
    sys.exit(main())
