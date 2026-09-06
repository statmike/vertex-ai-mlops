"""Render a `tools.yaml` and run MCP Toolbox against it.

Toolbox ships `--prebuilt bigquery|dataplex|looker` configurations, and the
obvious move is to just use them. **We render our own instead**, because the
prebuilt `bigquery` source is measurably unsafe for a controlled experiment:

- it is **write-enabled** — a `CREATE OR REPLACE TABLE` through `execute_sql`
  succeeds, so an agent can mutate the corpus mid-sweep;
- it is **unscoped** — `BIGQUERY_DATASET` does not constrain queries, so an
  agent running the tier-0 arm can read the governed tier-1 dataset and quietly
  contaminate the control.

Both were measured against the live server, not inferred. A rendered source sets
`writeMode: blocked` and `allowedDatasets`, which the server enforces, and names
the tier's service account so the process runs fenced. `--prebuilt` also cannot
be combined with `--config`: the config files conflict on the source name
`bigquery-source`.

The **tool inventory** still mirrors the prebuilt exactly, name for name, so
the Managed-vs-Toolbox comparison stays honest. Only the source is hardened.
"""

import os
import shutil
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

import config
import looker_client

BINARY = Path(__file__).resolve().parent.parent / "bin" / "toolbox"
TOOLBOX_VERSION = "1.10.0"
STARTUP_TIMEOUT_S = 30

# Source ids used inside the rendered YAML. Local to the file; not user-visible.
BQ_SOURCE = "bq"
DATAPLEX_SOURCE = "dp"
LOOKER_SOURCE = "lk"


@dataclass(frozen=True)
class ToolSpec:
    """One Toolbox tool: the name the agent sees, its kind, and its source."""

    kind: str
    source: str
    description: str


# Names on the left are what the agent sees. They match the prebuilt configs, so
# a trace from this harness is comparable to one from `--prebuilt`.
CATALOG: dict[str, ToolSpec] = {
    # --- bigquery source (mirrors `--prebuilt bigquery`, 8 tools) ---
    "list_dataset_ids": ToolSpec(
        "bigquery-list-dataset-ids", BQ_SOURCE, "List the BigQuery dataset ids in the project."
    ),
    "list_table_ids": ToolSpec(
        "bigquery-list-table-ids", BQ_SOURCE, "List the table ids inside a BigQuery dataset."
    ),
    "get_dataset_info": ToolSpec(
        "bigquery-get-dataset-info", BQ_SOURCE, "Get metadata for a BigQuery dataset."
    ),
    "get_table_info": ToolSpec(
        "bigquery-get-table-info",
        BQ_SOURCE,
        "Get a BigQuery table's schema, descriptions, and metadata.",
    ),
    "execute_sql": ToolSpec(
        "bigquery-execute-sql", BQ_SOURCE, "Run a read-only BigQuery SQL query and return rows."
    ),
    "forecast": ToolSpec(
        "bigquery-forecast", BQ_SOURCE, "Forecast a BigQuery time series with AI.FORECAST."
    ),
    "analyze_contribution": ToolSpec(
        "bigquery-analyze-contribution", BQ_SOURCE, "Run contribution analysis over a table."
    ),
    "ask_data_insights": ToolSpec(
        "bigquery-conversational-analytics",
        BQ_SOURCE,
        "Ask a natural-language question over BigQuery tables (Conversational Analytics).",
    ),
    # --- dataplex source (`--prebuilt dataplex` ships 24; the 15 read-only ones
    # are here, the 9 mutating/job-triggering ones are deliberately absent —
    # see `TOOLBOX_DATAPLEX_TOOLS` in mcp_clients.py) ---
    "search_entries": ToolSpec(
        "dataplex-search-entries", DATAPLEX_SOURCE, "Search the Knowledge Catalog for data assets."
    ),
    "lookup_entry": ToolSpec(
        "dataplex-lookup-entry", DATAPLEX_SOURCE, "Look up one catalog entry's aspects and schema."
    ),
    "lookup_context": ToolSpec(
        "dataplex-lookup-context",
        DATAPLEX_SOURCE,
        "Get LLM-ready governed context (descriptions, business rules, profiles) for resources.",
    ),
    "search_aspect_types": ToolSpec(
        "dataplex-search-aspect-types", DATAPLEX_SOURCE, "Search the available aspect types."
    ),
    "search_dq_scans": ToolSpec(
        "dataplex-search-dq-scans", DATAPLEX_SOURCE, "Search for data scans in the project."
    ),
    "get_data_profile": ToolSpec(
        "dataplex-get-data-profile",
        DATAPLEX_SOURCE,
        "Get a completed profile scan's column statistics: null ratios, cardinality, "
        "quartiles, and top frequent values.",
    ),
    "get_data_quality_results": ToolSpec(
        "dataplex-get-data-quality-results",
        DATAPLEX_SOURCE,
        "Get a completed data-quality scan's rule outcomes, dimension scores, and the SQL "
        "that returns the failing rows.",
    ),
    "get_data_insights": ToolSpec(
        "dataplex-get-data-insights",
        DATAPLEX_SOURCE,
        "Get a completed insights scan's generated descriptions and sample queries.",
    ),
    "get_discovery_results": ToolSpec(
        "dataplex-get-discovery-results",
        DATAPLEX_SOURCE,
        "Get a completed discovery scan's publishing metadata and audit statistics.",
    ),
    "get_run_status": ToolSpec(
        "dataplex-get-run-status", DATAPLEX_SOURCE, "Get the latest job status for a scan."
    ),
    "get_operation": ToolSpec(
        "dataplex-get-operation", DATAPLEX_SOURCE, "Poll a Dataplex long-running operation."
    ),
    "list_data_products": ToolSpec(
        "dataplex-list-data-products", DATAPLEX_SOURCE, "List Data Products across all locations."
    ),
    "get_data_product": ToolSpec(
        "dataplex-get-data-product", DATAPLEX_SOURCE, "Get one Data Product's metadata."
    ),
    "list_data_assets": ToolSpec(
        "dataplex-list-data-assets", DATAPLEX_SOURCE, "List the Data Assets under a Data Product."
    ),
    "get_data_asset": ToolSpec(
        "dataplex-get-data-asset", DATAPLEX_SOURCE, "Get one Data Asset's metadata."
    ),
    "search_catalog": ToolSpec(
        "bigquery-search-catalog", BQ_SOURCE, "Search the catalog for BigQuery assets."
    ),
    # --- looker source ---
    "get_models": ToolSpec("looker-get-models", LOOKER_SOURCE, "List the LookML models."),
    "get_explores": ToolSpec("looker-get-explores", LOOKER_SOURCE, "List a model's Explores."),
    "get_dimensions": ToolSpec(
        "looker-get-dimensions", LOOKER_SOURCE, "List an Explore's dimensions and descriptions."
    ),
    "get_measures": ToolSpec(
        "looker-get-measures", LOOKER_SOURCE, "List an Explore's measures and descriptions."
    ),
    "get_filters": ToolSpec("looker-get-filters", LOOKER_SOURCE, "List an Explore's filters."),
    "get_parameters": ToolSpec(
        "looker-get-parameters", LOOKER_SOURCE, "List an Explore's parameters."
    ),
    "query": ToolSpec("looker-query", LOOKER_SOURCE, "Run a Looker query against an Explore."),
    "query_sql": ToolSpec(
        "looker-query-sql", LOOKER_SOURCE, "Return the SQL Looker would run for a query."
    ),
    "looker_conversational_analytics": ToolSpec(
        "looker-conversational-analytics",
        LOOKER_SOURCE,
        "Ask a natural-language question over Looker Explores (Conversational Analytics).",
    ),
}


def _impersonation(tier: int) -> list[str]:
    """The `impersonateServiceAccount` line for a source, or nothing.

    Both the `bigquery` and `dataplex` sources take this field as of v1.10.0, so
    the tier identity is set per-source in the YAML and no credential file is
    ever written. Under v1.1.0 the dataplex source had no such field and had to
    be reached through process-level ADC, which did not work.
    """
    if not config.USE_TIER_SA:
        return []
    return [f"    impersonateServiceAccount: {config.tier_service_account(tier)}"]


def render(tools: list[str], tier: int) -> str:
    """Build the YAML for one config's tool list, scoped to one tier.

    The scoping is the point. `allowedDatasets` holds exactly one dataset, so a
    query that reaches across tiers is refused by the server rather than
    silently answered from the wrong arm of the experiment.
    """
    unknown = [name for name in tools if name not in CATALOG]
    if unknown:
        raise ValueError(f"Unknown Toolbox tools: {unknown}")

    needed = {CATALOG[name].source for name in tools}
    lines = ["sources:"]
    if BQ_SOURCE in needed:
        lines += [
            f"  {BQ_SOURCE}:",
            "    kind: bigquery",
            f"    project: {config.require_project()}",
            f"    location: {config.BQ_LOCATION}",
            "    writeMode: blocked",
            "    allowedDatasets:",
            f"      - {config.tier_dataset(tier)}",
            *_impersonation(tier),
        ]
    if DATAPLEX_SOURCE in needed:
        lines += [
            f"  {DATAPLEX_SOURCE}:",
            "    kind: dataplex",
            f"    project: {config.require_project()}",
            *_impersonation(tier),
        ]
    if LOOKER_SOURCE in needed:
        # Interpolated from the child's environment, which `start()` fills from
        # the *tier's* ini section — never written into this YAML, which lands on
        # disk. Tier-scoped rather than ambient on purpose: these API3 keys are
        # the only thing standing between a Path 2 arm and every model on a
        # shared instance, and an operator's shell most likely holds the admin's.
        #
        # snake_case here, camelCase above, in the same file. That is Toolbox's
        # own inconsistency as of v1.10.0, not a typo: the bigquery and dataplex
        # sources take `writeMode`/`allowedDatasets`, the looker source rejects
        # `baseUrl` and wants `base_url`. Measured field by field, because the
        # failure is a startup crash whose message names only the *first* bad
        # key, so a wrong guess looks like a different bug each time.
        lines += [
            f"  {LOOKER_SOURCE}:",
            "    kind: looker",
            f"    base_url: {config.LOOKER_BASE_URL}",
            "    client_id: ${LOOKER_CLIENT_ID}",
            "    client_secret: ${LOOKER_CLIENT_SECRET}",
            "    verify_ssl: true",
            # Only `looker-conversational-analytics` needs these, and it fails at
            # *call* time without them ("project must be defined for source"), not
            # at startup — so the server comes up healthy and the tool 500s. Set
            # unconditionally: the other looker tools ignore them, and a
            # conditional here would be one more way to get a silently broken arm.
            f"    project: {config.require_project()}",
            f"    location: {config.DATAPLEX_LOCATION}",
        ]

    lines.append("tools:")
    for name in tools:
        spec = CATALOG[name]
        lines += [
            f"  {name}:",
            f"    kind: {spec.kind}",
            f"    source: {spec.source}",
            f"    description: {spec.description!r}",
        ]

    lines += ["toolsets:", "  sandbox:"]
    lines += [f"    - {name}" for name in tools]
    return "\n".join(lines) + "\n"


def _free_port() -> int:
    """Ask the OS for an unused port, so parallel sweeps never collide."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
        return port


@dataclass
class Server:
    """A running Toolbox process and the MCP endpoint it serves."""

    url: str
    process: subprocess.Popen[bytes]
    config_dir: Path

    def stop(self) -> None:
        """Terminate the process and delete the rendered config."""
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
        shutil.rmtree(self.config_dir, ignore_errors=True)


def _redact(text: str, env: dict[str, str] | None) -> str:
    """Strip any secret we passed in out of text we are about to raise or log.

    Toolbox echoes the *interpolated* YAML back when it fails to parse it, so a
    bad field name upstream of `client_secret` puts a live Looker API3 key into
    stderr — and from there into an exception message, a traceback, and any
    transcript of the run. Found the honest way, by reading the leak in this
    project's own terminal (DEV_NOTES 2026-09-01).
    """
    for key, value in (env or {}).items():
        if value and ("SECRET" in key or "CLIENT_ID" in key):
            text = text.replace(value, f"${{{key}}}")
    return text


def _launch(selector: list[str], config_dir: Path, env: dict[str, str] | None = None) -> Server:
    """Run the binary with whatever config selector it was given, and wait."""
    if not BINARY.exists():
        raise RuntimeError(
            f"Toolbox binary not found at {BINARY}. Run: uv run python scripts/install_toolbox.py"
        )

    port = _free_port()
    process = subprocess.Popen(  # noqa: S603 - fixed binary, no shell, no user input
        [
            str(BINARY),
            *selector,
            "--port",
            str(port),
            "--address",
            "127.0.0.1",
            "--allowed-hosts",
            "127.0.0.1",
            "--disable-reload",
            "--log-level",
            "WARN",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env=env,
    )

    server = Server(url=f"http://127.0.0.1:{port}/mcp", process=process, config_dir=config_dir)
    _wait_until_ready(server, port, env)
    return server


def _looker_env(tools: list[str], tier: int) -> dict[str, str]:
    """The tier's Looker API3 pair, for configs that need the looker source.

    Passed through the environment rather than the YAML so the secret never
    touches disk, and read from the tier's own ini section so `p2_toolbox` and
    `p4_looker_ca` authenticate as the same scoped user the managed arm does.
    """
    if not any(CATALOG[name].source == LOOKER_SOURCE for name in tools):
        return {}

    client_id, client_secret = looker_client.credentials(looker_client.tier_section(tier))
    return {"LOOKER_CLIENT_ID": client_id, "LOOKER_CLIENT_SECRET": client_secret}


def start(tools: list[str], tier: int) -> Server:
    """Render a config, launch Toolbox, and wait until it answers.

    The caller owns the returned `Server` and must `stop()` it. Every config
    gets its own process on its own port, because the tool list and the tier
    scope are baked into the rendered YAML.
    """
    config_dir = Path(tempfile.mkdtemp(prefix="toolbox-"))
    (config_dir / "tools.yaml").write_text(render(tools, tier))
    env = os.environ | _looker_env(tools, tier)
    return _launch(["--config", str(config_dir / "tools.yaml")], config_dir, env)


def start_prebuilt(prebuilt: str) -> Server:
    """Launch Toolbox on a **vendor** `--prebuilt` config, unmodified.

    Only for measuring what a source actually ships (`make probe`). The sweep
    never uses this: the prebuilt bigquery source is write-enabled and has no
    `allowedDatasets`, which is the whole reason `render()` exists.
    """
    env = os.environ | {
        "BIGQUERY_PROJECT": config.require_project(),
        "DATAPLEX_PROJECT": config.require_project(),
        "BIGQUERY_LOCATION": config.BQ_LOCATION,
    }
    return _launch(["--prebuilt", prebuilt], Path(tempfile.mkdtemp(prefix="toolbox-")), env)


def _wait_until_ready(server: Server, port: int, env: dict[str, str] | None = None) -> None:
    """Poll the health endpoint, surfacing the process's own error if it died."""
    deadline = time.monotonic() + STARTUP_TIMEOUT_S
    while time.monotonic() < deadline:
        if server.process.poll() is not None:
            stderr = server.process.stderr.read().decode() if server.process.stderr else ""
            server.stop()
            raise RuntimeError(f"Toolbox exited during startup:\n{_redact(stderr, env)}")
        try:
            with urlopen(f"http://127.0.0.1:{port}/", timeout=1):  # noqa: S310 - localhost
                return
        except OSError:
            time.sleep(0.25)
    server.stop()
    raise RuntimeError(f"Toolbox did not become ready within {STARTUP_TIMEOUT_S}s")
