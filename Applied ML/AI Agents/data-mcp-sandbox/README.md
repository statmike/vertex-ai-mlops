# data-mcp-sandbox

**Does data governance actually make an AI agent more accurate — and what does
each way of connecting one to BigQuery cost?**

This is a controlled experiment, not a demo. One model asks fifteen questions
against one dataset through **twelve different ways of reaching the warehouse**,
at **two governance tiers over byte-identical copies of the data**, five times
each. Every answer is scored against a live oracle. The published capture is
**1,800 live cells**.

---

## Why this needs an experiment

The dataset is built to be hostile in the ways real warehouses are hostile:

- a column named `txn_amt_x2` that is gross, not net
- a `status_flg` boolean whose `TRUE` means **refunded**
- an `is_active` flag that disagrees with the business's own definition of "active"
- a `revenue_amount` column that is simply wrong

An agent that reads the schema and writes the obvious SQL gets a **confident
wrong answer**. Nothing about the query looks like a mistake. That is the
failure mode worth measuring, and it is invisible unless you grade against an
oracle that knows the intended answer.

So the question is not "can an agent query BigQuery." It is: *which of the
things we could spend effort on — documenting the data, buying a semantic layer,
handing the whole problem to a managed service — actually changes the answer,
and what does each one cost?*

---

## The vocabulary, once

Four words carry the whole repo. This is the only place they are defined.

**Tier** — the governance variable. Two byte-identical copies of the same data.
**Tier 0** gets nothing but the tables. **Tier 1** gets five things added:
column descriptions, a catalog `overview` aspect carrying the business rule, a
glossary with term-to-column links, profile and data-quality scans, and a LookML
semantic model. When this repo says *governed*, it means those five, together.
The tiers are separated by **IAM, not by prompt** — each arm runs as a per-tier
service account that can read exactly one tier's dataset.

**Path** — one of four architectures for putting a model in front of data.

| Path | Name | The idea |
|:--:|---|---|
| 1 | Raw Data Builder | Schema plus SQL. The agent writes its own queries. No governance surface at all. |
| 2 | Semantic Router | A Looker semantic layer is the *only* data access. No raw SQL, no table names. |
| 3 | Governed Context | Raw SQL **plus** the Knowledge Catalog — the agent can look the business rule up before querying. |
| 4 | Managed Agent | Hand the whole question to Conversational Analytics. The reasoning loop moves into the cloud. |

**Arm** — a path plus a decision about *who runs the tool server*. Twelve arms,
and the suffix is the decision:

| Arm | Who runs the tool server | What the model can reach |
|---|---|---|
| `p1_managed` | Google — `bigquery.googleapis.com/mcp` | raw BigQuery, 5 tools |
| `p1_toolbox` | you — MCP Toolbox, `bigquery` source | raw BigQuery, 8 tools |
| `p1_matched` | you — Toolbox cut down to the managed tool list | raw BigQuery, 5 tools |
| `p2_managed` | **Looker** — your instance's own `/mcp` endpoint | Looker semantic layer, 7 tools |
| `p2_toolbox` | you — Toolbox, `looker` source, same LookML models | Looker semantic layer, 7 tools |
| `p3_managed` | Google — the BigQuery **and** Dataplex MCP endpoints | BigQuery + Knowledge Catalog, 8 tools |
| `p3_toolbox` | you — Toolbox, `bigquery` + `dataplex` sources | BigQuery + Knowledge Catalog, 23 tools |
| `p3_matched` | you — Toolbox cut down to the managed tool lists | BigQuery + Knowledge Catalog, 8 tools |
| `p4_bq_ca` | you — Toolbox, one tool: `ask_data_insights` | CA over BigQuery |
| `p4_looker_ca` | you — Toolbox, one tool: `looker_conversational_analytics` | CA over Looker |
| `p4_bq_direct` | nobody — the CA API is called directly, no MCP | CA over BigQuery |
| `p4_bq_direct_ctx` | nobody — same call, with the tier's glossary injected | CA over BigQuery |

Two things the suffix does **not** tell you, and both have tripped up readers:

- **`managed` names a different vendor's server depending on the path.** On
  Paths 1 and 3 it is Google's BigQuery/Dataplex MCP endpoint. On Path 2 it is
  **Looker's own MCP server**, hosted on your Looker instance at
  `{LOOKER_BASE_URL}/mcp`. Same suffix, different product.
- **Looker is in three arms, and only one of them says so in its name.**
  `p2_managed` (Looker's MCP), `p2_toolbox` (self-hosted, same LookML), and
  `p4_looker_ca` (Conversational Analytics over Looker Explores). The other nine
  arms need no Looker instance at all.

**Deeper:** [`docs/paths.md`](docs/paths.md) — every arm's exact tool list, the
full option space including the combinations we *didn't* run, and the measured
answer to "is this comparison fair?"

---

## How it was measured

Every arm is the **same model** (`gemini-3.7-flash`, temperature 0) asking the
**same fifteen questions** against the **same data**, five replicates, both
tiers. Only the tool surface changes, so a score difference is attributable to
architecture rather than to the model.

Capture and scoring are separate programs. `run_battery.py` records what
happened — every tool call with its arguments and results, every answer, every
token count — and never judges it. `build_results.py` judges and never re-runs
an agent. That split is why you can re-score the published capture on a laptop
with no cloud account.

The 1,800 cells are merged from three runs over nine days, each keeping the
oracle that was true when it ran, because several questions are trailing windows
whose right answer moves with the calendar. **Twelve of the fifteen questions are
gradeable**; three are a documented defect, kept in the capture and left unscored
rather than deleted — see the caveat under the results.

**Cost is reported in units consumed, never dollars** — tokens in, tokens out,
seconds, BigQuery jobs, MiB scanned — and always per *correct* answer, because
an arm that is cheap and wrong is not cheap. Units you can check against your own
invoice; a dollar figure needs a rate card and would be wrong for most readers.
Prices are opt-in via `prices.json`.

**Deeper:** [`docs/method.md`](docs/method.md) — the protocol, why cells run
strictly one at a time, what each capture records about the conditions it ran
under, and how two captures are compared rather than merged.

---

## What was asked

Fifteen questions over four traps. Some are ordinary aggregations the schema can
answer. Some turn on a **governed definition** — a rule that exists in the
business but nowhere in the column names — and those are the ones that separate
the arms. The rest are distractors that punish an agent for trusting a
plausible-looking column.

**Deeper:** [`docs/questions.md`](docs/questions.md) — all fifteen questions, the
four traps, the 0.5% match tolerance, and why two metrics are deliberately left
blank rather than scored zero.

---

## What we found

### Governance is the largest effect measured — and it is not sufficient

**Accuracy roughly triples on every path**, tier 0 to tier 1: 33%→100% on
`p1_toolbox`, 12%→43% on `p4_looker_ca`. On the questions that turn on a governed
definition the separation is total — **0 correct out of 180 cells at tier 0**,
across all twelve arms, against 138/180 at tier 1.

**Which part of it pays is two rungs, for two different populations.** Splitting
tier 1 into five cumulative rungs: on the eight questions needing no governed
definition, **column descriptions alone** take every arm from 30–50% to
97.5–100% and nothing after that moves them. On the questions that turn on a
governed definition, descriptions are worth **0 points** and business rules take
all three Path 3 arms from **0% to 100%** — a step, not a curve. Profile scans
move nothing either way. Governance also pays for itself: tokens per correct
answer drop 3.6–8.1×.

**But no amount of it fixes an agent writing its own SQL.** From the first rung,
every arm that shows its work acquires the governed rule on 100% of cells — we
can read it in the tool results. Yet `p1_managed` and `p1_matched` answer the
governed-definition questions correctly **0 times in 20** at tier 1, and 1 time
in 50 at every ladder rung including the top. The captured SQL says why: it
selects Active users but writes no time window at all, so "an event in the
trailing 30 days" quietly becomes "appears in the log." It is not approximating
the governed answer; it is answering a different question. Only an arm that
already *encodes* the rule — a semantic layer, or a service with one behind it —
executes it.

### Cost is tool schema verbosity, not tool count

Schema characters predict an arm's median token spend at **r = 0.95** (tier 0)
and **r = 0.99** (tier 1). Tool count predicts nothing: **r = 0.12** and
**r = 0.11**. One managed `get_table_info` declaration is **78,214 characters** —
64% of its arm's prompt floor, and **120× the self-hosted equivalent** that does
the same job, re-sent every turn. `p1_managed` spends **1,870,343 input tokens
per correct answer against 5,934 output**: essentially none of the bill is the
model thinking.

**Managed and self-hosted behave the same and cost up to 12× apart.** They reach
the same verdict on 86–99% of paired cells while sharing a tool-call sequence
only 0–5% of the time. The cost gap is 6.9–7.7× on Path 1 and 4.8–4.9× on Path 3
— but only 1.1–1.3× on Path 2, and the schema sizes say exactly why.

**The managed agent was not actually cheapest.** Conversational Analytics bills
its own Gemini loop to a line item the API never returns. Read it back from Cloud
Monitoring and `p4_looker_ca` goes from 18,045 tokens per cell to **392,158** — a
22× understatement that moves it from the cheapest arm to the third most
expensive. Its 207 turns ran 1,220 server-side model calls. `p4_bq_ca` reports
nothing on that meter yet made **306 successful CA calls** on the same API in the
same window: its cost is on no meter this project can read, which is not the same
as being zero.

### Latency is a separate axis, and it does not track cost

Every MCP arm spends **4.3–5.5s per tool call** whatever its schema size, so
latency is turn count times a constant. Tokens against wall clock correlate at
only r = 0.28 and r = 0.33. Path 4 takes 1–3 calls and pays 20–70s for each,
because the loop moved server-side. Per **correct** answer at tier 1 — what a
user actually waits — that is 36–64s for every MCP arm, 199s for `p4_looker_ca`,
and 11s for the two direct arms. At tier 0 the Looker arm needs **24 minutes per
right answer**.

**Wrapping a service in MCP costs 3.1× the wall clock and no accuracy.**
`p4_bq_ca` and `p4_bq_direct` put the same questions to the same CA API over the
same data; one reaches it as a tool inside an agent, the other just calls it. At
tier 1 they land two cells apart — 60/60 against 58/60 — and the direct client
answers in a **10.5s median against 32.6s**. The wrapper also runs a local model
loop the direct call does not: 5,941 input tokens per tier-1 cell against none.
This is the one pair where data, service and model are identical and only the
transport differs.

**Going direct buys a thinking knob, not a model choice.** `ChatRequest.model` is
an enum with one selectable value. Only the direct route exposes `thinking_mode`,
and across three more captures (720 cells) `FAST` runs a **7.4s median against
`THINKING`'s 18.4s** — and `FAST` is *flat*, 6.5–7.7s whatever you ask, where the
default and `THINKING` scale with difficulty. On a governed warehouse `FAST`
costs no measurable accuracy; ungoverned it costs ~16 points.

### Does any of it hold up

**A new model changes the scores and not the ordering.** Every MCP arm re-run on
`gemini-3.8-flash` — both tiers, 720 cells, zero failures — pairs against the
published `gemini-3.7-flash` capture at Kendall tau **+1.00 at both tiers, zero
inversions**. Absolute accuracy shifts a few points in both directions; which
architecture beats which does not move. Only three deltas clear the noise floor,
two of them both Path 2 arms at tier 0 (+11.1 each) — so those two arms were
re-swept on the *original* model eight days later and reproduced the published
numbers **+0.0 on every cell**. That is the model, not capture drift.

**There is an accidental A/A control, and it holds.** `p4_bq_direct` and
`p4_bq_direct_ctx` differ only by a glossary payload, and at tier 0 that payload
is empty by design — so those 120 cells send byte-identical requests. They land
**one cell apart** (13/60 vs 14/60). At tier 1, with the glossary actually
injected, they land **one cell apart again** (58/60 vs 57/60). Most published
context-injection deltas have no control next to them at all.

> **One caveat, stated up front.** Chasing a failed replication check found a
> defect in our own corpus: "trailing 30 days" pins a window's *length* and never
> its *anchor*, so three questions scored near-arbitrarily depending on where the
> oracle's window happened to fall. Those three are marked unscoreable and
> **re-issued as three new questions that pin the anchor**, swept across all
> twelve arms and merged in — which is why the main capture grades **twelve of
> fifteen** questions and the governed-definition population is three questions
> rather than one. The five-rung ladder capture was *not* re-swept, so the
> step-function result above still rests on **one** question at five replicates.
> That is why it is stated separately from everything else.

> **These numbers are perishable.** They are specific to a pinned model version, a
> pinned MCP Toolbox, and vendor tool schemas that can change without notice — and
> that last one dominates the cost result.

**Deeper:** [`docs/results.md`](docs/results.md) — every result above with the
cells behind it, plus what is *unmeasurable* on Path 4 and why the report prints
`--` there rather than 0%. The generated tables are in
[`results/report.md`](results/report.md).

---

## Check the work without a cloud account

`results/capture.json.gz` is the raw sweep — every tool call with its arguments
and result, every answer, every token count — and it holds **no scores**. The
rubric is the part most worth arguing with, so it ships separately:

```bash
uv sync
uv run python examples/build_results.py \
  --results results/capture.json.gz --out /tmp/mine --no-judge --no-cost
```

No project, no corpus, no credentials; the goldens are frozen into the capture's
header. Change `src/scoring.py` and re-run — a rubric change costs a minute
instead of a day.

**Deeper:** [`notebooks/03_results.ipynb`](notebooks/03_results.ipynb) scores the
published capture and draws the charts. It ships with its outputs filled in, so
you can read the entire result without running anything.

---

## Run it yourself

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

Then walk down the cost ladder:

```bash
make preflight        # can you provision this? two read-only IAM calls, free
make bootstrap        # APIs, Toolbox binary, tier identities, corpus, governance
make verify-isolation # prove tier 0 cannot read tier 1 — do not skip this
make plan             # what a sweep would cost, in time and tokens. Free.
make smoke            # 12 cells, ~10 min. Proves the wiring end to end.
```

`make help` lists everything. Provisioning creates billable BigQuery storage and
Dataplex scans, and a full sweep is hours of live model calls; `make plan`
estimates before you spend and `make teardown` deletes everything `setup`
created.

**Without Looker.** Looker is the only component behind an annual-commitment
purchase, and `make bootstrap` deliberately **will not create an instance** — a
setup script must not be able to start an annual charge. Add `SKIP_LOOKER=1` to
any target and nine of the twelve arms remain, at both tiers:

```bash
make bootstrap SKIP_LOOKER=1
make sweep SKIP_LOOKER=1     # 1,350 cells instead of 1,800
```

The central governed-versus-ungoverned result survives; you lose Path 2 and the
Looker half of Path 4.

**Deeper:** [`docs/reproducing.md`](docs/reproducing.md) — the exact commands for
each capture, what will and will not reproduce, and how to compare two captures
that asked different questions.

---

## Run it on your own data

The point of the harness is that the questions, the corpus and the LookML are
*inputs*. [`docs/adapting.md`](docs/adapting.md) walks it in eight rungs:
re-score our capture with no cloud account, run it unchanged in your project,
then move it toward your data one verifiable step at a time, ending at your own
tables and your own Looker across all twelve arms. Start anywhere; stop anywhere.

---

## Layout

| Path | What it holds |
|------|---------------|
| `src/` | All logic — flat, single-responsibility modules |
| `examples/` | Runners: the sweep, the scorer, isolation and inventory probes |
| `scripts/` | Provisioning, teardown, capture export |
| `results/` | The report, the scores, and the publishable capture |
| `tests/` | pytest; imports flat modules from `src/` by name |
| `notebooks/` | [provision](notebooks/01_provision.ipynb) · [walkthrough](notebooks/02_walkthrough.ipynb) · [results](notebooks/03_results.ipynb) — narrative and execution only, no business logic |

Every document, in reading order:

| Document | What it answers |
|---|---|
| [`docs/paths.md`](docs/paths.md) | What each of the twelve arms *is*, and what we chose not to run |
| [`docs/method.md`](docs/method.md) | How the sweep runs and what each capture records |
| [`docs/questions.md`](docs/questions.md) | What was asked, and what counts as right |
| [`docs/results.md`](docs/results.md) | Every measured result, with the cells behind it |
| [`docs/design.md`](docs/design.md) | Why it is built this way, and what it does not claim |
| [`docs/reproducing.md`](docs/reproducing.md) | Re-running exactly this |
| [`docs/adapting.md`](docs/adapting.md) | Running it on your own data |
| [`docs/scoping.md`](docs/scoping.md) | Why the tier fence is IAM and not a prompt |
| [`docs/looker_setup.md`](docs/looker_setup.md) · [`docs/looker_runbook.md`](docs/looker_runbook.md) | Standing up the Looker side |

The reasoning that did not fit anywhere is in the module docstrings, which are
written to be read: [`src/cost.py`](src/cost.py) on why cost is reported in three
parts that are never silently summed,
[`src/service_tokens.py`](src/service_tokens.py) on metering the part the API will
not report, and [`src/scoring.py`](src/scoring.py) on the rubric.

```bash
make check    # ruff + mypy + pytest
```

---

Built from the [AI-Native Project Harness](https://github.com/statmike/agent-repo-template).
