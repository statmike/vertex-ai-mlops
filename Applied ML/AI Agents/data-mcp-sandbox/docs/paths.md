# The twelve arms

What each arm *is*: which server it talks to, which tools that server hands the
model, and which of the four independent design choices the arm pins. What the
arms scored is in [results](results.md).

Every arm is the **same model** (`gemini-3.7-flash`, temperature 0) asking the
**same fifteen questions** against the **same corpus**. Only the tool surface
changes, so a score difference is attributable to architecture rather than to
the model.

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

## The option space, and which of it we ran

Choosing how to put an LLM in front of BigQuery is not one decision. It is four,
and they are independent:

1. **Where the reasoning runs.** A local agent loop that calls tools and writes
   the SQL itself (Paths 1–3), or a cloud service that owns the loop and hands
   back a finished answer (Path 4).
2. **How you reach it.** As an MCP tool an agent calls, or as an API you call
   yourself. This is the axis that is easiest to miss, because for most of these
   options there is only one answer. For Conversational Analytics there are two,
   and they do not measure the same.
3. **Who hosts the tools.** A Google-managed MCP endpoint you authenticate to, or
   the **MCP Toolbox for Databases** running as your own process.
4. **Which tools you bind.** Every server ships more than you should hand an
   agent. You pick a subset under its ceiling — and the ceilings are very
   different sizes.

The one that catches people: **Conversational Analytics is not a fourth server.**
It is an API service that surfaces as a *single tool* on a server you already run
— and it is also an API you can call with no server at all. "Use the managed
agent" is a tool-selection decision, not an infrastructure one, which is why
Path 4 has no managed column.

Crossing choice 3 with choice 4 gives the grid. Twelve arms occupy it; the empty
cells are empty for stated reasons, not by omission.

| Tool configuration | Managed endpoint | Self-hosted Toolbox | No MCP server |
|---|---|---|---|
| **As shipped, minus write** | `p1_managed` `p2_managed` `p3_managed` | — *(a)* | n/a |
| **Matched to the managed list** | *(b)* | `p1_matched` `p3_matched` | n/a |
| **Curated for a real deployment** | *(c)* | `p1_toolbox` `p2_toolbox` `p3_toolbox` | n/a |
| **One tool that is a whole agent** | *(d)* | `p4_bq_ca` `p4_looker_ca` | `p4_bq_direct` `p4_bq_direct_ctx` *(e)* |

**(a) Toolbox exactly as it ships is not run, deliberately.** `--prebuilt
bigquery` is write-enabled and unscoped — a `CREATE OR REPLACE TABLE` succeeded
against our sandbox — and `--prebuilt dataplex` includes tools that start billable
scan jobs. No team should deploy that, so benchmarking it would measure a
configuration nobody runs. This is the one cell we skip on judgement rather than
on logic; the exclusion list is [below](#path-3--governed-context).

**(b) and (c) are the same cell on the managed side, and that is the finding.**
The managed servers expose 9 tools total (6 BigQuery + 3 catalog). We removed
exactly one, `execute_sql`, for write safety. There is no headroom to curate: the
vendor's list *is* the deployment list. Self-hosted Toolbox ships 32 (8 + 24), so
curation is unavoidable there — we cut 9 that mutate or trigger billable scans and
kept 23.

**(d) Conversational Analytics has no managed MCP endpoint.** Reached as a tool,
it is reachable only through Toolbox — so both MCP-transport Path 4 arms are
self-hosted even though the reasoning they invoke is entirely Google's.

**(e) The same service with no MCP server anywhere.** `p4_bq_direct` calls the
Conversational Analytics API itself. It is in the grid because the tool and the
API are not equivalent: the tool takes a question and returns prose, while the
API streams the SQL it generated and the BigQuery job that ran it. That
difference is why `p4_looker_ca` discloses no query on 42% of its cells and the
direct arms on 0% of theirs — a limit of the transport, not of the service.
Rule *acquisition* stays `--` on all four Path 4 arms regardless, because there
is no tool call to observe the agent reading a rule through. `p4_bq_direct_ctx`
is the same call with the tier's glossary passed inline, which is a governance
channel neither the catalog nor LookML provides.

**Path 2's seven tools are matched by construction, not by luck.** Looker's
managed MCP and the Toolbox `looker` source each expose the same seven, and we
bind all seven on both sides — but the managed toolset is explicitly filtered to
that list rather than taken whole, because it is a shared instance where an
admin enabling an eighth tool would un-match the pair without anyone noticing.
Nothing had to be trimmed; the filter exists so that stays true. That makes
Path 2 an accidental control — and it is the pair with the smallest cost gap in
the experiment (1.1–1.3× against 6.9–7.7× on Path 1), which is exactly what the
schema-verbosity finding below predicts.

### Is that fair?

Two things differ between a managed arm and its Toolbox twin: **the endpoint** and
**the tool list**. A raw managed-vs-toolbox gap cannot be assigned to either. The
`_matched` arms exist to break that tie — same server as `_toolbox`, restricted to
the same tool names as `_managed`, so tool count is held constant and only the
endpoint varies.

Both halves were then measured rather than argued.

**Holding the tool list constant, the endpoint is worth ~40×.** `p1_managed` and
`p1_matched` bind the **same five tools**. Managed serializes them in 120,009
characters; Toolbox in 3,019.

**Holding the endpoint constant, the tool list is worth almost nothing.**
`p3_toolbox` binds 23 tools against `p3_matched`'s 8 — 2.8× the schema — on the
same server, same model, same questions:

| Path 3 | tools | schema chars | tool calls | tokens in / correct | accuracy |
|---|---:|---:|---:|---:|---:|
| `p3_matched` · tier 0 | 8 | 6,809 | 18.5 | 554,297 | 47% |
| `p3_toolbox` · tier 0 | 23 | 18,865 | 17.0 | **417,432** | 44% |
| `p3_matched` · tier 1 | 8 | 6,809 | 5.0 | **46,360** | 100% |
| `p3_toolbox` · tier 1 | 23 | 18,865 | 7.0 | 53,979 | 100% |

Identical accuracy at tier 1 — 45/45 each — and under three points apart at tier
0. Cost splits: the larger surface is **25% cheaper** at tier 0, the *wrong*
direction, because it resolved in fewer turns and turn count absorbed the schema;
at tier 1 it is 16% dearer. So the eleven inert Dataplex tools discussed under
Path 3 are a real cost on paper and a small and unsigned one in the result.
*(Caveat: `p3_matched` tier 1 needed a quota retry on 14 of its 60 cells, the
most in the capture, so its cost figures carry the most retry overhead.)*

The two together are why the headline is about **schema verbosity, not tool
count** — and why trimming `p3_toolbox` to match would change the framing without
changing a number.

**Transport is the third pair, and it was the outcome worth least wanting.**
`p4_bq_ca` and `p4_bq_direct` reach the same service over different transports.
Every Path 4 number published before 2026-09-07 came from the tool, so the
question was whether that result described Conversational Analytics or Toolbox's
wrapper around it. The two disagree:

| Same service, same corpus, same model | accuracy | median s | tokens in / cell | sec / correct |
|---|---:|---:|---:|---:|
| `p4_bq_ca` · tier 0 | 23% | 61.2 | 12,363 | 277 |
| `p4_bq_direct` · tier 0 | 22% | **10.0** | 0 | **51** |
| `p4_bq_ca` · tier 1 | **100%** | 32.6 | 5,941 | 36 |
| `p4_bq_direct` · tier 1 | 97% | **10.5** | 0 | **11** |

**The transport costs 3.1× the wall clock at tier 1 and does not cost accuracy.**
On the twelve gradeable questions the wrapper is 60/60 and the direct client
58/60 — two cells apart, which is inside any floor this experiment can measure,
and the sign is against the direct client rather than for it. The
**thirteen-point** lead this table gave the direct client before 2026-09-13 was
made entirely of the three anchor-ambiguous questions, and is withdrawn. See
[the trailing-window
questions](results.md#the-trailing-window-questions-are-anchor-ambiguous). The tokens
column is not a saving either: the direct arm runs no local model, so its 0 is
what the harness records rather than what the question costs, and CA's own loop
is billed where neither arm can read it (see
[below](results.md#p4_bq_ca-reports-nothing-which-is-not-the-same-as-spending-nothing)).
The latency is the one difference that survives — and it is large.

So the Path 4 rows on every other table describe the wrapper as much as the
service. That is a limit on what this experiment can say about Conversational
Analytics — and it is exactly the limit the arms were built to expose rather than
to leave as a footnote.

**The fourth pair carries its own control.** `p4_bq_direct` and
`p4_bq_direct_ctx` differ only by a glossary passed in the request. That glossary
is empty at tier 0 by construction — tier 0 is the ungoverned control, and
injecting definitions there would hand the arm the very thing the other arms have
to discover. The two arms therefore send **byte-identical requests** across all
120 tier-0 cells, which makes them an accidental A/A test:

| | tier 0 (identical requests) | tier 1 (glossary injected) |
|---|---:|---:|
| `p4_bq_direct` | 22% | 97% |
| `p4_bq_direct_ctx` | 23% | 95% |

One cell apart when nothing differs — 13/60 against 14/60, which is what a
within-run floor looks like. And **one cell apart when the glossary does
differ**, in the other direction: 58/60 against 57/60. On the twelve gradeable
questions, injecting the glossary is worth nothing measurable.

That is not what this pair reported before 2026-09-13, which was seven points.
The whole of the old seven belongs to the three anchor-ambiguous questions, and
it is worth saying what the glossary actually did to them: `governed-q1` 4/5 →
5/5, `governed-q3` 3/5 → 5/5, `semantic-q2` 2/5 → 3/5. The glossary moved the
agent onto the *same anchoring the oracle happens to use*. That is a real effect
and it is not accuracy — a glossary that pins an ambiguous definition is doing
its job, but our oracle cannot distinguish "pinned it correctly" from "pinned it
the way we did." So the honest statement is narrower and more useful than the old
one: **on questions this corpus can grade, the glossary changes nothing; on the
three it cannot, the glossary is the entire effect.**

**Re-asking those three with the anchor pinned settled it.** On
`governed-q1a` and `governed-q3a` at tier 1 both arms score **5/5** — with the
glossary and without it. There is nothing left for the glossary to fix once the
question says when *now* is, which is the cleanest available evidence that the
old seven points were an anchoring artefact and never a governance effect. (On
`semantic-q2a` the pair is 4/5 without and 3/5 with, one cell, the wrong way.)

That "same day, same endpoint" is load-bearing, and this floor does not travel.
It is a **within-run** figure: the two arms share a sweep, an oracle, and an hour
of the service's weather. Comparing numbers across two *different* captures gets
a much larger floor — [~9 points, measured](results.md#the-cross-capture-noise-floor-is-9-points-not-2).

### What this does not cover

Stated so the grid is not mistaken for the whole world: one model, one corpus at
one scale, single-turn questions only, BigQuery as the only warehouse, and
Toolbox's non-Google sources untested. Conversational Analytics is exercised
stateless only — its `Conversation` and `DataAgent` modes wait on the multi-turn
work, and its Looker, property-graph and Looker Studio datasources are untried.
Those are on the roadmap, not in the result. See
[`design.md`](design.md#6-threats-to-validity).

**Governance on this page is one switch, not a dial.** Every tier-1 number above
turns on column descriptions, profile scans, business rules, a glossary, quality
scans and a LookML layer *together*, so it answers "does the lot of it pay" and
not "which part". Those six cost wildly different amounts of effort to produce,
so the second question is usually the one being asked. It now has an answer of
its own — see [which rung pays](results.md#which-rung-pays).

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

### What each catalog surface actually exposes

Measured by calling `tools/list` and `tools/call` against the live servers, not
read off documentation. Reproduce it with `make probe`.

The managed catalog server exposes **exactly three** tools — `search_entries`,
`lookup_context`, `lookup_entry` — against Toolbox's 24. That 8× gap is the
largest managed/self-hosted asymmetry anywhere in this experiment, and it is the
obvious reason to predict that Path 3 Managed cannot answer a question about data
quality or distribution.

**It is the wrong prediction, and the reason is worth knowing.** `lookup_context`
returns far more than its name implies. On the governed table it returns the
`overview` rule text, every column description, **the profile-scan statistics**
(`nullRatio`, `distinctValues`, `sampleValues`) and the linked glossary terms —
5,035 characters against 1,554 on the ungoverned control. So the profile data *is*
on the critical path for the managed arm. It has to extract a statistic from a
YAML blob rather than call a purpose-built tool, which is a difference in effort,
not in capability.

Two consequences that shape the scoring:

- **There is no glossary tool on either variant, and the glossary still arrives.**
  `lookup_context` renders each linked column with a `terms:` field carrying the
  term and its full definition. At tier 1 a business rule therefore reaches the
  agent **twice** — once as the table's `overview` aspect, once per linked column
  — and the acquisition check must not count that as two independent hits.
- **Availability is not reachability, twice over.** Binding a tool is not
  evidence an agent calls it — `get_data_quality_results` was bound on all 120
  Path-3 Toolbox cells and called **zero times**. And calling one is not evidence
  it answers. Every scan tool is denied to the tier identities, which hold no
  `dataplex.datascans.*` permission at all:

  | Tool | Calls | Errors |
  |---|---:|---:|
  | `search_dq_scans` | 59 | **59** |
  | `list_data_products` | 33 | **33** |
  | `get_data_profile` | 1 | **1** |

  93 calls, no successes, one cause. So the *only* Dataplex tools that returned
  anything on `p3_toolbox` are the four catalog ones — `search_entries`,
  `lookup_entry`, `lookup_context`, `search_aspect_types`. The profile
  statistics still reach the agent, but through `lookup_context`, exactly as they
  do on the managed arm that has no profile tool. **Eleven of fifteen Dataplex
  tools are surface area that costs schema tokens and returns nothing.**

`make probe` prints the shipped inventory and the configured inventory separately,
because those two numbers get conflated and only the second is what an agent sees.

**Why the eleven stay bound.** They are what a least-privilege deployment of the
self-hosted offer actually looks like, and removing them would make `p3_toolbox`
a duplicate of `p3_matched` — leaving nothing to measure the capability
difference against `p3_managed`. The two arms answer different questions:

| Read this pair | To ask |
|---|---|
| `p3_managed` vs `p3_matched` | Same tool list, different plumbing — what does the *endpoint* cost? |
| `p3_managed` vs `p3_toolbox` | What do you actually get from each one as you would deploy it? |

And the handicap is priced: [Is that fair?](#is-that-fair) measures `p3_toolbox`
against `p3_matched` directly. Carrying the eleven is 25% *cheaper* at tier 0 and
16% dearer at tier 1, with identical tier-1 accuracy.

## Path 4 — Managed Agent

The reasoning moves to the cloud. One question in, an answer out.

| Arm | Transport | Datasource | Context sent | Tools |
|---|---|---|---|---|
| `p4_bq_ca` | Toolbox MCP tool | BigQuery tables | whatever the tool sends | 1 |
| `p4_looker_ca` | Toolbox MCP tool | Looker Explores | whatever the tool sends | 1 |
| `p4_bq_direct` | the API itself | BigQuery tables | datasources only | — |
| `p4_bq_direct_ctx` | the API itself | BigQuery tables | + the tier's glossary | — |

The two direct arms bind no tools at all, which is why that column reads `—`
rather than `0`: there is no MCP server in the picture to count tools on. They
change one thing each. `p4_bq_ca → p4_bq_direct` isolates the **transport**;
`p4_bq_direct → p4_bq_direct_ctx` isolates the **context payload**, passing the
same business definitions the catalog carries at tier 1 straight into the
request. At tier 0 the glossary is empty on both, because tier 0 is the
ungoverned control.

What is deliberately *not* varied: the direct arms are stateless
(`inline_context`, no `Conversation` or `DataAgent`), run the default model and
thinking mode, and send no example queries — `ExampleQuery` carries a
`sql_query`, and the only queries we have that are correct and relevant are the
golden oracle's, so filling that field would leak the answer.

**And "the default model" is the only model.** Going direct is often assumed to
buy model choice that a managed tool hides. It does not: `ChatRequest.model` is
an enum, and its one selectable value is `LATEST_GA_MODEL` — a generation
pointer, not a model id. Enumerated against the pinned SDK (0.13.2), because
this is exactly the kind of surface that moves between releases.

So the real asymmetry is narrower and worth stating plainly. Neither route lets
you pick the model. Only the direct route lets you pick how hard it thinks:
`thinking_mode`, which is `FAST` or `THINKING`. The MCP arms expose neither
knob, and every published cell here ran the service default — the field has no
proto presence, so omitting it and sending "unspecified" are the same request.
`CA_THINKING_MODE` changes it, into a separate capture compared with
`make compare` (see [method](method.md#one-capture-per-experiment-compared-rather-than-merged)).
What the knob is worth, over three more captures, is in
[results](results.md#what-the-thinking-knob-is-actually-worth).

---

## Why Toolbox is configured, not used prebuilt

`toolbox_server.py` generates a config per arm rather than invoking
`--prebuilt bigquery`. Two reasons, both load-bearing:

- **`writeMode: blocked`** — no agent can mutate the corpus mid-sweep. The
  managed counterpart is binding `execute_sql_readonly` instead of `execute_sql`.
- **`allowedDatasets`** — a second, server-side fence on top of the IAM one.
  Neither managed endpoint offers an equivalent; they are scoped by *caller*
  only, which is why the tier service accounts are not optional.
