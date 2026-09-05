"""Prove the tier fence holds, against the live servers.

    uv run python examples/verify_isolation.py

**Diagnostic, not scored.** The experiment's central claim is that tier 0 and
tier 1 differ only in governance. That claim is worthless if a tier-0 agent can
read tier-1 metadata — and one demonstrably could, by asking the Knowledge
Catalog for "revenue" and being handed the governed entry (DEV_NOTES 2026-08-29).

Every negative check here is paired with a positive control on the same tool.
That pairing is the whole point: a call that fails because the arguments are
wrong, or a search that returns nothing at all, would otherwise *look* exactly
like a fence holding. An unproven negative is reported as `????`, not `PASS`.

  1. own dataset readable          -> control for (2)
  2. other tier's data NOT readable
  3. own entries found in search   -> control for (4)
  4. other tier's entries NOT in search   <- the leak that motivated this
  5. lookup_context on own entry   -> control for (6)
  6. lookup_context on other tier's entry refused
  7. governed rule text reachable from tier 1 and only from tier 1

Check 7 has no dataset behind it: a glossary is its own resource, so BigQuery
ACLs do not filter it. If the rule is reachable from tier 0 the fence leaks
through the business glossary even when every table check passes.

A separate check bounds the *blast radius* rather than the fence. Looker's
service agent can mint tokens for both tier identities, and on a shared instance
that is not scoped to our connections — so the tier identities' permission set
is what that grant is worth to anyone else on the instance. It is enumerated
against an allow-list, and grows loudly.

Path 2 (Looker) adds a second axis. It is the only path where the agent's
identity and the identity that reaches BigQuery are different accounts, so both
are checked: the sweep user must see exactly one model (on a shared instance,
visibility is capability — the agent picks its model from `get_models`), and the
connection must still take an IAM 403 across tiers.

Exits non-zero if any check fails or is inconclusive. IAM propagates in a minute
or two and the catalog search index lags further; a failure immediately after
`make identities` is worth re-running before believing.
"""

import argparse
import asyncio
import json
import sys

import _bootstrap  # noqa: F401 - import for the sys.path side effect
import httpx
from google.api_core import exceptions as gcp_exceptions
from google.cloud import resourcemanager_v3
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

import config
import corpus
import identity
import looker_client
import mcp_clients
import toolbox_server

# The phrase that gives the game away: the real revenue column. It appears in
# tier-1 descriptions and in the Net Revenue glossary term, never in tier 0.
GOVERNED_MARKER = "txn_amt_x2"

# Substrings that mark a refusal rather than a malformed request. Deliberately
# narrow — "error" is not on this list, because counting every error as a
# refusal is how a broken probe reports a fence that is not there.
REFUSALS = (
    "permission",
    "denied",
    "403",
    "not in the allowed list",
    "does not have",
    "access denied",
    "caller does not have",
)


def unwrap(exc: BaseException) -> str:
    """Flatten an ExceptionGroup — MCP hides the real cause inside a TaskGroup."""
    inner = getattr(exc, "exceptions", None)
    if inner:
        return " | ".join(unwrap(e) for e in inner)
    return f"{type(exc).__name__}: {exc}"


def _sse_payload(body: str) -> str:
    """Unwrap a `text/event-stream` frame, or pass a plain JSON body through."""
    for line in body.splitlines():
        if line.startswith("data:"):
            return line[len("data:") :].strip()
    return body


async def raw_call(url: str, tool: str, args: dict[str, object], headers: dict[str, str]) -> str:
    """Re-issue a call as plain JSON-RPC, to read an error the SDK discarded.

    Toolbox reports a refused tool call as a JSON-RPC error carried on HTTP 500.
    The MCP client raises on the status inside its streaming context, so the
    body is never read and the real message — an ordinary 403 — is gone by the
    time it surfaces. An opaque transport failure cannot be told apart from a
    broken call, which is the one distinction this whole script exists to make,
    so the call is repeated here at a level low enough to see the response.
    """
    post = dict(headers)
    post["Content-Type"] = "application/json"
    post["Accept"] = "application/json, text/event-stream"
    hello = {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "verify-isolation", "version": "1"},
    }
    async with httpx.AsyncClient(timeout=60) as client:
        opened = await client.post(
            url,
            headers=post,
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": hello},
        )
        session = opened.headers.get("mcp-session-id")
        if session:
            post["mcp-session-id"] = session
        await client.post(
            url, headers=post, json={"jsonrpc": "2.0", "method": "notifications/initialized"}
        )
        answered = await client.post(
            url,
            headers=post,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool, "arguments": args},
            },
        )
    payload = json.loads(_sse_payload(answered.text))
    if "error" in payload:
        return str(payload["error"].get("message", payload["error"]))
    blocks = payload.get("result", {}).get("content", [])
    return "\n".join(str(block.get("text", block)) for block in blocks)


async def call(url: str, tool: str, args: dict[str, object], token: str | None) -> str:
    """Call one MCP tool and flatten the response to text (refusals included)."""
    headers = {}
    if token:
        headers = {
            "Authorization": f"Bearer {token}",
            "x-goog-user-project": config.require_project(),
        }
    try:
        async with (
            streamablehttp_client(url, headers=headers or None) as (read, write, _),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            result = await session.call_tool(tool, args)
            return "\n".join(getattr(block, "text", str(block)) for block in result.content)
    except Exception as exc:  # noqa: BLE001 - a refusal is a valid, expected outcome
        detail = unwrap(exc)
        try:
            return await raw_call(url, tool, args, headers)
        except Exception:  # noqa: BLE001 - the original failure is the better report
            return f"ERROR: {detail}"


def refused(text: str) -> bool:
    """True when a response is an authorization refusal, not data and not a bug."""
    lowered = text.lower()
    return any(marker in lowered for marker in REFUSALS)


class Report:
    """Collects outcomes so the whole matrix runs before anything fails."""

    def __init__(self) -> None:
        self.bad = 0

    def positive(self, label: str, text: str, expect: str | None = None) -> bool:
        """A control: the call must succeed, and optionally contain `expect`."""
        ok = not text.startswith("ERROR:") and not refused(text)
        if ok and expect:
            ok = expect in text
        self._emit("PASS" if ok else "FAIL", label, "" if ok else text)
        return ok

    def negative(self, label: str, text: str, control_ok: bool, absent: str | None = None) -> None:
        """A fence check. Meaningless unless its control passed, so say so."""
        if not control_ok:
            self._emit("????", label, "control for this check failed — result proves nothing")
            return
        if absent is None:
            # The call itself must come back as an authorization refusal.
            blocked = refused(text)
        else:
            # The call must succeed and simply not mention the other tier.
            blocked = not text.startswith("ERROR:") and absent not in text
        self._emit("PASS" if blocked else "FAIL", label, "" if blocked else text)

    def result(self, label: str, ok: bool, detail: str = "") -> None:
        """A check whose logic lives at the call site."""
        self._emit("PASS" if ok else "FAIL", label, "" if ok else detail)

    def _emit(self, status: str, label: str, detail: str) -> None:
        print(f"  [{status}] {label}")
        if detail:
            print(f"         {detail.strip()[:280]}")
        if status != "PASS":
            self.bad += 1


async def verify_managed(tier: int, other: int, report: Report) -> None:
    print(f"\n=== tier {tier} on managed MCP as {identity.describe(tier)} ===")
    project = config.require_project()
    # Always a token: `identity.token` falls back to plain ADC when tier
    # identities are off, which is the baseline this run is measuring against.
    token = identity.token(tier)
    bq = mcp_clients.MANAGED_BIGQUERY_URL
    dp = mcp_clients.MANAGED_DATAPLEX_URL
    loc = config.CATALOG_LOCATION
    table = corpus.TRANSACTIONS.name

    def count(t: int) -> dict[str, object]:
        return {
            "projectId": project,
            "query": f"SELECT COUNT(*) AS n FROM `{config.table_ref(t, table)}`",
        }

    # 1 / 2 — BigQuery data access.
    control = report.positive(
        f"can query own dataset t{tier}", await call(bq, "execute_sql_readonly", count(tier), token)
    )
    report.negative(
        f"cannot query t{other} data",
        await call(bq, "execute_sql_readonly", count(other), token),
        control,
    )

    # 3 / 4 — catalog search. This is the check that matters: search is
    # content-addressed and project-wide, so only the caller's ACL scopes it.
    #
    # Two queries, because they fail differently. The table name is present in
    # every entry regardless of governance, so it is a fair control for both
    # arms — searching "revenue" is NOT, since a bare tier-0 table has no
    # metadata to match and would look absent when it is merely unindexed.
    # pageSize is maxed for the same reason: a truncated page would read as a
    # fence holding.
    async def search(query: str) -> str:
        return await call(
            dp, "search_entries", {"projectId": project, "query": query, "pageSize": 500}, token
        )

    by_name = await search(table)
    by_topic = await search("revenue")
    control = report.positive(
        f"own t{tier} entries appear in search", by_name, expect=config.tier_dataset(tier)
    )
    report.negative(
        f"t{other} absent from search by table name",
        by_name,
        control,
        absent=config.tier_dataset(other),
    )
    report.negative(
        f"t{other} absent from search for 'revenue'",
        by_topic,
        control,
        absent=config.tier_dataset(other),
    )

    # 5 / 6 — direct context lookup, in case search merely ranked it away.
    def ctx(t: int) -> dict[str, object]:
        return {
            "projectId": project,
            "location": loc,
            "resources": [config.dataplex_entry_name(t, table)],
        }

    control = report.positive(
        f"lookup_context works on own t{tier} entry",
        await call(dp, "lookup_context", ctx(tier), token),
    )
    # Measured: this does not 403 for an unauthorized entry, it returns `{}`.
    # Silently empty is a stronger outcome than a refusal — it discloses nothing,
    # not even the entry's existence — so the check is on content, not status.
    report.negative(
        f"lookup_context yields nothing for t{other}",
        await call(dp, "lookup_context", ctx(other), token),
        control,
        absent=config.tier_dataset(other),
    )

    # 7 — the glossary has no dataset behind it, so nothing above covers it.
    # roles/dataplex.catalogViewer bundles glossaryTerms.get, which is why the
    # bootstrap splits that role rather than granting it whole.
    rule = await search("Net Revenue")
    reachable = any(GOVERNED_MARKER in text for text in (rule, by_topic, by_name))
    if tier == 0:
        report.result(
            "governed rule unreachable from the control arm",
            not reachable,
            f"tier 0 can read {GOVERNED_MARKER} through the catalog",
        )
    else:
        report.result(
            "governed rule reachable from the treatment arm",
            reachable,
            "tier 1 cannot see its own governance — setup is incomplete",
        )


async def verify_toolbox(tier: int, other: int, report: Report) -> None:
    """Same fence, through the self-hosted server's process-level ADC."""
    print(f"\n=== tier {tier} via Toolbox subprocess ===")
    server = toolbox_server.start(["execute_sql", "search_entries"], tier)
    try:
        table = corpus.TRANSACTIONS.name
        control = report.positive(
            f"toolbox can query own t{tier}",
            await call(
                server.url,
                "execute_sql",
                {"sql": f"SELECT COUNT(*) AS n FROM `{config.table_ref(tier, table)}`"},
                None,
            ),
        )
        report.negative(
            f"toolbox refuses t{other} query",
            await call(
                server.url,
                "execute_sql",
                {"sql": f"SELECT COUNT(*) AS n FROM `{config.table_ref(other, table)}`"},
                None,
            ),
            control,
        )

        found = await call(
            server.url,
            "search_entries",
            {"projectId": config.require_project(), "query": "revenue"},
            None,
        )
        control = report.positive(
            f"toolbox search finds own t{tier}", found, expect=config.tier_dataset(tier)
        )
        report.negative(
            f"toolbox search omits t{other}", found, control, absent=config.tier_dataset(other)
        )
    finally:
        server.stop()


def verify_looker(tier: int, other: int, report: Report) -> None:
    """Path 2's fence, which is two fences and both have to hold.

    Looker is the only path where the agent's identity and the identity that
    reaches BigQuery are different accounts, so it needs both checks:

    * **Visibility** — the sweep user is non-admin with a one-model model set, so
      `get_models` must return exactly its own. The agent chooses its model from
      that list, so on a shared instance visibility *is* capability.
    * **Data** — the connection authenticates as itself, not as the caller, so a
      cross-tier read has to fail on IAM. This one is deliberately issued with
      ADMIN credentials: the sweep users have no `use_sql_runner`, and testing
      as the weaker identity would prove the wrong thing. What must hold is that
      even an admin cannot cross tiers *through a tier's connection*.
    """
    from looker_sdk.sdk.api40 import models as m

    print(f"\n=== tier {tier} on Looker as the {config.RESOURCE_PREFIX} t{tier} sweep user ===")
    model, other_model = config.looker_model(tier), config.looker_model(other)

    try:
        sweep = looker_client.sdk(section=looker_client.tier_section(tier))
        visible = sorted(x.name for x in sweep.all_lookml_models() if x.name)
    except Exception as exc:  # noqa: BLE001 - an unreachable instance is a failed check
        report.result(f"authenticate as t{tier} sweep user", False, unwrap(exc))
        return

    seen = ", ".join(visible) or "(none)"
    control = report.positive(f"t{tier} sweep user sees own model", seen, expect=model)
    report.negative(
        f"t{tier} sweep user cannot see t{other} model", seen, control, absent=other_model
    )
    report.result(
        f"t{tier} sweep user sees no other instance content",
        visible == [model],
        f"also visible: {[v for v in visible if v != model]}",
    )

    # The governed fields are the tier contrast itself: a stray measure in tier 0
    # would flatten it while every other check still passed.
    try:
        explore = sweep.lookml_model_explore(model, config.LOOKER_EXPLORE)
        measures = {f.name for f in (explore.fields.measures if explore.fields else [])}
    except Exception as exc:  # noqa: BLE001
        report.result(f"t{tier} explore '{config.LOOKER_EXPLORE}' resolves", False, unwrap(exc))
        return
    if tier == 0:
        report.result("t0 explore is a bare passthrough", not measures, f"measures: {measures}")
    else:
        report.result(
            "t1 explore carries the governed measure",
            "transactions.total_revenue" in measures,
            f"measures: {measures}",
        )

    admin = looker_client.sdk()
    ran = []
    for data_tier in (tier, other):
        sql = f"SELECT COUNT(*) AS n FROM `{config.table_ref(data_tier, 'transactions')}`"
        query = admin.create_sql_query(
            m.SqlQueryCreate(connection_name=config.looker_connection(tier), sql=sql)
        )
        try:
            ran.append(admin.run_sql_query(query.slug or "", "json"))
        except Exception as exc:  # noqa: BLE001 - the refusal text is the evidence
            ran.append(unwrap(exc))

    control = report.positive(f"t{tier} connection reads own dataset", ran[0])
    report.negative(f"t{tier} connection refuses t{other} data", ran[1], control)


# Project-level roles the tier identities are allowed to hold. Not an assertion
# that these are harmless — an assertion that the list is short, reviewed, and
# says so when it grows.
#
# It is here rather than in a unit test because it is the blast radius of a
# specific live grant. Looker's service agent holds
# `roles/iam.serviceAccountTokenCreator` on both tier accounts, which is what
# lets a per-tier connection carry the IAM fence into Path 2
# (`docs/looker_setup.md` §2). On a shared instance that grant is not scoped to
# our connections: anything that can open a connection there can mint a token
# for these identities. So whatever they can reach, it can reach, and this list
# is the honest statement of what that is.
ALLOWED_TIER_SA_ROLES = {
    "roles/bigquery.jobUser",  # run a job; reading a table still needs dataset ACL
    "roles/mcp.toolUser",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/geminidataanalytics.dataAgentStatelessUser",
    "mcpSandboxCatalogSearch",  # custom: project-wide Dataplex *metadata* read
    "mcpSandboxGlossaryReader",  # custom, tier 1 only: glossary read
}


def _role_key(role: str) -> str:
    """Match a policy role against `ALLOWED_TIER_SA_ROLES`.

    Predefined roles are global (`roles/bigquery.jobUser`) and compared whole.
    Custom ones carry the project (`projects/<id>/roles/mcpSandboxCatalogSearch`)
    and are compared on the bare name, so the allow-list stays portable to a
    reader's own project. Shortening both would let `roles/bigquery.jobUser` be
    matched by a bare `jobUser` entry, which is how the first version of this
    check reported four reviewed roles as unreviewed.
    """
    return role if role.startswith("roles/") else role.rsplit("/", 1)[-1]


def verify_blast_radius(report: Report) -> None:
    """Fail if a tier identity has picked up a role nobody reviewed.

    The two custom roles are deliberately in the allow-list *and* deliberately
    project-wide: `dataplex.entries.list` and `dataplex.projects.search` have no
    dataset scope to be given. That is a known, accepted widening rather than an
    oversight, and it is why the docs say catalog metadata is project-wide while
    table data is not. The check that matters is that nothing granting
    project-wide *data* access — `roles/bigquery.dataViewer` and relatives —
    ever appears here, which it enforces by allow-list rather than by blocklist.
    """
    client = resourcemanager_v3.ProjectsClient()
    try:
        policy = client.get_iam_policy(request={"resource": f"projects/{config.require_project()}"})
    except gcp_exceptions.GoogleAPICallError as exc:
        # A reader without `resourcemanager.projects.getIamPolicy` should not see
        # a red FAIL for a permission they do not need to run the sweep.
        print(f"  [SKIP] tier identity role review — cannot read the IAM policy ({exc.code})")
        return

    for tier in config.TIERS:
        member = f"serviceAccount:{config.tier_service_account(tier)}"
        held = {binding.role for binding in policy.bindings if member in binding.members}
        extra = sorted(r for r in held if _role_key(r) not in ALLOWED_TIER_SA_ROLES)
        report.result(
            f"t{tier} identity holds only reviewed roles ({len(held)} total)",
            not extra,
            f"unreviewed, and reachable by any Looker connection on the instance: {extra}",
        )


async def main_async(skip_toolbox: bool, skip_looker: bool) -> int:
    print(f"Verifying tier isolation in {config.require_project()}")
    if not config.USE_TIER_SA:
        print(
            "\nUSE_TIER_SA is off: every arm runs as your own ADC, so the cross-tier\n"
            "checks SHOULD fail. That is the baseline this fence exists to fix.\n"
            "Run `make identities`, set USE_TIER_SA=true in .env, then `make setup`."
        )

    report = Report()
    verify_blast_radius(report)
    for tier in config.TIERS:
        other = next(t for t in config.TIERS if t != tier)
        await verify_managed(tier, other, report)
        if not skip_toolbox:
            await verify_toolbox(tier, other, report)
        if not skip_looker and config.looker_configured():
            verify_looker(tier, other, report)

    print(f"\n{'FAILED' if report.bad else 'OK'} — {report.bad} check(s) not passing")
    return 1 if report.bad else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-toolbox", action="store_true", help="Managed servers only.")
    parser.add_argument("--skip-looker", action="store_true", help="Skip the Path 2 checks.")
    args = parser.parse_args()
    return asyncio.run(main_async(args.skip_toolbox, args.skip_looker))


if __name__ == "__main__":
    sys.exit(main())
