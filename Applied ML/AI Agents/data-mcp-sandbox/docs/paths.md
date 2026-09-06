# The ten arms

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

Across all ten arms, against median tokens per cell:

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

Tokens do not predict wall clock. Across the ten arms, median tokens against
median latency correlates at **r = 0.10 (tier 0)** and **r = -0.09 (tier 1)** —
no relationship in either direction. An arm that costs 100× more does not take
100× longer, and the cheapest arm on tokens is the slowest on the clock.

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

Every MCP arm sits between 4.1 and 5.4 seconds per tool call regardless of how
verbose its schemas are — a 47× spread in schema size and a 13× spread in tokens
produce no spread at all in the per-turn rate. Latency is turn count times a
constant, so the way to make one of these arms faster is to make it take fewer
steps, not to make its prompt smaller.

**Path 4 is the exception, and that is the finding.** Both CA arms take one to
three calls and pay 21s and 73s for each. The agent loop did not disappear when
the token count dropped — it moved into someone else's process. Latency is the
part of that hidden loop we can still see from outside.

### Seconds per *correct* answer, which is what a user waits

Per-call latency flatters an arm that answers quickly and wrongly. Normalising the
clock the same way the cost columns are normalised — per correct answer — compounds
speed with accuracy, and separates the field much further than either alone:

| Arm | Tier 0 | Tier 1 |
|---|---:|---:|
| `p2_toolbox` | 279s | **44s** |
| `p4_bq_ca` | 287s | 54s |
| `p2_managed` | 269s | 62s |
| `p1_toolbox` | 212s | 63s |
| `p3_toolbox` | 287s | 69s |
| `p3_managed` | 341s | 80s |
| `p1_managed` | 273s | 85s |
| `p1_matched` | 226s | 91s |
| `p3_matched` | 297s | 91s |
| `p4_looker_ca` | **1,113s** | **240s** |

At tier 0 the field is tight — 212s to 341s for every arm except `p4_looker_ca`,
which needs **19 minutes of wall clock per right answer**, 3–5× worse than
anything else. It is not merely the slowest per call; it is also the least
accurate, and the two multiply.

Governance is the biggest lever on this axis too. Every arm improves from tier 0
to tier 1, by 2.5× (`p1_matched`) to 6.3× (`p2_toolbox`), and almost none of that
is the model getting faster — it is fewer wasted turns and more of them landing
correct.

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
