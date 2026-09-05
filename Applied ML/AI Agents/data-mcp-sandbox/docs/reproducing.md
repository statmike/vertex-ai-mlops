# Reproducing this on your own BigQuery and Looker

Two different things you might want, which need very different amounts of work:

| You want to… | You need | Cost |
|---|---|---|
| **Check our arithmetic** — re-run the rubric over our capture, change it, disagree with it | Python and this repo. No cloud account. | free |
| **Re-run the experiment** — point the harness at your data, your governance, your rates | A GCP project. Looker optional. | ~$ and ~26h for a full sweep |

---

## 1. Re-scoring our capture (no cloud account)

`results/capture.json.gz` is the raw sweep: every question, every tool call with
its arguments and result, every answer, every token count. It carries **no
scores** — that split is deliberate, because the rubric is the part
most worth arguing with, and re-running 1,200 live cells to try a different
metric would be absurd.

```bash
uv sync
uv run python examples/build_results.py \
  --results results/capture.json.gz --out /tmp/mine --no-judge --no-cost
```

That reads the goldens frozen into the capture's header, so it needs no corpus,
no project, and no credentials. Change anything in `src/scoring.py` and re-run;
a rubric change costs a minute.

Read [questions.md](questions.md) first — it lays out the four traps, the twelve
questions, how a number becomes `correct` or `sprang_trap`, and the judge's
measured 1.3% verdict wobble, which is the floor on reading anything into a
small adherence difference.

Two passes stay off without cloud access. `--no-judge` skips the semantic
adherence grade (one Gemini call per governed cell). `--no-cost` skips BigQuery
job attribution, which reads `INFORMATION_SCHEMA` in *our* project and cannot be
reproduced anywhere else — the published capture is the only record of it.

The capture is scrubbed: project id, project number, and Looker host are replaced
with placeholders. `scripts/export_capture.py --check` re-reads a written file and
fails if any original identifier survived, so that claim is verified rather than
asserted.

---

## 2. Re-running it on your project

```bash
cp .env.example .env          # fill in GOOGLE_CLOUD_PROJECT
gcloud auth application-default login
make bootstrap                # APIs, toolbox binary, identities, corpus, governance
make verify-isolation         # prove tier 0 cannot read tier 1 — do not skip this
make plan                     # what a sweep would cost, in time and tokens. Free.
make smoke                    # 10 cells, ~10 min. Proves the wiring end to end.
```

Then walk down the rungs — `make smoke` → `make pilot` (240 cells, ~5h) →
`make sweep` (1,200 cells, ~26h). Each is the same harness at a different size,
so a broken credential shows up on the ten-minute rung.

### Without Looker

Looker is the only component behind an annual-commitment purchase, and
`make bootstrap` deliberately will not create an instance — a setup script must
not be able to start an annual charge. Add `SKIP_LOOKER=1` to any target:

```bash
make bootstrap SKIP_LOOKER=1
make sweep SKIP_LOOKER=1      # 840 cells, ~17h
```

Seven of ten arms remain, covering paths 1, 3 and Conversational Analytics over
BigQuery, at both governance tiers. **The central result survives**: governed
versus ungoverned is still measured on every remaining path. What you lose is
Path 2 — the semantic-layer arm — and the Looker half of the Path 4 comparison.

### Cost is reported in units, not dollars

The headline table is **tokens in, tokens out, seconds, BigQuery jobs, and MiB
scanned** — per correct answer, because an arm that is cheap and wrong is not
cheap. Those five are things you can check against your own invoice. A dollar
figure is not: it needs a rate card, and rates differ by region, edition and
committed-use discount, so it is the one number in this report guaranteed to be
wrong for most readers.

Input and output are separate columns because they neither cost nor behave alike.
Output bills several times higher than input everywhere, and it is the column that
moves when an arm starts reasoning rather than retrieving. Summed, the two hide
each other — and the split is what makes the headline cost result legible:
`p1_managed` at tier 0 spends 1,673,836 input tokens per correct answer against
5,487 output. Almost none of that is the model thinking. It is tool schemas,
re-sent every turn.

If you do want money, `cp prices.example.json prices.json` and fill it in. Nothing
is pre-filled. Leave it absent and every table still reports units; a `--` in the
USD column means *unpriced*, never free.

### Metering what the API does not report

`make report` publishes Path 4 as a `floor`, because Conversational Analytics
returns no usage. Recover the missing half separately:

```bash
uv run python examples/service_tokens.py --baseline 2026-08-25 2026-09-01  # first
make service-tokens                                                        # then
```

**Run the baseline first, and on your own quiet week.** The Monitoring metric is
labelled by `model_name` and `status` only — there is no caller dimension — so
attribution is by time window and will absorb any other Conversational Analytics
workload in the same project. Our baseline returns exactly zero, which is what
makes our numbers publishable; a busy shared project may have no clean window at
all, and in that case the honest output is the floor.

Two other limits: it needs `roles/monitoring.viewer`, and Monitoring retains these
metrics for six weeks, so a capture older than that can no longer be attributed.
This is why the number lives in a separate command rather than a report column —
it is time-blocked, project-wide, and perishable, and none of those are true of
the per-cell numbers `build_results.py` produces.

### Pointing it at your own data

The corpus (`src/corpus.py`) is synthetic and trap-laden by design — the traps
are the measurement. Swapping in your tables means rewriting `corpus.py`,
`golden.py` (the oracle), and `questions.json` together, because a question is
only scoreable against a golden that a query can compute. That is a real piece of
work, not a config change, and it is the honest answer.

---

## What will not reproduce, and why

**The numbers will differ. Some of them a lot.** Do not treat the tables in
`results/report.md` as constants.

- **Model version.** Results are specific to `gemini-3.7-flash` at temperature 0.
  Temperature 0 is not determinism — replicate variance is visible in the IQR
  columns, which is why the design runs five replicates rather than one.
- **Managed tool schemas are a vendor detail that can change without notice**,
  and they dominate the cost result. Tool declarations are re-sent every turn, so
  their serialized size sets a floor on prompt tokens; one endpoint's
  `get_table_info` alone accounted for 65% of an arm's surface. That single
  detail is worth up to 12× between two arms that behave near-identically, and
  the size of the gap tracks the schema sizes rather than the word "managed" —
  Path 2's managed endpoint is not bloated, and Path 2 shows no cost gap. The
  header of every capture records the measured schema sizes for exactly this
  reason.
- **MCP Toolbox is pinned to a version** (see `scripts/install_toolbox.py`). Its
  prebuilt tool inventories change between releases.
- **Dynamic shared quota.** `gemini-3.7-flash` has no per-project bucket, so 429s
  are contention with everyone else on the pool. This inflates wall clock
  unpredictably; latency is only compared across cells that never retried, and
  the report says how many were excluded.
- **Conversational Analytics spends model tokens we cannot see.** It runs its own
  Gemini calls server-side and does not report them. Its warehouse spend *is*
  attributable (the BigQuery jobs run under our identity, verified per cell), but
  its model spend is reported as `floor` coverage — unmeasured, never zero.
- **Estimates in `make plan`** come from medians measured on our corpus in
  September 2026. They are an order of magnitude, not a quote, and they exclude
  quota backoff entirely.

A reader re-running this in six months should expect different numbers. If the
*ordering* of the arms changes, that is the interesting finding, and it is the
one this harness exists to keep measurable.
