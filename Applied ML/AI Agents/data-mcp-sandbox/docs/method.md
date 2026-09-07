# How the experiment is run

The protocol. [paths](paths.md) is *what* is compared and [questions](questions.md)
is *what counts as right*; this page is the part in between — how a cell runs, why
they run one at a time, what the capture records, and how 1,200 cells become the
handful of numbers in `results/report.md`.

---

## One cell

A **cell** is one agent, answering one question, once.

```
cell_key = "governed-q1|p3_toolbox|tier1|run3"
             question    arm         tier   replicate
```

Each cell gets its own runner and its own MCP client connections, torn down
afterwards. Nothing is shared between cells except the warehouse itself, so a cell
cannot inherit context — or a token count — from the one before it.

## The factorial

| Factor | Levels | |
|---|---|---|
| Arm | 12 | `src/mcp_clients.py` `CONFIGS` |
| Question | 12 | `examples/questions.json` |
| Governance tier | 2 | tier 0 ungoverned, tier 1 governed |
| Replicate | 5 | `battery.DEFAULT_RUNS` |

**1,440 cells**, about 26 hours. `make plan` prints the estimate for whatever
subset you select; `--questions`, `--configs`, `--tiers` and `--runs` cut it down,
and `make smoke` (12 cells) and `make pilot` (288) are the pre-cut rungs.

The published capture covers **1,200 of those cells over ten arms**. The two
direct-API arms (`p4_bq_direct`, `p4_bq_direct_ctx`) were added after the sweep
and have not been run; `make plan` prices them at the worst arm it has actually
observed and says so on the line, rather than assuming they behave like
`p4_bq_ca`.

Cells are enumerated **config-major** — arm, then tier, then question, then
replicate. An interrupted sweep therefore leaves *whole arms* finished rather than
a thin slice of every one, so a partial capture is still comparable across the
arms it covers.

## Five replicates, because temperature 0 is not determinism

`gemini-3.7-flash` is a reasoning model. At `temperature=0` it still varies: re-judging
one capture moved 13 of 1,000 verdicts. Replicates are what turn that into a
visible interval instead of an invisible error bar — every per-arm table reports
an IQR alongside its median, and an IQR wider than the gap you are reading is the
signal to stop reading.

## Strictly sequential, and several things depend on it

Cells run one at a time. Never in parallel, and this is not a throughput oversight:

- **Token accounting.** `src/usage.py` is a process-local accumulator reset per
  cell. Two concurrent cells would bill each other's tokens.
- **BigQuery cost attribution.** `src/cost.py` maps jobs to cells by *time window*
  over `INFORMATION_SCHEMA.JOBS`. Overlapping cells make the mapping ambiguous.
- **Conversational Analytics server-side tokens.** `make service-tokens` reads a
  Cloud Monitoring metric labelled by model and status with no caller dimension,
  so time blocks are the only attribution available at all.
- **Latency.** Contention for a shared quota pool would land in the numbers as if
  it were an architectural property of the arm.

The price is wall clock: a full sweep is a day, and that is the trade being made.

## Resume is self-healing

Every cell has a stable key, and `--resume` skips only cells that *succeeded*.
Error cells re-run. So a sweep interrupted by a quota storm can be restarted
without hand-editing anything, and without silently keeping the failures.

## Capture now, score later

`run_battery.py` writes raw outputs and **performs no scoring**. Every score in
`results/report.md` is computed afterwards by `build_results.py` from the capture.

That split is why the rubric is arguable: changing `src/scoring.py` and re-running
the scorer costs a minute, where re-running the sweep costs a day and a live cloud
project. It is also why `results/capture.json.gz` ships — see
[reproducing](reproducing.md#1-re-scoring-our-capture-no-cloud-account).

### What the capture header records

Written by `battery.header()` into every results file, because a number with no
record of the conditions that produced it cannot be compared to anything later:

| | |
|---|---|
| `git_commit`, `started` | which code, when |
| `agent_model`, `temperature`, `model_location` | the model under test |
| `toolbox_version` | the pinned MCP Toolbox — its tool inventory changes between releases |
| `use_tier_sa` | whether the IAM tier fence was actually on. The difference between a measured isolation boundary and none |
| `runs`, `tiers`, `configs`, `question_ids`, `total_cells` | the subset that ran |
| `tool_schemas` | serialized size of each arm's tool declarations. A *result*, not diagnostics — schemas are re-sent every turn, so their size sets a floor on prompt tokens, and it predicted the observed cost gap almost exactly |
| `quality_scans` | whether this sandbox's Dataplex quality scans existed. `true`/`false`/`null`, where `null` means *did not look* — see [reproducing](reproducing.md#path-3-changed-after-the-published-capture-was-taken) |
| `goldens` | frozen by `make export` only. What lets a reader re-score with no cloud account |

---

## Aggregation

**Median + IQR** in the per-arm tables. **Means** in the headline.

Both, because either alone misleads here. On the easy categories medians saturate
at 1.0 and hide the tail, so a median-only headline would report several arms as
tied and perfect. Means keep the tail visible; the IQR is what stops a mean being
read as a point estimate.

**Error cells and empty answers count as failures, never dropped.** An arm that
crashes on a question has not opted out of it. Dropping those cells would rank an
unreliable arm above a reliable one that merely answered wrongly, which is the
opposite of the truth. `report.capture_health` prints how many there were per arm,
so an uneven failure rate — which means the factorial is no longer clean — is
visible rather than buried in a denominator.

The one exception is **latency**, where cells that hit a quota retry are excluded
and the count of exclusions is printed beside the number. A 429 backoff measures
the shared quota pool, not the arm.

## Unmeasured is never zero

The rule that outranks the others: a metric an arm was not eligible for prints
`--`, not `0.0`. Ranking an arm bottom on something it could never have scored is
a false finding rather than a conservative one.

It cuts the other way too. A direct-API arm never calls a model in this process,
so its token count is a truthful `0` — and printing it would sort the arm to the
top of every "cheapest" list while its whole model bill sits on a meter this
report cannot read. Those columns print `--` and the coverage column reads
**service only**, decided from the capture's own `model_calls` rather than from a
list of arm names. A capture that predates that field records `None`, which means
*not recorded* and keeps its numbers. See
[Unmeasured is not zero](questions.md#unmeasured-is-not-zero) for the cases and
[Reading Path 4's numbers fairly](paths.md#reading-path-4s-numbers-fairly) for the
arm it bites hardest.
