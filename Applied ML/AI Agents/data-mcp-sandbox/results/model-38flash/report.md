# Results

Model `gemini-3.8-flash` at temperature 0.0, 3 replicates, tier fence on, commit `46a646d4`, started 2026-09-12T14:26:22+00:00. Dataplex quality scans: present.


720 cells scored across 20 arm/tier pairs.

## Headline

| config | tier | accuracy (mean) | tokens in / correct | tokens out / correct | sec / correct | BQ jobs / correct | MiB / correct | coverage |
|---|---|---|---|---|---|---|---|---|
| p1_managed | 0 | 44% | 3988276 | 8102 | 524 | 57.0 | 572.5 | full |
| p1_managed | 1 | 93% | 500271 | 1534 | 70 | 8.2 | 95.2 | full |
| p1_toolbox | 0 | 41% | 686312 | 4829 | 348 | 47.3 | 438.2 | full |
| p1_toolbox | 1 | 100% | 40012 | 902 | 40 | 4.2 | 52.6 | full |
| p2_managed | 0 | 56% | 814736 | 5060 | 388 | 34.9 | 356.7 | full |
| p2_managed | 1 | 100% | 68328 | 947 | 50 | 4.4 | 62.2 | full |
| p2_toolbox | 0 | 52% | 708058 | 5397 | 420 | 34.4 | 268.6 | full |
| p2_toolbox | 1 | 100% | 59787 | 909 | 49 | 4.3 | 49.6 | full |
| p3_managed | 0 | 44% | 6758475 | 9510 | 627 | 54.1 | 539.2 | full |
| p3_managed | 1 | 100% | 537456 | 1507 | 73 | 4.9 | 66.3 | full |
| p3_toolbox | 0 | 44% | 1636452 | 5277 | 437 | 42.9 | 390.8 | full |
| p3_toolbox | 1 | 100% | 93628 | 932 | 44 | 3.9 | 50.4 | full |
| p1_matched | 0 | 44% | 1092446 | 5682 | 450 | 51.2 | 464.2 | full |
| p1_matched | 1 | 89% | 90593 | 1152 | 69 | 7.7 | 82.1 | full |
| p3_matched | 0 | 44% | 2832892 | 7216 | 512 | 52.8 | 470.0 | full |
| p3_matched | 1 | 100% | 118638 | 1174 | 67 | 4.3 | 55.2 | full |
| p4_bq_ca | 0 | 37% | 473717 | 4397 | 526 | 33.6 | 349.0 | floor |
| p4_bq_ca | 1 | 100% | 7454 | 477 | 37 | 1.9 | 23.0 | floor |
| p4_looker_ca | 0 | 15% | 1520034 | 6197 | 3107 | 68.5 | 810.0 | floor |
| p4_looker_ca | 1 | 56% | 97530 | 917 | 414 | 10.0 | 182.0 | floor |

**Do not sort this table by the cost columns.** `p4_bq_ca`, `p4_looker_ca` carry `floor` coverage: they spend model tokens server-side that the API never reports, so their figures are lower bounds and every other arm's are totals. Comparing them directly compares two different quantities. The gap is not small — `make service-tokens` meters `p4_looker_ca` from Cloud Monitoring at 392,158 tokens per cell against the 18,045 recorded here, a 22x understatement that moves it from the cheapest arm to the third most expensive. The floors are left uncorrected in the table on purpose: the meter attributes by time block, not per cell, and splitting a block across cells that vary in turn count would invent a distribution. Two honest numbers in two places beat one fused number that hides which half was inferred.

Accuracy, latency and the BigQuery columns are unaffected — those are measured client-side for every arm.

## Capture health

| config | tier | attempted | scored | failed | quota-retried | CA leak |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 36 | 36 | 0 | 1 | 0% |
| p1_managed | 1 | 36 | 36 | 0 | 0 | 0% |
| p1_toolbox | 0 | 36 | 36 | 0 | 0 | 67% |
| p1_toolbox | 1 | 36 | 36 | 0 | 0 | 39% |
| p2_managed | 0 | 36 | 36 | 0 | 0 | 0% |
| p2_managed | 1 | 36 | 36 | 0 | 0 | 0% |
| p2_toolbox | 0 | 36 | 36 | 0 | 0 | 0% |
| p2_toolbox | 1 | 36 | 36 | 0 | 0 | 0% |
| p3_managed | 0 | 36 | 36 | 0 | 6 | 0% |
| p3_managed | 1 | 36 | 36 | 0 | 0 | 0% |
| p3_toolbox | 0 | 36 | 36 | 0 | 0 | 75% |
| p3_toolbox | 1 | 36 | 36 | 0 | 0 | 36% |
| p1_matched | 0 | 36 | 36 | 0 | 0 | 0% |
| p1_matched | 1 | 36 | 36 | 0 | 1 | 0% |
| p3_matched | 0 | 36 | 36 | 0 | 1 | 0% |
| p3_matched | 1 | 36 | 36 | 0 | 0 | 0% |
| p4_bq_ca | 0 | 36 | 36 | 0 | 0 | 0% |
| p4_bq_ca | 1 | 36 | 36 | 0 | 0 | 0% |
| p4_looker_ca | 0 | 36 | 36 | 0 | 0 | 0% |
| p4_looker_ca | 1 | 36 | 36 | 0 | 0 | 0% |

**CA leak** is not a bug in the run — it is a property of the surface being measured. `ask_data_insights` ships inside the Toolbox BigQuery toolset, so `p1_toolbox` and `p3_toolbox` can reach Conversational Analytics and become Path 4 for that cell. The arms are reported as shipped rather than trimmed to be hermetic, so this column says how often it happened instead of hiding it.

## Accuracy

| config | tier | n | graded | correct | sprang trap | used decoy |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 36 | 27 | 44% | 33% | 50% |
| p1_managed | 1 | 36 | 27 | 93% | 6% | 44% |
| p1_toolbox | 0 | 36 | 27 | 41% | 17% | 50% |
| p1_toolbox | 1 | 36 | 27 | 100% | 0% | 19% |
| p2_managed | 0 | 36 | 27 | 56% | 28% | 50% |
| p2_managed | 1 | 36 | 27 | 100% | 0% | 6% |
| p2_toolbox | 0 | 36 | 27 | 52% | 28% | 50% |
| p2_toolbox | 1 | 36 | 27 | 100% | 0% | 6% |
| p3_managed | 0 | 36 | 27 | 44% | 28% | 50% |
| p3_managed | 1 | 36 | 27 | 100% | 0% | 31% |
| p3_toolbox | 0 | 36 | 27 | 44% | 11% | 50% |
| p3_toolbox | 1 | 36 | 27 | 100% | 0% | 19% |
| p1_matched | 0 | 36 | 27 | 44% | 33% | 50% |
| p1_matched | 1 | 36 | 27 | 89% | 17% | 42% |
| p3_matched | 0 | 36 | 27 | 44% | 31% | 50% |
| p3_matched | 1 | 36 | 27 | 100% | 0% | 33% |
| p4_bq_ca | 0 | 36 | 27 | 37% | 22% | 50% |
| p4_bq_ca | 1 | 36 | 27 | 100% | 0% | 6% |
| p4_looker_ca | 0 | 36 | 27 | 15% | 3% | 42% |
| p4_looker_ca | 1 | 36 | 27 | 56% | 0% | 11% |

**180 of 720 cells are excluded from every rate above.** 3 of the battery's questions are worded so that two answers are equally defensible, which makes the oracle an arbiter of a coin-flip rather than a grader. The cells ran, are in the capture, and carry a `correct` a reader can inspect — they are *unmeasured*, not zero, the same way an opaque path's evidence reads `--`.

* `governed-q1` — The governed rule defines Active as "had an event in the trailing 30 days", which pins the window's length but not its anchor. The answer is a count - extensive, so the two defensible anchorings differ by more than the 0.5% tolerance. See semantic-q2.
* `governed-q3` — Inherits the Active definition's unpinned anchor from governed-q1, and sums over it. The answer is an extensive quantity twice over - which users count, and how much they spent - so the two defensible anchorings diverge well past the 0.5% tolerance. See semantic-q2.
* `semantic-q2` — "trailing 30 days" pins the window's length but not its anchor. Anchoring to the data's latest timestamp is as defensible as anchoring to now, and agents pick between them nondeterministically at temperature 0 - the same arm answered 2,699 and 2,804 in consecutive runs. The answer is an extensive quantity (a sum), so the two readings differ by more than the 0.5% tolerance and the oracle arbitrates a coin-flip.

## Acquisition vs application

| config | tier | n | opaque | acquired | application loss |
|---|---|---|---|---|---|
| p1_managed | 0 | 21 | 0% | 0% | 0% |
| p1_managed | 1 | 21 | 0% | 100% | 10% |
| p1_toolbox | 0 | 21 | 0% | 0% | 0% |
| p1_toolbox | 1 | 21 | 0% | 100% | 0% |
| p2_managed | 0 | 21 | 0% | 0% | 0% |
| p2_managed | 1 | 21 | 0% | 100% | 0% |
| p2_toolbox | 0 | 21 | 0% | 0% | 0% |
| p2_toolbox | 1 | 21 | 0% | 100% | 0% |
| p3_managed | 0 | 21 | 0% | 0% | 0% |
| p3_managed | 1 | 21 | 0% | 100% | 0% |
| p3_toolbox | 0 | 21 | 0% | 0% | 0% |
| p3_toolbox | 1 | 21 | 0% | 100% | 0% |
| p1_matched | 0 | 21 | 0% | 0% | 0% |
| p1_matched | 1 | 21 | 0% | 100% | 14% |
| p3_matched | 0 | 21 | 0% | 0% | 0% |
| p3_matched | 1 | 21 | 0% | 100% | 0% |
| p4_bq_ca | 0 | 21 | 100% | -- | -- |
| p4_bq_ca | 1 | 21 | 100% | -- | -- |
| p4_looker_ca | 0 | 21 | 100% | -- | -- |
| p4_looker_ca | 1 | 21 | 100% | -- | -- |

## Evidence

| config | tier | no query disclosed | recall (median) | IQR | precision |
|---|---|---|---|---|---|
| p1_managed | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p1_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p1_toolbox | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p1_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p2_managed | 0 | 0% | 1.00 | 0.15 | 0.90 |
| p2_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p2_toolbox | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p2_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_managed | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p3_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_toolbox | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p3_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p1_matched | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p1_matched | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_matched | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p3_matched | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p4_bq_ca | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p4_bq_ca | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p4_looker_ca | 0 | 14% | 0.67 | 0.60 | 0.75 |
| p4_looker_ca | 1 | 19% | 1.00 | 0.33 | 1.00 |

## Latency

| config | tier | clean cells | excluded | median s | IQR | tool calls |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 35 | 1 | 258.3 | 271.4 | 33.0 |
| p1_managed | 1 | 36 | 0 | 40.3 | 171.7 | 10.0 |
| p1_toolbox | 0 | 36 | 0 | 132.6 | 135.4 | 22.5 |
| p1_toolbox | 1 | 36 | 0 | 33.4 | 67.0 | 8.0 |
| p2_managed | 0 | 36 | 0 | 197.1 | 211.4 | 30.0 |
| p2_managed | 1 | 36 | 0 | 38.7 | 43.8 | 9.0 |
| p2_toolbox | 0 | 36 | 0 | 176.8 | 193.4 | 30.0 |
| p2_toolbox | 1 | 36 | 0 | 47.3 | 34.1 | 9.5 |
| p3_managed | 0 | 30 | 6 | 274.9 | 353.5 | 48.5 |
| p3_managed | 1 | 36 | 0 | 60.3 | 179.6 | 10.5 |
| p3_toolbox | 0 | 36 | 0 | 197.1 | 214.5 | 36.0 |
| p3_toolbox | 1 | 36 | 0 | 44.7 | 64.0 | 9.0 |
| p1_matched | 0 | 36 | 0 | 177.6 | 270.4 | 26.0 |
| p1_matched | 1 | 35 | 1 | 31.5 | 151.4 | 8.0 |
| p3_matched | 0 | 35 | 1 | 223.4 | 301.3 | 44.0 |
| p3_matched | 1 | 36 | 0 | 55.9 | 126.3 | 8.0 |
| p4_bq_ca | 0 | 36 | 0 | 125.4 | 311.1 | 8.0 |
| p4_bq_ca | 1 | 36 | 0 | 37.5 | 50.1 | 2.5 |
| p4_looker_ca | 0 | 36 | 0 | 379.0 | 693.9 | 7.0 |
| p4_looker_ca | 1 | 36 | 0 | 84.6 | 143.8 | 2.0 |

## Cost

| config | tier | tokens (median) | IQR | thoughts | MiB billed | USD (mean) | unmeasured spend |
|---|---|---|---|---|---|---|---|
| p1_managed | 0 | 1645587 | 2162794 | 17526 | 280.0 | 0.00154 | full |
| p1_managed | 1 | 269716 | 1301142 | 1978 | 60.0 | 0.00084 | full |
| p1_toolbox | 0 | 208460 | 407684 | 4876 | 165.0 | 0.00103 | full |
| p1_toolbox | 1 | 40938 | 77106 | 1132 | 55.0 | 0.00042 | full |
| p2_managed | 0 | 385038 | 567229 | 12557 | 160.0 | 0.00116 | full |
| p2_managed | 1 | 47155 | 63206 | 1162 | 50.0 | 0.00039 | full |
| p2_toolbox | 0 | 320548 | 508733 | 11901 | 100.0 | 0.00079 | full |
| p2_toolbox | 1 | 36196 | 49124 | 1224 | 45.0 | 0.00034 | full |
| p3_managed | 0 | 3547610 | 4067554 | 19204 | 260.0 | 0.00148 | full |
| p3_managed | 1 | 484822 | 1459621 | 2598 | 60.0 | 0.00058 | full |
| p3_toolbox | 0 | 637213 | 1065248 | 6592 | 155.0 | 0.00105 | full |
| p3_toolbox | 1 | 83706 | 209696 | 1661 | 50.0 | 0.00041 | full |
| p1_matched | 0 | 253490 | 869246 | 6818 | 145.0 | 0.00125 | full |
| p1_matched | 1 | 32528 | 393430 | 1158 | 50.0 | 0.00075 | full |
| p3_matched | 0 | 1135388 | 1851969 | 13062 | 195.0 | 0.00126 | full |
| p3_matched | 1 | 48637 | 471072 | 1334 | 50.0 | 0.00053 | full |
| p4_bq_ca | 0 | 50422 | 308684 | 2028 | 110.0 | 0.00074 | floor |
| p4_bq_ca | 1 | 7946 | 19111 | 516 | 20.0 | 0.00025 | floor |
| p4_looker_ca | 0 | 105884 | 381254 | 2132 | 75.0 | 0.00073 | floor |
| p4_looker_ca | 1 | 8676 | 19277 | 490 | 20.0 | 0.00055 | floor |

Prices: cloud.google.com/bigquery/pricing, US multi-region on-demand list price (verified 2026-09-03). Token rates are unset unless a `prices.json` supplies them, so a `--` in the USD column means *unpriced*, not free. Dollars are the only derived number in this report and the only one that depends on a rate card, which is why every other column is in units consumed.

The last column is how complete the picture is. **full** means everything this sweep spent, it saw. **floor** means the arm also spent model tokens server-side that the API never reported back — Conversational Analytics runs its own Gemini loop on our behalf. A floor is a lower bound, not a total, and it is not small: `make service-tokens` meters it from Cloud Monitoring and finds `p4_looker_ca` consumed 22x the tokens recorded here.

## Semantic adherence (judged)

| config | tier | n | governed | partial | invented | unclear |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 30 | 10% | 30% | 60% | 0% |
| p1_managed | 1 | 30 | 50% | 47% | 3% | 0% |
| p1_toolbox | 0 | 30 | 7% | 20% | 73% | 0% |
| p1_toolbox | 1 | 30 | 80% | 20% | 0% | 0% |
| p2_managed | 0 | 30 | 10% | 27% | 63% | 0% |
| p2_managed | 1 | 30 | 80% | 20% | 0% | 0% |
| p2_toolbox | 0 | 30 | 10% | 30% | 60% | 0% |
| p2_toolbox | 1 | 30 | 80% | 20% | 0% | 0% |
| p3_managed | 0 | 30 | 10% | 30% | 60% | 0% |
| p3_managed | 1 | 30 | 80% | 20% | 0% | 0% |
| p3_toolbox | 0 | 30 | 10% | 20% | 70% | 0% |
| p3_toolbox | 1 | 30 | 80% | 20% | 0% | 0% |
| p1_matched | 0 | 30 | 10% | 30% | 60% | 0% |
| p1_matched | 1 | 30 | 50% | 43% | 7% | 0% |
| p3_matched | 0 | 30 | 10% | 33% | 57% | 0% |
| p3_matched | 1 | 30 | 80% | 20% | 0% | 0% |
| p4_bq_ca | 0 | 30 | 3% | 23% | 73% | 0% |
| p4_bq_ca | 1 | 30 | 80% | 20% | 0% | 0% |
| p4_looker_ca | 0 | 30 | 0% | 17% | 80% | 3% |
| p4_looker_ca | 1 | 30 | 50% | 20% | 7% | 23% |

## Equivalence

| config A | config B | pairs | graded | same tool sequence | same value | same verdict |
|---|---|---|---|---|---|---|
| p1_managed | p1_toolbox | 72 | 54 | 0% | 68% | 94% |
| p2_managed | p2_toolbox | 72 | 54 | 0% | 88% | 98% |
| p3_managed | p3_toolbox | 72 | 54 | 0% | 81% | 100% |
| p1_managed | p1_matched | 72 | 54 | 0% | 90% | 98% |
| p3_managed | p3_matched | 72 | 54 | 0% | 82% | 100% |
| p4_bq_ca | p4_looker_ca | 72 | 54 | 0% | 39% | 67% |

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
