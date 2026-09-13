# Results

Model `gemini-3.7-flash` at temperature 0.0, 5 replicates, tier fence on, merged from 2 runs: `834421c3` (p1_managed, p1_toolbox, p2_managed, p2_toolbox, p3_managed, p3_toolbox, p1_matched, p3_matched, p4_bq_ca, p4_looker_ca, started 2026-09-05T02:07:23+00:00); `b987b497` (p4_bq_direct, p4_bq_direct_ctx, started 2026-09-07T14:26:18+00:00). Dataplex quality scans: not recorded for `834421c3`; present for `b987b497`.

> **Path 3 comparability.** The p3_managed, p3_matched, p3_toolbox cells predate the `quality_scans` header field, so this capture cannot state whether this sandbox's Dataplex data-quality scans existed when they ran. That matters for Path 3 tier 1 only: with the scans in place `lookup_context` adds a `qualityStatus` line per governed table, and all three Path 3 arms call it. Do not merge tier-1 Path 3 cells from this capture with cells from a fresh `make setup`, which now creates them. See `docs/reproducing.md`.

1440 cells scored across 24 arm/tier pairs.

## Headline

| config | tier | accuracy (mean) | tokens in / correct | tokens out / correct | sec / correct | BQ jobs / correct | MiB / correct | coverage |
|---|---|---|---|---|---|---|---|---|
| p1_managed | 0 | 49% | 1163956 | 3790 | 190 | 24.0 | 201.8 | full |
| p1_managed | 1 | 89% | 268637 | 1061 | 41 | 5.1 | 61.2 | full |
| p1_toolbox | 0 | 44% | 175354 | 2528 | 160 | 18.8 | 150.5 | full |
| p1_toolbox | 1 | 100% | 22267 | 669 | 34 | 2.9 | 36.2 | full |
| p2_managed | 0 | 44% | 278217 | 3457 | 214 | 18.7 | 179.5 | full |
| p2_managed | 1 | 98% | 40970 | 722 | 48 | 3.2 | 36.6 | full |
| p2_toolbox | 0 | 42% | 395521 | 3848 | 215 | 20.3 | 156.3 | full |
| p2_toolbox | 1 | 100% | 63826 | 750 | 33 | 2.9 | 30.4 | full |
| p3_managed | 0 | 47% | 2151215 | 5063 | 239 | 27.2 | 219.5 | full |
| p3_managed | 1 | 100% | 283550 | 965 | 46 | 3.0 | 36.7 | full |
| p3_toolbox | 0 | 44% | 417432 | 2983 | 190 | 19.5 | 159.5 | full |
| p3_toolbox | 1 | 100% | 53979 | 699 | 39 | 3.0 | 35.8 | full |
| p1_matched | 0 | 47% | 252863 | 3066 | 162 | 22.4 | 167.6 | full |
| p1_matched | 1 | 89% | 36139 | 899 | 44 | 4.8 | 54.8 | full |
| p3_matched | 0 | 47% | 554297 | 3710 | 208 | 23.5 | 186.2 | full |
| p3_matched | 1 | 100% | 46360 | 796 | 45 | 3.1 | 34.2 | full |
| p4_bq_ca | 0 | 31% | 36421 | 1834 | 213 | 11.7 | 109.3 | floor |
| p4_bq_ca | 1 | 100% | 4613 | 428 | 35 | 1.7 | 20.2 | floor |
| p4_looker_ca | 0 | 16% | 171902 | 2180 | 1068 | 16.4 | 178.6 | floor |
| p4_looker_ca | 1 | 47% | 19780 | 531 | 197 | 2.7 | 38.1 | floor |
| p4_bq_direct | 0 | 29% | -- | -- | 38 | 5.3 | 47.7 | service only |
| p4_bq_direct | 1 | 98% | -- | -- | 10 | 1.1 | 11.6 | service only |
| p4_bq_direct_ctx | 0 | 31% | -- | -- | 39 | 6.0 | 54.3 | service only |
| p4_bq_direct_ctx | 1 | 98% | -- | -- | 10 | 1.1 | 11.4 | service only |

**Do not sort this table by the cost columns.** `p4_bq_ca`, `p4_bq_direct`, `p4_bq_direct_ctx`, `p4_looker_ca` carry `floor` coverage: they spend model tokens server-side that the API never reports, so their figures are lower bounds and every other arm's are totals. Comparing them directly compares two different quantities. The gap is not small — `make service-tokens` meters `p4_looker_ca` from Cloud Monitoring at 392,158 tokens per cell against the 18,045 recorded here, a 22x understatement that moves it from the cheapest arm to the third most expensive. The floors are left uncorrected in the table on purpose: the meter attributes by time block, not per cell, and splitting a block across cells that vary in turn count would invent a distribution. Two honest numbers in two places beat one fused number that hides which half was inferred.

Accuracy, latency and the BigQuery columns are unaffected — those are measured client-side for every arm.

## Capture health

| config | tier | attempted | scored | failed | quota-retried | CA leak |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 60 | 60 | 0 | 8 | 0% |
| p1_managed | 1 | 60 | 60 | 0 | 1 | 0% |
| p1_toolbox | 0 | 60 | 60 | 0 | 5 | 57% |
| p1_toolbox | 1 | 60 | 60 | 0 | 4 | 32% |
| p2_managed | 0 | 60 | 60 | 0 | 5 | 0% |
| p2_managed | 1 | 60 | 60 | 0 | 4 | 0% |
| p2_toolbox | 0 | 60 | 60 | 0 | 4 | 0% |
| p2_toolbox | 1 | 60 | 60 | 0 | 0 | 0% |
| p3_managed | 0 | 60 | 60 | 0 | 8 | 0% |
| p3_managed | 1 | 60 | 60 | 0 | 2 | 0% |
| p3_toolbox | 0 | 60 | 60 | 0 | 2 | 65% |
| p3_toolbox | 1 | 60 | 60 | 0 | 0 | 30% |
| p1_matched | 0 | 60 | 60 | 0 | 1 | 0% |
| p1_matched | 1 | 60 | 60 | 0 | 1 | 0% |
| p3_matched | 0 | 60 | 60 | 0 | 10 | 0% |
| p3_matched | 1 | 60 | 60 | 0 | 14 | 0% |
| p4_bq_ca | 0 | 60 | 60 | 0 | 7 | 0% |
| p4_bq_ca | 1 | 60 | 60 | 0 | 0 | 0% |
| p4_looker_ca | 0 | 60 | 60 | 0 | 0 | 0% |
| p4_looker_ca | 1 | 60 | 60 | 0 | 0 | 0% |
| p4_bq_direct | 0 | 60 | 60 | 0 | 0 | 0% |
| p4_bq_direct | 1 | 60 | 60 | 0 | 0 | 0% |
| p4_bq_direct_ctx | 0 | 60 | 60 | 0 | 0 | 0% |
| p4_bq_direct_ctx | 1 | 60 | 60 | 0 | 0 | 0% |

**CA leak** is not a bug in the run — it is a property of the surface being measured. `ask_data_insights` ships inside the Toolbox BigQuery toolset, so `p1_toolbox` and `p3_toolbox` can reach Conversational Analytics and become Path 4 for that cell. The arms are reported as shipped rather than trimmed to be hermetic, so this column says how often it happened instead of hiding it.

## Accuracy

| config | tier | n | graded | correct | sprang trap | used decoy |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 60 | 45 | 49% | 33% | 50% |
| p1_managed | 1 | 60 | 45 | 89% | 8% | 30% |
| p1_toolbox | 0 | 60 | 45 | 44% | 18% | 50% |
| p1_toolbox | 1 | 60 | 45 | 100% | 0% | 13% |
| p2_managed | 0 | 60 | 45 | 44% | 33% | 50% |
| p2_managed | 1 | 60 | 45 | 98% | 0% | 0% |
| p2_toolbox | 0 | 60 | 45 | 42% | 32% | 50% |
| p2_toolbox | 1 | 60 | 45 | 100% | 0% | 2% |
| p3_managed | 0 | 60 | 45 | 47% | 33% | 50% |
| p3_managed | 1 | 60 | 45 | 100% | 0% | 18% |
| p3_toolbox | 0 | 60 | 45 | 44% | 12% | 50% |
| p3_toolbox | 1 | 60 | 45 | 100% | 0% | 5% |
| p1_matched | 0 | 60 | 45 | 47% | 33% | 50% |
| p1_matched | 1 | 60 | 45 | 89% | 8% | 18% |
| p3_matched | 0 | 60 | 45 | 47% | 33% | 50% |
| p3_matched | 1 | 60 | 45 | 100% | 0% | 12% |
| p4_bq_ca | 0 | 60 | 45 | 31% | 8% | 50% |
| p4_bq_ca | 1 | 60 | 45 | 100% | 0% | 7% |
| p4_looker_ca | 0 | 60 | 45 | 16% | 5% | 17% |
| p4_looker_ca | 1 | 60 | 45 | 47% | 0% | 3% |
| p4_bq_direct | 0 | 60 | 45 | 29% | 10% | 50% |
| p4_bq_direct | 1 | 60 | 45 | 98% | 0% | 0% |
| p4_bq_direct_ctx | 0 | 60 | 45 | 31% | 8% | 50% |
| p4_bq_direct_ctx | 1 | 60 | 45 | 98% | 0% | 0% |

**360 of 1440 cells are excluded from every rate above.** 3 of the battery's questions are worded so that two answers are equally defensible, which makes the oracle an arbiter of a coin-flip rather than a grader. The cells ran, are in the capture, and carry a `correct` a reader can inspect — they are *unmeasured*, not zero, the same way an opaque path's evidence reads `--`.

* `governed-q1` — The governed rule defines Active as "had an event in the trailing 30 days", which pins the window's length but not its anchor. The answer is a count - extensive, so the two defensible anchorings differ by more than the 0.5% tolerance. See semantic-q2.
* `governed-q3` — Inherits the Active definition's unpinned anchor from governed-q1, and sums over it. The answer is an extensive quantity twice over - which users count, and how much they spent - so the two defensible anchorings diverge well past the 0.5% tolerance. See semantic-q2.
* `semantic-q2` — "trailing 30 days" pins the window's length but not its anchor. Anchoring to the data's latest timestamp is as defensible as anchoring to now, and agents pick between them nondeterministically at temperature 0 - the same arm answered 2,699 and 2,804 in consecutive runs. The answer is an extensive quantity (a sum), so the two readings differ by more than the 0.5% tolerance and the oracle arbitrates a coin-flip.

## Acquisition vs application

| config | tier | n | opaque | acquired | application loss |
|---|---|---|---|---|---|
| p1_managed | 0 | 35 | 0% | 0% | 0% |
| p1_managed | 1 | 35 | 0% | 100% | 14% |
| p1_toolbox | 0 | 35 | 0% | 0% | 0% |
| p1_toolbox | 1 | 35 | 0% | 100% | 0% |
| p2_managed | 0 | 35 | 0% | 0% | 0% |
| p2_managed | 1 | 35 | 0% | 100% | 3% |
| p2_toolbox | 0 | 35 | 0% | 0% | 0% |
| p2_toolbox | 1 | 35 | 0% | 100% | 0% |
| p3_managed | 0 | 35 | 0% | 0% | 0% |
| p3_managed | 1 | 35 | 0% | 100% | 0% |
| p3_toolbox | 0 | 35 | 0% | 0% | 0% |
| p3_toolbox | 1 | 35 | 0% | 100% | 0% |
| p1_matched | 0 | 35 | 0% | 0% | 0% |
| p1_matched | 1 | 35 | 0% | 100% | 14% |
| p3_matched | 0 | 35 | 0% | 0% | 0% |
| p3_matched | 1 | 35 | 0% | 100% | 0% |
| p4_bq_ca | 0 | 35 | 100% | -- | -- |
| p4_bq_ca | 1 | 35 | 100% | -- | -- |
| p4_looker_ca | 0 | 35 | 100% | -- | -- |
| p4_looker_ca | 1 | 35 | 100% | -- | -- |
| p4_bq_direct | 0 | 35 | 100% | -- | -- |
| p4_bq_direct | 1 | 35 | 100% | -- | -- |
| p4_bq_direct_ctx | 0 | 35 | 100% | -- | -- |
| p4_bq_direct_ctx | 1 | 35 | 100% | -- | -- |

## Evidence

| config | tier | no query disclosed | recall (median) | IQR | precision |
|---|---|---|---|---|---|
| p1_managed | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p1_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p1_toolbox | 0 | 0% | 1.00 | 0.20 | 0.90 |
| p1_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p2_managed | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p2_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p2_toolbox | 0 | 0% | 1.00 | 0.20 | 0.90 |
| p2_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_managed | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p3_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_toolbox | 0 | 0% | 1.00 | 0.20 | 0.90 |
| p3_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p1_matched | 0 | 0% | 1.00 | 0.15 | 0.90 |
| p1_matched | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_matched | 0 | 0% | 1.00 | 0.15 | 0.90 |
| p3_matched | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p4_bq_ca | 0 | 0% | 1.00 | 0.33 | 0.92 |
| p4_bq_ca | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p4_looker_ca | 0 | 42% | 0.40 | 1.00 | 1.00 |
| p4_looker_ca | 1 | 38% | 1.00 | 0.60 | 1.00 |
| p4_bq_direct | 0 | 0% | 0.67 | 0.60 | 0.83 |
| p4_bq_direct | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p4_bq_direct_ctx | 0 | 0% | 0.67 | 0.60 | 0.88 |
| p4_bq_direct_ctx | 1 | 0% | 1.00 | 0.00 | 1.00 |

## Latency

| config | tier | clean cells | excluded | median s | IQR | tool calls |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 52 | 8 | 76.7 | 110.0 | 16.5 |
| p1_managed | 1 | 59 | 1 | 35.1 | 74.6 | 7.0 |
| p1_toolbox | 0 | 55 | 5 | 64.3 | 62.3 | 13.0 |
| p1_toolbox | 1 | 56 | 4 | 35.2 | 57.0 | 6.0 |
| p2_managed | 0 | 55 | 5 | 76.1 | 69.7 | 14.0 |
| p2_managed | 1 | 56 | 4 | 38.5 | 19.1 | 7.0 |
| p2_toolbox | 0 | 56 | 4 | 64.0 | 72.2 | 15.0 |
| p2_toolbox | 1 | 60 | 0 | 33.3 | 17.7 | 7.0 |
| p3_managed | 0 | 52 | 8 | 96.4 | 127.4 | 19.0 |
| p3_managed | 1 | 58 | 2 | 37.6 | 68.5 | 7.0 |
| p3_toolbox | 0 | 58 | 2 | 82.3 | 83.0 | 17.0 |
| p3_toolbox | 1 | 60 | 0 | 39.8 | 55.5 | 7.0 |
| p1_matched | 0 | 59 | 1 | 71.9 | 71.9 | 14.0 |
| p1_matched | 1 | 59 | 1 | 29.1 | 60.8 | 7.0 |
| p3_matched | 0 | 50 | 10 | 89.7 | 102.6 | 18.5 |
| p3_matched | 1 | 46 | 14 | 32.3 | 60.7 | 5.0 |
| p4_bq_ca | 0 | 53 | 7 | 62.4 | 45.1 | 3.0 |
| p4_bq_ca | 1 | 60 | 0 | 32.8 | 23.7 | 2.0 |
| p4_looker_ca | 0 | 60 | 0 | 146.0 | 86.8 | 2.0 |
| p4_looker_ca | 1 | 60 | 0 | 59.4 | 58.5 | 1.0 |
| p4_bq_direct | 0 | 60 | 0 | 10.0 | 5.2 | 0.0 |
| p4_bq_direct | 1 | 60 | 0 | 10.3 | 5.1 | 0.0 |
| p4_bq_direct_ctx | 0 | 60 | 0 | 10.1 | 5.6 | 0.0 |
| p4_bq_direct_ctx | 1 | 60 | 0 | 10.3 | 3.8 | 0.0 |

## Cost

| config | tier | tokens (median) | IQR | thoughts | MiB billed | USD (mean) | unmeasured spend |
|---|---|---|---|---|---|---|---|
| p1_managed | 0 | 554528 | 711770 | 2656 | 90.0 | 0.00065 | full |
| p1_managed | 1 | 198442 | 499559 | 810 | 45.0 | 0.00054 | full |
| p1_toolbox | 0 | 79841 | 91597 | 1256 | 60.0 | 0.00042 | full |
| p1_toolbox | 1 | 25620 | 45005 | 728 | 40.0 | 0.00029 | full |
| p2_managed | 0 | 79744 | 101420 | 1483 | 60.0 | 0.00045 | full |
| p2_managed | 1 | 32313 | 23668 | 536 | 30.0 | 0.00024 | full |
| p2_toolbox | 0 | 71362 | 143814 | 1928 | 40.0 | 0.00036 | full |
| p2_toolbox | 1 | 24894 | 29766 | 618 | 20.0 | 0.00022 | full |
| p3_managed | 0 | 930883 | 1310283 | 3213 | 85.0 | 0.00067 | full |
| p3_managed | 1 | 265727 | 635084 | 811 | 35.0 | 0.00034 | full |
| p3_toolbox | 0 | 193550 | 210747 | 1608 | 70.0 | 0.00045 | full |
| p3_toolbox | 1 | 54732 | 120618 | 864 | 30.0 | 0.00031 | full |
| p1_matched | 0 | 78004 | 154936 | 1925 | 60.0 | 0.00048 | full |
| p1_matched | 1 | 22884 | 78885 | 674 | 40.0 | 0.00046 | full |
| p3_matched | 0 | 207233 | 397270 | 2208 | 65.0 | 0.00054 | full |
| p3_matched | 1 | 34490 | 115438 | 729 | 30.0 | 0.00030 | full |
| p4_bq_ca | 0 | 8867 | 13246 | 353 | 25.0 | 0.00022 | floor |
| p4_bq_ca | 1 | 4634 | 4974 | 332 | 20.0 | 0.00016 | floor |
| p4_looker_ca | 0 | 16829 | 19376 | 267 | 20.0 | 0.00016 | floor |
| p4_looker_ca | 1 | 4228 | 6609 | 230 | 10.0 | 0.00010 | floor |
| p4_bq_direct | 0 | -- | -- | -- | 10.0 | 0.00008 | service only |
| p4_bq_direct | 1 | -- | -- | -- | 10.0 | 0.00010 | service only |
| p4_bq_direct_ctx | 0 | -- | -- | -- | 10.0 | 0.00009 | service only |
| p4_bq_direct_ctx | 1 | -- | -- | -- | 10.0 | 0.00008 | service only |

Prices: cloud.google.com/bigquery/pricing, US multi-region on-demand list price (verified 2026-09-03). Token rates are unset unless a `prices.json` supplies them, so a `--` in the USD column means *unpriced*, not free. Dollars are the only derived number in this report and the only one that depends on a rate card, which is why every other column is in units consumed.

The last column is how complete the picture is. **full** means everything this sweep spent, it saw. **floor** means the arm also spent model tokens server-side that the API never reported back — Conversational Analytics runs its own Gemini loop on our behalf. A floor is a lower bound, not a total, and it is not small: `make service-tokens` meters it from Cloud Monitoring and finds `p4_looker_ca` consumed 22x the tokens recorded here. **service only** means the arm never called a model in this process at all — the direct-API arms hand the question to the service and read back an answer — so its token columns read `--`. That is absent, not free; the model spend is entirely on the meter this report cannot see.

## Semantic adherence (judged)

| config | tier | n | governed | partial | invented | unclear |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 50 | 10% | 34% | 56% | 0% |
| p1_managed | 1 | 50 | 50% | 50% | 0% | 0% |
| p1_toolbox | 0 | 50 | 10% | 20% | 70% | 0% |
| p1_toolbox | 1 | 50 | 80% | 20% | 0% | 0% |
| p2_managed | 0 | 50 | 10% | 32% | 58% | 0% |
| p2_managed | 1 | 50 | 80% | 20% | 0% | 0% |
| p2_toolbox | 0 | 50 | 8% | 30% | 62% | 0% |
| p2_toolbox | 1 | 50 | 80% | 20% | 0% | 0% |
| p3_managed | 0 | 50 | 10% | 32% | 58% | 0% |
| p3_managed | 1 | 50 | 80% | 20% | 0% | 0% |
| p3_toolbox | 0 | 50 | 10% | 18% | 72% | 0% |
| p3_toolbox | 1 | 50 | 80% | 20% | 0% | 0% |
| p1_matched | 0 | 50 | 10% | 32% | 58% | 0% |
| p1_matched | 1 | 50 | 50% | 46% | 4% | 0% |
| p3_matched | 0 | 50 | 10% | 30% | 60% | 0% |
| p3_matched | 1 | 50 | 80% | 20% | 0% | 0% |
| p4_bq_ca | 0 | 50 | 2% | 16% | 82% | 0% |
| p4_bq_ca | 1 | 50 | 80% | 20% | 0% | 0% |
| p4_looker_ca | 0 | 50 | 0% | 14% | 58% | 28% |
| p4_looker_ca | 1 | 50 | 30% | 26% | 2% | 42% |
| p4_bq_direct | 0 | 50 | 2% | 16% | 82% | 0% |
| p4_bq_direct | 1 | 50 | 82% | 18% | 0% | 0% |
| p4_bq_direct_ctx | 0 | 50 | 4% | 22% | 74% | 0% |
| p4_bq_direct_ctx | 1 | 50 | 80% | 20% | 0% | 0% |

## Equivalence

| config A | config B | pairs | graded | same tool sequence | same value | same verdict |
|---|---|---|---|---|---|---|
| p1_managed | p1_toolbox | 120 | 90 | 0% | 67% | 92% |
| p2_managed | p2_toolbox | 120 | 90 | 7% | 92% | 96% |
| p3_managed | p3_toolbox | 120 | 90 | 0% | 70% | 99% |
| p1_managed | p1_matched | 120 | 90 | 0% | 91% | 99% |
| p3_managed | p3_matched | 120 | 90 | 0% | 88% | 98% |
| p4_bq_ca | p4_looker_ca | 120 | 90 | 0% | 42% | 66% |

## Tool surface

Schemas are re-sent on every turn, so their size is a per-call floor on prompt tokens. Measured live at sweep time, because a vendor can change them without notice.

| config | tools | schema chars |
|---|---|---|
| p3_managed | 8 | 143814 |
| p1_managed | 5 | 120009 |
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
