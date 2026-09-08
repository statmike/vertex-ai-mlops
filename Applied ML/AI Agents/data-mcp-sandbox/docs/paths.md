# The twelve arms

The *what* of the comparison. [method](method.md) is how the sweep is run,
[questions](questions.md) is what counts as a right answer.

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
| `p3_matched` · tier 0 | 8 | 6,809 | 18.5 | 763,580 | 35% |
| `p3_toolbox` · tier 0 | 23 | 18,865 | 17.0 | **574,456** | 33% |
| `p3_matched` · tier 1 | 8 | 6,809 | 5.0 | **113,687** | 75% |
| `p3_toolbox` · tier 1 | 23 | 18,865 | 7.0 | 121,638 | 75% |

Identical accuracy at tier 1, two points apart at tier 0, and cost within ±7% —
going the *wrong* way at tier 0, where the larger surface is cheaper because it
resolved in fewer turns and turn count absorbed the schema. So the eleven inert
Dataplex tools discussed under Path 3 are a real cost on paper and not a
measurable one in the result. *(Caveat: `p3_matched` tier 1 excluded 14 of 60
cells, the most in the capture, so that 7% rests on 46 clean cells against 60.)*

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
| `p4_bq_ca` · tier 0 | 23% | 62.4 | 8,867 | 287 |
| `p4_bq_direct` · tier 0 | 22% | **10.0** | 0 | **51** |
| `p4_bq_ca` · tier 1 | 75% | 32.8 | 4,634 | 54 |
| `p4_bq_direct` · tier 1 | **88%** | **10.3** | 0 | **13** |

Thirteen accuracy points and 3.2× the wall clock at tier 1, for the transport
alone. The tokens column is not a saving: the direct arm runs no local model, so
its 0 is what the harness records rather than what the question costs, and CA's
own loop is billed where neither arm can read it (see
[below](#p4_bq_ca-reports-nothing-which-is-not-the-same-as-spending-nothing)).
The latency and the accuracy are real.

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
| `p4_bq_direct` | 22% | 88% |
| `p4_bq_direct_ctx` | 23% | **95%** |

One point apart when nothing differs; seven points apart when the glossary does.
The tier-1 effect is seven times the noise floor the same pair measured for
itself on the same day against the same endpoint — which is a stronger claim than
a 7-point delta usually gets to make.

That "same day, same endpoint" is load-bearing, and this floor does not travel.
It is a **within-run** figure: the two arms share a sweep, an oracle, and an hour
of the service's weather. Comparing numbers across two *different* captures gets
a much larger floor — [~7 points, measured](#the-cross-capture-noise-floor-is-7-points-not-1).

### What this does not cover

Stated so the grid is not mistaken for the whole world: one model, one corpus at
one scale, single-turn questions only, BigQuery as the only warehouse, and
Toolbox's non-Google sources untested. Conversational Analytics is exercised
stateless only — its `Conversation` and `DataAgent` modes wait on the multi-turn
work, and its Looker, property-graph and Looker Studio datasources are untried.
Those are on the roadmap, not in the result. See
[`design.md`](design.md#6-threats-to-validity).

**And governance here is one switch, not a dial.** Tier 1 turns on column
descriptions, profile scans, business rules, a glossary, quality scans and a
LookML layer *together*, so every governance number on this page answers "does
the lot of it pay" and none of them answers "which part". Those six cost
wildly different amounts of effort to produce, so the second question is
usually the one being asked. The harness can now ask it — `LADDER=1` splits the
switch into six channels over five rungs
([method](method.md#governance-is-one-switch-by-default-and-six-channels-on-request),
[reproducing](reproducing.md#running-the-governance-ladder)) — but **that sweep
has not been run, so there is no result here to read.** Anyone attributing the
tier-1 gain to a particular surface is guessing, including us.

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
against `p3_matched` directly. Carrying the eleven costs within 7% and identical
tier-1 accuracy.

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

### What the thinking knob is actually worth

Three captures, 720 cells, zero failures: `FAST`, `THINKING`, and a same-window
re-run of the default. All at n=5 over both direct arms and both tiers.

**The default is not an alias for either mode.** It is adaptive — it spends
deliberation in proportion to how hard the question is, which neither explicit
setting does. Median latency per question, pooled over both arms and tiers:

| question | FAST | default | THINKING |
|---|---:|---:|---:|
| `direct-q1` (easiest) | 6.5s | 6.7s | 9.9s |
| `metadata-q1` | 6.7s | 7.8s | 10.7s |
| `semantic-q2` | 7.2s | 10.2s | 17.7s |
| `governed-q2` | 7.7s | 12.8s | 19.7s |
| `trap-q1` (hardest) | 6.7s | 14.7s | 23.5s |

Read the FAST column first: **6.5–7.7s no matter what you ask.** Question
difficulty does not move it. The default ranges 6.7–14.7s over the same
questions, tracking THINKING's ordering at roughly half its cost.

It is not routing each request to one of the two modes either — that would show
up as a bimodal split, part of the distribution sitting on FAST's ~7s. On
`trap-q1` the default's 20 cells run continuously from 8.2s to 24.1s with
nothing at FAST's baseline.

The gap is deliberation, not warehouse work: all three modes issue ~1.0
BigQuery jobs per cell with comparable SQL length, so nothing here is explained
by one mode querying more.

**On accuracy, almost nothing survives the noise floor.** Two effects clear it:

* **FAST costs ~12 points at tier 0** on both arms (28% → 17%), where there is
  no governance to lean on. At tier 1 it is indistinguishable from the default
  (+1.7, +3.3 — both inside the floor) while running ~30% faster. On a governed
  warehouse, FAST is close to free.
* **THINKING costs 10 points on `p4_bq_direct_ctx` at tier 1** (90% → 80%), and
  13 against FAST. This is the one large, well-resolved accuracy effect in the
  axis, and it is worth understanding before reading it as "deliberation is
  bad".

#### The one place deliberation hurts, and why it is not what it looks like

All of the tier-1 loss is on the **trap** questions: `trap-q1` goes 5/5 to 0/5.
The obvious reading — that more reasoning talks the model out of the governed
definition — is wrong. It applies the definition *harder*:

> "I excluded refunded transactions, as the business definition of net revenue
> requires their exclusion."

`NET_REVENUE_RULE` says Net Revenue "MUST exclude refunded transactions". That
is a claim about the **aggregate metric**. `trap-q1` asks a **per-row**
question — how many transactions have a list price more than 100× *the net
revenue recorded for that transaction* — where refund status is irrelevant, and
the golden applies no such filter. THINKING answers 212 against an oracle of
235 by taking a MUST literally.

The control is what makes this attributable. `p4_bq_direct` reads the same rule
through catalog metadata and holds at 4–5/5 under THINKING; only
`p4_bq_direct_ctx`, which receives the rule as text pasted into the request,
collapses. So the effect is **injected context × deliberation**, not
deliberation alone — the more prominently a rule is placed, the more literally a
deliberating model applies it, including where it does not apply.

Two honest caveats. Our rule wording genuinely is ambiguous between the metric
and a row value, so part of this is a property of this corpus rather than of the
service. And the oracle encodes one of two defensible readings. Neither changes
the measured interaction, and the rule is deliberately left as-is: it is read by
every governed arm, so editing it would invalidate every capture taken against
the old wording.

#### The cross-capture noise floor is ~7 points, not 1

This sandbox's headline A/A floor is 1 point, from two arms at tier 0 that send
byte-identical requests. That is a **within-run** figure — those arms share a
sweep, an oracle and an hour of the service's weather.

Re-running one configuration unchanged a day later moves it up to **6.7 points**
(`p4_bq_direct` tier 0, 21.7% → 28.3%). Nothing varied but the date. So any
comparison *between* captures needs the larger floor, and `compare.NOISE_FLOOR`
uses it. Under the 1-point floor, several deltas in this axis read as findings
that are in fact day-to-day drift.

---

## Managed vs. self-hosted: what actually differs

This surprised us, so it is worth stating precisely.

**Behaviourally, they are near-identical.** Across paths 1–3, the managed and
Toolbox arms reach the *same verdict* on 94–99% of paired cells — while agreeing
on the exact tool-call sequence 0–7% of the time. Two different routes, same
destination.

**In cost, they differ by up to 12×, and not evenly.** The gap is not a property
of "managed" as a category — it is a different size on each path:

| Pair | Median tokens | Tokens per correct |
|---|---:|---:|
| `p1_managed` / `p1_toolbox` | 6.9× (t0), 7.7× (t1) | 6.7×, 12.3× |
| `p3_managed` / `p3_toolbox` | 4.8×, 4.9× | 5.4×, 5.0× |
| `p2_managed` / `p2_toolbox` | **1.1×, 1.3×** | **0.8×, 0.7×** |

Path 2's managed and self-hosted arms cost essentially the same, while Path 1's
differ sevenfold. Whatever explains this has to explain that unevenness too, and
the tool list does not: all three pairs bind comparable tools.

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

Across the ten arms that bind tools, against median tokens per cell (the two
direct-API arms bind none and run no local model, so neither axis exists for
them — the chart names them rather than dropping them silently):

| Predictor | tier 0 | tier 1 |
|---|---:|---:|
| schema characters | **r = 0.97** | **r = 0.99** |
| tool count | r = 0.14 | r = 0.10 |

Tool count is uncorrelated with what an arm costs. Schema size is very nearly the
whole story, on both tiers independently.

That also settles the uneven managed/self-hosted gap above. `p2_managed` is the
one managed endpoint whose schemas are not bloated — 11,721 chars against
`p2_toolbox`'s 5,602, about 2× — and it is the one pair whose costs match. Path 1
differs 17× in schema size and 7× in cost. The category "managed vs self-hosted"
predicts nothing on its own; the bytes on the wire predict it precisely.

One tool dominates:

| `get_table_info` | chars | share of arm |
|---|---:|---:|
| managed endpoint | 78,197 | 65.2% |
| self-hosted Toolbox | 653 | 0.6% |

A single vendor tool declaration, resent every turn, is two thirds of an arm's
entire prompt floor and 120× its self-hosted equivalent.

This is exactly why `p1_matched` and `p3_matched` exist. The
as-shipped comparison varies two things at once — which tools are bound, and
whose endpoint describes them — and the matched arms hold the first constant to
isolate the second.

**Treat these numbers as perishable.** Managed tool schemas are a vendor detail
that can change without notice, and this table shows that detail dominating the
cost result. Every capture records its own measured sizes for that reason. See
[`reproducing.md`](reproducing.md).

---

## Latency is a separate axis from cost

Tokens do not predict wall clock. Across the ten arms that spend tokens locally,
median tokens against median latency correlates at **r = 0.10 (tier 0)** and
**r = -0.09 (tier 1)** — no relationship in either direction. An arm that costs
100× more does not take 100× longer, and the cheapest arm on tokens is the
slowest on the clock. The two direct-API arms are the limiting case: they spend
no local tokens at all and are the fastest arms in the experiment.

What does predict latency is **how many turns the agent takes**, at a near
constant price per turn (tier 0, single-attempt cells only, so no retry backoff
is counted):

| Arm | Schema chars | Median tokens | Median latency | Tool calls | s / call |
|---|---:|---:|---:|---:|---:|
| `p3_managed` | 143,814 | 930,883 | 96.4s | 20.5 | 4.7 |
| `p1_managed` | 120,009 | 554,528 | 76.7s | 16.5 | 4.6 |
| `p3_toolbox` | 18,865 | 193,550 | 82.3s | 17.0 | 4.8 |
| `p2_managed` | 11,721 | 79,744 | 76.1s | 14.0 | 5.4 |
| `p1_toolbox` | 7,030 | 79,841 | 64.3s | 13.0 | 4.9 |
| `p3_matched` | 6,809 | 207,233 | 89.7s | 19.5 | 4.6 |
| `p2_toolbox` | 5,602 | 71,362 | 64.0s | 15.5 | 4.1 |
| `p1_matched` | 3,019 | 78,004 | 71.9s | 14.0 | 5.1 |
| `p4_bq_ca` | 882 | 8,867 | 62.4s | 3.0 | **20.8** |
| `p4_looker_ca` | 817 | 16,829 | **146.0s** | 2.0 | **73.0** |
| `p4_bq_direct` | 0 | 0 | **10.0s** | 0.0 | n/a |
| `p4_bq_direct_ctx` | 0 | 0 | **10.1s** | 0.0 | n/a |

Every MCP arm sits between 4.1 and 5.4 seconds per tool call regardless of how
verbose its schemas are — a 47× spread in schema size and a 13× spread in tokens
produce no spread at all in the per-turn rate. Latency is turn count times a
constant, so the way to make one of these arms faster is to make it take fewer
steps, not to make its prompt smaller.

**Path 4 is the exception, and that is the finding.** Both CA *tool* arms take
one to three calls and pay 21s and 73s for each. The agent loop did not disappear
when the token count dropped — it moved into someone else's process. Latency is
the part of that hidden loop we can still see from outside.

The direct arms have no per-call rate because they make no tool call: one API
round-trip, 10 seconds, done. That is the same hidden loop `p4_bq_ca` invokes,
reached without the local agent wrapped around it — and it runs **6× faster**.
The 52 seconds in between are the wrapper.

### Seconds per *correct* answer, which is what a user waits

Per-call latency flatters an arm that answers quickly and wrongly. Normalising the
clock the same way the cost columns are normalised — per correct answer — compounds
speed with accuracy, and separates the field much further than either alone:

| Arm | Tier 0 | Tier 1 |
|---|---:|---:|
| `p4_bq_direct_ctx` | **50s** | **12s** |
| `p4_bq_direct` | **51s** | **13s** |
| `p2_toolbox` | 279s | 44s |
| `p4_bq_ca` | 287s | 54s |
| `p2_managed` | 269s | 62s |
| `p1_toolbox` | 212s | 63s |
| `p3_toolbox` | 287s | 69s |
| `p3_managed` | 341s | 80s |
| `p1_managed` | 273s | 85s |
| `p1_matched` | 226s | 91s |
| `p3_matched` | 297s | 91s |
| `p4_looker_ca` | **1,113s** | **240s** |

The two direct arms are in a class of their own on this axis: **12–13 seconds per
correct answer at tier 1, against 44s for the best MCP arm** and 54s for the same
service reached as a tool. They are fast *and* the most accurate, which is the
combination the rest of the field has to trade between. At tier 0 they are
4–7× ahead of everything else for the same reason — one round trip instead of
thirteen to twenty.

Among the MCP arms the tier-0 field is tight, 212s to 341s, except `p4_looker_ca`,
which needs **19 minutes of wall clock per right answer** — 3–5× worse than any
other MCP arm. It is not merely the slowest per call; it is also the least
accurate, and the two multiply.

Governance is the biggest lever on this axis too. Every arm improves from tier 0
to tier 1, by 2.5× (`p1_matched`) to 6.3× (`p2_toolbox`), and almost none of that
is the model getting faster — it is fewer wasted turns and more of them landing
correct. On the direct arms, which take one turn either way, the 4× improvement
is *entirely* accuracy: same clock, more of the answers right.

---

## Reading Path 4's numbers fairly

`p4_bq_ca` and `p4_looker_ca` post the smallest token totals in the sweep, by an
order of magnitude. Taken at face value that reads as the cheap option. It is not
a like-for-like number, and for `p4_looker_ca` we can now say by how much.

1. **The model spend is off-book — but not unmeasurable.** CA plans the query,
   inspects results, and writes the prose using its own Gemini calls,
   server-side. The API reports none of it. Cloud Monitoring does:
   `geminidataanalytics.googleapis.com/chat/{input,output}_token_count`.
   `examples/service_tokens.py` reads those back over each arm's block.
2. **The warehouse spend *is* on-book.** CA's BigQuery jobs run under our tier
   service account, so `INFORMATION_SCHEMA` attribution catches them per cell —
   the MiB column for Path 4 is real, and it is not zero.
3. **The latency said the work was happening.** 73 seconds inside a single
   `ask_data_insights` call was never a cheap call; it was an entire agent loop
   billed to a line item we could not read. The token metric is that loop,
   itemised.

### What the server-side meter says

| Arm | Tier | Recorded | Server-side | True per cell | Understated by |
|---|:-:|--:|--:|--:|:-:|
| `p4_looker_ca` | 0 | 1,643,038 | 30,183,342 | 530,439 | **19×** |
| `p4_looker_ca` | 1 | 522,358 | 14,778,233 | 255,009 | **29×** |
| `p4_bq_ca` | 0 | 776,495 | `--` | `--` | not attributable |
| `p4_bq_ca` | 1 | 396,310 | `--` | `--` | not attributable |

Averaged over its 120 cells, `p4_looker_ca` recorded 18,045 tokens per cell and
actually consumed **392,158**. That does not soften the ranking, it inverts it:

| Arm | Tokens / cell | |
|---|--:|---|
| `p3_managed` | 787,623 | |
| `p1_managed` | 500,454 | |
| **`p4_looker_ca`** | **392,158** | ← recorded 18,045; third most expensive, not cheapest |
| `p3_matched` | 180,108 | |
| `p3_toolbox` | 143,949 | |
| `p2_toolbox` | 107,714 | |
| `p1_matched` | 92,325 | |
| `p2_managed` | 81,256 | |
| `p1_toolbox` | 59,564 | |
| `p4_bq_ca` | 9,773 | floor — 306 CA calls that no meter costs |

The 207 CA turns behind those tokens ran **1,220 server-side model calls**, about
5.9 per turn. That is the agent loop we thought we had removed, running where the
invoice for it is someone else's.

**Why this is ours and not the project's.** The metric's only labels are
`model_name` and `status` — no conversation, agent, or caller dimension — so
attribution is by time window and would absorb anything else in the project using
CA during the sweep. Two checks say nothing else was: `--baseline` over the week
before the sweep returns **exactly zero** turns, and the 207 measured turns line
up with the 120-cell block that produced them. Anyone rerunning this on a busier
project must repeat the baseline check before treating the numbers as measured.

### `p4_bq_ca` reports nothing, which is not the same as spending nothing

Across its entire 2h08m block, `p4_bq_ca` emits **zero** on this metric — and on
all thirteen `geminidataanalytics` metrics — while `p4_looker_ca` emits 44.9M
tokens in the same sweep. Both reach CA, through Toolbox's
`bigquery-conversational-analytics` and `looker-conversational-analytics`.

A zero has two readings, and the usage meter cannot tell them apart: *the arm did
nothing*, or *the meter is not watching*. A second, independent meter can.
`serviceruntime.googleapis.com/api/request_count` is published by the API
front-end every consumed Google API passes through, not by CA itself, so it
answers only "were the calls made":

| Arm | Tier | Successful `Chat` RPCs | CA usage meter |
|---|:-:|--:|--:|
| `p4_bq_ca` | 0 | **189** | 0 |
| `p4_bq_ca` | 1 | **117** | 0 |
| `p4_looker_ca` | 0 | 133 | 30,183,342 |
| `p4_looker_ca` | 1 | 75 | 14,778,233 |

Both arms call the **same RPC** — `google.cloud.geminidataanalytics.v1.DataChatService.Chat`,
same service, same version, every response 200 — and `p4_bq_ca` makes *more* of
them. That settles two of the three mechanisms this document used to list:

- ~~*The BigQuery CA tool routes to a different service that meters elsewhere.*~~
  It does not. Same service, same method, same API version.
- ~~*`p4_bq_ca` genuinely does less server-side work.*~~ It makes 306 successful
  CA calls to Looker CA's 208, at 20.8 s each. Whatever those seconds are, they
  are not idleness.
- *The meter counts only some paths.* This is what is left. It is also weaker
  evidence than it looks: `chat/conversation/created_count` reads **zero for the
  Looker arm too**, so "no conversation was opened" cannot be inferred from a zero
  turn counter — the two zeros agreeing was a coincidence, not a finding.

A controlled run closes it. Three `p4_bq_ca` cells, tier 1, in a four-minute
window whose preceding baseline had **no CA requests at all**: 14 successful
`Chat` calls, and every CA metric still read zero. The calls are real and the
usage meter does not see them.

**The direct arms rule out the tool.** Until 2026-09-07 every BigQuery-backed CA
call in this experiment went through Toolbox's
`bigquery-conversational-analytics`, so "the wrapper routes somewhere unmetered"
remained a live explanation. The direct arms use no Toolbox, no MCP server and no
agent — `ca_direct.py` calls `DataChatServiceClient.chat` itself — and across
their 240 cells they made **243 successful `Chat` RPCs and emitted zero on every
CA usage metric**, exactly like `p4_bq_ca`:

| Arm | Tier | Successful `Chat` RPCs | CA usage meter | On our Vertex quota |
|---|:-:|--:|--:|--:|
| `p4_bq_direct` | 0 | 58 | 0 | 0 |
| `p4_bq_direct` | 1 | 64 | 0 | 0 |
| `p4_bq_direct_ctx` | 0 | 63 | 0 | 0 |
| `p4_bq_direct_ctx` | 1 | 58 | 0 | 0 |

So the discriminator is the **data source, not the transport**: Looker-backed
conversations meter and BigQuery-backed ones do not, however they are invoked.
That also settles what the direct arms' `service only` coverage means. Their zero
recorded tokens are not a new gap opened by going direct — they are `p4_bq_ca`'s
existing unmetered floor with the local agent loop removed, and the local loop is
the only part that was ever on a meter. The Vertex column is the check: it reads
0 for arms that run no local model and tracks the harness exactly for the ones
that do.

**The spend is not on our quota either.** The `on our quota` column of
`examples/service_tokens.py` reads the Vertex publisher metric
(`aiplatform.googleapis.com/publisher/online_serving/token_count`) for
`AGENT_MODEL` over each block. This document used to say that metric "cannot
separate" our agent from the rest of the project. That was wrong twice over: the
monitored resource carries `model_user_id`, which isolates the one model the sweep
holds constant from the ~1.2B tokens other workloads in this project spend on
other models; and separating by label was never the strong test anyway. The
arithmetic is. Per block, Vertex metered 840,055 / 414,334 / 1,637,404 / 531,574
against a harness that recorded 776,495 / 396,310 / 1,643,038 / 522,358 — our own
agent, and nothing else. Looker CA's 44.9M server-side tokens appear **nowhere**
on the Vertex meter. The two meters are disjoint, and a third of a million
unexplained tokens could not hide in a gap that size, let alone 44.9M.

So the honest statement is narrow and it is measured: `p4_bq_ca` performs the same
server-side work through the same API, and **no meter this project can read
reports its cost** — not CA's, not Vertex's. Reporting `--` is the accurate
answer. It stays a `floor`, and now the floor is a demonstrated one rather than an
absence of evidence.

So the honest comparison is not "Path 4 is 105× cheaper." For the Looker arm it is
now the opposite of cheap. For the BigQuery arm it remains a floor. The report
never adds a floor to a full measurement, and neither should a reader.

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

Rule acquisition is **unmeasurable** on all four Path 4 arms rather than zero, so
the report prints `--`, never `0%`. Ranking an arm bottom on a metric it was never
eligible for is a false finding, not a conservative one. Evidence recall was in
the same position and no longer is — the direct arms recovered it, which is what
the rest of this section is about.

**The opacity is our transport's, not the service's.** The two MCP-transport
Path 4 arms call Toolbox's `bigquery-conversational-analytics` tool, which takes
a question and returns prose. The Conversational Analytics API underneath it
returns much more. Probed live against `google-cloud-geminidataanalytics` 0.13.2,
one `inline_context` chat over one governed table streamed back the SQL and the
BigQuery job that ran it:

```text
generated_sql   SELECT SUM(txn_amt_x2) AS total_net_revenue
                FROM `<project>.data_mcp_sandbox_t1.transactions_v2_final`
                WHERE status_flg IS FALSE OR status_flg IS NULL
big_query_job   job_id=job_ZxxUiB2hEmMxg8M4UaPUcUhfsgXR  location=US
```

Two separate messages, not one — `DataMessage.kind` is a `oneof`, so the query
and the job that ran it can never appear on the same message and must be read
off the stream as a whole.

That is scorable on both metrics — and it is a partial trap hit worth scoring,
since it applied the refund rule on `status_flg` but summed the gross-not-net
`txn_amt_x2`. The `job_id` also makes Path 4's warehouse cost attributable per
*cell* rather than per time window.

The `--` was correct and the reason behind it was mis-stated: we attributed to
Conversational Analytics a limitation that belongs to the MCP tool we reached it
through. `p4_bq_direct` closed it by calling the API directly, and it scores
through the **existing** rubric — the scorer prefers SQL a service disclosed
about itself and falls back to scraping a tool trace, so every arm that still
discloses nothing keeps its `--`. Swept, the two direct arms disclose a query on
**100% of their cells**, against 58–62% for `p4_looker_ca`:

| Arm | Tier | No query disclosed | Recall (median) | Precision |
|---|:-:|--:|--:|--:|
| `p4_bq_direct` | 0 | **0%** | 0.67 | 0.83 |
| `p4_bq_direct` | 1 | **0%** | 1.00 | 1.00 |
| `p4_bq_direct_ctx` | 0 | **0%** | 0.67 | 0.88 |
| `p4_bq_direct_ctx` | 1 | **0%** | 1.00 | 1.00 |
| `p4_looker_ca` | 0 | 42% | 0.40 | 1.00 |
| `p4_looker_ca` | 1 | 38% | 1.00 | 1.00 |

Acquisition stays `--` on them all the same, and that is not a gap the transport
can close: acquisition asks whether the agent *read* the governed rule, and a
direct call has no tool trace to read it in. On `p4_bq_direct_ctx` the glossary is
injected by construction rather than discovered, so scoring it as acquired would
be reading our own request payload back to ourselves. Going direct buys back
evidence; it does not buy back acquisition. *(Verified for the BigQuery
datasource only. Whether CA over Looker Explores discloses an equivalent query
object is untested.)*

Its warehouse spend *is* attributable — CA's BigQuery jobs run under our own tier
service account and were verified per cell. Its **model** spend is not: CA makes
its own Gemini calls server-side and does not report them, so Path 4 totals are
published as a floor.

One measured trap for anyone reading CA output: **at tier 0 it hallucinated the
governed net-revenue rule and inverted it.** Generative prose can therefore never
serve as evidence that governance was delivered — only a tool result can.

## Where CA does its arithmetic decides whether it is right

`p4_looker_ca` is the one arm governance barely rescues: 15% → 35%, against
75% for every other tier-1 arm. The tier-1 replicates say why, and it is not
randomness.

| Question (tier 1) | Governed measure available? | Five runs | Truth |
|---|---|---|---|
| `semantic-q1` | `total_revenue` | 4,032,361 ×5 | 4,032,361 |
| `semantic-q2` | `total_revenue` + date filter | 241,972 ×5 | 241,972 |
| `governed-q1` | none — governed dimension only | 2,699 ×4, **805** ×1 | 2,699 |
| `direct-q1` | none | 1,000 ×4, **5,000** ×1 | 5,000 |

Where a measure exists, CA is exact and stable across all five replicates. Where
none exists it has to assemble the answer itself, and then it sometimes retrieves
rows and counts them client-side over an incomplete set. The two runs name their
own method: the correct `governed-q1` run reported *"Dimension: `users.user_id`
(Count Distinct)"*; the wrong one reported *"Fields: `users.user_id`, Row Limit:
`-1` (unlimited)"* and returned 805.

Mechanisms ruled out with evidence rather than assertion: it is not a flat
1,000-row cap (2,699 comes back correctly four times in five, and 805 is not a
round number); not Looker's own row limit (`run_inline_query` with no limit, with
`limit="5000"`, and with `limit="-1"` each returned all 5,000 users); not an
inner join dropping rows (all 5,000 users appear in the transactions table); and
not fan-out (all three views declare `primary_key: yes`). What is left is **where
the aggregation happens**. Asking for unlimited rows did not prevent it, so the
bound is not something the caller can opt out of.

The consequence is general, and it lands on this project's thesis from an angle
we did not design for: a silently incomplete row set produces a *confident wrong
answer* whenever the agent derives the result by counting what it received. No
error is raised. A defined measure is not only a statement of business meaning —
it keeps the arithmetic in the warehouse, so governance here defends against an
architectural failure mode, not just a semantic one.
