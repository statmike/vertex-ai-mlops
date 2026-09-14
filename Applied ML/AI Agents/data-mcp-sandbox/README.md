# data-mcp-sandbox

**Twelve ways to connect an AI agent to BigQuery, measured against the same
fifteen questions on the same data.** 1,800 live cells, scored against an oracle.

The answer, in three lines:

- **Documenting your data is the biggest lever there is.** Accuracy roughly
  triples on every architecture.
- **It is still not enough.** An agent that writes its own SQL reads the rule,
  restates it correctly, and then applies half of it.
- **Cost is dominated by tool *schema* size, not tool count** — one vendor tool
  declaration is 78,214 characters, re-sent every turn.

---

## Start here: one question, three answers

> *"Treat 2026-09-09 00:00:00 UTC as the current time. How many Active users do
> we have?"*

The business has a written rule for **Active**: the account is flagged active
**and** the user has an event in the trailing 30 days. Both halves. Here is what
the agents actually returned:

| What the agent did | Answer | |
|---|---:|---|
| Trusted the `is_active` column | **3,520** | ❌ 20% of flagged users are dormant |
| Applied the 30-day window, **dropped the flag** | **3,995** | ❌ counts users who were never flagged |
| Applied both halves of the rule | **2,804** | ✅ |

Three plausible queries. Three confident answers. No error message anywhere.

**Row 1 is what every arm does without governance** — 57 of 60 ungoverned cells
returned 3,520. **Row 2 is the surprise:** that is a *governed* run. The agent
read the rule, said out loud *"rather than relying on the raw `users.is_active`
account flag"*, wrote a correct 30-day window — and threw away the half of the
rule it had just quoted.

That gap is what this repo measures, across twelve architectures.

---

## The data is built to be hostile

Real warehouses are hostile in specific, boring ways. This corpus reproduces four
of them:

| Column | Looks like | Actually is |
|---|---|---|
| `txn_amt_x2` | a transaction amount | **gross**, not net |
| `status_flg` | "is it OK?" | `TRUE` means **refunded** |
| `is_active` | who is active | disagrees with the business's own definition |
| `revenue_amount` | revenue | **wrong** |

An agent that reads the schema and writes the obvious SQL gets a confident wrong
answer. That is invisible unless you grade against an oracle that knows the
intended number — which is the whole reason this is an experiment and not a demo.

---

## The two variables

Everything in this repo is one of these two things changing. Nothing else moves:
same model (`gemini-3.7-flash`, temperature 0), same questions, same data, five
replicates.

### Variable 1 — governance, as a **tier**

Two byte-identical copies of the data.

| | Tier 0 | Tier 1 |
|---|---|---|
| the tables | ✅ | ✅ |
| column descriptions | — | ✅ |
| business rule, as a catalog `overview` aspect | — | ✅ |
| glossary with term-to-column links | — | ✅ |
| profile + data-quality scans | — | ✅ |
| LookML semantic model | — | ✅ |

When this repo says **governed**, it means those five, together.

The tiers are separated by **IAM, not by prompt**. Each arm runs as a per-tier
service account that can read exactly one tier's dataset — because catalog search
is project-wide, and a tier-0 agent asking for "revenue" was otherwise handed the
governed entry and answered from it.

### Variable 2 — architecture, as a **path**

Four ways to put a model in front of data:

```mermaid
flowchart LR
    Q["the 15 questions"]

    subgraph Paths["four architectures"]
        P1["Path 1 - Raw Data Builder<br/>schema plus SQL"]
        P2["Path 2 - Semantic Router<br/>Looker is the only access"]
        P3["Path 3 - Governed Context<br/>SQL plus the catalog"]
        P4["Path 4 - Managed Agent<br/>the cloud owns the loop"]
    end

    DP["Knowledge Catalog<br/>rules, glossary, scans"]
    LK["Looker<br/>semantic layer"]
    BQ[("BigQuery corpus<br/>tier 0 and tier 1")]

    Q --> P1
    Q --> P2
    Q --> P3
    Q --> P4

    P1 --> BQ
    P2 --> LK
    P3 --> DP
    P3 --> BQ
    P4 --> BQ
    P4 --> LK
    DP -.-> BQ
    LK --> BQ

    classDef path fill:#1a73e8,stroke:#0b57d0,color:#fff
    class P1,P2,P3,P4 path
```

Each path is run several ways, and each of those is an **arm**. There are twelve.
**An arm's name starts with its path number** — every `p1_` arm is Path 1, every
`p3_` arm is Path 3 — and the rest of the name says *who runs the tool server*.

#### Path 1 — Raw Data Builder

Schema plus SQL. The agent writes its own queries. No governance surface at all.
This is the baseline everything else has to beat.

| Arm | Tool server | Tools |
|---|---|---:|
| `p1_managed` | Google — `bigquery.googleapis.com/mcp` | 5 |
| `p1_toolbox` | you — MCP Toolbox, `bigquery` source | 8 |
| `p1_matched` | you — Toolbox, cut down to the managed tool list | 5 |

#### Path 2 — Semantic Router

A **Looker** semantic layer is the *only* data access. No raw SQL, no table
names: the agent can reach a measure or it cannot.

| Arm | Tool server | Tools |
|---|---|---:|
| `p2_managed` | **Looker** — your instance's own `/mcp` endpoint | 7 |
| `p2_toolbox` | you — Toolbox, `looker` source, same LookML models | 7 |

> ⚠️ **`managed` does not mean the same vendor on every path.** On Paths 1 and 3
> it is Google's MCP endpoint. Here it is **Looker's own server**, hosted on your
> Looker instance at `{LOOKER_BASE_URL}/mcp`.

#### Path 3 — Governed Context

Raw SQL **plus** the Knowledge Catalog, so the agent can look the business rule
up before it queries.

| Arm | Tool server | Tools |
|---|---|---:|
| `p3_managed` | Google — the BigQuery **and** Dataplex MCP endpoints | 8 |
| `p3_toolbox` | you — Toolbox, `bigquery` + `dataplex` sources | 23 |
| `p3_matched` | you — Toolbox, cut down to the managed tool lists | 8 |

#### Path 4 — Managed Agent

Hand the whole question to Conversational Analytics. The reasoning loop moves
into the cloud, so there is no local agent to watch.

| Arm | Tool server | Reaches |
|---|---|---|
| `p4_bq_ca` | you — Toolbox, one tool: `ask_data_insights` | CA over BigQuery |
| `p4_looker_ca` | you — Toolbox, one tool: `looker_conversational_analytics` | CA over **Looker** |
| `p4_bq_direct` | *none* — the CA API is called directly | CA over BigQuery |
| `p4_bq_direct_ctx` | *none* — same call, glossary injected | CA over BigQuery |

**Where Looker appears:** three arms — `p2_managed`, `p2_toolbox`,
`p4_looker_ca`. The other nine need no Looker instance at all.

**Deeper:** [`docs/paths.md`](docs/paths.md) — every arm's exact tool list, the
full option space including what we chose *not* to run, and the measured answer
to "is this comparison fair?"

---

## What we found

### 1. Governance is the largest effect measured

Accuracy roughly triples, tier 0 → tier 1, on every path: 33%→100% on
`p1_toolbox`, 12%→43% on `p4_looker_ca`.

On questions that turn on a governed **definition**, the separation is total:

> **0 correct out of 180 cells at tier 0** — across all twelve arms — against
> 138/180 at tier 1.

### 2. Only two parts of governance actually pay

Split tier 1 into five cumulative rungs and the populations separate cleanly:

| Question type | What moves the needle | What does nothing |
|---|---|---|
| Ordinary aggregations (8 questions) | **column descriptions alone**: 30–50% → 97.5–100% | everything after that |
| Governed definitions | **business rules**: 0% → 100% on all three Path 3 arms | descriptions (worth 0 points) |

A step, not a curve. Profile scans move nothing either way. And governance pays
for itself — tokens per correct answer drop **3.6–8.1×**.

### 3. Governance is necessary, not sufficient

From the first rung, **every arm that shows its work acquires the rule on 100% of
cells** — we can read it in the tool results.

`p1_managed` and `p1_matched` still answer the governed-definition questions
correctly **0 times in 20** at tier 1, and 1 time in 50 at every ladder rung
including the top. The worked example at the top of this page is that failure:
the rule is a conjunction, and the agent applies one conjunct.

Only an arm that already *encodes* the rule — a semantic layer, or a service with
one behind it — executes it. On this corpus a semantic layer is not an
optimisation; it is the thing that works.

### 4. Cost is tool schema verbosity, not tool count

| Predictor of an arm's token spend | tier 0 | tier 1 |
|---|---:|---:|
| **schema characters** | r = 0.95 | r = 0.99 |
| tool count | r = 0.12 | r = 0.11 |

One managed `get_table_info` declaration is **78,214 characters** — 64% of its
arm's entire prompt floor, and **120×** the self-hosted equivalent that does the
same job. Re-sent every turn.

`p1_managed` spends **1,870,343 input tokens per correct answer against 5,934
output**. Essentially none of the bill is the model thinking.

**Managed and self-hosted behave the same and cost up to 12× apart.** Same
verdict on 86–99% of paired cells, while sharing a tool-call sequence only 0–5%
of the time. The gap is 6.9–7.7× on Path 1, 4.8–4.9× on Path 3, and only 1.1–1.3×
on Path 2 — and the schema sizes say exactly why.

### 5. Latency is a separate axis, and it does not track cost

Every MCP arm spends **4.3–5.5s per tool call** whatever its schema size, so
latency is just turn count times a constant. Tokens against wall clock correlate
at only r = 0.28 and r = 0.33.

Per **correct** answer at tier 1 — what a user actually waits:

| | seconds per correct answer |
|---|---:|
| every MCP arm | 36–64s |
| `p4_looker_ca` | 199s |
| the two direct arms | 11s |

At tier 0 the Looker CA arm needs **24 minutes** per right answer.

**Wrapping a service in MCP costs 3.1× the wall clock and no accuracy.**
`p4_bq_ca` and `p4_bq_direct` put the same question to the same API over the same
data; one goes through a tool, the other just calls it. Tier 1: 60/60 against
58/60, and a **10.5s median against 32.6s**. The wrapper also burns 5,941 input
tokens per cell that the direct call does not. It is the one pair where data,
service and model are identical and only the transport differs.

What going direct *does* buy is a thinking knob — not a model choice, since
`ChatRequest.model` is an enum with one selectable value. Over three more
captures (720 cells), `FAST` runs a **7.4s median against `THINKING`'s 18.4s**,
and `FAST` is *flat* — 6.5–7.7s whatever you ask, where the other modes scale
with difficulty. On a governed warehouse it costs no measurable accuracy;
ungoverned it costs ~16 points.

### 6. The managed agent was not actually the cheapest

Conversational Analytics bills its own Gemini loop to a line item the API never
returns. Read it back from Cloud Monitoring:

| `p4_looker_ca` tokens per cell | |
|---|---:|
| as the API reports it | 18,045 |
| as Cloud Monitoring meters it | **392,158** |

A 22× understatement — enough to move it from the cheapest arm to the third most
expensive. Its 207 turns ran 1,220 server-side model calls.

`p4_bq_ca` reports nothing on that meter, yet made **306 successful CA calls** on
the same API in the same window. Its cost is on no meter this project can read,
which is not the same as zero.

### 7. It survives a model change

Every MCP arm re-run on `gemini-3.8-flash` — both tiers, 720 cells, zero failures
— pairs against the published `gemini-3.7-flash` capture at Kendall tau **+1.00
at both tiers, zero inversions**. Absolute scores shift a few points; which
architecture beats which does not move.

And there is an accidental **A/A control**: `p4_bq_direct` and
`p4_bq_direct_ctx` differ only by a glossary payload, which at tier 0 is empty by
design — so those 120 cells send byte-identical requests. They land one cell
apart (13/60 vs 14/60). At tier 1, with the glossary actually injected, one cell
apart again (58/60 vs 57/60). Most published context-injection deltas have no
control next to them at all.

**Deeper:** [`docs/results.md`](docs/results.md) — every number above with the
cells behind it. The generated tables are in
[`results/report.md`](results/report.md).

---

## What this does not claim

> **A defect we found in our own corpus.** "Trailing 30 days" pins a window's
> *length*, never its *anchor*, so three questions scored near-arbitrarily
> depending on where the oracle's window fell. They are marked unscoreable and
> **re-issued as three anchored questions**, swept across all twelve arms and
> merged in. So the capture grades **twelve of fifteen** questions. The five-rung
> ladder was *not* re-swept, which means the 0%→100% step in finding 2 still
> rests on **one** question at five replicates. It is queued.

> **These numbers are perishable.** They are specific to a pinned model version,
> a pinned MCP Toolbox, and vendor tool schemas that can change without notice —
> and that last one dominates the cost result.

**Cost is reported in units consumed, never dollars** — tokens, seconds,
BigQuery jobs, MiB scanned — and always per *correct* answer, because an arm that
is cheap and wrong is not cheap. Units you can check against your own invoice; a
dollar figure needs a rate card and would be wrong for most readers. Prices are
opt-in via `prices.json`.

---

## Check the work yourself — no cloud account, 6 seconds

`results/capture.json.gz` holds the raw sweep: every tool call with its arguments
and results, every answer, every token count. It contains **no scores**. The
rubric is the part most worth arguing with, so it ships separately:

```bash
uv sync
uv run python examples/build_results.py \
  --results results/capture.json.gz --out /tmp/mine --no-judge --no-cost
```

No project, no corpus, no credentials — the goldens are frozen into the capture's
header. Change `src/scoring.py`, re-run, and a rubric change costs a minute
instead of a day.

[`notebooks/03_results.ipynb`](notebooks/03_results.ipynb) does the same thing
with charts, and ships with its outputs filled in — you can read the entire
result without running anything.

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
[Google Cloud CLI](https://cloud.google.com/sdk/docs/install). Never `pip` — `uv`
manages all dependencies, environments, and the lockfile.

Then walk down the cost ladder:

```bash
make preflight        # can you provision this? two read-only IAM calls, free
make bootstrap        # APIs, Toolbox binary, tier identities, corpus, governance
make verify-isolation # prove tier 0 cannot read tier 1 — do not skip this
make plan             # what a sweep would cost, in time and tokens. Free.
make smoke            # 12 cells, ~10 min. Proves the wiring end to end.
```

`make help` lists everything. Provisioning creates billable BigQuery storage and
Dataplex scans and a full sweep is hours of live model calls, so `make plan`
estimates before you spend and `make teardown` removes everything `setup` made.

**No Looker?** It is the only component behind an annual commitment, and
`make bootstrap` deliberately **will not create an instance** — a setup script
must not be able to start an annual charge. Add `SKIP_LOOKER=1` to any target:

```bash
make bootstrap SKIP_LOOKER=1
make sweep SKIP_LOOKER=1     # 1,350 cells instead of 1,800
```

Nine of twelve arms remain at both tiers. The central governed-versus-ungoverned
result survives; you lose Path 2 and the Looker half of Path 4.

**Deeper:** [`docs/reproducing.md`](docs/reproducing.md) — the exact commands per
capture, what will and will not reproduce, and how to compare two captures that
asked different questions.

---

## Run it on your own data

The questions, the corpus and the LookML are *inputs*.
[`docs/adapting.md`](docs/adapting.md) walks it in eight rungs: re-score our
capture with no cloud account, run it unchanged in your project, then move it
toward your data one verifiable step at a time, ending at your own tables and
your own Looker across all twelve arms. Start anywhere; stop anywhere.

---

## Where everything lives

| Document | What it answers |
|---|---|
| [`docs/paths.md`](docs/paths.md) | What each of the twelve arms *is*, and what we chose not to run |
| [`docs/questions.md`](docs/questions.md) | All fifteen questions, the four traps, and what counts as right |
| [`docs/method.md`](docs/method.md) | How the sweep runs and what each capture records |
| [`docs/results.md`](docs/results.md) | Every measured result, with the cells behind it |
| [`docs/design.md`](docs/design.md) | Why it is built this way, and what it does not claim |
| [`docs/reproducing.md`](docs/reproducing.md) | Re-running exactly this |
| [`docs/adapting.md`](docs/adapting.md) | Running it on your own data |
| [`docs/scoping.md`](docs/scoping.md) | Why the tier fence is IAM and not a prompt |
| [`docs/looker_setup.md`](docs/looker_setup.md) · [`docs/looker_runbook.md`](docs/looker_runbook.md) | Standing up the Looker side |

| Directory | What it holds |
|---|---|
| `src/` | All logic — flat, single-responsibility modules |
| `examples/` | Runners: the sweep, the scorer, isolation and inventory probes |
| `scripts/` | Provisioning, teardown, capture export |
| `results/` | The report, the scores, and the publishable capture |
| `notebooks/` | [provision](notebooks/01_provision.ipynb) · [walkthrough](notebooks/02_walkthrough.ipynb) · [results](notebooks/03_results.ipynb) — narrative only, no business logic |
| `tests/` | pytest; imports flat modules from `src/` by name |

Reasoning that did not fit anywhere is in the module docstrings, which are
written to be read: [`src/cost.py`](src/cost.py) on why cost is reported in three
parts that are never silently summed,
[`src/service_tokens.py`](src/service_tokens.py) on metering the part the API
will not report, and [`src/scoring.py`](src/scoring.py) on the rubric.

```bash
make check    # ruff + mypy + pytest
```

---

Built from the [AI-Native Project Harness](https://github.com/statmike/agent-repo-template).
