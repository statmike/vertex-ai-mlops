# Results

Model `gemini-3.7-flash` at temperature 0.0, 5 replicates, tier fence on, commit `3434d16a`, started 2026-09-08T23:28:04+00:00. Dataplex quality scans: present.


1800 cells scored across 30 arm/tier pairs.

| rung | cell key | increment | carries |
|---|---|---|---|
| 0 | `tier0` | ungoverned control | nothing |
| 1 | `tier2` | + column descriptions | descriptions |
| 2 | `tier3` | + profile scans | descriptions, profiles |
| 3 | `tier4` | + business rules | descriptions, profiles, rules |
| 4 | `tier1` | + glossary, quality scans, LookML — the published governed tier | descriptions, profiles, rules, glossary, quality, lookml |

Rungs are cumulative and the tier integers are append-only, so they are not in rung order — `tier1` is the top rung, not the second. Every table below is sorted by rung.

## Headline

| config | rung | accuracy (mean) | tokens in / correct | tokens out / correct | sec / correct | BQ jobs / correct | MiB / correct | coverage |
|---|---|---|---|---|---|---|---|---|
| p1_managed | 0 | 32% | 2473838 | 7384 | 265 | 43.2 | 406.3 | full |
| p1_managed | 1 | 73% | 600635 | 2120 | 71 | 10.7 | 127.5 | full |
| p1_managed | 2 | 72% | 586753 | 2233 | 76 | 10.6 | 132.1 | full |
| p1_managed | 3 | 75% | 605709 | 2199 | 74 | 9.9 | 120.9 | full |
| p1_managed | 4 | 75% | 612448 | 2208 | 74 | 10.4 | 127.3 | full |
| p3_managed | 0 | 33% | 3725035 | 8289 | 302 | 42.8 | 394.0 | full |
| p3_managed | 1 | 72% | 1264810 | 2690 | 101 | 9.6 | 120.2 | full |
| p3_managed | 2 | 73% | 1284909 | 2494 | 88 | 9.0 | 114.5 | full |
| p3_managed | 3 | 100% | 373814 | 1432 | 42 | 4.1 | 52.7 | full |
| p3_managed | 4 | 100% | 427623 | 1375 | 44 | 4.3 | 53.5 | full |
| p3_toolbox | 0 | 33% | 616624 | 4182 | 253 | 28.8 | 245.5 | full |
| p3_toolbox | 1 | 65% | 153072 | 1462 | 78 | 7.1 | 88.7 | full |
| p3_toolbox | 2 | 67% | 235296 | 1619 | 89 | 7.6 | 90.0 | full |
| p3_toolbox | 3 | 92% | 124237 | 1543 | 59 | 5.4 | 76.2 | full |
| p3_toolbox | 4 | 92% | 101248 | 1180 | 47 | 4.5 | 58.4 | full |
| p1_matched | 0 | 33% | 351277 | 4302 | 184 | 32.3 | 303.5 | full |
| p1_matched | 1 | 73% | 74213 | 1535 | 57 | 8.7 | 105.7 | full |
| p1_matched | 2 | 70% | 93780 | 1614 | 62 | 9.7 | 113.1 | full |
| p1_matched | 3 | 73% | 76936 | 1532 | 59 | 8.8 | 105.9 | full |
| p1_matched | 4 | 75% | 75674 | 1464 | 57 | 8.6 | 107.3 | full |
| p3_matched | 0 | 33% | 908833 | 5802 | 277 | 37.4 | 314.0 | full |
| p3_matched | 1 | 68% | 463353 | 2126 | 105 | 9.1 | 113.4 | full |
| p3_matched | 2 | 68% | 565669 | 2098 | 111 | 8.5 | 102.0 | full |
| p3_matched | 3 | 93% | 89135 | 1459 | 46 | 4.7 | 65.5 | full |
| p3_matched | 4 | 95% | 94119 | 1369 | 43 | 4.8 | 61.4 | full |
| p4_bq_ca | 0 | 20% | 67651 | 3044 | 281 | 17.9 | 179.2 | floor |
| p4_bq_ca | 1 | 67% | 10169 | 750 | 64 | 3.4 | 46.2 | floor |
| p4_bq_ca | 2 | 67% | 8805 | 709 | 57 | 3.0 | 38.0 | floor |
| p4_bq_ca | 3 | 67% | 15638 | 861 | 65 | 3.1 | 41.2 | floor |
| p4_bq_ca | 4 | 92% | 6854 | 547 | 42 | 2.0 | 30.0 | floor |

**Do not sort this table by the cost columns.** `p4_bq_ca` carry `floor` coverage: they spend model tokens server-side that the API never reports, so their figures are lower bounds and every other arm's are totals. Comparing them directly compares two different quantities. The gap is not small — `make service-tokens` meters `p4_looker_ca` from Cloud Monitoring at 392,158 tokens per cell against the 18,045 recorded here, a 22x understatement that moves it from the cheapest arm to the third most expensive. The floors are left uncorrected in the table on purpose: the meter attributes by time block, not per cell, and splitting a block across cells that vary in turn count would invent a distribution. Two honest numbers in two places beat one fused number that hides which half was inferred.

Accuracy, latency and the BigQuery columns are unaffected — those are measured client-side for every arm.

## Capture health

| config | rung | attempted | scored | failed | quota-retried | CA leak |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 60 | 60 | 0 | 0 | 0% |
| p1_managed | 1 | 60 | 60 | 0 | 0 | 0% |
| p1_managed | 2 | 60 | 60 | 0 | 0 | 0% |
| p1_managed | 3 | 60 | 60 | 0 | 0 | 0% |
| p1_managed | 4 | 60 | 60 | 0 | 0 | 0% |
| p3_managed | 0 | 60 | 60 | 0 | 0 | 0% |
| p3_managed | 1 | 60 | 60 | 0 | 0 | 0% |
| p3_managed | 2 | 60 | 60 | 0 | 0 | 0% |
| p3_managed | 3 | 60 | 60 | 0 | 0 | 0% |
| p3_managed | 4 | 60 | 60 | 0 | 0 | 0% |
| p3_toolbox | 0 | 60 | 60 | 0 | 0 | 68% |
| p3_toolbox | 1 | 60 | 60 | 0 | 0 | 33% |
| p3_toolbox | 2 | 60 | 60 | 0 | 0 | 33% |
| p3_toolbox | 3 | 60 | 60 | 0 | 0 | 32% |
| p3_toolbox | 4 | 60 | 60 | 0 | 0 | 27% |
| p1_matched | 0 | 60 | 60 | 0 | 0 | 0% |
| p1_matched | 1 | 60 | 60 | 0 | 0 | 0% |
| p1_matched | 2 | 60 | 60 | 0 | 0 | 0% |
| p1_matched | 3 | 60 | 60 | 0 | 0 | 0% |
| p1_matched | 4 | 60 | 60 | 0 | 0 | 0% |
| p3_matched | 0 | 60 | 60 | 0 | 0 | 0% |
| p3_matched | 1 | 60 | 60 | 0 | 0 | 0% |
| p3_matched | 2 | 60 | 60 | 0 | 0 | 0% |
| p3_matched | 3 | 60 | 60 | 0 | 0 | 0% |
| p3_matched | 4 | 60 | 60 | 0 | 0 | 0% |
| p4_bq_ca | 0 | 60 | 60 | 0 | 0 | 0% |
| p4_bq_ca | 1 | 60 | 60 | 0 | 0 | 0% |
| p4_bq_ca | 2 | 60 | 60 | 0 | 0 | 0% |
| p4_bq_ca | 3 | 60 | 60 | 0 | 0 | 0% |
| p4_bq_ca | 4 | 60 | 60 | 0 | 0 | 0% |

**CA leak** is not a bug in the run — it is a property of the surface being measured. `ask_data_insights` ships inside the Toolbox BigQuery toolset, so `p1_toolbox` and `p3_toolbox` can reach Conversational Analytics and become Path 4 for that cell. The arms are reported as shipped rather than trimmed to be hermetic, so this column says how often it happened instead of hiding it.

## Accuracy

| config | rung | n | correct | sprang trap | used decoy |
|---|---|---|---|---|---|
| p1_managed | 0 | 60 | 32% | 32% | 50% |
| p1_managed | 1 | 60 | 73% | 10% | 35% |
| p1_managed | 2 | 60 | 72% | 8% | 28% |
| p1_managed | 3 | 60 | 75% | 8% | 25% |
| p1_managed | 4 | 60 | 75% | 8% | 30% |
| p3_managed | 0 | 60 | 33% | 30% | 50% |
| p3_managed | 1 | 60 | 72% | 8% | 22% |
| p3_managed | 2 | 60 | 73% | 10% | 20% |
| p3_managed | 3 | 60 | 100% | 0% | 8% |
| p3_managed | 4 | 60 | 100% | 0% | 20% |
| p3_toolbox | 0 | 60 | 33% | 12% | 50% |
| p3_toolbox | 1 | 60 | 65% | 8% | 22% |
| p3_toolbox | 2 | 60 | 67% | 8% | 17% |
| p3_toolbox | 3 | 60 | 92% | 0% | 7% |
| p3_toolbox | 4 | 60 | 92% | 0% | 10% |
| p1_matched | 0 | 60 | 33% | 28% | 50% |
| p1_matched | 1 | 60 | 73% | 8% | 32% |
| p1_matched | 2 | 60 | 70% | 8% | 20% |
| p1_matched | 3 | 60 | 73% | 8% | 28% |
| p1_matched | 4 | 60 | 75% | 8% | 20% |
| p3_matched | 0 | 60 | 33% | 32% | 50% |
| p3_matched | 1 | 60 | 68% | 8% | 23% |
| p3_matched | 2 | 60 | 68% | 8% | 17% |
| p3_matched | 3 | 60 | 93% | 0% | 8% |
| p3_matched | 4 | 60 | 95% | 0% | 13% |
| p4_bq_ca | 0 | 60 | 20% | 8% | 50% |
| p4_bq_ca | 1 | 60 | 67% | 8% | 3% |
| p4_bq_ca | 2 | 60 | 67% | 8% | 8% |
| p4_bq_ca | 3 | 60 | 67% | 10% | 8% |
| p4_bq_ca | 4 | 60 | 92% | 0% | 3% |

## Acquisition vs application

| config | rung | n | opaque | acquired | application loss |
|---|---|---|---|---|---|
| p1_managed | 0 | 50 | 0% | 0% | 0% |
| p1_managed | 1 | 50 | 0% | 100% | 32% |
| p1_managed | 2 | 50 | 0% | 100% | 34% |
| p1_managed | 3 | 50 | 0% | 100% | 30% |
| p1_managed | 4 | 50 | 0% | 100% | 30% |
| p3_managed | 0 | 50 | 0% | 0% | 0% |
| p3_managed | 1 | 50 | 0% | 100% | 34% |
| p3_managed | 2 | 50 | 0% | 100% | 32% |
| p3_managed | 3 | 50 | 0% | 100% | 0% |
| p3_managed | 4 | 50 | 0% | 100% | 0% |
| p3_toolbox | 0 | 50 | 0% | 0% | 0% |
| p3_toolbox | 1 | 50 | 0% | 100% | 42% |
| p3_toolbox | 2 | 50 | 0% | 100% | 40% |
| p3_toolbox | 3 | 50 | 0% | 100% | 10% |
| p3_toolbox | 4 | 50 | 0% | 100% | 10% |
| p1_matched | 0 | 50 | 0% | 0% | 0% |
| p1_matched | 1 | 50 | 0% | 100% | 32% |
| p1_matched | 2 | 50 | 0% | 100% | 36% |
| p1_matched | 3 | 50 | 0% | 100% | 32% |
| p1_matched | 4 | 50 | 0% | 100% | 30% |
| p3_matched | 0 | 50 | 0% | 0% | 0% |
| p3_matched | 1 | 50 | 0% | 100% | 38% |
| p3_matched | 2 | 50 | 0% | 100% | 38% |
| p3_matched | 3 | 50 | 0% | 100% | 8% |
| p3_matched | 4 | 50 | 0% | 100% | 6% |
| p4_bq_ca | 0 | 50 | 100% | -- | -- |
| p4_bq_ca | 1 | 50 | 100% | -- | -- |
| p4_bq_ca | 2 | 50 | 100% | -- | -- |
| p4_bq_ca | 3 | 50 | 100% | -- | -- |
| p4_bq_ca | 4 | 50 | 100% | -- | -- |

## Evidence

| config | rung | no query disclosed | recall (median) | IQR | precision |
|---|---|---|---|---|---|
| p1_managed | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p1_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p1_managed | 2 | 0% | 1.00 | 0.00 | 1.00 |
| p1_managed | 3 | 0% | 1.00 | 0.00 | 1.00 |
| p1_managed | 4 | 0% | 1.00 | 0.00 | 1.00 |
| p3_managed | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p3_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_managed | 2 | 0% | 1.00 | 0.00 | 1.00 |
| p3_managed | 3 | 0% | 1.00 | 0.00 | 1.00 |
| p3_managed | 4 | 0% | 1.00 | 0.00 | 1.00 |
| p3_toolbox | 0 | 0% | 1.00 | 0.20 | 0.92 |
| p3_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_toolbox | 2 | 0% | 1.00 | 0.00 | 1.00 |
| p3_toolbox | 3 | 0% | 1.00 | 0.00 | 1.00 |
| p3_toolbox | 4 | 0% | 1.00 | 0.00 | 1.00 |
| p1_matched | 0 | 0% | 1.00 | 0.15 | 0.90 |
| p1_matched | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p1_matched | 2 | 0% | 1.00 | 0.00 | 1.00 |
| p1_matched | 3 | 0% | 1.00 | 0.00 | 1.00 |
| p1_matched | 4 | 0% | 1.00 | 0.00 | 1.00 |
| p3_matched | 0 | 0% | 1.00 | 0.15 | 0.90 |
| p3_matched | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_matched | 2 | 0% | 1.00 | 0.00 | 1.00 |
| p3_matched | 3 | 0% | 1.00 | 0.00 | 1.00 |
| p3_matched | 4 | 0% | 1.00 | 0.00 | 1.00 |
| p4_bq_ca | 0 | 0% | 1.00 | 0.38 | 0.92 |
| p4_bq_ca | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p4_bq_ca | 2 | 0% | 1.00 | 0.00 | 1.00 |
| p4_bq_ca | 3 | 0% | 1.00 | 0.00 | 1.00 |
| p4_bq_ca | 4 | 0% | 1.00 | 0.00 | 1.00 |

## Latency

| config | rung | clean cells | excluded | median s | IQR | tool calls |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 60 | 0 | 75.9 | 89.7 | 20.5 |
| p1_managed | 1 | 60 | 0 | 34.2 | 55.6 | 8.0 |
| p1_managed | 2 | 60 | 0 | 30.5 | 64.0 | 7.0 |
| p1_managed | 3 | 60 | 0 | 30.8 | 64.3 | 8.0 |
| p1_managed | 4 | 60 | 0 | 32.0 | 54.2 | 8.0 |
| p3_managed | 0 | 60 | 0 | 92.4 | 89.8 | 23.0 |
| p3_managed | 1 | 60 | 0 | 39.2 | 91.2 | 9.0 |
| p3_managed | 2 | 60 | 0 | 36.5 | 72.6 | 8.5 |
| p3_managed | 3 | 60 | 0 | 32.9 | 34.3 | 8.0 |
| p3_managed | 4 | 60 | 0 | 33.8 | 32.1 | 8.0 |
| p3_toolbox | 0 | 60 | 0 | 80.9 | 71.7 | 17.0 |
| p3_toolbox | 1 | 60 | 0 | 37.2 | 58.5 | 8.5 |
| p3_toolbox | 2 | 60 | 0 | 34.2 | 70.9 | 8.0 |
| p3_toolbox | 3 | 60 | 0 | 31.6 | 67.2 | 7.0 |
| p3_toolbox | 4 | 60 | 0 | 29.4 | 53.0 | 6.0 |
| p1_matched | 0 | 60 | 0 | 54.5 | 59.1 | 13.5 |
| p1_matched | 1 | 60 | 0 | 27.4 | 51.1 | 7.0 |
| p1_matched | 2 | 60 | 0 | 26.0 | 59.1 | 7.0 |
| p1_matched | 3 | 60 | 0 | 24.8 | 55.6 | 7.0 |
| p1_matched | 4 | 60 | 0 | 23.7 | 62.3 | 6.5 |
| p3_matched | 0 | 60 | 0 | 77.2 | 87.2 | 20.0 |
| p3_matched | 1 | 60 | 0 | 40.7 | 93.1 | 8.0 |
| p3_matched | 2 | 60 | 0 | 31.0 | 88.8 | 8.0 |
| p3_matched | 3 | 60 | 0 | 29.6 | 51.2 | 7.0 |
| p3_matched | 4 | 60 | 0 | 29.6 | 47.7 | 6.5 |
| p4_bq_ca | 0 | 60 | 0 | 48.0 | 46.2 | 3.0 |
| p4_bq_ca | 1 | 60 | 0 | 33.3 | 32.7 | 2.0 |
| p4_bq_ca | 2 | 60 | 0 | 29.3 | 23.1 | 2.0 |
| p4_bq_ca | 3 | 60 | 0 | 29.0 | 27.5 | 2.0 |
| p4_bq_ca | 4 | 60 | 0 | 30.2 | 17.7 | 2.0 |

## Cost

| config | rung | tokens (median) | IQR | thoughts | MiB billed | USD (mean) | unmeasured spend |
|---|---|---|---|---|---|---|---|
| p1_managed | 0 | 733016 | 993318 | 2795 | 120.0 | 0.00077 | full |
| p1_managed | 1 | 220980 | 572160 | 952 | 50.0 | 0.00056 | full |
| p1_managed | 2 | 223065 | 503716 | 910 | 40.0 | 0.00056 | full |
| p1_managed | 3 | 233648 | 588669 | 987 | 40.0 | 0.00054 | full |
| p1_managed | 4 | 217942 | 546174 | 984 | 50.0 | 0.00057 | full |
| p3_managed | 0 | 1098024 | 1472682 | 4309 | 125.0 | 0.00078 | full |
| p3_managed | 1 | 302221 | 1337212 | 1063 | 40.0 | 0.00051 | full |
| p3_managed | 2 | 309322 | 1273783 | 1021 | 45.0 | 0.00050 | full |
| p3_managed | 3 | 291434 | 355699 | 970 | 35.0 | 0.00031 | full |
| p3_managed | 4 | 294180 | 461794 | 904 | 40.0 | 0.00032 | full |
| p3_toolbox | 0 | 188824 | 206591 | 1464 | 70.0 | 0.00049 | full |
| p3_toolbox | 1 | 61552 | 119576 | 760 | 40.0 | 0.00034 | full |
| p3_toolbox | 2 | 63253 | 209938 | 922 | 30.0 | 0.00036 | full |
| p3_toolbox | 3 | 56601 | 165648 | 828 | 30.0 | 0.00042 | full |
| p3_toolbox | 4 | 46176 | 129807 | 788 | 30.0 | 0.00032 | full |
| p1_matched | 0 | 81693 | 149520 | 1708 | 85.0 | 0.00060 | full |
| p1_matched | 1 | 23317 | 77527 | 684 | 40.0 | 0.00046 | full |
| p1_matched | 2 | 21572 | 108085 | 736 | 40.0 | 0.00047 | full |
| p1_matched | 3 | 22518 | 96192 | 650 | 40.0 | 0.00046 | full |
| p1_matched | 4 | 20410 | 83757 | 699 | 40.0 | 0.00048 | full |
| p3_matched | 0 | 208982 | 372230 | 2210 | 70.0 | 0.00062 | full |
| p3_matched | 1 | 36440 | 535102 | 708 | 30.0 | 0.00046 | full |
| p3_matched | 2 | 43850 | 468044 | 769 | 30.0 | 0.00042 | full |
| p3_matched | 3 | 43262 | 126202 | 666 | 30.0 | 0.00036 | full |
| p3_matched | 4 | 35610 | 159083 | 768 | 30.0 | 0.00035 | full |
| p4_bq_ca | 0 | 8450 | 15190 | 407 | 30.0 | 0.00021 | floor |
| p4_bq_ca | 1 | 4836 | 6802 | 342 | 20.0 | 0.00018 | floor |
| p4_bq_ca | 2 | 4358 | 4232 | 346 | 15.0 | 0.00015 | floor |
| p4_bq_ca | 3 | 4531 | 5965 | 326 | 20.0 | 0.00016 | floor |
| p4_bq_ca | 4 | 4120 | 3786 | 334 | 15.0 | 0.00016 | floor |

Prices: cloud.google.com/bigquery/pricing, US multi-region on-demand list price (verified 2026-09-03). Token rates are unset unless a `prices.json` supplies them, so a `--` in the USD column means *unpriced*, not free. Dollars are the only derived number in this report and the only one that depends on a rate card, which is why every other column is in units consumed.

The last column is how complete the picture is. **full** means everything this sweep spent, it saw. **floor** means the arm also spent model tokens server-side that the API never reported back — Conversational Analytics runs its own Gemini loop on our behalf. A floor is a lower bound, not a total, and it is not small: `make service-tokens` meters it from Cloud Monitoring and finds `p4_looker_ca` consumed 22x the tokens recorded here.

## Semantic adherence (judged)

| config | rung | n | governed | partial | invented | unclear |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 50 | 8% | 30% | 62% | 0% |
| p1_managed | 1 | 50 | 50% | 48% | 2% | 0% |
| p1_managed | 2 | 50 | 50% | 46% | 4% | 0% |
| p1_managed | 3 | 50 | 50% | 48% | 2% | 0% |
| p1_managed | 4 | 50 | 50% | 48% | 2% | 0% |
| p3_managed | 0 | 50 | 10% | 26% | 64% | 0% |
| p3_managed | 1 | 50 | 50% | 50% | 0% | 0% |
| p3_managed | 2 | 50 | 50% | 48% | 2% | 0% |
| p3_managed | 3 | 50 | 80% | 20% | 0% | 0% |
| p3_managed | 4 | 50 | 80% | 20% | 0% | 0% |
| p3_toolbox | 0 | 50 | 10% | 22% | 68% | 0% |
| p3_toolbox | 1 | 50 | 50% | 46% | 4% | 0% |
| p3_toolbox | 2 | 50 | 50% | 48% | 2% | 0% |
| p3_toolbox | 3 | 50 | 78% | 22% | 0% | 0% |
| p3_toolbox | 4 | 50 | 80% | 20% | 0% | 0% |
| p1_matched | 0 | 50 | 10% | 24% | 66% | 0% |
| p1_matched | 1 | 50 | 50% | 46% | 4% | 0% |
| p1_matched | 2 | 50 | 50% | 46% | 4% | 0% |
| p1_matched | 3 | 50 | 50% | 50% | 0% | 0% |
| p1_matched | 4 | 50 | 50% | 48% | 2% | 0% |
| p3_matched | 0 | 50 | 10% | 30% | 60% | 0% |
| p3_matched | 1 | 50 | 50% | 46% | 4% | 0% |
| p3_matched | 2 | 50 | 50% | 46% | 4% | 0% |
| p3_matched | 3 | 50 | 80% | 20% | 0% | 0% |
| p3_matched | 4 | 50 | 80% | 20% | 0% | 0% |
| p4_bq_ca | 0 | 50 | 2% | 12% | 86% | 0% |
| p4_bq_ca | 1 | 50 | 50% | 48% | 2% | 0% |
| p4_bq_ca | 2 | 50 | 50% | 50% | 0% | 0% |
| p4_bq_ca | 3 | 50 | 50% | 48% | 2% | 0% |
| p4_bq_ca | 4 | 50 | 80% | 20% | 0% | 0% |

## Equivalence

| config A | config B | pairs | same tool sequence | same value | same verdict |
|---|---|---|---|---|---|
| p3_managed | p3_toolbox | 300 | 0% | 84% | 93% |
| p1_managed | p1_matched | 300 | 0% | 94% | 97% |
| p3_managed | p3_matched | 300 | 0% | 91% | 94% |

## Tool surface

Schemas are re-sent on every turn, so their size is a per-call floor on prompt tokens. Measured live at sweep time, because a vendor can change them without notice.

| config | tools | schema chars |
|---|---|---|
| p3_managed | 8 | 144519 |
| p1_managed | 5 | 120714 |
| p3_toolbox | 23 | 18865 |
| p3_matched | 8 | 6809 |
| p1_matched | 5 | 3019 |
| p4_bq_ca | 1 | 882 |
