"""The 8 configurations, and the MCP toolsets each one binds.

This is the experiment's independent variable made concrete. Every config is the
*same brain* (`config.AGENT_MODEL`) pointed at a different tool surface, so any
score difference is attributable to the architecture rather than the model.

Two server flavours:

- **Managed** — Google-hosted remote HTTP MCP on a `googleapis.com` host, or the
  Looker instance's own `/mcp`. Auth is a bearer token, minted fresh per request
  by `_header_provider` (CODE_STANDARDS §4 — never a service-account key).
- **Toolbox** — a self-hosted subprocess per config, tier-scoped and read-only.
  See `toolbox_server.py` for why the prebuilt configs are not used directly.

Neither managed server can be scoped by request: they expose no dataset
allowlist, and `search_entries` takes a query rather than a scope. Both are
scoped by *caller* instead — every toolset here is bound to a tier and mints
that tier's impersonated token, so the two arms of the experiment are separated
by IAM. Toolbox additionally enforces `allowedDatasets` in the server. See
`identity.py` and `docs/scoping.md`.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

import config
import identity
import looker_client
import toolbox_server

MANAGED_BIGQUERY_URL = "https://bigquery.googleapis.com/mcp"
MANAGED_DATAPLEX_URL = "https://dataplex.googleapis.com/mcp"

# Managed BigQuery MCP exposes execute_sql *and* execute_sql_readonly. Only the
# read-only one is bound, so no agent can mutate the corpus mid-sweep. This is
# the managed counterpart to Toolbox's `writeMode: blocked`.
MANAGED_BIGQUERY_TOOLS = [
    "list_dataset_ids",
    "list_table_ids",
    "get_dataset_info",
    "get_table_info",
    "execute_sql_readonly",
]
MANAGED_DATAPLEX_TOOLS = ["search_entries", "lookup_entry", "lookup_context"]

# The Toolbox names for exactly what the managed endpoints expose, for the matched
# arms (Amendment A.3.3). The only name that differs across the two servers is the
# executor — managed calls it `execute_sql_readonly`, Toolbox `execute_sql` under
# `writeMode: blocked` — so these are equivalent surfaces, not identical strings.
MATCHED_BIGQUERY_TOOLS = [
    "list_dataset_ids",
    "list_table_ids",
    "get_dataset_info",
    "get_table_info",
    "execute_sql",
]
MATCHED_DATAPLEX_TOOLS = ["search_entries", "lookup_entry", "lookup_context"]

TOOLBOX_BIGQUERY_TOOLS = [
    "list_dataset_ids",
    "list_table_ids",
    "get_dataset_info",
    "get_table_info",
    "execute_sql",
    "forecast",
    "analyze_contribution",
    "ask_data_insights",
]
# `--prebuilt dataplex` ships 24 tools. All 15 read-only ones are bound; the 9
# that mutate or trigger billable scan jobs are not, because the dataplex source
# has no `writeMode` equivalent to neuter them with (docs/paths.md).
#
# Reachability in *this corpus* is uneven and was measured, not assumed.
# `get_data_quality_results` used to return a profile scan
# with no `dataQualityResult` field rather than an error, so an agent got a
# confident-looking success carrying nothing. Since 2026-09-05 the corpus carries
# real DATA_QUALITY scans (`catalog_setup.create_and_run_quality_scans`) and it
# returns rules and failure rates, so any capture from before that date measured
# a different surface than one taken after.
TOOLBOX_DATAPLEX_TOOLS = [
    "search_entries",
    "lookup_entry",
    "lookup_context",
    "search_aspect_types",
    "search_dq_scans",
    "get_data_profile",
    "get_data_quality_results",
    "get_data_insights",
    "get_discovery_results",
    "get_run_status",
    "get_operation",
    "list_data_products",
    "get_data_product",
    "list_data_assets",
    "get_data_asset",
]
TOOLBOX_LOOKER_TOOLS = [
    "get_models",
    "get_explores",
    "get_dimensions",
    "get_measures",
    "get_filters",
    "query",
    "query_sql",
]


@dataclass(frozen=True)
class PathConfig:
    """One cell of the 4-path x 2-variant matrix (docs/paths.md)."""

    key: str
    path: int
    name: str
    variant: str  # "managed" or "toolbox"
    summary: str
    managed_urls: dict[str, list[str]] = field(default_factory=dict)  # url -> tool filter
    toolbox_tools: list[str] = field(default_factory=list)
    needs_looker: bool = False


CONFIGS: dict[str, PathConfig] = {
    "p1_managed": PathConfig(
        key="p1_managed",
        path=1,
        name="Raw Data Builder",
        variant="managed",
        summary="Managed BigQuery MCP only. Schema plus SQL, no governance surface.",
        managed_urls={MANAGED_BIGQUERY_URL: MANAGED_BIGQUERY_TOOLS},
    ),
    "p1_toolbox": PathConfig(
        key="p1_toolbox",
        path=1,
        name="Raw Data Builder",
        variant="toolbox",
        summary="Self-hosted BigQuery source. Same job, wider tool surface.",
        toolbox_tools=TOOLBOX_BIGQUERY_TOOLS,
    ),
    "p2_managed": PathConfig(
        key="p2_managed",
        path=2,
        name="Semantic Router",
        variant="managed",
        summary="Looker's instance-hosted MCP. The semantic layer is the only data access.",
        managed_urls={},  # filled at build time; the URL depends on LOOKER_BASE_URL
        needs_looker=True,
    ),
    "p2_toolbox": PathConfig(
        key="p2_toolbox",
        path=2,
        name="Semantic Router",
        variant="toolbox",
        summary="Self-hosted Looker source against the same LookML models.",
        toolbox_tools=TOOLBOX_LOOKER_TOOLS,
        needs_looker=True,
    ),
    "p3_managed": PathConfig(
        key="p3_managed",
        path=3,
        name="Governed Context",
        variant="managed",
        summary="Managed Knowledge Catalog MCP alongside BigQuery. Read the rule, then query.",
        managed_urls={
            MANAGED_DATAPLEX_URL: MANAGED_DATAPLEX_TOOLS,
            MANAGED_BIGQUERY_URL: MANAGED_BIGQUERY_TOOLS,
        },
    ),
    "p3_toolbox": PathConfig(
        key="p3_toolbox",
        path=3,
        name="Governed Context",
        variant="toolbox",
        summary="Self-hosted dataplex + bigquery sources, including aspect-type search.",
        toolbox_tools=TOOLBOX_DATAPLEX_TOOLS + TOOLBOX_BIGQUERY_TOOLS,
    ),
    # --- Matched arms (Amendment A.3.3) --------------------------------------
    #
    # Identical tool *lists* to their managed twins, so the only variable left is
    # whose endpoint serves the schema. Needed because `p1_managed` vs
    # `p1_toolbox` currently varies two things at once — list contents and
    # endpoint verbosity — and the second is worth ~27x the first.
    #
    # Matching runs Toolbox-downward rather than managed-upward: the managed
    # endpoints expose no more than these tools, so there is nothing to add on
    # that side. Any drift between `MANAGED_*_TOOLS` and these lists silently
    # un-matches the arm, which is what `test_matched_arms_really_match` guards.
    "p1_matched": PathConfig(
        key="p1_matched",
        path=1,
        name="Direct Query",
        variant="toolbox",
        summary="Self-hosted BigQuery restricted to the managed endpoint's exact tool list.",
        toolbox_tools=MATCHED_BIGQUERY_TOOLS,
    ),
    "p3_matched": PathConfig(
        key="p3_matched",
        path=3,
        name="Governed Context",
        variant="toolbox",
        summary="Self-hosted dataplex + bigquery restricted to the managed endpoints' tool lists.",
        toolbox_tools=MATCHED_DATAPLEX_TOOLS + MATCHED_BIGQUERY_TOOLS,
    ),
    "p4_bq_ca": PathConfig(
        key="p4_bq_ca",
        path=4,
        name="Managed Agent",
        variant="toolbox",
        summary="Conversational Analytics over BigQuery. The reasoning moves to the cloud.",
        toolbox_tools=["ask_data_insights"],
    ),
    "p4_looker_ca": PathConfig(
        key="p4_looker_ca",
        path=4,
        name="Managed Agent",
        variant="toolbox",
        summary="Conversational Analytics over Looker Explores.",
        toolbox_tools=["looker_conversational_analytics"],
        needs_looker=True,
    ),
}

CONFIG_KEYS = tuple(CONFIGS)

# The three arms that cannot run without a Looker instance. Kept as a derived
# value rather than a hand-written list so adding a Looker-backed config to
# CONFIGS above cannot forget to update it.
LOOKER_CONFIG_KEYS = tuple(key for key, cfg in CONFIGS.items() if cfg.needs_looker)


def has_unmeasured_service(config_key: str) -> bool:
    """Does this arm hand work to a service that bills its own model calls?

    True for Path 4 — Conversational Analytics runs a Gemini loop server-side and
    returns no usage for it, so every number we record for these arms is a floor
    rather than a total. Three places need that distinction and each one is a
    correctness question, not a presentation one: `cost.py` stamps the cell,
    `report.py` prints `floor` instead of `full`, and `plots.py` draws the marker
    hollow so a lower bound cannot be read off a cost axis as a measurement.

    Derived from the config table rather than listed, so a new Path 4 variant
    cannot be added without inheriting the caveat.
    """
    spec = CONFIGS.get(config_key)
    return spec is not None and spec.path == 4


def drop_looker(config_keys: list[str]) -> tuple[list[str], list[str]]:
    """Split requested configs into (runnable without Looker, dropped).

    Looker is the only component of this sandbox behind an annual-commitment
    purchase, which makes it the difference between "most people can reproduce
    this" and "almost nobody can". Seven arms remain, including both governance
    tiers on every path except 2 — so the central T1-vs-T0 result survives a
    Looker-free run, and only the semantic-layer comparison is lost.
    """
    dropped = [key for key in config_keys if key in LOOKER_CONFIG_KEYS]
    return [key for key in config_keys if key not in dropped], dropped


def looker_mcp_url() -> str:
    """Looker's MCP endpoint. Instance-hosted, not a googleapis.com host (F6)."""
    if not config.looker_configured():
        raise RuntimeError(
            f"LOOKER_BASE_URL is {config.LOOKER_BASE_URL or 'unset'!r}; Path 2 and p4_looker_ca "
            "cannot run. Point it at a real Looker instance — see .env.example."
        )
    return f"{config.LOOKER_BASE_URL.rstrip('/')}/mcp"


def _header_provider(tier: int) -> Callable[[ReadonlyContext | None], dict[str, str]]:
    """Build the per-request auth header factory for one tier.

    ADK calls this per request, so a long sweep cannot fail partway through on
    an expired token. The token is the tier's own identity when `USE_TIER_SA` is
    on — which is the only thing that keeps a managed-MCP agent inside its arm,
    since these servers accept no scoping parameter of their own.
    """

    def headers(_context: ReadonlyContext | None = None) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {identity.token(tier)}",
            "x-goog-user-project": config.require_project(),
        }

    return headers


def _looker_header_provider(tier: int) -> Callable[[ReadonlyContext | None], dict[str, str]]:
    """The same job as `_header_provider`, but Looker's `/mcp` is not a GCP server.

    It authenticates *Looker* users, so it takes the tier's API3 session token,
    not an impersonated GCP token — and that token is also the whole fence here.
    The sweep user's model set is what makes the other tier return 404, so
    sending the wrong credential does not merely fail, it would fail *open* if
    the wrong one happened to be an admin's.
    """

    def headers(_context: ReadonlyContext | None = None) -> dict[str, str]:
        return looker_client.auth_header(looker_client.tier_section(tier))

    return headers


def _managed_toolset(
    url: str,
    tool_filter: list[str],
    tier: int,
    header_provider: Callable[[ReadonlyContext | None], dict[str, str]] | None = None,
) -> McpToolset:
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(url=url, timeout=120),
        tool_filter=tool_filter or None,
        header_provider=header_provider or _header_provider(tier),
    )


@dataclass
class Bound:
    """The toolsets for one config, plus any subprocess that must be stopped."""

    toolsets: list[McpToolset]
    servers: list[toolbox_server.Server] = field(default_factory=list)

    def close(self) -> None:
        """Stop every Toolbox process this binding started."""
        for server in self.servers:
            server.stop()
        self.servers.clear()


def bind(config_key: str, tier: int) -> Bound:
    """Build the toolsets for one config at one tier.

    The caller owns the result and must `close()` it, or Toolbox processes leak
    across a 960-cell sweep.
    """
    spec = CONFIGS[config_key]
    toolsets: list[McpToolset] = []
    servers: list[toolbox_server.Server] = []

    for url, tool_filter in spec.managed_urls.items():
        toolsets.append(_managed_toolset(url, tool_filter, tier))

    if spec.variant == "managed" and spec.needs_looker:
        # Filtered to the same seven as `TOOLBOX_LOOKER_TOOLS` so the managed and
        # self-hosted arms of Path 2 offer the identical surface and F4 compares
        # plumbing rather than menu size. The instance publishes exactly these
        # seven today, but that is an admin setting on a *shared* instance and
        # someone else enabling an eighth must not silently widen this arm.
        toolsets.append(
            _managed_toolset(
                looker_mcp_url(),
                TOOLBOX_LOOKER_TOOLS,
                tier,
                header_provider=_looker_header_provider(tier),
            )
        )

    if spec.toolbox_tools:
        server = toolbox_server.start(spec.toolbox_tools, tier)
        servers.append(server)
        toolsets.append(
            McpToolset(
                connection_params=StreamableHTTPConnectionParams(url=server.url, timeout=120),
            )
        )

    return Bound(toolsets=toolsets, servers=servers)
