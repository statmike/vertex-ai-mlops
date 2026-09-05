# Looker setup — Path 2 and `p4_looker_ca`

> **Standing it up right now?** Follow [`looker_runbook.md`](looker_runbook.md) — the ordered
> checklist. This file is the reference behind it: what each object is for, and why.

Most of this is scripted. With **admin** API3 credentials resolvable (`LOOKER_INI` in `.env`, or
`LOOKERSDK_*` exported — see `src/looker_client.py`):

```bash
uv run python scripts/looker_provision.py           # dry run, changes nothing
uv run python scripts/looker_provision.py --apply   # create what is missing
```

Exactly one step needs a human — getting the LookML *files* into the project,
because Looker has no file-write API. `src/looker_check.py` verifies the result and
refuses to let Path 2 run until it passes.

## The instance

This sandbox runs on an existing shared instance rather than its own. Identifiers below are the
placeholders `scripts/export_capture.py` substitutes into the published capture — the real ones live
in `.env`:

| | |
|---|---|
| Instance | one Looker Core instance, us-central1, project `example-project` |
| Edition | `LOOKER_CORE_ENTERPRISE_ANNUAL` |
| `LOOKER_BASE_URL` | `https://looker.example.com` |

A dedicated instance was considered and rejected on cost: Looker Core bills a platform fee per
instance (market-observed ~$60k/yr for Standard), so a second instance is a procurement decision, not
a provisioning step. Instance creation is therefore **never** automated in `scripts/setup.py` — a
setup script must not be able to start an annual-commitment charge.

### 🚧 The hard constraint

> **This sandbox is a guest.** It may add its own LookML project and its own BigQuery connections. It
> must not modify anything already on the instance, and must not read any of it.

This is enforced twice, not trusted. `scripts/looker_provision.py` only ever *creates* — it reports
pre-existing objects and leaves them exactly as found, and it refuses to act on any name outside the
`data_mcp_sandbox` namespace, so a mistyped `.env` cannot point it at a neighbour's model. And
`looker_check.check()` lists every model the sweep's API3 credentials can see and **fails** if even
one is not ours, because in Looker visibility *is* capability — the agent chooses its model from
whatever `get_models` returns. A neighbour's model is simultaneously a constraint violation and an
experimental confound: a plausibly-named production model is exactly the decoy this experiment is
otherwise carefully constructing on purpose.

## 1. LookML project — the one manual step

The provisioner creates the empty project `data_mcp_sandbox`. Getting files into it is manual:
`all_project_files` and `project_file` are **read-only**, so there is no API that writes LookML.
Either paste the 10 files from [`looker/`](../looker/) through the Looker IDE, or point the project
at a Git remote containing them. Then **Deploy to Production** — models are invisible to the API
until they are in production.

They define two models, mirroring the governance tiers:

- `data_mcp_sandbox_t0` — raw passthrough. Dimensions map 1:1 to columns, **no measures**. A Path 2
  agent here sees the same bare schema as tier 0 everywhere else.
- `data_mcp_sandbox_t1` — semantic. Adds `total_revenue` (net, refunds excluded) and
  `active_user_status` (the governed Active definition).

The checker asserts tier 0 has no measures. A stray measure there leaks governance into the control
and flattens the tier contrast, which is the one thing the whole design is measuring.

## 2. BigQuery connections — one per tier, and that is the point

The provisioner creates `data_mcp_sandbox_t0` and `data_mcp_sandbox_t1`, each using **Application
Default Credentials** with the *Impersonated Service Account* field set to that tier's sandbox
identity (`mcp-sandbox-t0@…` / `mcp-sandbox-t1@…`). No key file is uploaded, so the project's
no-service-account-keys rule holds here too.

A Looker connection authenticates as **the connection**, not as the calling user. A single shared
connection would therefore have made Path 2 the only arm whose tier boundary was not an IAM
boundary — its fence would have rested entirely on LookML and Looker's model ACL, a different and
weaker mechanism than the 403 every other path gets. Per-connection impersonation removes that
asymmetry: a tier-0 model pointed at tier-1 data now fails the same way it fails everywhere else.

This requires one GCP-side grant, handled by `scripts/bootstrap_identities.sh`: Looker's service
agent (`service-<project-number>@gcp-sa-looker.iam.gserviceaccount.com`) needs
`roles/iam.serviceAccountTokenCreator` on both tier service accounts.

Note the scope. That grant is not restricted to our connections, so on a shared instance *anything*
that can open a connection there can mint a token for these identities. Their permission set is
therefore what the grant is worth to everyone else on the instance, and it is worth stating exactly
rather than waving at:

| | Reach |
|---|---|
| Table data | **Dataset-scoped.** Only the sandbox's own tier datasets — `roles/bigquery.jobUser` runs a job, reading a table still needs the dataset ACL |
| Catalog metadata | **Project-wide.** `dataplex.entries.list` and `dataplex.projects.search` have no dataset scope to be given, so the custom `mcpSandboxCatalogSearch` role sees every Dataplex entry in the project |
| Writes | none |

The metadata row is the accepted widening, and it is the same project-wide-list hole already
documented for glossaries, aspect types and `search_dq_scans`. It is not an oversight and it is not
narrowable: the permission does not take a scope.

Rather than leave that as prose, `make verify-isolation` enumerates both identities' project roles
against a reviewed allow-list and fails when it grows, so a role added later cannot quietly widen
what a Looker connection can borrow.

## 3. Roles, model sets, and API3 credentials

The provisioner creates one permission set (`access_data`, `explore`, `see_lookml` — nothing that can
edit, and deliberately no `use_sql_runner`, since an agent that can drop to raw SQL is no longer being
measured on the semantic layer), plus:

| Model set | Contains | Role | User |
|---|---|---|---|
| `data_mcp_sandbox_t0_only` | `data_mcp_sandbox_t0` | `data_mcp_sandbox_t0_role` | `data_mcp_sandbox t0` |
| `data_mcp_sandbox_t1_only` | `data_mcp_sandbox_t1` | `data_mcp_sandbox_t1_role` | `data_mcp_sandbox t1` |

Neither user is an admin. That is load-bearing rather than tidiness: an admin sees every model
regardless of model set, so an admin sweep user would fail the containment check by design.

API3 credentials are issued at `--apply` time and printed **once**, to stdout. Export them; **never**
put them in `.env`:

```bash
export LOOKERSDK_BASE_URL="$LOOKER_BASE_URL"       # https://<instance>.looker.app
export LOOKERSDK_CLIENT_ID=...
export LOOKERSDK_CLIENT_SECRET=...
# Toolbox reads its own pair:
export LOOKER_CLIENT_ID="$LOOKERSDK_CLIENT_ID"
export LOOKER_CLIENT_SECRET="$LOOKERSDK_CLIENT_SECRET"
```

## 4. OAuth client app

The instance-hosted MCP endpoint (`$LOOKER_BASE_URL/mcp`) is in preview and requires an admin to
pre-register the calling agent as an OAuth client app. The provisioner registers it as
`data_mcp_sandbox_agent`. Until that exists, `make probe` reports the Looker MCP as UNREACHABLE —
expected output, not a bug.

## 5. Verify

```bash
make probe            # tool inventories, including Looker MCP
uv run python -c "import sys; sys.path.insert(0,'src'); import looker_check; looker_check.report()"
```

`report()` prints `Looker OK: <models>` only when both models resolve, tier 0 is bare, tier 1 carries
its semantic fields, **and** nothing foreign is visible.
