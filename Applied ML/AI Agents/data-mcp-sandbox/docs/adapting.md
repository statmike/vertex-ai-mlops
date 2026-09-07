# Adapting the sandbox to your own environment

Run the experiment exactly as published, then move it toward your warehouse one
step at a time. Each rung below is independently runnable and independently
useful — you can stop at any of them and still have a result.

The order is deliberate: every rung costs more and touches more code than the one
above it, and each one puts a *check* between you and the next. The expensive
mistake in this project is not a crash, it is a sweep that runs to completion and
scores something other than what you meant. Most of these checks exist to catch
exactly that.

```
0  Read our result          no cloud account          minutes
1  Run it unchanged         your project, our data    ~10 min → ~26 h
2  Retune the knobs         .env only                 no code
3  Ask your own questions   questions.json            offline check
4  Add your own metric      + golden.py
5  Write your governance    + corpus.py               the T1 text
6  Bring your own tables    + 4 more modules          9 BigQuery arms
7  Bring your own Looker    + lookml.py + a runbook   all 12 arms
```

Rungs 1–6 run **nine of the twelve arms** — both governance tiers, all three
BigQuery paths, and the BigQuery half of Path 4. That is enough for the central
T1-vs-T0 result. Rung 7 adds the semantic-layer path, and it is the only rung
that needs a product you may not already own.

After **every** edit from rung 3 onward:

```bash
make validate     # offline, free, no credentials
```

It cross-checks `corpus.py`, `golden.py`, `questions.json`, `scoring.py` and
`lookml.py`, which are joined *by name* and by nothing a type checker can see.
`make setup` runs it first and refuses to provision an incoherent set. Add
`SKIP_LOOKER=1` to drop the Path 2 checks. See
[why that matters](#why-the-check-exists) below.

---

## Rung 0 — Read our result

No account, no credentials, no spend.

```bash
uv sync
uv run python examples/build_results.py \
  --results results/capture.json.gz --out /tmp/mine --no-judge --no-cost
```

Or open [`03_results.ipynb`](../notebooks/03_results.ipynb), which ships with its
outputs. Full detail in [reproducing.md](reproducing.md#1-re-scoring-our-capture-no-cloud-account).

**Change the rubric here first.** `src/scoring.py` is the part most worth arguing
with, and disagreeing with it costs a minute rather than a sweep.

Changing only the report's *wording* is cheaper still — `--from-scores` rebuilds
`report.md` from a previous run's `scores.json`, with no judge calls and no
BigQuery, so the diff is your edit and nothing else:

```bash
uv run python examples/build_results.py \
  --results results/capture.json.gz --from-scores results/scores.json --out results
```

## Rung 1 — Run it unchanged

Your project, our corpus, our questions. This is the rung that proves your
environment works before any of your own thinking is mixed in.

```bash
make preflight   # free, read-only: can you provision this at all?
make bootstrap && make verify-isolation && make plan && make smoke
```

`make preflight` answers [what you need to be able to
do](reproducing.md#what-you-need-to-be-before-you-start) against your actual project
rather than making you read a table. `make bootstrap` creates service accounts and IAM
bindings, and finding out you cannot halfway through is the annoying way to learn it.

Walk the rungs: `make smoke` (12 cells, ~10 min) → `make pilot` (288, ~5 h) →
`make sweep` (1,440, ~26 h).

**No Looker instance?** Add `SKIP_LOOKER=1` to any target — 9 arms, 1,080 cells,
~20 h. Looker is the one component behind an annual-commitment purchase, so no
script here creates an instance. What you give up is Path 2 entirely (the
semantic-layer arms `p2_managed`, `p2_toolbox`, and `p4_looker_ca`); what you keep
is both tiers on every BigQuery path, which is where the largest measured effect
lives. Rung 7 is how you add it back.

**Expect different numbers than ours**, and read
[what will not reproduce](reproducing.md#what-will-not-reproduce-and-why) before
concluding anything from the difference. Vendor tool schemas move, and they
dominate the cost result.

## Rung 2 — Retune the knobs

No code. Everything here is `.env`, read by `src/config.py`:

| Knob | What moves |
|---|---|
| `AGENT_MODEL`, `JUDGE_MODEL` | the model under test, and the grader |
| `MODEL_LOCATION` | region for every model call |
| `BQ_LOCATION`, `DATAPLEX_LOCATION` | where data and scans live |
| `RESOURCE_PREFIX` | dataset and scan names — change it to run a second sandbox alongside the first |
| `USE_TIER_SA` | the IAM tier fence. Off means **no fence at all**, not a softer one |
| `LOOKER_*` | instance, models, connections for Path 2 |

Changing the agent model is the single most interesting free experiment here: the
whole sweep holds one model constant so it measures *architecture*, and varying it
tests whether the path ranking is model-dependent at all.

`USE_TIER_SA=false` deserves its own warning. It does not weaken isolation, it
removes it — catalog search is project-wide and content-addressed, so a tier-0
agent will be handed tier-1 governed entries and answer from them. `make
verify-isolation` is what tells a real fence from an assumed one.

## Rung 3 — Ask your own questions

Edit [`examples/questions.json`](../examples/questions.json). Our tables, our
oracle, your questions. Each entry:

```json
{
  "id": "direct-q1",
  "category": "direct",
  "question": "How many registered users are there?",
  "golden_key": "total_users",
  "evidence": { "must_have": ["users"], "nice_to_have": ["user_id"], "distractor": [] }
}
```

- `golden_key` must name an entry in `golden.GOLDENS`, or be `""` for a question
  with no numeric answer.
- `evidence` terms must be real table or column names — they are matched against
  the SQL the agent wrote, to measure whether it looked at the right things.
  `distractor` is how you score an agent for reaching at a decoy.

Then `make validate && make smoke`. There is no hardcoded question count anywhere;
adding or removing entries is expected.

**Phrase windows as trailing N days, never "last month".** The oracle recomputes
live and cannot score an answer the question did not pin down.

## Rung 4 — Add your own metric

A new question needs a new oracle entry unless it reuses one. Add a `Golden` to
`src/golden.py`:

```python
Golden(
    key="net_revenue_by_channel",
    description="Net revenue for the top channel, refunds excluded.",
    sql=lambda t: f"SELECT ... FROM {_txn(t)} WHERE NOT status_flg ...",
    trap_sql=lambda t: f"SELECT ... FROM {_txn(t)} ...",   # optional
    trap_name="included refunded transactions",
)
```

`sql` takes a tier and returns SQL producing one column named `v`. Both tiers hold
byte-identical data, so a golden must return the same number for each — `make
setup` asserts that and fails loudly if not, because a divergence means the tiers
are no longer a clean control.

`trap_sql` is the interesting half. It encodes *the wrong answer worth naming* —
the number a reasonable agent produces when it misses the governance. Supplying it
turns an undifferentiated wrong answer into a diagnosed one ("sprang the trap"),
which is what makes the results legible rather than just low.

Never cache a golden value. The generator anchors timestamps to build time, so a
stored number rots — we watched the active-user count drift 2,671 → 2,768 → 2,804
across four days, which is exactly why the oracle recomputes.

## Rung 5 — Write your own governance

This is where the experiment starts being about *your* organisation, and it is the
best value-for-effort rung in the list.

Tier 1 governance is generated from `src/corpus.py`:

- `Column.description` — published to BigQuery and the catalog at tier 1 only
- `GUIDELINES` — the business rules attached as catalog aspects, which is what
  actually reaches the model through `lookup_context`
- `GLOSSARY_TERMS` — real glossary entries, console fidelity only

Replace `NET_REVENUE_RULE` and `ACTIVE_USER_RULE` with your organisation's actual
definitions and re-run `make setup`. Tier 0 is stripped of all of it and is
unaffected, so the T1−T0 contrast now measures **whether your governance text
works** — which is a question about your writing, not about MCP.

Two things to keep if you want the results to stay comparable to ours:

- Rules must name the columns they govern. `test_guidelines_name_the_columns_they_govern`
  enforces it, because a rule that never names `txn_amt_x2` cannot be shown to have
  been acquired.
- If you reword a description, check `scoring.GOVERNANCE_MARKERS`. Acquisition is
  measured by looking for those phrases; a reword without updating them silently
  zeroes it. A test pins them to the corpus text, so you will be told.

## Rung 6 — Bring your own tables

The real project. Be honest with yourself about the size of it: this is not a
config change, and it touches seven files — not the three
[reproducing.md](reproducing.md#pointing-it-at-your-own-data) used to name.

**What is already generic.** Dataset creation, the tier copy, description
apply/strip, catalog aspects, glossary links and profile scans all iterate
`corpus.CORPUS`. Describe your tables there and that machinery follows you for
free.

**What is corpus-specific and must be rewritten:**

| File | What it holds | Needed for |
|---|---|---|
| `src/corpus.py` | table + column declarations, guidelines, glossary | everything |
| `src/golden.py` | the oracle SQL and the trap SQL | scoring |
| `examples/questions.json` | the questions | the battery |
| `src/bq_setup.py` | `_users_sql`, `_events_sql`, `_transactions_sql` | **only if you generate data** |
| `src/scoring.py` | `RULE_TRIGGERS`, `GOVERNANCE_MARKERS` | acquisition scoring |
| `src/catalog_setup.py` | the `DataQualityRule` set | Path 3's quality scans |
| `src/lookml.py` | views, keys, measures, the Explore | **Path 2 — see rung 7** |

**You probably do not need the generator.** Those three functions in `bq_setup.py`
exist to build a synthetic trap corpus. If you already have tables, replace
`generate_source_tier` with a copy or a `CREATE TABLE ... AS SELECT` into the
tier-0 dataset; `copy_to_other_tiers` and everything downstream is already generic.
Point it at a snapshot, not at live production tables — the tiers must hold
byte-identical data or the control is contaminated, and a table that changes under
the sweep breaks that.

**Keep the traps, or know what you gave up.** The four traps are the measurement,
not decoration: a misleading column name, an inverted boolean, a flag that
contradicts the governed definition, and nulls plus outliers. A corpus without
something like them will show every arm scoring well at both tiers, and the
governance effect — the largest one this project measured — will vanish. If your
real warehouse has its own traps, use those; they are better than ours because
they are real. If it genuinely has none, you are measuring something else, which
is fine as long as you say so.

`make validate` catches the name-level mistakes. It cannot tell you your oracle is
wrong — for that, `make golden` prints every value live and `make setup` cross-checks
the tiers.

## Rung 7 — Bring your own Looker

This is the only rung with a manual, click-through component, and the only one
gated on a product you may not own. Budget a couple of hours the first time.
[`docs/looker_runbook.md`](looker_runbook.md) is the step-by-step; this is what it
adds up to.

**The instance is never automated.** No script in this repo creates one — that is
an annual commitment, and a setup script should not be able to start a charge.
Bring your own, or an existing one you already have.

**Two BigQuery connections, one per tier.** Not one shared connection. A Looker
connection authenticates *as itself*, not as the calling user, so a single shared
connection would make Path 2 the only arm whose tier boundary is not an IAM
boundary — the arm would still run, still answer, and quietly stop being a
control. Each connection is ADC + `impersonated_service_account` =
`config.tier_service_account(tier)`, which keeps it keyless. See
[`docs/looker_setup.md`](looker_setup.md#2-bigquery-connections--one-per-tier-and-that-is-the-point).

**One genuine secret.** The Looker API has no ADC equivalent, so API3
credentials live in `looker.ini` — gitignored, `0600`, project-local. It is the
single exception to this project's no-keys rule, and the runbook explains why.

**Then the LookML.** `make lookml` generates every file from `corpus.CORPUS`, and
most of it follows your tables for free: one view per table, one dimension per
column, descriptions and measures at tier 1 only, tier 0 stripped. What does *not*
follow your tables, and must be edited in `src/lookml.py`:

| What | Why it is hand-maintained |
|---|---|
| `VIEW_NAMES` | views are named for the *concept*, not the physical table — that is the point of a semantic layer, and it keeps the T1 naming trap out of the field names |
| `PRIMARY_KEYS` | Looker needs a declared key for symmetric aggregates. Without one a summed measure **fans out across the join and silently inflates** |
| `LOOKER_TYPES` / `TIME_TYPES` | only `STRING`, `FLOAT64`, `INT64`, `BOOL`, `TIMESTAMP`, `DATE` are mapped. A `NUMERIC` column has nothing to render as |
| `_governed_fields()` | the tier-1-only measures — hardcoded per table. **This is the actual experiment on Path 2**: the governed `total_revenue` measure and `active_user_status` dimension are what tier 0 must not have |
| `_model()` | the Explore and its joins are hand-written, keyed on `user_id`. Your join graph is yours |

`make validate` checks the first three plus `LOOKER_EXPLORE` offline, so a table
you forgot to map fails in a free second rather than as a `KeyError` after
BigQuery is already provisioned. It cannot check the last two — a wrong join is
still SQL that runs.

**Loading the files is manual.** `make looker-plan` / `make looker-apply` create
the connections and are additive-only, refusing any name outside the sandbox
namespace. But the `.lkml` files themselves are dragged into the Looker IDE in
Development Mode, validated, committed and deployed by hand — runbook
[Step 3](looker_runbook.md#step-3--load-the-lookml-files-manual). There is no API
for it that we chose to depend on.

**Prove the fence before you trust the arm.** `make verify-isolation` and
`looker_check.report()` confirm tier 0 cannot see tier-1 fields. Path 2 is the
arm where a broken fence is least visible, because the semantic layer will happily
answer from whatever it can reach.

If you are running against a **shared** Looker instance, add only your own content
and leave everything else alone. `looker-apply` is namespace-guarded for exactly
this reason, and you should still read the plan before applying it.

---

## Why the check exists

`corpus.py`, `golden.py`, `questions.json`, `scoring.py` and `lookml.py` describe
one experiment from five angles and are joined by string equality. Most of the ways
to break that join fail *silently*, and the loud one fails late:

| Mistake | What actually happens | Without the check, you learn |
|---|---|---|
| `golden_key` typo | resolves to `None`, which is the legal state for a prose question — every cell scores wrong | after the sweep |
| evidence term typo | can never be matched, so evidence recall is a floor forever | never — it reads as a finding |
| `RULE_TRIGGERS` column renamed | `rules_for()` returns `[]`, so acquisition is "not applicable" everywhere | never — it reads as "no governance to acquire" |
| duplicate question id | cell keys collide and replicates overwrite each other | maybe, from a low cell count |
| table missing from `VIEW_NAMES` | `KeyError` in `make lookml` | loudly, but only after BigQuery is provisioned |
| stale `PRIMARY_KEYS` entry | no symmetric aggregates, so summed measures fan out across the join | never — the number is just too big |

All four are the "unmeasured reported as zero" mistake this project takes pains to
avoid everywhere else, arriving by typo. That is why `make validate` is offline,
free, and wired into both `make check` and `make setup`.
