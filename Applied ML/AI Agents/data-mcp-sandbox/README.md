# data-mcp-sandbox

**Does data governance actually make an AI agent more accurate — and what does
each way of connecting one to BigQuery cost?**

This is a controlled experiment, not a demo. The same model asks the same twelve
questions against the same data through **twelve different ways of reaching the
warehouse**, at **two governance tiers** over byte-identical corpora, five times
each. Every answer is scored against a live oracle.

The published capture is **1,440 live cells over all twelve arms**, merged from
two runs two days apart. Each run keeps the oracle that was true when it ran:
four of the twelve questions are trailing windows over data anchored at build
time, so the right answer moves with the calendar and a shared oracle would have
graded correct answers wrong.

The corpus is built to be hostile in the ways real warehouses are hostile:
columns named `txn_amt_x2` that are gross-not-net, a `status_flg` boolean whose
`TRUE` means refunded, an `is_active` flag that disagrees with the governed
definition of "active", and a `revenue_amount` column that is wrong. An agent
that reads the schema and writes the obvious SQL gets a confident wrong answer.

---

## The headline

| Question | Answer |
|---|---|
| Does governance help? | **Yes, and it is the largest effect measured.** Accuracy roughly doubles from tier 0 to tier 1 on every path — 33%→75% on `p1_toolbox`, 15%→35% on `p4_looker_ca`. |
| Which *part* of it pays? | **Only one rung is governance, and only one path can use it.** Tier 1 turns six channels on at once; `LADDER=1` splits them into five cumulative rungs over 1,800 cells, zero failures. The twelve questions turn out to be two populations. On the **eight that need no governed definition**, column descriptions alone take every arm from 30–50% to 98–100% at rung 1 and the remaining rungs do nothing — that is documentation, and it is the best-value rung on the ladder. On the **questions that turn on a governed definition**, descriptions are worth **0 points** and rung 3 (business rules) takes all three Path 3 arms from **0% to 100%**. Not a curve — a step. Profile scans move nothing on either population, and governance pays for itself: every arm's tokens per correct answer drop 4–10×. [Full ladder →](docs/paths.md#which-rung-pays) |
| Is it enough? | **No, and for Path 1 no amount of it is.** From rung 1 onward *every arm that shows its work* acquires the governed rule on 100% of cells — read from the tool results, not from the answer. Yet **Path 1 answers a governed-definition question correctly 1 time in 150, at every rung including the top one.** It replies `5000` for the Active-user count, which is the total user count, and all-time revenue for revenue-from-Active-users. It is not approximating the governed answer; it is answering a different question. Acquiring a rule and applying it are different problems, and on this corpus **a semantic layer is the only thing that makes a written rule executable.** |
| Managed or self-hosted MCP? | **Behaviourally the same, up to 12× apart on cost.** They reach the same verdict on 94–99% of paired cells while sharing a tool-call sequence 0–7% of the time. The gap is 6.9–7.7× on Path 1 and 4.8–4.9× on Path 3 — but only 1.1–1.3× on Path 2, and the schema sizes say why. |
| Where does the cost come from? | **Tool schema verbosity, not tool count.** Schema characters predict an arm's median tokens at r = 0.97 (tier 0) and r = 0.99 (tier 1); tool count predicts nothing at r = 0.14 and r = 0.10. One managed `get_table_info` declaration is 78,197 chars — 65% of its arm's prompt floor, and 120× the self-hosted equivalent that does the same job. Splitting input from output shows it directly: `p1_managed` spends **1,673,836 input tokens per correct answer against 5,487 output**. Essentially none of the bill is the model thinking. It is tool definitions, re-sent every turn. |
| How long does it take? | **Latency is a separate axis — it does not track cost.** Tokens against wall clock correlates at r = 0.10 and r = -0.09. Every MCP arm spends 4.1–5.4s per tool call whatever its schema size, so latency is turn count times a constant. Path 4 takes 1–3 calls and pays 21–73s for each, because the loop moved server-side. Measured as **seconds per correct answer**, which is what a user actually waits, tier 1 runs 44–91s for every arm except `p4_looker_ca` at 240s — and at tier 0 that arm needs **19 minutes per right answer**, 3–5× worse than anything else. |
| Does wrapping a service in MCP cost anything? | **Yes — 13 accuracy points and 3.2× the wall clock, with the service held fixed.** `p4_bq_ca` and `p4_bq_direct` put the same questions to the same Conversational Analytics API over the same BigQuery corpus; one reaches it as a tool inside an ADK agent, the other calls it. At tier 1 the direct arm scores **88% against 75%** and answers in a **10.3s median against 32.8s** — 13s per correct answer against 54s. The wrapper also runs a local model loop the direct call does not: 7,596 input tokens per cell against none. This is the one pair in the experiment where the data source, the service, and the model are all identical and only the transport differs. |
| Does injecting business context help, and by how much more than noise? | **7 points, against a measured noise floor of 1.** `p4_bq_direct` and `p4_bq_direct_ctx` differ only by a glossary payload, and at tier 0 that payload is empty by design — so those 120 cells send byte-identical requests and are an accidental A/A control. They land **1 point apart** (22% vs 23%). At tier 1 the glossary is worth **7 points** (88% vs 95%), seven times the floor the same pair just measured for itself. Most published context-injection deltas have no such control next to them. |
| Going direct — what does it actually buy you? | **Not a choice of model. A choice of how hard it thinks, and that knob is worth ~2.4× on latency.** `ChatRequest.model` is an enum with one selectable value, so neither route lets you pick a model; only the direct route exposes `thinking_mode`. Across three more captures (720 cells), `FAST` runs a **7.4s median against `THINKING`'s 18.4s** — and `FAST` is *flat*, 6.5–7.7s no matter which question you ask, where the default and `THINKING` both scale with difficulty. On a governed warehouse `FAST` costs no measurable accuracy; ungoverned it costs ~12 points. `THINKING` is the one that surprises: it loses 10–13 points at tier 1 on the context-injected arm, entirely by applying a governed rule *too* literally. |
| Is the managed agent really cheapest? | **No — that was an accounting artifact, and it inverts once you meter it.** Conversational Analytics bills its own Gemini loop to a line item the API never returns. Read it back from Cloud Monitoring and `p4_looker_ca` goes from 18,045 tokens per cell to **392,158** — a 22× understatement that moves it from the cheapest arm to the third most expensive. Its 207 turns ran 1,220 server-side model calls. `p4_bq_ca` reports nothing on that meter, but it made **306 successful CA calls** on the same API in the same window — its cost is on no meter this project can read, which is not the same as being zero. |

**Cost is reported in units consumed, not dollars** — tokens in, tokens out,
seconds, BigQuery jobs, MiB scanned, all per *correct* answer, because an arm that
is cheap and wrong is not cheap. Those you can check against your own invoice; a
dollar figure needs a rate card and would be wrong for most readers. Prices are
opt-in via `prices.json`.

### Read it in order

| To ask | Read |
|---|---|
| What are my actual options, and which of them did you run? | [`docs/paths.md`](docs/paths.md#the-option-space-and-which-of-it-we-ran) — the option space and the empty cells |
| Is the comparison fair? | [`docs/paths.md`](docs/paths.md#is-that-fair) — the endpoint is worth 40×, the tool list under 7%, both measured |
| Why is it built this way, and what does it *not* claim? | [`docs/design.md`](docs/design.md) |
| What was asked, and what counts as right? | [`docs/questions.md`](docs/questions.md) |
| What happened? | [`results/report.md`](results/report.md) — full tables |
| How do I re-run exactly this? | [`docs/reproducing.md`](docs/reproducing.md) |
| How do I run it on my own data? | [`docs/adapting.md`](docs/adapting.md) |

> **These numbers are perishable.** They are specific to a pinned model version,
> a pinned MCP Toolbox, and vendor tool schemas that can change without notice —
> and that last one dominates the cost result. See
> [`docs/reproducing.md`](docs/reproducing.md) for what will and will not
> reproduce.

**Want it on your own warehouse?** [`docs/adapting.md`](docs/adapting.md) walks it
in eight rungs — re-score our capture with no cloud account, run it unchanged in
your project, then move it toward your data one verifiable step at a time, ending
at your own tables and your own Looker for all twelve arms. Start anywhere; stop
anywhere. Nine of the twelve arms need no Looker instance at all.

---

## Setup

Self-contained `uv` project. Run everything from inside this folder.

```bash
cd "Applied ML/AI Agents/data-mcp-sandbox"

uv sync                                   # create .venv from pyproject.toml + uv.lock
gcloud auth application-default login     # ADC — this project never uses SA JSON keys
cp .env.example .env                      # then fill in GOOGLE_CLOUD_PROJECT
```

Requires [`uv`](https://docs.astral.sh/uv/) and the
[Google Cloud CLI](https://cloud.google.com/sdk/docs/install). Never use `pip` —
`uv` manages all dependencies, environments, and the lockfile.

Then provision and walk down the cost ladder:

```bash
make preflight        # can you provision this? two read-only IAM calls, free
make bootstrap        # APIs, Toolbox binary, tier identities, corpus, governance
make verify-isolation # prove tier 0 cannot read tier 1 — do not skip this
make plan             # what a sweep would cost, in time and tokens. Free.
make smoke            # 12 cells, ~10 min. Proves the wiring end to end.
```

`make help` lists everything.

### Without Looker

Looker is the only component behind an annual-commitment purchase, and
`make bootstrap` deliberately **will not create an instance** — a setup script
must not be able to start an annual charge. Add `SKIP_LOOKER=1` to any target:

```bash
make bootstrap SKIP_LOOKER=1
make sweep SKIP_LOOKER=1     # 1,080 cells instead of 1,440
```

Nine of twelve arms remain, at both governance tiers. The central governed-vs-
ungoverned result survives; you lose the semantic-layer path.

---

## Notebooks

The same steps with the reasoning in between. They import `src/` and call the
functions the `make` targets call, so the two paths cannot drift apart.

| | | |
|---|---|---|
| [`01_provision.ipynb`](notebooks/01_provision.ipynb) | build the corpus, apply governance, prove the fence | costs money |
| [`02_walkthrough.ipynb`](notebooks/02_walkthrough.ipynb) | one arm, one question, both tiers — tool call by tool call | live model calls |
| [`03_results.ipynb`](notebooks/03_results.ipynb) | score the published capture and draw the charts | free, offline |

Notebook 3 needs nothing but `uv sync` — it reads `results/capture.json.gz` and
ships with its outputs, so you can read the whole result without a Google Cloud
project. Start there if you are only here to check the work.

---

## Re-scoring without a cloud account

`results/capture.json.gz` is the raw sweep — every tool call with its arguments
and result, every answer, every token count — and it holds **no scores**. The
rubric is the part most worth arguing with, so it ships separately:

```bash
uv run python examples/build_results.py \
  --results results/capture.json.gz --out /tmp/mine --no-judge --no-cost
```

No project, no corpus, no credentials. The goldens are frozen into the capture's
header. Change `src/scoring.py` and re-run; a rubric change costs a minute
instead of a day.

[`docs/questions.md`](docs/questions.md) is the map before you start: the four
traps, all twelve questions, the 0.5% match tolerance, and why two metrics are
deliberately left blank rather than scored zero.

---

## How it works

**Four independent choices, not one.** Where the reasoning runs — a local agent
loop (paths 1–3) or a cloud service that owns the loop (path 4). How you reach it
— as an MCP tool an agent calls, or as an API you call yourself. Who hosts the
tools — a Google-managed MCP endpoint or a self-hosted MCP Toolbox. And which
tools you bind under that server's ceiling, which is 9 on the managed side and 32
on Toolbox. Path 1 is raw BigQuery, Path 2 routes through a Looker semantic
layer, Path 3 adds the Knowledge Catalog, Path 4 hands the whole question to
Conversational Analytics — which is not a fourth server but a *single tool* on one
you already run, and also an API you can call with no server at all. The grid, and
why some of its cells are empty, is in
[`docs/paths.md`](docs/paths.md#the-option-space-and-which-of-it-we-ran).

**Fairness is decomposed, not asserted.** Managed and self-hosted differ on two
things at once — the endpoint and the tool list — so the `_matched` arms hold the
tool list constant and vary only the endpoint. `p1_managed` and `p1_matched` bind
the same five tools and differ **40×** on schema size. `p3_toolbox` and
`p3_matched` share an endpoint with 23 tools against 8 and differ by **under 7%**,
at identical tier-1 accuracy. The endpoint is the whole cost story; the tool count
is not. The same decomposition now runs one layer down on Path 4: `p4_bq_direct`
reaches Conversational Analytics without Toolbox's tool in between, so "the
service" and "the wrapper we reached it through" stop being one variable. Those
cells are built but not yet swept.

**Tiers are separated by IAM, not by prompt.** Knowledge Catalog search is
project-wide and content-addressed — `search_entries` takes a query, not a scope
— so a tier-0 agent asking for "revenue" was handed the tier-1 governed entry and
answered from it. No MCP parameter can prevent that; catalog search being
ACL-filtered per caller can. Each arm runs as a per-tier service account,
keylessly impersonated from your own ADC. `make verify-isolation` is what tells a
real fence from an assumed one. See [`docs/scoping.md`](docs/scoping.md).

**Capture and scoring are separate programs.** `run_battery.py` records what
happened and never judges it; `build_results.py` judges and never re-runs an
agent. Three scoring passes, independently skippable because they have different
costs: deterministic (free), BigQuery cost attribution (one
`INFORMATION_SCHEMA` query), and a blind LLM judge for semantic adherence (one
model call per governed cell). The protocol — 1,440 cells, five replicates, why
they run strictly one at a time, and what each capture records about the
conditions it ran under — is in [`docs/method.md`](docs/method.md).

**Unmeasured is never reported as zero.** No Path 4 cell lets us watch the agent
*read* a governed rule, because there is no tool call to watch, so rule
acquisition is *unmeasurable* on those arms and the report prints `--` rather
than 0%. Ranking an arm bottom on a metric it was never eligible for is a false
finding, not a conservative one.

Evidence was in the same position and is no longer. Reaching Conversational
Analytics through an MCP tool leaves only its prose to scrape, which is why
`p4_looker_ca` discloses no query on 42% of its cells. That is a limit of the
tool, not of CA: called directly, the API streams the generated SQL and the
BigQuery job id, which we
[verified live](docs/paths.md#what-is-opaque-and-what-that-costs-the-measurement).
`p4_bq_direct` is that call, and now that it has been swept the arm scores
through the existing rubric at **0% undisclosed** and 1.00 median recall at tier
1. Going direct buys back evidence; it does not buy back acquisition, and the
report keeps those two apart. Conversational Analytics also spends model tokens
server-side that it does not report, so its cost is published as a floor.

**A floor is a debt, not a conclusion.** That Path 4 floor turned out to be
readable after all — not from the API, but from Cloud Monitoring, which meters
CA's own Gemini loop:

```bash
uv run python examples/service_tokens.py --results results/capture.json.gz
uv run python examples/service_tokens.py --baseline 2026-08-25 2026-09-01
```

It cost `p4_looker_ca` its first-place finish on cost. Run `--baseline` first: the
metric has no caller label, so it attributes by time window and only holds if
nothing else in the project is using CA.

**A zero needs a second meter.** `p4_bq_ca` reads zero on every CA usage metric,
which could mean the arm did nothing or that nothing was counting. The `CA calls`
column settles it from the API front-end rather than from CA itself — 306
successful calls to the very same RPC the Looker arm uses — and the `on our quota`
column shows Vertex metering only our own agent, so the missing spend is not
hiding there either. Both arms do the work; only one of them is billed where we
can see it. [docs/paths.md](docs/paths.md#p4_bq_ca-reports-nothing-which-is-not-the-same-as-spending-nothing)

---

## Layout

| Path | What it holds |
|------|---------------|
| `src/` | All logic — flat, single-responsibility modules |
| `examples/` | Runners: the sweep, the scorer, isolation and inventory probes |
| `scripts/` | Provisioning, teardown, capture export |
| `docs/` | [design](docs/design.md) · [paths](docs/paths.md) · [questions & rubric](docs/questions.md) · [method](docs/method.md) · [reproducing](docs/reproducing.md) · [**adapting**](docs/adapting.md) · [scoping](docs/scoping.md) · [Looker setup](docs/looker_setup.md) · [runbook](docs/looker_runbook.md) |
| `results/` | The report, the scores, and the publishable capture |
| `tests/` | pytest; imports flat modules from `src/` by name |
| `notebooks/` | [provision](notebooks/01_provision.ipynb) · [walkthrough](notebooks/02_walkthrough.ipynb) · [results](notebooks/03_results.ipynb) — narrative and execution only, no business logic |

The reasoning that did not fit here is in the module docstrings, which are written
to be read: [`src/cost.py`](src/cost.py) on why cost is reported in three parts
that are never silently summed, [`src/service_tokens.py`](src/service_tokens.py)
on metering the part the API will not report, and
[`src/scoring.py`](src/scoring.py) on the rubric.

## Checks

```bash
make check    # ruff + mypy + pytest
```

## Cost and teardown

Provisioning creates billable BigQuery storage and Dataplex scans; a full sweep
is hours of live model calls. `make plan` estimates before you spend, and
`make teardown` deletes everything `setup` created.

---

Built from the [AI-Native Project Harness](https://github.com/statmike/agent-repo-template).
