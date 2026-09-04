# Scoping MCP tools to a dataset

How do you stop an MCP agent reading data you did not point it at? This matters here for a specific
reason — the sandbox runs an ungoverned **tier 0** control against a governed **tier 1**, and a
tier-0 agent that reaches tier 1 contaminates the experiment. It matters in production for the
obvious reason.

Everything below was **measured**, against `bigquery.googleapis.com/mcp`,
`dataplex.googleapis.com/mcp`, and the pinned MCP Toolbox **v1.10.0** binary in `bin/`. Reproduce the
tool-surface half with `make probe`, and the fence itself with `make verify-isolation`.

## Summary

| Layer | BigQuery | Catalog entries | Glossaries, aspect types |
|---|---|---|---|
| Managed MCP tool parameters | ❌ none | ❌ none | ❌ none |
| Toolbox source config | ✅ `allowedDatasets`, `writeMode` | ❌ nothing | ❌ nothing |
| Dataset IAM on the caller | ✅ | ✅ (search is ACL-filtered) | ❌ **no dataset behind them** |
| Dataplex IAM on the caller | — | ✅ | ✅ **the only lever** |
| Agent instruction | ⚠️ advisory | ⚠️ advisory | ⚠️ advisory |

Two things to take away:

1. **Only IAM scopes the catalog.** Everything else is advisory or BigQuery-only.
2. **Dataset-scoped IAM does not scope the catalog's *own* resources.** Glossaries and aspect types
   live in Dataplex, not BigQuery, so no dataset ACL filters them. Scoping an agent by dataset and
   assuming the catalog follows fails in the way that is hardest to notice — the agent's SQL still
   names the right dataset.

## 1. Managed MCP has no scoping parameters

The tool input schemas take a project and a target, and nothing that constrains them:

```jsonc
// bigquery.googleapis.com/mcp :: list_table_ids
{"projectId": "Required. Project ID of the table request.",
 "datasetId": "Required. Dataset ID of the table request."}
```

`projectId` is *attribution*, not restriction — the description says it is the project the request is
"attributed" to. Any `projectId`/`datasetId` the caller's IAM allows will be served. `get_table_info`,
`get_dataset_info`, `execute_sql` and `execute_sql_readonly` behave the same way.

The catalog is worse, because search is content-addressed rather than path-addressed:

```jsonc
// dataplex.googleapis.com/mcp :: search_entries
{"projectId": "Required. …the caller must have dataplex.projects.search…",
 "query":     "Required. …Knowledge Catalog search syntax…",
 "scopeId":   "Optional. The ID of the scope to limit the search space (e.g. organization ID,
               or project ID/number depending on the scope_type).",
 "scopeType": "Optional. Type of the scope to limit the search space.",
 "pageSize": …, "pageToken": …, "orderBy": …}
```

There *is* a scope pair here — and it is no help, for two independent reasons. Its granularity is
**organization or project**, so it cannot separate two datasets inside one project, which is exactly
the boundary this experiment needs. And like `query`, it is an ordinary optional tool argument: the
**agent** fills it in. A parameter the caller can choose not to send is not a control. The same goes
for the query syntax's `name:`, `parent:`, `system:` and `type:` operators — those are the agent's
options, not yours.

This is not theoretical. A tier-0 agent in this sandbox ran:

```
search_entries(projectId="…", query="revenue")
  -> …/datasets/data_mcp_sandbox_t1/tables/transactions_v2_final
```

and answered correctly using the tier-1 governed rule it should never have seen.

## 2. Toolbox scopes BigQuery well and the catalog only by identity

Probed by feeding each candidate field to the v1.10.0 binary and seeing whether the server starts:

| Field | `bigquery` | `dataplex` |
|---|:-:|:-:|
| `allowedDatasets` | ✅ | ❌ |
| `writeMode` | ✅ | ❌ |
| `useClientOAuth` | ✅ | ❌ |
| `maxQueryResultRows` | ✅ | ❌ |
| `maximumBytesBilled` | ✅ | ❌ |
| `location` | ✅ | ❌ |
| `readOnly` | ✅ | ❌ |
| `quotaProject` | ✅ | ❌ |
| `apiEndpoint` | ✅ | ❌ |
| `impersonateServiceAccount` | ✅ | ✅ |
| `scopes` | ✅ | ✅ |

The `dataplex` source takes **`project`, `impersonateServiceAccount` and `scopes`** — no
content-level scoping of any kind. Which is the theme of this whole document: the only thing that
narrows the catalog is *who is asking*.

> Probe carefully. A rejected config is not the same as an unknown field — feeding
> `allowedDatasets: [some_dataset]` a dataset that does not exist, or an
> `impersonateServiceAccount` that does not resolve, fails startup with a message about the *value*.
> Read the error before recording a ❌; the first run of this table got two entries wrong that way.

Version matters more than it should here. Against **v1.1.0**, the `dataplex` source accepted `project`
and nothing else, and the two fields that let it be fenced simply did not exist — see §3 and
`DEV_NOTES.md`. `maximumBytesBilled` likewise appears in the docs, is rejected by v1.1.0, and works in
v1.10.0.

`allowedDatasets` is genuinely enforced, not advisory: Toolbox **dry-runs** each query, reads the
tables it touches, and rejects anything outside the list. Statements whose table set cannot be
determined statically (`EXECUTE IMMEDIATE`, `CREATE PROCEDURE`, `CALL`) and dataset-level DDL are
refused outright, so the analysis cannot be dodged. Verified live — a cross-tier query returns:

> query accesses dataset '…t1', which is not in the allowed list

and with `writeMode: blocked`:

> write mode is 'blocked', only SELECT statements are allowed

That is what `src/toolbox_server.py` renders. Note `--prebuilt bigquery` sets **neither** — it is
write-enabled and unscoped, and it cannot be merged with `--config` (they collide on the source
name), which is why this repo renders its own YAML.

Once the source also carries `impersonateServiceAccount`, that message stops appearing — the dry-run
job is submitted *as the tier's account*, so IAM refuses before `allowedDatasets` is ever consulted:

> Error 403: Access Denied: Table …:data_mcp_sandbox_t1.transactions_v2_final: User does not have
> permission to query table …, accessDenied

Same outcome, stronger reason. The allowlist is the second layer, and it is worth keeping precisely
because it still holds if the identity is ever over-granted.

## 3. IAM is the only thing that scopes the catalog

`SearchEntries` results are **ACL-filtered per caller, against the source system**. Catalog roles let
you *issue* a search; whether a given entry comes back depends on your permission on the underlying
resource — `bigquery.tables.get` for a BigQuery table. Two consequences:

- A principal without `bigquery.tables.get` on the tier-1 tables **cannot see them in search
  results**, no matter what query the agent writes.
- Granting `roles/dataplex.catalogViewer` broadly is safe on its own; it grants the ability to
  search, not the ability to see.

Caveats worth knowing: permission changes propagate to the search index with a delay, and search does
not guarantee full recall — a missing entry is not proof of a working ACL.

### The role that undoes it: `roles/dataplex.catalogViewer`

This is the obvious grant for a search-capable identity, and it is a trap if any catalog resource is
itself sensitive. Among its permissions:

```
dataplex.glossaries.get / list
dataplex.glossaryTerms.get / list
```

A **glossary term has no BigQuery table behind it**, so dataset ACLs cannot filter it. In this
sandbox the `net-revenue` term contains the governed business rule verbatim, and
`search_entries(query="revenue")` returns it *ahead of every table*:

```
projects/…/entryGroups/@dataplex/entries/projects/…/glossaries/…/terms/net-revenue
```

An identity with perfectly dataset-scoped BigQuery IAM still reads it. So split the role: grant the
search half to everyone who needs to search, and the glossary half only to who should see the
business definitions.

```bash
gcloud iam roles create mcpSandboxCatalogSearch --project "$P" --stage=GA \
  --title="MCP Sandbox Catalog Search" \
  --permissions=dataplex.projects.search,dataplex.entries.get,dataplex.entries.list,\
dataplex.entryGroups.get,dataplex.entryGroups.list,dataplex.entryTypes.get,dataplex.entryTypes.list,\
dataplex.aspectTypes.get,dataplex.aspectTypes.list,dataplex.entryLinks.get,\
dataplex.locations.get,dataplex.locations.list,resourcemanager.projects.get
```

`scripts/bootstrap_identities.sh` does this, plus a `mcpSandboxGlossaryReader` for the other half.

### Doing it without service-account keys

`CODE_STANDARDS.md` §4 forbids service-account JSON keys, and impersonation satisfies that: the token
is minted from your own ADC, and no key material exists anywhere.

```bash
gcloud iam service-accounts create mcp-sandbox-t0 --project "$P"
SA=mcp-sandbox-t0@$P.iam.gserviceaccount.com

# Search and query, but no data access by default. Note the custom search role
# rather than roles/dataplex.catalogViewer — see the warning just above.
gcloud projects add-iam-policy-binding "$P" --member="serviceAccount:$SA" \
  --role="projects/$P/roles/mcpSandboxCatalogSearch" --condition=None
gcloud projects add-iam-policy-binding "$P" --member="serviceAccount:$SA" \
  --role=roles/bigquery.jobUser --condition=None

# Data access on exactly one dataset
bq add-iam-policy-binding --member="serviceAccount:$SA" \
  --role=roles/bigquery.dataViewer "$P:data_mcp_sandbox_t0"

# Let your own ADC mint tokens for it — no key is created
gcloud iam service-accounts add-iam-policy-binding "$SA" \
  --member="user:$(gcloud config get-value account)" \
  --role=roles/iam.serviceAccountTokenCreator
```

**Toolbox** takes it natively, on both sources, as of v1.10.0 — so nothing is written to disk:

```yaml
sources:
  bq:
    kind: bigquery
    project: my-project
    impersonateServiceAccount: mcp-sandbox-t0@my-project.iam.gserviceaccount.com
    writeMode: blocked
    allowedDatasets: [data_mcp_sandbox_t0]
  dp:
    kind: dataplex
    project: my-project
    impersonateServiceAccount: mcp-sandbox-t0@my-project.iam.gserviceaccount.com
```

⚠️ **Do not try this on v1.1.0.** The `dataplex` source had no such field, and the obvious
workaround — pointing `GOOGLE_APPLICATION_CREDENTIALS` at an `impersonated_service_account` ADC
config — *silently does not work*, because that source called `FindDefaultCredentials` with no
scopes and then suppressed the client's defaults with `option.WithCredentials`. Every catalog call
dies in the token exchange with a `400 INVALID_ARGUMENT` that names neither scopes nor
impersonation. The BigQuery source is unaffected, so half the server works and half does not.
`DEV_NOTES.md` has the full diagnosis; the general lesson is that
**`option.WithCredentials` overrides a Google client library's default scopes**, which is invisible
with user ADC and fatal with impersonated ADC.

**Managed MCP** is scoped in the `header_provider`, which is where `src/mcp_clients.py` already mints
its bearer token:

```python
source, _ = google.auth.default(scopes=[CLOUD_PLATFORM])
credentials = google.auth.impersonated_credentials.Credentials(
    source_credentials=source,
    target_principal=f"mcp-sandbox-t{tier}@{project}.iam.gserviceaccount.com",
    target_scopes=[CLOUD_PLATFORM],
)
credentials.refresh(google.auth.transport.requests.Request())
```

## 4. What this sandbox does

Each arm runs as its own service account, `mcp-sandbox-t0` and `mcp-sandbox-t1`, holding:

| Grant | t0 | t1 | Where | Why |
|---|:-:|:-:|---|---|
| `roles/mcp.toolUser` | ✅ | ✅ | project | call any `googleapis.com/mcp` tool at all |
| `roles/bigquery.jobUser` | ✅ | ✅ | project | run query jobs — *not* read data |
| `roles/serviceusage.serviceUsageConsumer` | ✅ | ✅ | project | the `x-goog-user-project` quota header |
| `roles/geminidataanalytics.dataAgentStatelessUser` | ✅ | ✅ | project | Path 4 `ask_data_insights` |
| `mcpSandboxCatalogSearch` (custom) | ✅ | ✅ | project | issue a search; results stay ACL-filtered |
| `mcpSandboxGlossaryReader` (custom) | ❌ | ✅ | project | **the glossary is treatment** |
| `READER` on `…_t0` | ✅ | ❌ | dataset ACL | **the independent variable** |
| `READER` on `…_t1` | ❌ | ✅ | dataset ACL | **the independent variable** |

Only the last three rows differ between the arms, and that is the entire design: everything an agent
needs in order to *try* is granted equally, so the only thing separating tier 0 from tier 1 is what
the data and the governance will let it reach.

```bash
make identities          # one-time, privileged: creates the SAs and custom roles
echo 'USE_TIER_SA=true' >> .env
make setup               # grants each SA reader on its own dataset
make verify-isolation    # proves the fence holds
```

Dataset ACLs are set by `make setup` rather than the bootstrap, because dataset-level IAM is not
reachable through `bq add-iam-policy-binding` (tables only) and belongs with provisioning anyway.
Every tier's entry is removed from every dataset that is not its own, so a stale grant cannot quietly
reopen the leak.

`make verify-isolation` is the part worth copying. It runs 24 checks — both tiers × both server
kinds × data, catalog search, direct entry lookup and glossary reachability — and currently passes
all 24. Each "cannot reach" check is paired with a positive control on the same tool, and reports
`????` rather than `PASS` when its control fails.

That pairing was learned the hard way, three times. The first version reported the fence as holding
while it leaked: it called `lookup_entry` with the wrong field name and scored the resulting
`INVALID_ARGUMENT` as a refusal. The third failed the opposite way — Toolbox v1.10.0 returns a
refusal as a JSON-RPC error on HTTP 500, the MCP client raised before reading the body, and a
perfectly good `403 accessDenied` arrived as an opaque transport error that the script (rightly)
declined to score. **A scoping test that cannot tell a broken call from a working fence is worse than
no test**, in both directions.

### If you cannot create service accounts

There is a design for it — provision one tier at a time, so with tier 1 absent there is nothing for a
tier-0 agent to find. It needs no IAM at all. It was **never built, and the stub was removed**
(DEV_NOTES.md 2026-08-31): it costs a second provisioning cycle and the loss of an interleaved sweep,
which puts the two arms days apart — a time confound sitting directly on the independent variable.

So this is not a fallback you can reach for today. Without the tier service accounts there is **no
fence**, and `make verify-isolation` will say so rather than quietly passing. If you cannot run
`scripts/bootstrap_identities.sh` yourself, get someone who can to run it once; the alternative is
rebuilding the epoch path, which is a worse experiment even when it works.

## Rules of thumb

1. **Never rely on the instruction.** *"Use only this dataset"* is a request. Every leak found here
   happened while that sentence was in the system prompt.
2. **Scope the identity, not the tool.** Tool-level allowlists are a second layer; only IAM covers
   every tool, including ones you did not know the server exposed.
3. **Check the surface you actually got.** `--prebuilt bigquery` is write-enabled and unscoped, the
   managed BigQuery server exposes `execute_sql` alongside `execute_sql_readonly`, and the docs
   describe fields the pinned binary rejects. Run `make probe`.
4. **Catalog search ignores your dataset allowlist.** It is content-addressed and project-wide. If
   the catalog matters to your threat model, IAM is the whole answer.
5. **Audit the bundle, not the role name.** `roles/dataplex.catalogViewer` sounds like read-only
   metadata access and carries `glossaryTerms.get`, which no dataset ACL filters. Run
   `gcloud iam roles describe` before granting.
6. **Pair every negative test with a positive control.** Otherwise a typo in your probe looks
   identical to a fence that holds.
7. **A tool parameter is never a security control.** `search_entries` grew `scopeId`/`scopeType`, and
   they change nothing: the agent decides whether to send them. Only the parts of the request the
   agent cannot forge — its identity — constrain it.
8. **Version-pin, but be willing to move the pin.** v1.1.0's catalog source could not be fenced at
   all, and the failure looked like a credentials problem rather than a missing feature. When a
   security property cannot be expressed in the version you pinned, that is a reason to upgrade,
   not a reason to weaken the property.

## Sources

- [Search for resources in Dataplex Universal Catalog](https://cloud.google.com/dataplex/docs/search-assets)
- [Method: projects.locations.searchEntries](https://cloud.google.com/dataplex/docs/reference/rest/v1/projects.locations/searchEntries)
- [Dataplex Universal Catalog IAM roles](https://cloud.google.com/dataplex/docs/iam-roles)
- [BigQuery Source | MCP Toolbox for Databases](https://mcp-toolbox.dev/integrations/bigquery/source/)
