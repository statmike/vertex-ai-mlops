# The ten arms

The experiment's independent variable. Every arm is the **same model**
(`gemini-3.7-flash`, temperature 0) asking the **same twelve questions** against
the **same corpus**. Only the tool surface changes, so a score difference is
attributable to architecture rather than to the model.

Each arm runs at two governance tiers over byte-identical data:

- **Tier 0** — ungoverned control. No column descriptions, no catalog aspects, no
  glossary, no semantic model. Raw tables with hostile names.
- **Tier 1** — governed. Descriptions, Knowledge Catalog business rules, a
  glossary with term-to-column links, and a semantic LookML model.

The tiers are separated by IAM, not by prompt. Each arm runs as a per-tier
service account holding `dataViewer` on exactly one tier dataset — necessary
because Knowledge Catalog search is project-wide and content-addressed, so a
tier-0 agent asking for "revenue" was handed the tier-1 governed entry and
answered from it. See [`scoping.md`](scoping.md).

---

## Path 1 — Raw Data Builder

Schema plus SQL. No governance surface at all. The baseline every other path has
to beat.

| Arm | Server | Tools |
|---|---|---|
| `p1_managed` | `bigquery.googleapis.com/mcp` | 5 |
| `p1_toolbox` | self-hosted MCP Toolbox, `bigquery` source | 8 |
| `p1_matched` | self-hosted, restricted to the managed tool list | 5 |

## Path 2 — Semantic Router

The semantic layer is the *only* data access. No raw SQL, no table names — the
agent can reach a measure or it cannot.

| Arm | Server | Tools |
|---|---|---|
| `p2_managed` | the Looker instance's own `/mcp` | 7 |
| `p2_toolbox` | self-hosted Toolbox, `looker` source | 7 |

Note the endpoint: Looker's MCP is **instance-hosted**, at
`LOOKER_BASE_URL + /mcp`, not a `googleapis.com` host. One BigQuery connection
per tier, each impersonating that tier's service account, so Path 2 sits behind
the same IAM fence as everything else instead of being the one arm whose boundary
is a Looker setting.

## Path 3 — Governed Context

Catalog alongside the warehouse. Read the rule, then query.

| Arm | Server | Tools |
|---|---|---|
| `p3_managed` | `dataplex.googleapis.com/mcp` + `bigquery.googleapis.com/mcp` | 8 |
| `p3_toolbox` | self-hosted Toolbox, `dataplex` + `bigquery` sources | 23 |
| `p3_matched` | self-hosted, restricted to the managed tool lists | 8 |

`p3_toolbox` binds 15 of the 24 tools `--prebuilt dataplex` ships. The 9 that
mutate or trigger billable scan jobs are excluded, because the dataplex source
has no `writeMode` equivalent to neuter them with.

## Path 4 — Managed Agent

The reasoning moves to the cloud. One tool, one question in, an answer out.

| Arm | Server | Tools |
|---|---|---|
| `p4_bq_ca` | Conversational Analytics over BigQuery | 1 |
| `p4_looker_ca` | Conversational Analytics over Looker Explores | 1 |

---

## Managed vs. self-hosted: what actually differs

This surprised us, so it is worth stating precisely.

**Behaviourally, they are near-identical.** Across paths 1–3, the managed and
Toolbox arms reach the *same verdict* on 93–98% of paired cells — while agreeing
on the exact tool-call sequence 0–7% of the time. Two different routes, same
destination.

**In cost, they differ by up to 27×.** And the cause is not the tool list.

Tool declarations are re-sent to the model on **every turn**, so their serialized
size sets a floor on prompt tokens for the whole conversation. Measured at sweep
time and recorded in every capture's header:

| Arm | Tools | Schema chars |
|---|---:|---:|
| `p1_managed` | 5 | 120,009 |
| `p1_matched` | 5 | **3,019** |
| `p3_managed` | 8 | 143,814 |
| `p3_matched` | 8 | **6,809** |
| `p3_toolbox` | 23 | 18,865 |
| `p2_managed` | 7 | 11,721 |
| `p2_toolbox` | 7 | 5,602 |
| `p1_toolbox` | 8 | 7,030 |
| `p4_bq_ca` | 1 | 882 |
| `p4_looker_ca` | 1 | 817 |

`p1_managed` and `p1_matched` bind the **same five tools** and differ **40×**.
`p3_toolbox` binds nearly 3× as many tools as `p3_managed` and is **7.6× smaller**.
Tool *count* does not predict cost; tool *schema verbosity* does.

One tool dominates:

| `get_table_info` | chars | share of arm |
|---|---:|---:|
| managed endpoint | 78,197 | 65.2% |
| self-hosted Toolbox | 653 | 0.6% |

A single vendor tool declaration, resent every turn, is two thirds of an arm's
entire prompt floor and 120× its self-hosted equivalent.

This is exactly why `p1_matched` and `p3_matched` exist (Amendment A.3.3). The
as-shipped comparison varies two things at once — which tools are bound, and
whose endpoint describes them — and the matched arms hold the first constant to
isolate the second.

**Treat these numbers as perishable.** Managed tool schemas are a vendor detail
that can change without notice, and this table shows that detail dominating the
cost result. Every capture records its own measured sizes for that reason. See
[`reproducing.md`](reproducing.md).

---

## Why Toolbox is configured, not used prebuilt

`toolbox_server.py` generates a config per arm rather than invoking
`--prebuilt bigquery`. Two reasons, both load-bearing:

- **`writeMode: blocked`** — no agent can mutate the corpus mid-sweep. The
  managed counterpart is binding `execute_sql_readonly` instead of `execute_sql`.
- **`allowedDatasets`** — a second, server-side fence on top of the IAM one.
  Neither managed endpoint offers an equivalent; they are scoped by *caller*
  only, which is why the tier service accounts are not optional.

## What is opaque, and what that costs the measurement

Path 4 discloses no query. Conversational Analytics over BigQuery emits SQL we
can recover from its response; CA over Looker emits none and never names a field.
So evidence recall and rule acquisition are **unmeasurable** on those arms rather
than zero, and the report prints `--`, never `0%`. Ranking an arm bottom on a
metric it was never eligible for is a false finding, not a conservative one.

Its warehouse spend *is* attributable — CA's BigQuery jobs run under our own tier
service account and were verified per cell. Its **model** spend is not: CA makes
its own Gemini calls server-side and does not report them, so Path 4 totals are
published as a floor.

One measured trap for anyone reading CA output: **at tier 0 it hallucinated the
governed net-revenue rule and inverted it.** Generative prose can therefore never
serve as evidence that governance was delivered — only a tool result can.
