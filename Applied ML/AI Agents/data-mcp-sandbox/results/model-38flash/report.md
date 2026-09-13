# Results

Model `gemini-3.8-flash` at temperature 0.0, 3 replicates, tier fence on, commit `46a646d4`, started 2026-09-12T14:26:22+00:00. Dataplex quality scans: present.


720 cells scored across 20 arm/tier pairs.

## Headline

| config | tier | accuracy (mean) | tokens in / correct | tokens out / correct | sec / correct | BQ jobs / correct | MiB / correct | coverage |
|---|---|---|---|---|---|---|---|---|
| p1_managed | 0 | 33% | 5357284 | 11270 | 693 | 77.3 | 775.8 | full |
| p1_managed | 1 | 72% | 1102089 | 3024 | 161 | 17.7 | 196.2 | full |
| p1_toolbox | 0 | 31% | 907753 | 6515 | 451 | 61.7 | 566.4 | full |
| p1_toolbox | 1 | 92% | 66279 | 1250 | 63 | 6.3 | 77.3 | full |
| p2_managed | 0 | 42% | 1086981 | 6881 | 502 | 46.0 | 468.0 | full |
| p2_managed | 1 | 92% | 77498 | 1040 | 56 | 4.9 | 71.5 | full |
| p2_toolbox | 0 | 39% | 899962 | 7002 | 521 | 44.0 | 340.0 | full |
| p2_toolbox | 1 | 92% | 62898 | 993 | 55 | 4.8 | 62.1 | full |
| p3_managed | 0 | 33% | 9438139 | 13253 | 846 | 73.9 | 743.3 | full |
| p3_managed | 1 | 89% | 1082190 | 2541 | 131 | 8.4 | 109.4 | full |
| p3_toolbox | 0 | 33% | 2157142 | 7134 | 572 | 56.8 | 526.7 | full |
| p3_toolbox | 1 | 97% | 146161 | 1266 | 61 | 5.3 | 70.3 | full |
| p1_matched | 0 | 33% | 1494722 | 7829 | 615 | 69.7 | 630.0 | full |
| p1_matched | 1 | 67% | 248427 | 2372 | 142 | 17.5 | 188.3 | full |
| p3_matched | 0 | 33% | 3836008 | 9876 | 696 | 72.5 | 631.7 | full |
| p3_matched | 1 | 75% | 370177 | 2351 | 128 | 9.7 | 118.5 | full |
| p4_bq_ca | 0 | 28% | 628224 | 5808 | 723 | 42.4 | 448.0 | floor |
| p4_bq_ca | 1 | 75% | 24181 | 981 | 77 | 4.0 | 55.2 | floor |
| p4_looker_ca | 0 | 11% | 2036222 | 8135 | 4189 | 90.8 | 1107.5 | floor |
| p4_looker_ca | 1 | 42% | 105749 | 1099 | 487 | 11.6 | 223.3 | floor |

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

| config | tier | n | correct | sprang trap | used decoy |
|---|---|---|---|---|---|
| p1_managed | 0 | 36 | 33% | 33% | 50% |
| p1_managed | 1 | 36 | 72% | 6% | 44% |
| p1_toolbox | 0 | 36 | 31% | 17% | 50% |
| p1_toolbox | 1 | 36 | 92% | 0% | 19% |
| p2_managed | 0 | 36 | 42% | 28% | 50% |
| p2_managed | 1 | 36 | 92% | 0% | 6% |
| p2_toolbox | 0 | 36 | 39% | 28% | 50% |
| p2_toolbox | 1 | 36 | 92% | 0% | 6% |
| p3_managed | 0 | 36 | 33% | 28% | 50% |
| p3_managed | 1 | 36 | 89% | 0% | 31% |
| p3_toolbox | 0 | 36 | 33% | 11% | 50% |
| p3_toolbox | 1 | 36 | 97% | 0% | 19% |
| p1_matched | 0 | 36 | 33% | 33% | 50% |
| p1_matched | 1 | 36 | 67% | 17% | 42% |
| p3_matched | 0 | 36 | 33% | 31% | 50% |
| p3_matched | 1 | 36 | 75% | 0% | 33% |
| p4_bq_ca | 0 | 36 | 28% | 22% | 50% |
| p4_bq_ca | 1 | 36 | 75% | 0% | 6% |
| p4_looker_ca | 0 | 36 | 11% | 3% | 42% |
| p4_looker_ca | 1 | 36 | 42% | 0% | 11% |

## Acquisition vs application

| config | tier | n | opaque | acquired | application loss |
|---|---|---|---|---|---|
| p1_managed | 0 | 30 | 0% | 0% | 0% |
| p1_managed | 1 | 30 | 0% | 100% | 33% |
| p1_toolbox | 0 | 30 | 0% | 0% | 0% |
| p1_toolbox | 1 | 30 | 0% | 100% | 10% |
| p2_managed | 0 | 30 | 0% | 0% | 0% |
| p2_managed | 1 | 30 | 0% | 100% | 10% |
| p2_toolbox | 0 | 30 | 0% | 0% | 0% |
| p2_toolbox | 1 | 30 | 0% | 100% | 10% |
| p3_managed | 0 | 30 | 0% | 0% | 0% |
| p3_managed | 1 | 30 | 0% | 100% | 13% |
| p3_toolbox | 0 | 30 | 0% | 0% | 0% |
| p3_toolbox | 1 | 30 | 0% | 100% | 3% |
| p1_matched | 0 | 30 | 0% | 0% | 0% |
| p1_matched | 1 | 30 | 0% | 100% | 40% |
| p3_matched | 0 | 30 | 0% | 0% | 0% |
| p3_matched | 1 | 30 | 0% | 100% | 30% |
| p4_bq_ca | 0 | 30 | 100% | -- | -- |
| p4_bq_ca | 1 | 30 | 100% | -- | -- |
| p4_looker_ca | 0 | 30 | 100% | -- | -- |
| p4_looker_ca | 1 | 30 | 100% | -- | -- |

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

## Equivalence

| config A | config B | pairs | same tool sequence | same value | same verdict |
|---|---|---|---|---|---|
| p1_managed | p1_toolbox | 72 | 0% | 68% | 86% |
| p2_managed | p2_toolbox | 72 | 0% | 88% | 99% |
| p3_managed | p3_toolbox | 72 | 0% | 81% | 96% |
| p1_managed | p1_matched | 72 | 0% | 90% | 97% |
| p3_managed | p3_matched | 72 | 0% | 82% | 93% |
| p4_bq_ca | p4_looker_ca | 72 | 0% | 39% | 75% |

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
