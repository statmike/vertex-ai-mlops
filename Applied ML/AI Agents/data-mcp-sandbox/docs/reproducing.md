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
most worth arguing with, and re-running 1,440 live cells to try a different
metric would be absurd.

```bash
uv sync
uv run python examples/build_results.py \
  --results results/capture.json.gz --out /tmp/mine --no-judge --no-cost
```

That reads the goldens frozen into the capture's header, so it needs no corpus,
no project, and no credentials. Change anything in `src/scoring.py` and re-run;
a rubric change costs a minute.

Those goldens were resolved when each sweep *started* (`goldens_frozen_at` in the
header, per run in a merged capture), which matters because four of them are
trailing windows that move with the calendar — see
[method](method.md#the-oracle-is-frozen-when-the-sweep-starts). The published
capture predates that fix and carries ~24h of skew on those four; every capture
taken since is exact.

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

### What you need to be, before you start

`make bootstrap` creates service accounts, custom roles and project IAM bindings. Those
are administrative operations, and a reader who only has data access will get through
API enablement and corpus generation and *then* fail — after creating billable objects.

**Don't read this table to find out. Run the check:**

```bash
make preflight
```

Two read-only calls, no mutations, nothing created. It asks
`projects.testIamPermissions` for every permission the table below implies and prints
which step you would fail at, plus whether a token actually mints for each tier service
account. `make bootstrap` runs it first and stops if provisioning is blocked.

It fails **only** on a permission that blocks provisioning. A gap in a later step — cost
attribution needs `bigquery.jobs.listAll`, which a data-only reader often lacks — is
reported and does not stop you: it costs a report column, not the experiment.

| Step | What it does that needs privilege | Capability |
|---|---|---|
| `make apis` | enables 9 services (11 with Looker) | `roles/serviceusage.serviceUsageAdmin` |
| `make identities` | creates 2 custom roles | `roles/iam.roleAdmin` |
| `make identities` | creates 2 service accounts, and grants *you* `tokenCreator` on each | `roles/iam.serviceAccountAdmin` |
| `make identities` | binds 5–6 project roles per identity | `roles/resourcemanager.projectIamAdmin` |
| `make setup` | datasets, tables, per-tier dataset ACLs | `roles/bigquery.admin` |
| `make setup` | Dataplex scans, aspects, glossary, entry links | `roles/dataplex.admin` |
| `make smoke` / `pilot` / `sweep` | Gemini calls for the agents and the judge | `roles/aiplatform.user` |
| `make report` | `INFORMATION_SCHEMA.JOBS` for cost attribution | covered by `bigquery.admin` |
| `make service-tokens` | reads Cloud Monitoring | `roles/monitoring.viewer` |
| Path 2 | Looker instance admin, plus LookML developer mode | see [looker_setup.md](looker_setup.md) |

**This list is derived from the operations the code performs, not from a least-privilege
run.** Nobody has stood the sandbox up from exactly these roles and nothing else, so treat
it as the shape of what is needed rather than a verified minimum — if you are `roles/owner`
on a sandbox project, which is the expected case, none of it binds. The reason to read it
anyway is the opposite situation: a shared or org-managed project where you *will* be told
no, and it is much better to find that out before `make bootstrap` starts creating things.

The same caveat applies to `make preflight`: a clean result means *nothing obviously
blocks you*, not that provisioning is proven to succeed. A **failure** is the reliable
half — `testIamPermissions` is authoritative about what you hold, and it rejects a
permission string it does not recognize rather than reporting it as denied, so preflight
cannot invent a denial out of a typo.

Nothing here needs a service account key. The tier fence is impersonation from your own
ADC, which is why `iam.serviceAccountAdmin` appears above and `serviceAccountKeyAdmin`
does not.

### Running it

```bash
cp .env.example .env          # fill in GOOGLE_CLOUD_PROJECT
gcloud auth application-default login
make preflight                # read-only: can you provision this? free
make bootstrap                # APIs, toolbox binary, identities, corpus, governance
make verify-isolation         # prove tier 0 cannot read tier 1 — do not skip this
make plan                     # what a sweep would cost, in time and tokens. Free.
make smoke                    # 12 cells, ~10 min. Proves the wiring end to end.
```

Then walk down the rungs — `make smoke` → `make pilot` (288 cells, ~5h) →
`make sweep` (1,440 cells, ~26h). Each is the same harness at a different size,
so a broken credential shows up on the ten-minute rung.

### Without Looker

Looker is the only component behind an annual-commitment purchase, and
`make bootstrap` deliberately will not create an instance — a setup script must
not be able to start an annual charge. Add `SKIP_LOOKER=1` to any target:

```bash
make bootstrap SKIP_LOOKER=1
make sweep SKIP_LOOKER=1      # 1,080 cells, ~20h
```

Nine of twelve arms remain, covering paths 1, 3 and Conversational Analytics over
BigQuery — as a tool and as a direct API call — at both governance tiers. **The
central result survives**: governed versus ungoverned is still measured on every
remaining path. What you lose is Path 2 — the semantic-layer arm — and the Looker
half of the Path 4 comparison.

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

**Read the `CA calls` column before you believe a zero.** It comes from
`serviceruntime.googleapis.com/api/request_count`, published by the API front-end
rather than by CA, so it is the one number that separates "this arm made no calls"
from "this arm's calls were not counted". On our capture `p4_bq_ca` reads zero
tokens against **306 successful `DataChatService.Chat` calls** — the identical RPC
the Looker arm bills 44.9M tokens for. The adjacent `on our quota` column rules
out the other place that spend could be hiding, by showing Vertex metering our own
agent and nothing more. If you point this at a different project and see the same
shape, the arm is uninstrumented, not cheap.

Two other limits: it needs `roles/monitoring.viewer`, and Monitoring retains these
metrics for six weeks, so a capture older than that can no longer be attributed.
This is why the number lives in a separate command rather than a report column —
it is time-blocked, project-wide, and perishable, and none of those are true of
the per-cell numbers `build_results.py` produces.

### Pointing it at your own data

The corpus (`src/corpus.py`) is synthetic and trap-laden by design — the traps
are the measurement. Swapping in your tables is a real piece of work, not a config
change: seven files describe the experiment and are joined *by name*, so they have
to move together. That is the honest answer.

But you do not have to do it in one jump, and you should not. **[adapting.md](adapting.md)
lays out eight rungs** from "re-score our capture" through "bring your own tables"
to "bring your own Looker" for all twelve arms — each independently runnable, each
with the check that proves you got it right.
`make validate` is the fast loop — offline, free, and run automatically before
`make setup` provisions anything.

### Replicating one axis instead of the whole sweep

The full factorial is a day. A single **axis** is usually not, and it is the
cheaper way to ask a question this sandbox did not already answer — or to check
one of ours against your own environment.

The pattern is three commands. Take a capture with one thing changed, export it
so it carries its own frozen oracle and no project identifiers, then compare:

```bash
make sweep-thinking MODE=THINKING          # 240 cells, ~40m, no local tokens
make export RESULTS=results/raw/thinking-thinking.json \
            OUT=results/capture-thinking-thinking.json.gz
make compare BASE=results/capture.json.gz \
             AGAINST=results/capture-thinking-thinking.json.gz \
             AXIS=ca_thinking_mode
```

Three things make this safe to read, and each of them is a refusal rather than
a convenience:

* **`make export` is not optional.** The published capture is scrubbed, so its
  `project` reads `example-project` while yours reads your real id — and
  `project` is a field the comparison is not allowed to vary. Compare exported
  files with exported files.
* **The comparison names its axis, and only that axis may differ.** Anything
  else in `MUST_AGREE` that disagrees is printed and the command exits non-zero
  with no numbers. So it will refuse if your model, Toolbox version, replicate
  count or tier fence differs from ours — which they may well, and which is
  exactly when a delta would be meaningless.
* **A declared axis that did not actually vary is also a refusal.** Otherwise a
  misconfigured run reports zeros and they read as a null result.

Cells are paired by key and unpaired ones are counted, not pooled, so a smaller
replicate count than ours costs precision rather than correctness. Comparison
runs the deterministic scorer only, never the judge.

**Latency needs its control inside the same window.** Wall clock is measured
against a shared service, so comparing your latency to a capture taken on
another day mixes the effect you are testing with how loaded the service was.
`make sweep-thinking MODE=DEFAULT` exists for this: it re-runs the published
setting alongside your other captures so the baseline is contemporaneous.

**And measure your own noise floor before you believe a small delta.** That
`MODE=DEFAULT` capture has a second job: paired against ours, it varies nothing
at all, which makes it an A/A test.

```bash
make compare-aa BASE=results/capture.json.gz \
                AGAINST=results/capture-thinking-default.json.gz
```

This is the mode where two identical captures are the *valid* input — a
`MUST_AGREE` difference is fatal instead, since an A/A that varied something
publishes an effect under the name of noise and suppresses real findings
everywhere downstream. It reports the largest drift it saw, compares that to the
floor `compare` currently applies, and tells you to raise it if yours is worse.
It prints no ranking table; ranking noise invites reading an order into it.

Our floor is **6.7 points**, and it is the number that decides whether any
cross-capture delta on this page is `resolved`. Do not inherit it blindly. It
was measured on two direct-API arms a day apart at n=5, and an arm that runs a
local model, a shorter interval, or a different replicate count will not have
the same one.

The floor is also not one number across tiers. Restricting the same A/A shows
tier 0 drifting 6.7 points and tier 1 drifting 5.0 — the ungoverned condition
moves most, which is what you would expect when accuracy sits near 25% and every
arm is guessing more:

```bash
make compare-aa BASE=results/capture.json.gz \
                AGAINST=results/capture-thinking-default.json.gz TIER=0
```

### Running the governance ladder

The published experiment has two tiers, ungoverned and fully governed, and so it
can say whether governance pays but not which part of it does. `LADDER=1` splits
governance into six channels over five rungs — see
[method](method.md#governance-is-one-switch-by-default-and-six-channels-on-request)
for the rung table and why the tier integers are not the rung positions.

It has to be set consistently, because it changes what gets built as well as what
gets measured: three more datasets, three more service accounts, more Dataplex
scans.

```bash
LADDER=1 make identities        # privileged, one-time
LADDER=1 make setup
LADDER=1 make plan              # read the number before spending a day on it
LADDER=1 make sweep-ladder      # 1,800 cells
LADDER=1 make sweep-ladder-control   # 360 cells: rung 0 again, LAST
```

The control is not optional and not a formality. Five rungs run in sequence over
a day, so the highest rung is measured many hours after the lowest, and *elapsed
time is confounded with governance* — a rising line is what both a real effect
and a drifting service produce. Re-running rung 0 at the end and differencing it
against the ladder's own rung 0 separates them, and nothing else in the design
can.

It costs 360 cells but **eight hours, not the four** a sixth of the ladder
suggests. Rung 0 is the *expensive* condition: ungoverned, the agent explores,
and `p3_managed` spends 207k tokens at tier 0 against 34k at tier 1. Budget the
control off its own measured rate.

Reading the ladder against the published capture needs `TIER`, because the two
files declare different tier sets and `tiers` is a field a comparison may not
vary:

```bash
make export RESULTS=results/raw/ladder.json OUT=results/capture-ladder.json.gz
make compare-aa BASE=results/capture.json.gz \
                AGAINST=results/capture-ladder.json.gz TIER="0 1"
```

That is the ladder's replication check: its rungs 0 and 4 are the published tiers
0 and 1, re-run, so agreement within the floor says the ladder measured the same
thing the published capture did before you read anything into the rungs between.
Tiers 2, 3 and 4 exist in only one of the two files and asking for them is
refused rather than paired against nothing.

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
  its model spend is reported as `floor` coverage — unmeasured, never zero. For
  `p4_looker_ca` Cloud Monitoring recovers it. For `p4_bq_ca` no meter in this
  project does, and that is measured rather than assumed: the calls are visible on
  the request meter, their cost is on neither the CA meter nor Vertex's.
- **Estimates in `make plan`** come from medians measured on our corpus in
  September 2026. They are an order of magnitude, not a quote, and they exclude
  quota backoff entirely.

### Path 3 changed after the published capture was taken

⚠️ **The shipped `results/capture.json.gz` predates this sandbox's Dataplex
data-quality scans, and `make setup` now creates them.** So a fresh run is *not*
comparable to the published Path 3 numbers, for a knowable reason rather than
noise.

| | |
|---|---|
| Published sweep started | 2026-09-05 02:07 UTC, at commit `834421c3` |
| Quality scans added and run | 2026-09-05 15:59 UTC, commit `e13a98c9` |

**What moves is `lookup_context`, and none of the quality tools.** That is the
opposite of the obvious guess, so it is worth being precise about, because the
guess picks the wrong arms.

Every Dataplex scan tool is **permanently denied to the tier service accounts**,
before and after provisioning. `mcpSandboxCatalogSearch` grants entry and aspect
reads and no `dataplex.datascans.*` at all, so `search_dq_scans` fails at
`locations/-/dataScans` — a project-wide list, refused before a single scan is
enumerated. Creating scans cannot change that answer. Measured across the
capture, on `p3_toolbox`:

| Tool | Calls | Errors | Denied permission |
|---|---:|---:|---|
| `search_dq_scans` | 59 | **59** | `dataplex.datascans.list` |
| `list_data_products` | 33 | **33** | `dataplex.dataProducts.list` |
| `get_data_profile` | 1 | **1** | `dataplex.datascans.getData` |
| `get_data_quality_results` | 0 | – | never called |

93 calls, zero successes. Re-probed live after provisioning: still denied,
identically. So the tool everyone would name is not the mechanism.

The mechanism is a **field**. `lookup_context` renders a `qualityStatus` line per
table, and it appears **0 times in all 12,555 tool calls** of the published
capture and on every tier-1 table today:

```
qualityStatus: FAIL
```

Quality scans are governed-tier only (`GOVERNED_TIERS` in `src/catalog_setup.py`),
so tier 0's payload is unchanged and only the **treatment** moved.

Concretely:

- **Do not merge** tier-1 Path 3 cells from the published capture with cells from
  a fresh setup. Re-run Path 3 whole, or leave it whole.
- It is **all three** Path 3 arms, not just the Toolbox one. `lookup_context` was
  called 93 times on `p3_managed`, 80 on `p3_matched`, 58 on `p3_toolbox` — and
  it is one of only three tools the managed catalog server exposes at all.
- **Tier 0 is unaffected**, on every arm. The comparison that moved is the
  governed one.
- Paths 1, 2 and 4 are unaffected — none of them call `lookup_context`.
- Captures from now on record `quality_scans: true | false | null` in the header
  and `make report` prints it, so this is self-describing rather than something
  you have to date against a commit. `null` means "did not look", which is not
  the same as "absent".
- To match the published environment exactly, provision normally and then drop
  just the quality scans — `catalog_setup.delete_quality_scans()`. Note that
  `scripts/setup.py --skip-scans` will *not* do it: that skips profile scans too,
  and the published capture had those.

A reader re-running this in six months should expect different numbers. If the
*ordering* of the arms changes, that is the interesting finding, and it is the
one this harness exists to keep measurable.
