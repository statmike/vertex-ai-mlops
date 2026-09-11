# What was asked, and what counts as right

The rubric is the part of this experiment most worth arguing with, so it ships
as data and code you can change rather than as a claim. This page is the map:
what the corpus hides, what the twelve questions ask, and how an answer becomes
a `correct` or a `sprang_trap`.

The *what counts as right*. [paths](paths.md) is what is being compared and
[method](method.md) is how the sweep is run.

Nothing here needs a cloud account. `results/capture.json.gz` carries the raw
sweep and the frozen oracle, so you can re-score the whole thing offline — see
[reproducing](reproducing.md#1-re-scoring-our-capture-no-cloud-account).

---

## The corpus is hostile on purpose

Three tables, built by `src/corpus.py`, which is also what provisioning reads —
so this page cannot drift from what actually gets created.

| Table | What it is |
|---|---|
| `users` | 5,000 registered users, with an `is_active` flag that is *not* the governed definition of active |
| `raw_events_2026` | clickstream, 400 days of history — the only way to tell who is genuinely active |
| `transactions_v2_final` | transactions, where the column named `revenue_amount` is not revenue |

Every trap is a case where reading the raw schema and writing the obvious SQL
produces a **plausible, confident, wrong** answer. That is the point: an agent
that fails these does not error, it reports a number.

| | Trap | The naive read | Why it is wrong | Calibration |
|---|---|---|---|---|
| **T1** | Misleading name | `SUM(revenue_amount)` | gross list price, not revenue — net lives in `txn_amt_x2` | gross = net × 1.25 |
| **T2** | Inverted boolean | ignore `status_flg` | `TRUE` means *refunded*; those rows must come out | 12% of rows refunded |
| **T3** | Contradicted flag | `WHERE is_active` | the governed rule defines Active as "had an event in the trailing 30 days" | 20% of flagged users are dormant |
| **T4** | Nulls and outliers | `AVG`, `COUNT(*)` | `txn_amt_x2` is nullable, and `revenue_amount` carries seeded outliers | 7% null, 5 outliers per 1,000 |

T1's 25% spread is also the tightest gap in the corpus between a correct answer
and a trap answer, which is what sets the numeric tolerance below.

**Tier 0 and tier 1 hold byte-identical data.** The only difference is whether
the warehouse describes itself — catalog aspects and LookML at tier 1, nothing
at tier 0. So any accuracy difference is governance and cannot be anything else.
The separation is enforced by IAM, not by prompt; see [scoping](scoping.md).

---

## The twelve questions

`examples/questions.json`. Five categories, chosen so that a single accuracy
number cannot hide a lopsided result — two of them are answerable without any
governance at all, which is how you tell a broken arm from a governed one.

The two `trap` rows below are abridged to fit; the agents were asked the longer
wording in `questions.json`, and the exact phrasing is part of the measurement.

| id | Category | Question | Traps in play |
|---|---|---|---|
| `direct-q1` | direct | How many registered users are there? | — |
| `direct-q2` | direct | How many distinct event types appear in the 2026 raw events? | — |
| `semantic-q1` | semantic-ambiguity | What is our total net revenue, all time? | T1, T2 |
| `semantic-q2` | semantic-ambiguity | What was our net revenue over the trailing 30 days? | T1, T2 |
| `semantic-q3` | semantic-ambiguity | Which sales region produced the most net revenue, and how much? | T1, T2 |
| `governed-q1` | governed-logic | How many Active users do we have? | T3 |
| `governed-q2` | governed-logic | What is the average net transaction value for our Active users? | T1, T2, T3, T4 |
| `governed-q3` | governed-logic | How much of our net revenue comes from Active users? | T1, T2, T3 |
| `metadata-q1` | metadata | How many transactions are missing a net revenue value? | T1, T4 |
| `metadata-q2` | metadata | How many transactions were refunded? | T2 |
| `trap-q1` | trap | How many transactions have a gross list price more than 100× the net revenue? | T1, T4 |
| `trap-q2` | trap | If we summed `revenue_amount`, by what percent would that overstate net revenue? | T1, T2 |

T1, T2 and T3 are readable straight off each question's `evidence` block —
naming `revenue_amount`/`txn_amt_x2`, `status_flg` or `is_active` is what puts
them in play, so that column is checkable against `questions.json` rather than
asserted here. T4 is not tied to a column and is marked where the question turns
on nulls or outliers: averaging a nullable measure, counting the missing, or
hunting the seeded gross-price outliers.

The two `direct` questions are the control. An arm that misses those is broken,
not ungoverned, and `report.capture_health` is where that shows up.

Every question is phrased as a **trailing N days** window, never "last month",
because "last month" is ambiguous between calendar and trailing and the oracle
cannot score an answer to a question that did not pin its own window down.

⚠️ **That is not sufficient, and the governance ladder measured it.** "Trailing
30 days" fixes the window's *length* and not its *anchor*. Anchoring to the
data's own latest timestamp is as defensible as anchoring to now, and the agents
pick between the two **nondeterministically, run to run, at temperature 0** —
the same arm answered 2,699 and 2,804 Active users in consecutive runs a minute
apart. `golden.py` anchors to now, so the oracle silently picks a side.

Whether that costs an arm anything depends on where the frozen oracle's anchor
lands relative to the agent's. In the ladder capture the gap was 0.32% and both
readings scored correct; in the published capture it was 1.05% and 4.98% and
both scored wrong, giving **0/30 at tier 1** on questions the same arms answer
competently. The 0.5% tolerance below cannot help — the spread between anchorings
is set by the data, not by the tolerance.

It bites the trailing-window questions whose answer is an **extensive** quantity
(`governed-q1`, `governed-q3`, `semantic-q2` — a count or a sum) and spares the
intensive one (`governed-q2`, an average, which barely moves). These questions
therefore report a question-design defect on top of whatever they report about
the agent, and
[paths](paths.md#the-trailing-window-questions-are-anchor-ambiguous) sets out
what it does and does not change. The fix is to pin the anchor in the question
wording; it is not applied here because changing a question invalidates
comparison with every capture already published, which is the more expensive
loss.

---

## How an answer is scored

Three passes, independently skippable because they cost different amounts. Only
the first is free and offline.

### 1. Deterministic — `src/scoring.py`

No model calls. Everything decidable by parsing is decided by parsing; asking an
LLM to compare two numbers adds variance for no gain.

**`correct`** — the number parsed out of the answer matches the oracle within a
relative tolerance of **0.5%** (`golden.DEFAULT_TOLERANCE`). Generous enough to
absorb rounding and float aggregation order, tight enough that no trap answer
can slip through: the smallest correct-to-trap gap in this corpus is T1's 25%.

**`sprang_trap`** — the answer matches the *trap* value, the specific wrong
number a naive query produces. This is what makes a failure legible. "Wrong" and
"wrong in exactly the way the corpus set out to catch" are different results,
and only the second tells you the governance was the missing piece.

**The oracle is recomputed live**, never cached, because the generator anchors
timestamps to build time and a stored number rots as the sandbox ages. For
readers, `make export` freezes the goldens into the capture header — which is
why re-scoring our capture needs no BigQuery.

**Evidence recall and precision** — the emitted SQL is parsed for the columns a
correct answer must touch (`must_have`) and the ones it must not (`distractor`).
`used_distractor` is the direct measurement of an agent reaching for
`revenue_amount`.

### 2. Acquisition versus application

The decomposition that the headline result rests on. A single accuracy number
conflates two failures that need different fixes:

- **Acquisition** — did the governed rule ever reach the agent? Read from tool
  *results*, never from the answer, because an answer that recites the rule
  proves only that the agent had it, not that the architecture delivered it.
- **Application** — the rule arrived and the answer is still wrong.

At tier 1 acquisition runs at 100% on every inspectable arm, and application
loss is 30–40%. Getting metadata to an agent is close to solved. Getting the
agent to use it is not.

### 3. The judge — `src/judge.py`

One model call per governed cell, for the one thing code cannot decide: did this
agent reason from the governed definitions, or invent a calculation? Verdicts
are `governed`, `partial`, `invented`, `unclear`.

It is **blind to the config** — the prompt never names the path, variant, tier
or server, and a test greps the rendered prompt for every config key. A judge
told it is looking at "the governed context arm" will find governance in it.

It does **not** re-decide the number; accuracy is already settled against the
oracle. A judge call that errors returns `unclear` rather than raising, so one
bad response cannot void a pass over 1,440 cells.

**Expect it to wobble.** `gemini-3.7-flash` is a reasoning model, so temperature
0 is not determinism. Re-judging the same capture moved 13 of 1,000 verdicts
(1.3%), all across the `partial`/`invented` boundary, changing no adherence cell
by more than 2 points. The deterministic scores were byte-identical. That is the
ratio to keep in mind before reading anything into a small adherence difference,
and it is why the design runs five replicates rather than one.

---

## Unmeasured is not zero

The rule that governs every table and every chart here. Two things are
deliberately left blank rather than scored:

- **Evidence on opaque paths.** Conversational Analytics narrates itself in
  prose and often never names the field it used, so there is no query to
  inspect. Scoring it 0.0 recall beside Toolbox's 1.0 would publish "Path 4
  ignores the semantic layer" when the truth is "Path 4 does not show its work."
- **Acquisition at tier 0.** There is no governed description to acquire, so the
  check returns False by construction. That is the intended reading, not a gap.

Ranking an arm bottom on a metric it was never eligible for is a false finding,
not a conservative one. The report prints `--`; the charts drop the arm and say
so in the subtitle, or draw it as a bound. See
[Reading Path 4's numbers fairly](paths.md#reading-path-4s-numbers-fairly).

---

## Changing the rubric

Scores live beside the capture, never inside it, so a rubric change re-scores
what already ran instead of re-running it:

```bash
uv run python examples/build_results.py \
  --results results/capture.json.gz --out /tmp/mine --no-judge --no-cost
```

Edit `src/scoring.py` and run it again — a minute, not a day. Disagree with the
0.5% tolerance, with counting a trap match separately, with which columns are
`must_have`? Those are all one file and one JSON away.

Swapping in **your own tables** is a bigger job and worth being honest about:
`corpus.py`, `golden.py` and `questions.json` have to change together, because a
question is only scoreable against a golden some query can compute. The traps
are the measurement, not decoration. See
[reproducing](reproducing.md#pointing-it-at-your-own-data).
