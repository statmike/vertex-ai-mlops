# Ground Truth — the rubric behind `questions.json`

12 questions, one per entry in [`src/golden.py`](../src/golden.py). This file documents how they are
scored, which decoys each one baits, and the rules for editing them. `questions.json` is the machine
copy; this is the reasoning.

Nothing here records a *number*. Every answer is recomputed live against the corpus by
`golden.resolve()`, because the generated timestamps hang off build time and a cached number would
rot silently as the sandbox ages.

## Why graded, and not correct/incorrect

A flat pass/fail forces every failure into one bucket, and the whole point of this sandbox is that
the failures differ. An agent that returns the wrong number because it never found the governed rule
has a different problem from one that found the rule and did the arithmetic wrong. So each question
carries three independent signals:

| Signal | Definition | What it isolates |
|---|---|---|
| **Evidence recall** | `\|emitted ∩ must_have\| / \|must_have\|` | Did it *acquire* the right context? |
| **Evidence precision** | `\|emitted ∩ (must ∪ nice)\| / \|emitted\|` | Did it stay on the right context? A distractor drags this down. |
| **Answer accuracy** | numeric match to `golden.py` within `tolerance` | Did it *apply* the context correctly? |

Acquisition and application come apart, and that gap is the headline metric (DESIGN.md §9.1). High
recall with a wrong answer means the architecture delivered the governance and the model fumbled it.
Low recall with a right answer usually means luck, and n=5 is there to catch it.

A wrong answer that matches `trap_value` is scored as a **diagnosed** failure — "sprang T2" rather
than "was wrong" — which is what makes the trap taxonomy legible in the results.

### Evidence tokens

An evidence entry is a **table or column identifier**, matched against the identifiers appearing in
the SQL the agent emitted. Every token in `questions.json` is asserted to be a real name in
`corpus.py`; a typo would silently deflate recall for every config equally, which is the kind of bug
that looks like a finding.

Paths that emit no SQL (Path 2 through Looker, Path 4 through Conversational Analytics) are scored on
the fields and Explore dimensions named in their trace instead. Same three signals, different
extraction — see `traces.py`.

## The four traps

| | Trap | Bait | Discriminator |
|---|---|---|---|
| **T1** | Naming | `txn_amt_x2` is the real revenue column; nothing about the name says so | uses `txn_amt_x2` |
| **T2** | Refunds | `status_flg` is TRUE for refunded rows and must be excluded | filters on `status_flg` |
| **T3** | Governed definition | `users.is_active` is *not* the governed Active definition | joins `raw_events_2026` on `event_ts` |
| **T4** | Nulls + outliers | `txn_amt_x2` is nullable; `revenue_amount` carries extreme outliers | acknowledges the nulls |

`revenue_amount` is the standing **decoy**: plausibly named, genuinely present, and wrong for every
revenue question. It is listed as a distractor on all seven revenue questions and on `metadata-q1`.

## The questions

### `direct` (2) — baseline plumbing

`direct-q1`, `direct-q2`. Answerable from raw schema, no governance required. All 8 configs should
pass these at both tiers; a failure here is a broken config, not a finding. They are the canary that
tells a genuine capability gap apart from a misconfigured arm.

No distractors — there is nothing to bait.

### `semantic-ambiguity` (3) — springs T1 and T2

`semantic-q1` all-time, `semantic-q2` trailing 30 days, `semantic-q3` top region. Each needs both the
right revenue column and the refund exclusion, so `must_have` is `txn_amt_x2` + `status_flg`, and
`revenue_amount` is a distractor. Their `trap_sql` sums gross list price, so an agent that misses T1
lands on a specific, recognisable wrong number rather than an arbitrary one.

`semantic-q2` says **"trailing 30 days"**, not "last month". The two differ, and the oracle cannot
score an answer to a question that was not pinned down. Any new time-windowed question must use the
trailing-window phrasing.

### `governed-logic` (3) — springs T3

`governed-q1` count, `governed-q2` average transaction value, `governed-q3` revenue share. The
governed definition of Active is *flagged **and** seen in the trailing 30 days*, so `is_active` alone
is insufficient — which is why `is_active` appears in `must_have` rather than as a distractor. It is
genuinely required; it is just not sufficient. The discriminator is whether the agent also reaches
`raw_events_2026` and `event_ts`.

This is the sharpest test of Path 3, because the rule lives only in the catalog `overview` aspect.
An agent with no governance surface cannot infer it from the schema — the column descriptions warn
that `is_active` is not the governed definition, but only the rule says what the definition *is*.

### `metadata` (2) — springs T4

`metadata-q1` null revenue count, `metadata-q2` refunded count. Profiling territory. Path 3 Managed
was expected to fail outright here; finding F3 revised that — `lookup_context` returns the profile
statistics inline, so it must extract them from a YAML blob rather than call a purpose-built tool.
That is the subtler and more interesting comparison, and it is what these two measure.

### `trap` (2) — reasoning *about* the decoy

`trap-q1` outlier count, `trap-q2` gross-vs-net overstatement.

These deviate from the seed archetype in DESIGN.md §8, which described the category as questions
"phrased to bait a decoy column outright". Both of these instead require `revenue_amount`
legitimately, so it is **not** a distractor here. The reason: a question that merely baits the decoy
is already covered three times over by the `semantic-ambiguity` set, and a fourth would add rows
without adding a dimension. Asking the agent to *compare* the two columns tests something none of the
others do — whether it understands the decoy well enough to reason about it, rather than merely
avoiding it. An agent can dodge a trap by pattern-matching a column name; it cannot answer `trap-q2`
that way.

`trap-q2` is also where T1 and T4 compound. The gap is far larger than the 25% per-transaction
gross-to-net spread, because the list-price outliers dominate the aggregate — so an agent that dodged
the naming trap but ignored the outliers still lands somewhere wrong.

## Editing rules

1. **One question per golden key, one golden key per question.** Enforced — the validator fails on an
   orphan in either direction. Adding a question means adding an oracle entry.
2. **A distractor must be genuinely present and genuinely wrong for *that* question.** Listing a
   column that the correct answer needs, or one that does not exist, corrupts precision for every
   config at once. `trap-q1` and `trap-q2` are the worked example of why this is checked per question
   rather than globally.
3. **Never cache an answer here.** Numbers belong in `golden.py`, computed live.
4. **Trailing windows, never calendar months.**
5. **Keep the category counts.** 2/3/3/2/2 is what makes per-category medians mean anything at n=5;
   changing the mix changes the power of every comparison in the report.
6. **Both tiers must agree.** T0 and T1 hold identical data, so every golden value must resolve the
   same on both. `scripts/setup.py` asserts it — a divergence means the tiers stopped being a clean
   control and no score from that run is trustworthy.
