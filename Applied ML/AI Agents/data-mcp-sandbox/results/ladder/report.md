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
| p1_managed | 0 | 42% | 1748130 | 5167 | 194 | 30.4 | 280.0 | full |
| p1_managed | 1 | 89% | 341006 | 1249 | 44 | 5.9 | 72.5 | full |
| p1_managed | 2 | 89% | 313851 | 1268 | 44 | 5.3 | 68.2 | full |
| p1_managed | 3 | 89% | 349740 | 1329 | 44 | 5.3 | 66.2 | full |
| p1_managed | 4 | 89% | 351149 | 1345 | 47 | 5.9 | 71.8 | full |
| p3_managed | 0 | 44% | 2632318 | 5784 | 221 | 30.2 | 272.0 | full |
| p3_managed | 1 | 87% | 664048 | 1544 | 61 | 5.3 | 68.7 | full |
| p3_managed | 2 | 87% | 697342 | 1478 | 53 | 5.3 | 67.9 | full |
| p3_managed | 3 | 100% | 290020 | 1017 | 34 | 3.0 | 36.2 | full |
| p3_managed | 4 | 100% | 311266 | 981 | 35 | 3.3 | 38.7 | full |
| p3_toolbox | 0 | 44% | 452301 | 3040 | 190 | 20.9 | 175.5 | full |
| p3_toolbox | 1 | 87% | 68705 | 884 | 42 | 4.0 | 47.2 | full |
| p3_toolbox | 2 | 89% | 95364 | 882 | 44 | 3.6 | 40.0 | full |
| p3_toolbox | 3 | 100% | 66089 | 988 | 33 | 3.2 | 42.0 | full |
| p3_toolbox | 4 | 100% | 53823 | 711 | 30 | 3.0 | 35.3 | full |
| p1_matched | 0 | 44% | 257188 | 3107 | 135 | 23.2 | 216.0 | full |
| p1_matched | 1 | 91% | 33454 | 863 | 32 | 4.5 | 57.1 | full |
| p1_matched | 2 | 89% | 36981 | 871 | 32 | 4.7 | 55.2 | full |
| p1_matched | 3 | 87% | 35930 | 895 | 34 | 4.7 | 57.9 | full |
| p1_matched | 4 | 89% | 35119 | 856 | 32 | 4.6 | 55.5 | full |
| p3_matched | 0 | 44% | 669395 | 4204 | 205 | 26.9 | 220.5 | full |
| p3_matched | 1 | 89% | 189487 | 1064 | 55 | 4.6 | 56.8 | full |
| p3_matched | 2 | 89% | 227490 | 1084 | 57 | 4.3 | 50.5 | full |
| p3_matched | 3 | 100% | 47632 | 859 | 30 | 3.0 | 39.6 | full |
| p3_matched | 4 | 98% | 51563 | 869 | 30 | 3.2 | 39.1 | full |
| p4_bq_ca | 0 | 27% | 53611 | 2298 | 219 | 13.4 | 130.0 | floor |
| p4_bq_ca | 1 | 89% | 5337 | 459 | 38 | 1.9 | 20.5 | floor |
| p4_bq_ca | 2 | 89% | 4378 | 426 | 33 | 1.6 | 14.5 | floor |
| p4_bq_ca | 3 | 89% | 8859 | 506 | 37 | 1.9 | 20.2 | floor |
| p4_bq_ca | 4 | 100% | 5332 | 438 | 33 | 1.5 | 20.2 | floor |

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

| config | rung | n | graded | correct | sprang trap | used decoy |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 60 | 45 | 42% | 32% | 50% |
| p1_managed | 1 | 60 | 45 | 89% | 10% | 35% |
| p1_managed | 2 | 60 | 45 | 89% | 8% | 28% |
| p1_managed | 3 | 60 | 45 | 89% | 8% | 25% |
| p1_managed | 4 | 60 | 45 | 89% | 8% | 30% |
| p3_managed | 0 | 60 | 45 | 44% | 30% | 50% |
| p3_managed | 1 | 60 | 45 | 87% | 8% | 22% |
| p3_managed | 2 | 60 | 45 | 87% | 10% | 20% |
| p3_managed | 3 | 60 | 45 | 100% | 0% | 8% |
| p3_managed | 4 | 60 | 45 | 100% | 0% | 20% |
| p3_toolbox | 0 | 60 | 45 | 44% | 12% | 50% |
| p3_toolbox | 1 | 60 | 45 | 87% | 8% | 22% |
| p3_toolbox | 2 | 60 | 45 | 89% | 8% | 17% |
| p3_toolbox | 3 | 60 | 45 | 100% | 0% | 7% |
| p3_toolbox | 4 | 60 | 45 | 100% | 0% | 10% |
| p1_matched | 0 | 60 | 45 | 44% | 28% | 50% |
| p1_matched | 1 | 60 | 45 | 91% | 8% | 32% |
| p1_matched | 2 | 60 | 45 | 89% | 8% | 20% |
| p1_matched | 3 | 60 | 45 | 87% | 8% | 28% |
| p1_matched | 4 | 60 | 45 | 89% | 8% | 20% |
| p3_matched | 0 | 60 | 45 | 44% | 32% | 50% |
| p3_matched | 1 | 60 | 45 | 89% | 8% | 23% |
| p3_matched | 2 | 60 | 45 | 89% | 8% | 17% |
| p3_matched | 3 | 60 | 45 | 100% | 0% | 8% |
| p3_matched | 4 | 60 | 45 | 98% | 0% | 13% |
| p4_bq_ca | 0 | 60 | 45 | 27% | 8% | 50% |
| p4_bq_ca | 1 | 60 | 45 | 89% | 8% | 3% |
| p4_bq_ca | 2 | 60 | 45 | 89% | 8% | 8% |
| p4_bq_ca | 3 | 60 | 45 | 89% | 10% | 8% |
| p4_bq_ca | 4 | 60 | 45 | 100% | 0% | 3% |

**450 of 1800 cells are excluded from every rate above.** 3 of the battery's questions are worded so that two answers are equally defensible, which makes the oracle an arbiter of a coin-flip rather than a grader. The cells ran, are in the capture, and carry a `correct` a reader can inspect — they are *unmeasured*, not zero, the same way an opaque path's evidence reads `--`.

* `governed-q1` — The governed rule defines Active as "had an event in the trailing 30 days", which pins the window's length but not its anchor. The answer is a count - extensive, so the two defensible anchorings differ by more than the 0.5% tolerance. See semantic-q2.
* `governed-q3` — Inherits the Active definition's unpinned anchor from governed-q1, and sums over it. The answer is an extensive quantity twice over - which users count, and how much they spent - so the two defensible anchorings diverge well past the 0.5% tolerance. See semantic-q2.
* `semantic-q2` — "trailing 30 days" pins the window's length but not its anchor. Anchoring to the data's latest timestamp is as defensible as anchoring to now, and agents pick between them nondeterministically at temperature 0 - the same arm answered 2,699 and 2,804 in consecutive runs. The answer is an extensive quantity (a sum), so the two readings differ by more than the 0.5% tolerance and the oracle arbitrates a coin-flip.

## Acquisition vs application

| config | rung | n | opaque | acquired | application loss |
|---|---|---|---|---|---|
| p1_managed | 0 | 35 | 0% | 0% | 0% |
| p1_managed | 1 | 35 | 0% | 100% | 14% |
| p1_managed | 2 | 35 | 0% | 100% | 14% |
| p1_managed | 3 | 35 | 0% | 100% | 14% |
| p1_managed | 4 | 35 | 0% | 100% | 14% |
| p3_managed | 0 | 35 | 0% | 0% | 0% |
| p3_managed | 1 | 35 | 0% | 100% | 17% |
| p3_managed | 2 | 35 | 0% | 100% | 17% |
| p3_managed | 3 | 35 | 0% | 100% | 0% |
| p3_managed | 4 | 35 | 0% | 100% | 0% |
| p3_toolbox | 0 | 35 | 0% | 0% | 0% |
| p3_toolbox | 1 | 35 | 0% | 100% | 17% |
| p3_toolbox | 2 | 35 | 0% | 100% | 14% |
| p3_toolbox | 3 | 35 | 0% | 100% | 0% |
| p3_toolbox | 4 | 35 | 0% | 100% | 0% |
| p1_matched | 0 | 35 | 0% | 0% | 0% |
| p1_matched | 1 | 35 | 0% | 100% | 11% |
| p1_matched | 2 | 35 | 0% | 100% | 14% |
| p1_matched | 3 | 35 | 0% | 100% | 17% |
| p1_matched | 4 | 35 | 0% | 100% | 14% |
| p3_matched | 0 | 35 | 0% | 0% | 0% |
| p3_matched | 1 | 35 | 0% | 100% | 14% |
| p3_matched | 2 | 35 | 0% | 100% | 14% |
| p3_matched | 3 | 35 | 0% | 100% | 0% |
| p3_matched | 4 | 35 | 0% | 100% | 3% |
| p4_bq_ca | 0 | 35 | 100% | -- | -- |
| p4_bq_ca | 1 | 35 | 100% | -- | -- |
| p4_bq_ca | 2 | 35 | 100% | -- | -- |
| p4_bq_ca | 3 | 35 | 100% | -- | -- |
| p4_bq_ca | 4 | 35 | 100% | -- | -- |

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

| config A | config B | pairs | graded | same tool sequence | same value | same verdict |
|---|---|---|---|---|---|---|
| p3_managed | p3_toolbox | 300 | 225 | 0% | 84% | 99% |
| p1_managed | p1_matched | 300 | 225 | 0% | 94% | 99% |
| p3_managed | p3_matched | 300 | 225 | 0% | 91% | 99% |

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
