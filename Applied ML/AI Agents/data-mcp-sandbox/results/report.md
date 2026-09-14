# Results

Model `gemini-3.7-flash` at temperature 0.0, 5 replicates, tier fence on, merged from 3 runs: `834421c3` (p1_managed, p1_toolbox, p2_managed, p2_toolbox, p3_managed, p3_toolbox, p1_matched, p3_matched, p4_bq_ca, p4_looker_ca, started 2026-09-05T02:07:23+00:00); `b987b497` (p4_bq_direct, p4_bq_direct_ctx, started 2026-09-07T14:26:18+00:00); `dc2ceaf9` (p1_managed, p1_toolbox, p2_managed, p2_toolbox, p3_managed, p3_toolbox, p1_matched, p3_matched, p4_bq_ca, p4_looker_ca, p4_bq_direct, p4_bq_direct_ctx, started 2026-09-13T20:22:45+00:00). Dataplex quality scans: not recorded for `834421c3`; present for `b987b497`; present for `dc2ceaf9`.

> **Path 3 comparability.** The p3_managed, p3_matched, p3_toolbox cells predate the `quality_scans` header field, so this capture cannot state whether this sandbox's Dataplex data-quality scans existed when they ran. That matters for Path 3 tier 1 only: with the scans in place `lookup_context` adds a `qualityStatus` line per governed table, and all three Path 3 arms call it. Do not merge tier-1 Path 3 cells from this capture with cells from a fresh `make setup`, which now creates them. See `docs/reproducing.md`.

1800 cells scored across 24 arm/tier pairs.

## Headline

| config | tier | accuracy (mean) | tokens in / correct | tokens out / correct | sec / correct | BQ jobs / correct | MiB / correct | coverage |
|---|---|---|---|---|---|---|---|---|
| p1_managed | 0 | 37% | 1870343 | 5934 | 261 | 36.7 | 339.5 | full |
| p1_managed | 1 | 75% | 471289 | 1840 | 64 | 8.9 | 103.6 | full |
| p1_toolbox | 0 | 33% | 272677 | 3818 | 211 | 28.6 | 251.0 | full |
| p1_toolbox | 1 | 100% | 29837 | 843 | 39 | 3.7 | 47.5 | full |
| p2_managed | 0 | 33% | 414122 | 4969 | 291 | 27.3 | 249.0 | full |
| p2_managed | 1 | 93% | 63792 | 907 | 55 | 4.1 | 48.8 | full |
| p2_toolbox | 0 | 32% | 980755 | 5401 | 302 | 29.3 | 223.7 | full |
| p2_toolbox | 1 | 90% | 88067 | 928 | 43 | 3.8 | 40.9 | full |
| p3_managed | 0 | 35% | 3174955 | 7619 | 319 | 40.0 | 355.2 | full |
| p3_managed | 1 | 100% | 361420 | 1202 | 51 | 4.0 | 48.7 | full |
| p3_toolbox | 0 | 33% | 609067 | 4394 | 252 | 28.3 | 242.5 | full |
| p3_toolbox | 1 | 100% | 65805 | 887 | 38 | 3.7 | 46.3 | full |
| p1_matched | 0 | 35% | 354206 | 4341 | 211 | 32.5 | 256.2 | full |
| p1_matched | 1 | 75% | 68236 | 1445 | 60 | 8.0 | 90.4 | full |
| p3_matched | 0 | 35% | 824615 | 5364 | 271 | 34.5 | 288.6 | full |
| p3_matched | 1 | 100% | 55548 | 927 | 43 | 3.6 | 42.2 | full |
| p4_bq_ca | 0 | 23% | 51735 | 2715 | 277 | 16.1 | 167.1 | floor |
| p4_bq_ca | 1 | 100% | 5190 | 504 | 36 | 1.8 | 24.3 | floor |
| p4_looker_ca | 0 | 12% | 212586 | 2928 | 1435 | 27.3 | 348.6 | floor |
| p4_looker_ca | 1 | 43% | 17937 | 611 | 199 | 3.3 | 60.8 | floor |
| p4_bq_direct | 0 | 22% | -- | -- | 51 | 6.8 | 67.7 | service only |
| p4_bq_direct | 1 | 97% | -- | -- | 11 | 1.1 | 14.0 | service only |
| p4_bq_direct_ctx | 0 | 23% | -- | -- | 49 | 7.2 | 70.7 | service only |
| p4_bq_direct_ctx | 1 | 95% | -- | -- | 11 | 1.1 | 13.2 | service only |

**Do not sort this table by the cost columns.** `p4_bq_ca`, `p4_bq_direct`, `p4_bq_direct_ctx`, `p4_looker_ca` carry `floor` coverage: they spend model tokens server-side that the API never reports, so their figures are lower bounds and every other arm's are totals. Comparing them directly compares two different quantities. The gap is not small — `make service-tokens` meters `p4_looker_ca` from Cloud Monitoring at 392,158 tokens per cell against the 18,045 recorded here, a 22x understatement that moves it from the cheapest arm to the third most expensive. The floors are left uncorrected in the table on purpose: the meter attributes by time block, not per cell, and splitting a block across cells that vary in turn count would invent a distribution. Two honest numbers in two places beat one fused number that hides which half was inferred.

Accuracy, latency and the BigQuery columns are unaffected — those are measured client-side for every arm.

## Capture health

| config | tier | attempted | scored | failed | quota-retried | CA leak |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 75 | 75 | 0 | 10 | 0% |
| p1_managed | 1 | 75 | 75 | 0 | 2 | 0% |
| p1_toolbox | 0 | 75 | 75 | 0 | 5 | 57% |
| p1_toolbox | 1 | 75 | 75 | 0 | 4 | 39% |
| p2_managed | 0 | 75 | 75 | 0 | 5 | 0% |
| p2_managed | 1 | 75 | 75 | 0 | 4 | 0% |
| p2_toolbox | 0 | 75 | 75 | 0 | 4 | 0% |
| p2_toolbox | 1 | 75 | 75 | 0 | 0 | 0% |
| p3_managed | 0 | 75 | 75 | 0 | 8 | 0% |
| p3_managed | 1 | 75 | 75 | 0 | 4 | 0% |
| p3_toolbox | 0 | 75 | 75 | 0 | 2 | 67% |
| p3_toolbox | 1 | 75 | 75 | 0 | 0 | 24% |
| p1_matched | 0 | 75 | 75 | 0 | 1 | 0% |
| p1_matched | 1 | 75 | 75 | 0 | 1 | 0% |
| p3_matched | 0 | 75 | 75 | 0 | 10 | 0% |
| p3_matched | 1 | 75 | 75 | 0 | 14 | 0% |
| p4_bq_ca | 0 | 75 | 75 | 0 | 7 | 0% |
| p4_bq_ca | 1 | 75 | 75 | 0 | 0 | 0% |
| p4_looker_ca | 0 | 75 | 75 | 0 | 0 | 0% |
| p4_looker_ca | 1 | 75 | 75 | 0 | 0 | 0% |
| p4_bq_direct | 0 | 75 | 75 | 0 | 0 | 0% |
| p4_bq_direct | 1 | 75 | 75 | 0 | 0 | 0% |
| p4_bq_direct_ctx | 0 | 75 | 75 | 0 | 0 | 0% |
| p4_bq_direct_ctx | 1 | 75 | 75 | 0 | 0 | 0% |

**CA leak** is not a bug in the run — it is a property of the surface being measured. `ask_data_insights` ships inside the Toolbox BigQuery toolset, so `p1_toolbox` and `p3_toolbox` can reach Conversational Analytics and become Path 4 for that cell. The arms are reported as shipped rather than trimmed to be hermetic, so this column says how often it happened instead of hiding it.

## Accuracy

| config | tier | n | graded | correct | sprang trap | used decoy |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 75 | 60 | 37% | 45% | 53% |
| p1_managed | 1 | 75 | 60 | 75% | 7% | 31% |
| p1_toolbox | 0 | 75 | 60 | 33% | 24% | 53% |
| p1_toolbox | 1 | 75 | 60 | 100% | 0% | 11% |
| p2_managed | 0 | 75 | 60 | 33% | 47% | 53% |
| p2_managed | 1 | 75 | 60 | 93% | 0% | 0% |
| p2_toolbox | 0 | 75 | 60 | 32% | 45% | 53% |
| p2_toolbox | 1 | 75 | 60 | 90% | 0% | 1% |
| p3_managed | 0 | 75 | 60 | 35% | 47% | 53% |
| p3_managed | 1 | 75 | 60 | 100% | 0% | 17% |
| p3_toolbox | 0 | 75 | 60 | 33% | 17% | 53% |
| p3_toolbox | 1 | 75 | 60 | 100% | 0% | 7% |
| p1_matched | 0 | 75 | 60 | 35% | 47% | 53% |
| p1_matched | 1 | 75 | 60 | 75% | 7% | 19% |
| p3_matched | 0 | 75 | 60 | 35% | 47% | 53% |
| p3_matched | 1 | 75 | 60 | 100% | 0% | 12% |
| p4_bq_ca | 0 | 75 | 60 | 23% | 16% | 53% |
| p4_bq_ca | 1 | 75 | 60 | 100% | 0% | 7% |
| p4_looker_ca | 0 | 75 | 60 | 12% | 12% | 23% |
| p4_looker_ca | 1 | 75 | 60 | 43% | 0% | 7% |
| p4_bq_direct | 0 | 75 | 60 | 22% | 16% | 53% |
| p4_bq_direct | 1 | 75 | 60 | 97% | 0% | 0% |
| p4_bq_direct_ctx | 0 | 75 | 60 | 23% | 12% | 53% |
| p4_bq_direct_ctx | 1 | 75 | 60 | 95% | 0% | 0% |

**360 of 1800 cells are excluded from every rate above.** 3 of the battery's questions are worded so that two answers are equally defensible, which makes the oracle an arbiter of a coin-flip rather than a grader. The cells ran, are in the capture, and carry a `correct` a reader can inspect — they are *unmeasured*, not zero, the same way an opaque path's evidence reads `--`.

* `governed-q1` — The governed rule defines Active as "had an event in the trailing 30 days", which pins the window's length but not its anchor. The answer is a count - extensive, so the two defensible anchorings differ by more than the 0.5% tolerance. See semantic-q2.
* `governed-q3` — Inherits the Active definition's unpinned anchor from governed-q1, and sums over it. The answer is an extensive quantity twice over - which users count, and how much they spent - so the two defensible anchorings diverge well past the 0.5% tolerance. See semantic-q2.
* `semantic-q2` — "trailing 30 days" pins the window's length but not its anchor. Anchoring to the data's latest timestamp is as defensible as anchoring to now, and agents pick between them nondeterministically at temperature 0 - the same arm answered 2,699 and 2,804 in consecutive runs. The answer is an extensive quantity (a sum), so the two readings differ by more than the 0.5% tolerance and the oracle arbitrates a coin-flip.

### Questions no arm got right

| question | tier | arms | shut out | answered | distinct answers | most common | verdict |
|---|---|---|---|---|---|---|---|
| `governed-q1a` | 0 | 12 | 12 | 60 | 5 | 3,520 (55) | expected |
| `governed-q1a` | 1 | 12 | 3 | 15 | 5 | 3,995 (10) | expected |
| `governed-q2` | 0 | 12 | 12 | 60 | 7 | 99 (31) | expected |
| `governed-q3a` | 0 | 12 | 12 | 60 | 4 | 21,961,256 (34) | expected |
| `governed-q3a` | 1 | 12 | 4 | 20 | 2 | 3,873,375 (10) | expected |
| `metadata-q1` | 0 | 12 | 7 | 34 | 1 | 0 (34) | **suspect** |
| `semantic-q1` | 0 | 12 | 12 | 60 | 5 | 31,700,036 (33) | expected |
| `semantic-q2a` | 0 | 12 | 12 | 60 | 4 | 2,580,231 (36) | expected |
| `semantic-q3` | 0 | 12 | 12 | 60 | 6 | 8,134,071 (34) | expected |
| `trap-q2` | 0 | 12 | 12 | 60 | 10 | 776 (23) | expected |

* `governed-q1a` tier 0 — 55/60 sprang the trap — the corpus working as designed
* `governed-q1a` tier 1 — 5 distinct answers — varied wrongness, not one shared cause
* `governed-q2` tier 0 — 31/60 sprang the trap — the corpus working as designed
* `governed-q3a` tier 0 — 34/60 sprang the trap — the corpus working as designed
* `governed-q3a` tier 1 — the modal answer spans only 2 arm(s)
* `metadata-q1` tier 0 — 7 shut-out arms agree on 0 and the oracle rejects it, while 5 other arm(s) scored normally — but the same question is answered correctly 58 time(s) at another tier, so the golden computes a reachable number. Read this as a naive answer the oracle has no trap recorded for, not as a bad golden
* `semantic-q1` tier 0 — 33/60 sprang the trap — the corpus working as designed
* `semantic-q2a` tier 0 — 36/60 sprang the trap — the corpus working as designed
* `semantic-q3` tier 0 — 34/60 sprang the trap — the corpus working as designed
* `trap-q2` tier 0 — 10 distinct answers — varied wrongness, not one shared cause

⚠️ **1 flagged: `metadata-q1` tier 0.** Several arms going 0/n while agreeing with each other is a claim about the rubric, not about the agents. There are two repairs and they are not interchangeable:

* **The golden or the wording is wrong.** Fix the golden if it computes the wrong thing; if the question admits two defensible answers instead, mark it `scoreable: false` with a reason rather than letting one arbitrary reading count as n failures per arm.
* **The trap is simply not recorded.** A question whose oracle carries no trap value cannot report a trap-shaped miss as one, so textbook naive behaviour lands in the same bucket as genuine error. Add the `trap_sql` — the cells do not need re-running, but a capture that froze its oracle before the trap existed will keep flagging until it is re-swept.

For `metadata-q1` tier 0 the second is the one to reach for. The same question is answered correctly at another tier, so the golden computes a number that is reachable from the corpus — what the shut-out arms found is a naive answer with no trap recorded against it, not evidence that the oracle is wrong.


## Acquisition vs application

| config | tier | n | opaque | acquired | application loss |
|---|---|---|---|---|---|
| p1_managed | 0 | 50 | 0% | 0% | 0% |
| p1_managed | 1 | 50 | 0% | 100% | 30% |
| p1_toolbox | 0 | 50 | 0% | 0% | 0% |
| p1_toolbox | 1 | 50 | 0% | 100% | 0% |
| p2_managed | 0 | 50 | 0% | 0% | 0% |
| p2_managed | 1 | 50 | 0% | 100% | 8% |
| p2_toolbox | 0 | 50 | 0% | 0% | 0% |
| p2_toolbox | 1 | 50 | 0% | 100% | 12% |
| p3_managed | 0 | 50 | 0% | 0% | 0% |
| p3_managed | 1 | 50 | 0% | 100% | 0% |
| p3_toolbox | 0 | 50 | 0% | 0% | 0% |
| p3_toolbox | 1 | 50 | 0% | 100% | 0% |
| p1_matched | 0 | 50 | 0% | 0% | 0% |
| p1_matched | 1 | 50 | 0% | 100% | 30% |
| p3_matched | 0 | 50 | 0% | 0% | 0% |
| p3_matched | 1 | 50 | 0% | 100% | 0% |
| p4_bq_ca | 0 | 50 | 100% | -- | -- |
| p4_bq_ca | 1 | 50 | 100% | -- | -- |
| p4_looker_ca | 0 | 50 | 100% | -- | -- |
| p4_looker_ca | 1 | 50 | 100% | -- | -- |
| p4_bq_direct | 0 | 50 | 100% | -- | -- |
| p4_bq_direct | 1 | 50 | 100% | -- | -- |
| p4_bq_direct_ctx | 0 | 50 | 100% | -- | -- |
| p4_bq_direct_ctx | 1 | 50 | 100% | -- | -- |

## Evidence

| config | tier | no query disclosed | recall (median) | IQR | precision |
|---|---|---|---|---|---|
| p1_managed | 0 | 0% | 1.00 | 0.00 | 0.83 |
| p1_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p1_toolbox | 0 | 0% | 1.00 | 0.00 | 0.83 |
| p1_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p2_managed | 0 | 0% | 1.00 | 0.00 | 0.83 |
| p2_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p2_toolbox | 0 | 0% | 1.00 | 0.20 | 0.83 |
| p2_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_managed | 0 | 0% | 1.00 | 0.00 | 0.83 |
| p3_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_toolbox | 0 | 0% | 1.00 | 0.00 | 0.83 |
| p3_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p1_matched | 0 | 0% | 1.00 | 0.00 | 0.83 |
| p1_matched | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_matched | 0 | 0% | 1.00 | 0.00 | 0.83 |
| p3_matched | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p4_bq_ca | 0 | 0% | 1.00 | 0.33 | 0.83 |
| p4_bq_ca | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p4_looker_ca | 0 | 39% | 0.33 | 0.60 | 0.88 |
| p4_looker_ca | 1 | 41% | 0.90 | 0.57 | 1.00 |
| p4_bq_direct | 0 | 0% | 0.67 | 0.60 | 0.67 |
| p4_bq_direct | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p4_bq_direct_ctx | 0 | 0% | 0.67 | 0.60 | 0.67 |
| p4_bq_direct_ctx | 1 | 0% | 1.00 | 0.00 | 1.00 |

## Latency

| config | tier | clean cells | excluded | median s | IQR | tool calls |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 65 | 10 | 78.9 | 109.4 | 18.0 |
| p1_managed | 1 | 73 | 2 | 41.4 | 72.5 | 8.0 |
| p1_toolbox | 0 | 70 | 5 | 67.0 | 65.9 | 13.0 |
| p1_toolbox | 1 | 71 | 4 | 41.6 | 46.4 | 7.0 |
| p2_managed | 0 | 70 | 5 | 82.5 | 70.2 | 15.0 |
| p2_managed | 1 | 71 | 4 | 43.0 | 25.0 | 7.0 |
| p2_toolbox | 0 | 71 | 4 | 72.3 | 72.0 | 16.0 |
| p2_toolbox | 1 | 75 | 0 | 36.2 | 19.0 | 8.0 |
| p3_managed | 0 | 67 | 8 | 111.8 | 124.3 | 22.0 |
| p3_managed | 1 | 71 | 4 | 49.2 | 57.5 | 8.0 |
| p3_toolbox | 0 | 73 | 2 | 86.6 | 81.6 | 17.0 |
| p3_toolbox | 1 | 75 | 0 | 38.4 | 43.3 | 7.0 |
| p1_matched | 0 | 74 | 1 | 74.0 | 71.9 | 14.5 |
| p1_matched | 1 | 74 | 1 | 35.8 | 59.1 | 8.0 |
| p3_matched | 0 | 65 | 10 | 91.1 | 94.4 | 21.0 |
| p3_matched | 1 | 61 | 14 | 33.1 | 35.9 | 7.0 |
| p4_bq_ca | 0 | 68 | 7 | 61.1 | 45.6 | 3.0 |
| p4_bq_ca | 1 | 75 | 0 | 32.6 | 23.6 | 2.0 |
| p4_looker_ca | 0 | 75 | 0 | 140.1 | 92.8 | 2.0 |
| p4_looker_ca | 1 | 75 | 0 | 55.0 | 58.8 | 1.0 |
| p4_bq_direct | 0 | 75 | 0 | 10.0 | 5.1 | 0.0 |
| p4_bq_direct | 1 | 75 | 0 | 10.5 | 4.6 | 0.0 |
| p4_bq_direct_ctx | 0 | 75 | 0 | 9.8 | 5.0 | 0.0 |
| p4_bq_direct_ctx | 1 | 75 | 0 | 10.3 | 4.0 | 0.0 |

## Cost

| config | tier | tokens (median) | IQR | thoughts | MiB billed | USD (mean) | unmeasured spend |
|---|---|---|---|---|---|---|---|
| p1_managed | 0 | 601656 | 913857 | 2832 | 110.0 | 0.00076 | full |
| p1_managed | 1 | 227498 | 625792 | 1270 | 50.0 | 0.00060 | full |
| p1_toolbox | 0 | 81767 | 111699 | 1299 | 70.0 | 0.00050 | full |
| p1_toolbox | 1 | 31953 | 46897 | 792 | 50.0 | 0.00033 | full |
| p2_managed | 0 | 95152 | 115881 | 1652 | 70.0 | 0.00047 | full |
| p2_managed | 1 | 38139 | 49272 | 762 | 30.0 | 0.00028 | full |
| p2_toolbox | 0 | 95536 | 166450 | 1952 | 50.0 | 0.00039 | full |
| p2_toolbox | 1 | 29354 | 52493 | 789 | 20.0 | 0.00025 | full |
| p3_managed | 0 | 1120646 | 1402874 | 3719 | 120.0 | 0.00076 | full |
| p3_managed | 1 | 313961 | 617832 | 1137 | 50.0 | 0.00037 | full |
| p3_toolbox | 0 | 198899 | 191259 | 1652 | 80.0 | 0.00050 | full |
| p3_toolbox | 1 | 65844 | 126248 | 1101 | 50.0 | 0.00034 | full |
| p1_matched | 0 | 83308 | 168561 | 2131 | 70.0 | 0.00054 | full |
| p1_matched | 1 | 28007 | 117786 | 1373 | 50.0 | 0.00052 | full |
| p3_matched | 0 | 253643 | 380498 | 2258 | 100.0 | 0.00061 | full |
| p3_matched | 1 | 47336 | 105315 | 868 | 40.0 | 0.00032 | full |
| p4_bq_ca | 0 | 8946 | 11832 | 407 | 30.0 | 0.00024 | floor |
| p4_bq_ca | 1 | 4719 | 4813 | 380 | 20.0 | 0.00017 | floor |
| p4_looker_ca | 0 | 15980 | 16341 | 266 | 20.0 | 0.00023 | floor |
| p4_looker_ca | 1 | 4226 | 4729 | 219 | 10.0 | 0.00014 | floor |
| p4_bq_direct | 0 | -- | -- | -- | 10.0 | 0.00009 | service only |
| p4_bq_direct | 1 | -- | -- | -- | 10.0 | 0.00010 | service only |
| p4_bq_direct_ctx | 0 | -- | -- | -- | 10.0 | 0.00009 | service only |
| p4_bq_direct_ctx | 1 | -- | -- | -- | 10.0 | 0.00009 | service only |

Prices: cloud.google.com/bigquery/pricing, US multi-region on-demand list price (verified 2026-09-03). Token rates are unset unless a `prices.json` supplies them, so a `--` in the USD column means *unpriced*, not free. Dollars are the only derived number in this report and the only one that depends on a rate card, which is why every other column is in units consumed.

The last column is how complete the picture is. **full** means everything this sweep spent, it saw. **floor** means the arm also spent model tokens server-side that the API never reported back — Conversational Analytics runs its own Gemini loop on our behalf. A floor is a lower bound, not a total, and it is not small: `make service-tokens` meters it from Cloud Monitoring and finds `p4_looker_ca` consumed 22x the tokens recorded here. **service only** means the arm never called a model in this process at all — the direct-API arms hand the question to the service and read back an answer — so its token columns read `--`. That is absent, not free; the model spend is entirely on the meter this report cannot see.

## Semantic adherence (judged)

| config | tier | n | governed | partial | invented | unclear |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 65 | 8% | 26% | 66% | 0% |
| p1_managed | 1 | 65 | 46% | 54% | 0% | 0% |
| p1_toolbox | 0 | 65 | 8% | 22% | 71% | 0% |
| p1_toolbox | 1 | 65 | 85% | 15% | 0% | 0% |
| p2_managed | 0 | 65 | 8% | 31% | 62% | 0% |
| p2_managed | 1 | 65 | 83% | 17% | 0% | 0% |
| p2_toolbox | 0 | 65 | 6% | 28% | 66% | 0% |
| p2_toolbox | 1 | 65 | 82% | 18% | 0% | 0% |
| p3_managed | 0 | 65 | 8% | 29% | 63% | 0% |
| p3_managed | 1 | 65 | 85% | 15% | 0% | 0% |
| p3_toolbox | 0 | 65 | 8% | 17% | 75% | 0% |
| p3_toolbox | 1 | 65 | 85% | 15% | 0% | 0% |
| p1_matched | 0 | 65 | 8% | 29% | 63% | 0% |
| p1_matched | 1 | 65 | 46% | 51% | 3% | 0% |
| p3_matched | 0 | 65 | 8% | 29% | 63% | 0% |
| p3_matched | 1 | 65 | 85% | 15% | 0% | 0% |
| p4_bq_ca | 0 | 65 | 2% | 14% | 85% | 0% |
| p4_bq_ca | 1 | 65 | 85% | 15% | 0% | 0% |
| p4_looker_ca | 0 | 65 | 0% | 18% | 57% | 25% |
| p4_looker_ca | 1 | 65 | 32% | 20% | 3% | 45% |
| p4_bq_direct | 0 | 65 | 2% | 20% | 78% | 0% |
| p4_bq_direct | 1 | 65 | 86% | 14% | 0% | 0% |
| p4_bq_direct_ctx | 0 | 65 | 3% | 25% | 72% | 0% |
| p4_bq_direct_ctx | 1 | 65 | 85% | 15% | 0% | 0% |

## Equivalence

| config A | config B | pairs | graded | same tool sequence | same value | same verdict |
|---|---|---|---|---|---|---|
| p1_managed | p1_toolbox | 150 | 120 | 0% | 62% | 86% |
| p2_managed | p2_toolbox | 150 | 120 | 5% | 92% | 94% |
| p3_managed | p3_toolbox | 150 | 120 | 0% | 70% | 99% |
| p1_managed | p1_matched | 150 | 120 | 0% | 92% | 99% |
| p3_managed | p3_matched | 150 | 120 | 0% | 90% | 98% |
| p4_bq_ca | p4_looker_ca | 150 | 120 | 0% | 39% | 66% |

## Tool surface

Schemas are re-sent on every turn, so their size is a per-call floor on prompt tokens. Measured live at sweep time, because a vendor can change them without notice.

| config | tools | schema chars |
|---|---|---|
| p3_managed | 8 | 146148 |
| p1_managed | 5 | 122343 |
| p3_toolbox | 23 | 18865 |
| p2_managed | 7 | 11721 |
| p1_toolbox | 8 | 7030 |
| p3_matched | 8 | 6809 |
| p2_toolbox | 7 | 5602 |
| p1_matched | 5 | 3019 |
| p4_bq_ca | 1 | 882 |
| p4_looker_ca | 1 | 817 |
| p4_bq_direct | 0 | 0 |
| p4_bq_direct_ctx | 0 | 0 |
