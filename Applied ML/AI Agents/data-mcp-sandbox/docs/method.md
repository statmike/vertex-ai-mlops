# How the experiment is run

The protocol. [paths](paths.md) is *what* is compared and [questions](questions.md)
is *what counts as right*; this page is the part in between — how a cell runs, why
they run one at a time, what the capture records, and how 1,440 cells become the
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
| Governance tier | 2 | tier 0 ungoverned, tier 1 governed (5 with `LADDER=1`, below) |
| Replicate | 5 | `battery.DEFAULT_RUNS` |

**1,440 cells**, about 26 hours. `make plan` prints the estimate for whatever
subset you select; `--questions`, `--configs`, `--tiers` and `--runs` cut it down,
and `make smoke` (12 cells) and `make pilot` (288) are the pre-cut rungs.

The published capture covers **all 1,440**, merged from two runs: ten arms on
2026-09-05 and the two direct-API arms on 2026-09-07. `make plan` now prices every
shipped arm off its own measurement — `estimate.PENDING_MEASUREMENT` is empty for
the first time.

### Governance is one switch by default, and six channels on request

Tier 1 turns on everything at once: column descriptions, profile scans, business
rules, a glossary, quality scans, and a LookML semantic layer. That answers *does
governance pay* and cannot answer *which part of it pays* — a question anyone
deciding what to fund asks immediately, since those six cost wildly different
amounts of effort to produce.

`LADDER=1` splits the switch into six channels and interpolates three rungs:

| Rung | Tier | Carries |
|---:|---:|---|
| 0 | `tier0` | nothing — the ungoverned control |
| 1 | `tier2` | + column descriptions |
| 2 | `tier3` | + profile scans |
| 3 | `tier4` | + business rules |
| 4 | `tier1` | + glossary, quality scans, LookML — the published governed tier |

**The tier integer is not the rung position, and that is deliberate.** 1,440
published cells are keyed on `tier0`/`tier1`, so renumbering would silently
re-interpret every one of them; rungs are *appended* as 2, 3, 4 and the two
published tiers keep their meaning. `config.RUNG_ORDER = (0, 2, 3, 4, 1)` states
the reading order once, `config.rung_of()` converts, and the raw integer is never
rendered in a chart or a table — a reader who sees `tier4` next to `tier1` and
infers more governance has been misled by the numbering, not by the data.

Each rung carries everything below it, checked as a strict subset chain by
`validate.ladder_problems()`. That check is not ceremony: the rung table is
joined to the provisioning code by string, and a rung provisioned with the wrong
channels does not raise — it produces a step of zero and reads as *"this
increment of governance does not pay"*, which is a false finding at the end of a
day-long sweep rather than a message before it starts.

Two arms are excluded. Path 2 and `p4_looker_ca` need a Looker semantic model,
LookML arrives as one lump at the top rung, and laddering it means semantic-model
surgery on a shared instance this project is a guest on. Asking for a Looker
model at rungs 1–3 raises rather than quietly returning the tier-1 one, which
would have made rung 1 score like rung 4 and reported that column descriptions
deliver the whole semantic layer.

The ladder is 1,800 cells at n=5 plus a 360-cell rung-0-last control. Not n=3:
the interesting claim is not "the line rises" but "*this* rung is the one that
pays", which is a per-step comparison against the noise floor, and at n=3 most
single-rung steps would have to be published as unresolved.

### Merging two runs without flattening them

A merged capture is not a concatenation. Three things have to survive the join,
and `scripts/merge_captures.py` refuses rather than guesses when they cannot:

* **Provenance.** No single `git_commit` may stand for cells it never produced,
  so the header keeps one entry per run and the report prints all of them.
* **The oracle.** Four of the twelve goldens are trailing windows over data
  anchored at build time, so the right answer moves with the calendar. Between
  the two runs, `active_user_count` went from 2,671 to 2,786 — a 4.3% drift
  against a 0.5% tolerance. Carrying the first run's oracle onto the second would
  have marked correct answers wrong on four questions × two arms × five
  replicates, and it would have looked like the direct API being inaccurate. Each
  run therefore keeps the oracle frozen when *it* ran, and a run that froze none
  is refused rather than scored against today's.
* **Everything that must not differ.** Model, temperature, replicate count, tier
  fence, question set, project, Toolbox version: a disagreement on any of these
  means the two runs measured different things, and the merge fails with the
  field named. `quality_scans` is deliberately not on that list — it changes what
  `lookup_context` returns on Path 3 tier 1 and nothing else, so it moves per-run
  and the report says which arms it is unknown for.

Adding an arm must also not move the published numbers for the other ten. The
judge is a model call, so re-grading settled cells would shift adherence figures
for reasons unrelated to the new arm; `build_results.py --reuse-verdicts` grades
only the cells it has no verdict for. The B.6 merge judged 200 new cells, reused
1,000, and the report diff was purely additive.

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

### One capture per experiment, compared rather than merged

`MUST_AGREE` holds `agent_model` and `tiers`, so a sweep on a different model, or
over a different set of governance rungs, **cannot** be merged into the published
capture. That is not a limitation to work around — those sweeps did not measure
the same thing, and one accuracy number averaged over two different independent
variables is not a result.

So the project produces a **family** of captures, each varying one axis and each
self-describing through its own header — own oracle, own freeze time, own commit:

| File | Varies |
|---|---|
| `results/capture.json.gz` | the published twelve-arm factorial |
| `capture-thinking-fast.json.gz`, `capture-thinking-thinking.json.gz`, `capture-thinking-default.json.gz` | `thinking_mode` on the direct arms |
| `capture-ladder.json.gz` | governance rungs |
| `capture-model-<id>.json.gz` | the client model |

Note the third thinking capture. It re-runs the *published* setting — no
`thinking_mode` at all — in the same window as the other two, and it is not
redundant with the published capture it duplicates. Wall-clock latency is
measured against a shared service, so a baseline taken a day earlier confounds
"this is what the default does" with "the service was differently loaded then".
A capture family compared on latency needs its control inside the window, which
is the same argument the governance ladder's rung-0-last control rests on.

`scripts/compare_captures.py` is how they are read together. A comparison
declares the axes it is allowed to vary; anything else in `MUST_AGREE` that
differs is a **conflict**, and the script prints it and exits non-zero rather
than emitting a delta. It withholds the numbers in that case, and also when the
declared axis turns out to be identical in both files — a table printed under a
warning banner gets quoted as a result with an asterisk.

Two properties worth knowing before reading any cross-capture number:

* **Cells are paired by key, never pooled.** A question, tier or replicate
  present in only one capture is dropped and counted, so comparing an n=3 sweep
  against an n=5 one silently changes no denominator — it pairs three replicates
  and reports the other two as unpaired.
* **Captures that ran different tiers are compared on the tiers they share, or
  not at all.** `tiers` is in `MUST_AGREE`, so the five-tier ladder capture and
  the two-tier published one are refused outright — which would forbid the exact
  comparison the append-don't-renumber scheme was built to permit. `--tier N`
  narrows both sides, and then two things are checked instead of one. `tiers`
  becomes presence: a tier asked for and absent is a refusal, never an empty
  pairing reported as 0.0 drift. `tier_semantics` becomes *declared*
  compatibility — `compare.SEMANTICS_SHARE` says the ladder and the published
  scheme agree on tiers 0 and 1 and nothing else — because that field is what
  makes relaxing `tiers` safe, and waiving both would leave nothing checking that
  `tier1` means the same condition in both files. A vocabulary not on the table
  shares no tiers, so a capture from a fork is refused rather than assumed
  compatible.
* **A field added after a capture was taken is not a difference.** Every new
  entry in `MUST_AGREE` is missing from every capture that predates it. Absent
  and empty therefore collapse to one *unset* value — otherwise adding an axis
  would make the published capture incomparable to the very sweeps measured
  against it.
* **Arm orderings closer than the noise floor are `unresolved`, not ordered.**
  Rank agreement is computed over resolved pairs only; counting the rest as
  agreement would let a comparison in which nothing separated any arm report
  perfect stability.
* **The floor here is the cross-capture one: ~7 points, not 1.** The 1-point A/A
  control in [paths](paths.md) is measured *within* a run, between two arms
  sharing a sweep, an oracle and an hour of the service's weather. Two captures
  share none of that: re-running one configuration unchanged a day later moved
  it 6.7 points. `compare.NOISE_FLOOR` is set from the larger figure, because
  the floor's job is to stop a false finding rather than to describe typical
  drift. This one is measured on the two direct arms at n=5; a comparison
  turning on a delta near the floor should measure its own A/A rather than
  inherit theirs — `make compare-aa` is that, and it is where the 6.7 came
  from. It is the mirror image of a normal comparison: every `MUST_AGREE` field
  identical is the *valid* case, a difference is fatal, and the output is
  labelled a floor with no ranking table, because ranking noise invites reading
  an order into it.

Comparison runs the deterministic scorer only — no judge. The judge is a model
call with ~1.3% verdict wobble, which would let two captures differ because they
were graded twice rather than because they measured different things.

### The oracle is frozen when the sweep starts

Scoring is deferred, but the *right answers* cannot be. The corpus anchors its
timestamps to build time, so four of the twelve goldens are trailing windows
whose correct value moves with the calendar — measured drift is ~2% a day against
a 0.5% tolerance. Resolve them at scoring time and you grade Monday's cells
against Wednesday's answers.

So `battery.run` resolves the whole oracle before it spends a single cell and
writes it into the header with `goldens_frozen_at`. That is the last moment the
answers are knowably true of the run they will grade, and doing it first also
means a BigQuery outage costs seconds at cell 0 rather than a day-long capture
nobody can score. `make export` has nothing left to resolve; it only falls back
to resolving live for captures taken before this existed, and says so when it
does.

A `--resume` keeps the oracle already on the file rather than re-freezing —
otherwise the restart introduces exactly the skew this removes. What it cannot
fix is that the resumed cells really did run later, so a carried oracle more than
a day old prints a warning instead of pretending one number covers both days.

### What the capture header records

Written by `battery.header()` into every results file, because a number with no
record of the conditions that produced it cannot be compared to anything later:

| | |
|---|---|
| `git_commit`, `started` | which code, when |
| `agent_model`, `temperature`, `model_location` | the model under test |
| `toolbox_version` | the pinned MCP Toolbox — its tool inventory changes between releases |
| `use_tier_sa` | whether the IAM tier fence was actually on. The difference between a measured isolation boundary and none |
| `ca_thinking_mode`, `ca_model` | the two settings the direct-API arms can send. `ca_model` is constant — the enum has one selectable value, so there is nothing to choose — and `ca_thinking_mode` is empty for the service default. Both are recorded on every sweep, including ones with no direct arm |
| `runs`, `tiers`, `configs`, `question_ids`, `total_cells` | the subset that ran |
| `tool_schemas` | serialized size of each arm's tool declarations. A *result*, not diagnostics — schemas are re-sent every turn, so their size sets a floor on prompt tokens, and it predicted the observed cost gap almost exactly |
| `quality_scans` | whether this sandbox's Dataplex quality scans existed. `true`/`false`/`null`, where `null` means *did not look* — see [reproducing](reproducing.md#path-3-changed-after-the-published-capture-was-taken) |
| `goldens`, `goldens_frozen_at` | the oracle, resolved when the sweep *started*, and when that was. What lets a reader re-score with no cloud account |

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
