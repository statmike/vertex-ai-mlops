# data-mcp-sandbox

**Does data governance actually make an AI agent more accurate — and what does
each way of connecting one to BigQuery cost?**

This is a controlled experiment, not a demo. The same model asks the same twelve
questions against the same data through **ten different MCP tool surfaces**, at
**two governance tiers** over byte-identical corpora, five times each. 1,200 live
cells. Every answer is scored against a live oracle.

The corpus is built to be hostile in the ways real warehouses are hostile:
columns named `txn_amt_x2` that are gross-not-net, a `status_flg` boolean whose
`TRUE` means refunded, an `is_active` flag that disagrees with the governed
definition of "active", and a `revenue_amount` column that is wrong. An agent
that reads the schema and writes the obvious SQL gets a confident wrong answer.

---

## The headline

| Question | Answer |
|---|---|
| Does governance help? | **Yes, and it is the largest effect measured.** Accuracy roughly doubles from tier 0 to tier 1 on every path — 30%→75% on `p1_toolbox`, 13%→57% on `p4_looker_ca`. |
| Is it enough? | **No.** At tier 1 the governed rule reaches the agent 100% of the time, and it still gets the answer wrong on 30–40% of those cells. Acquiring a rule and applying it are different problems. |
| Managed or self-hosted MCP? | **Behaviourally the same, 27× apart on cost.** They reach the same verdict on 93–98% of paired cells while sharing a tool-call sequence 0–7% of the time. |
| Where does the cost come from? | **Tool schema verbosity, not tool count.** One managed `get_table_info` declaration is 78,197 chars — 65% of its arm's prompt floor, and 120× the self-hosted equivalent that does the same job. |

Full tables: [`results/report.md`](results/report.md). How the arms differ:
[`docs/paths.md`](docs/paths.md).

> **These numbers are perishable.** They are specific to a pinned model version,
> a pinned MCP Toolbox, and vendor tool schemas that can change without notice —
> and that last one dominates the cost result. See
> [`docs/reproducing.md`](docs/reproducing.md) for what will and will not
> reproduce.

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
make bootstrap        # APIs, Toolbox binary, tier identities, corpus, governance
make verify-isolation # prove tier 0 cannot read tier 1 — do not skip this
make plan             # what a sweep would cost, in time and tokens. Free.
make smoke            # 10 cells, ~10 min. Proves the wiring end to end.
```

`make help` lists everything.

### Without Looker

Looker is the only component behind an annual-commitment purchase, and
`make bootstrap` deliberately **will not create an instance** — a setup script
must not be able to start an annual charge. Add `SKIP_LOOKER=1` to any target:

```bash
make bootstrap SKIP_LOOKER=1
make sweep SKIP_LOOKER=1     # 840 cells instead of 1,200
```

Seven of ten arms remain, at both governance tiers. The central governed-vs-
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

---

## How it works

**Four paths × two server flavours, plus two matched arms and two managed
agents.** Path 1 is raw BigQuery. Path 2 routes through a Looker semantic layer.
Path 3 adds the Knowledge Catalog. Path 4 hands the whole question to
Conversational Analytics. Each of paths 1–3 runs both a Google-managed MCP
endpoint and a self-hosted MCP Toolbox. Details in [`docs/paths.md`](docs/paths.md).

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
model call per governed cell).

**Unmeasured is never reported as zero.** Path 4 discloses no query, so evidence
recall and rule acquisition are *unmeasurable* on those arms — the report prints
`--`. Conversational Analytics spends model tokens server-side that it does not
report, so its cost is published as a floor. Ranking an arm bottom on a metric it
was never eligible for is a false finding, not a conservative one.

---

## Layout

| Path | What it holds |
|------|---------------|
| `src/` | All logic — flat, single-responsibility modules |
| `examples/` | Runners: the sweep, the scorer, isolation and inventory probes |
| `scripts/` | Provisioning, teardown, capture export |
| `docs/` | [paths](docs/paths.md) · [reproducing](docs/reproducing.md) · [scoping](docs/scoping.md) · [Looker setup](docs/looker_setup.md) |
| `results/` | The report, the scores, and the publishable capture |
| `tests/` | pytest; imports flat modules from `src/` by name |
| `notebooks/` | [provision](notebooks/01_provision.ipynb) · [walkthrough](notebooks/02_walkthrough.ipynb) · [results](notebooks/03_results.ipynb) — narrative and execution only, no business logic |

Design rationale is in [`DESIGN.md`](DESIGN.md); engineering decisions and the
things that went wrong are in [`DEV_NOTES.md`](DEV_NOTES.md).

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
