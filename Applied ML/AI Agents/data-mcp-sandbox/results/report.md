# Results

Model `gemini-3.7-flash` at temperature 0.0, 5 replicates, tier fence on, commit `aa872df2`, started 2026-09-03T11:46:51+00:00.

960 cells scored across 16 arm/tier pairs.

## Headline

| config | tier | accuracy (mean) | tokens / correct | MiB / correct | USD / correct | coverage |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 32% | 2106021 | -- | -- | -- |
| p1_managed | 1 | 67% | 603668 | -- | -- | -- |
| p1_toolbox | 0 | 30% | 300044 | -- | -- | -- |
| p1_toolbox | 1 | 75% | 60612 | -- | -- | -- |
| p2_managed | 0 | 35% | 370877 | -- | -- | -- |
| p2_managed | 1 | 75% | 51909 | -- | -- | -- |
| p2_toolbox | 0 | 32% | 470672 | -- | -- | -- |
| p2_toolbox | 1 | 70% | 108261 | -- | -- | -- |
| p3_managed | 0 | 33% | 3049772 | -- | -- | -- |
| p3_managed | 1 | 73% | 608014 | -- | -- | -- |
| p3_toolbox | 0 | 32% | 669867 | -- | -- | -- |
| p3_toolbox | 1 | 75% | 122562 | -- | -- | -- |
| p4_bq_ca | 0 | 20% | 87759 | -- | -- | -- |
| p4_bq_ca | 1 | 75% | 9390 | -- | -- | -- |
| p4_looker_ca | 0 | 13% | 282943 | -- | -- | -- |
| p4_looker_ca | 1 | 57% | 18377 | -- | -- | -- |

## Capture health

| config | tier | attempted | scored | failed | quota-retried | CA leak |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 60 | 60 | 0 | 0 | 0% |
| p1_managed | 1 | 60 | 60 | 0 | 0 | 0% |
| p1_toolbox | 0 | 60 | 60 | 0 | 0 | 63% |
| p1_toolbox | 1 | 60 | 60 | 0 | 0 | 33% |
| p2_managed | 0 | 60 | 60 | 0 | 0 | 0% |
| p2_managed | 1 | 60 | 60 | 0 | 0 | 0% |
| p2_toolbox | 0 | 60 | 60 | 0 | 0 | 0% |
| p2_toolbox | 1 | 60 | 60 | 0 | 0 | 0% |
| p3_managed | 0 | 60 | 60 | 0 | 0 | 0% |
| p3_managed | 1 | 60 | 60 | 0 | 0 | 0% |
| p3_toolbox | 0 | 60 | 60 | 0 | 0 | 70% |
| p3_toolbox | 1 | 60 | 60 | 0 | 0 | 33% |
| p4_bq_ca | 0 | 60 | 60 | 0 | 0 | 0% |
| p4_bq_ca | 1 | 60 | 60 | 0 | 0 | 0% |
| p4_looker_ca | 0 | 60 | 60 | 0 | 0 | 0% |
| p4_looker_ca | 1 | 60 | 60 | 0 | 0 | 0% |

**CA leak** is not a bug in the run — it is a property of the surface being measured. `ask_data_insights` ships inside the Toolbox BigQuery toolset, so `p1_toolbox` and `p3_toolbox` can reach Conversational Analytics and become Path 4 for that cell. The arms are reported as shipped rather than trimmed to be hermetic, so this column says how often it happened instead of hiding it.

## Accuracy

| config | tier | n | correct | sprang trap | used decoy |
|---|---|---|---|---|---|
| p1_managed | 0 | 60 | 32% | 33% | 50% |
| p1_managed | 1 | 60 | 67% | 8% | 30% |
| p1_toolbox | 0 | 60 | 30% | 18% | 50% |
| p1_toolbox | 1 | 60 | 75% | 0% | 10% |
| p2_managed | 0 | 60 | 35% | 30% | 50% |
| p2_managed | 1 | 60 | 75% | 0% | 2% |
| p2_toolbox | 0 | 60 | 32% | 28% | 50% |
| p2_toolbox | 1 | 60 | 70% | 0% | 2% |
| p3_managed | 0 | 60 | 33% | 33% | 50% |
| p3_managed | 1 | 60 | 73% | 0% | 17% |
| p3_toolbox | 0 | 60 | 32% | 10% | 50% |
| p3_toolbox | 1 | 60 | 75% | 0% | 7% |
| p4_bq_ca | 0 | 60 | 20% | 17% | 50% |
| p4_bq_ca | 1 | 60 | 75% | 0% | 7% |
| p4_looker_ca | 0 | 60 | 13% | 7% | 27% |
| p4_looker_ca | 1 | 60 | 57% | 0% | 2% |

## Acquisition vs application

| config | tier | n | opaque | acquired | application loss |
|---|---|---|---|---|---|
| p1_managed | 0 | 50 | 0% | 0% | 0% |
| p1_managed | 1 | 50 | 0% | 100% | 40% |
| p1_toolbox | 0 | 50 | 0% | 0% | 0% |
| p1_toolbox | 1 | 50 | 0% | 100% | 30% |
| p2_managed | 0 | 50 | 0% | 0% | 0% |
| p2_managed | 1 | 50 | 0% | 100% | 30% |
| p2_toolbox | 0 | 50 | 0% | 0% | 0% |
| p2_toolbox | 1 | 50 | 0% | 100% | 36% |
| p3_managed | 0 | 50 | 0% | 0% | 0% |
| p3_managed | 1 | 50 | 0% | 100% | 32% |
| p3_toolbox | 0 | 50 | 0% | 0% | 0% |
| p3_toolbox | 1 | 50 | 0% | 100% | 30% |
| p4_bq_ca | 0 | 50 | 100% | -- | -- |
| p4_bq_ca | 1 | 50 | 100% | -- | -- |
| p4_looker_ca | 0 | 50 | 100% | -- | -- |
| p4_looker_ca | 1 | 50 | 100% | -- | -- |

## Evidence

| config | tier | no query disclosed | recall (median) | IQR | precision |
|---|---|---|---|---|---|
| p1_managed | 0 | 0% | 1.00 | 0.15 | 0.90 |
| p1_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p1_toolbox | 0 | 0% | 1.00 | 0.20 | 0.90 |
| p1_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p2_managed | 0 | 0% | 1.00 | 0.15 | 0.92 |
| p2_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p2_toolbox | 0 | 0% | 1.00 | 0.20 | 0.90 |
| p2_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_managed | 0 | 0% | 1.00 | 0.15 | 0.90 |
| p3_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p3_toolbox | 0 | 0% | 1.00 | 0.15 | 0.92 |
| p3_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p4_bq_ca | 0 | 0% | 1.00 | 0.15 | 0.92 |
| p4_bq_ca | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p4_looker_ca | 0 | 32% | 0.33 | 1.00 | 0.50 |
| p4_looker_ca | 1 | 55% | 1.00 | 0.80 | 1.00 |

## Latency

| config | tier | clean cells | excluded | median s | IQR | tool calls |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 60 | 0 | 88.5 | 80.4 | 16.5 |
| p1_managed | 1 | 60 | 0 | 36.0 | 88.6 | 6.5 |
| p1_toolbox | 0 | 60 | 0 | 79.3 | 81.3 | 13.0 |
| p1_toolbox | 1 | 60 | 0 | 33.1 | 78.4 | 7.0 |
| p2_managed | 0 | 60 | 0 | 77.7 | 80.8 | 15.0 |
| p2_managed | 1 | 60 | 0 | 43.1 | 23.9 | 7.0 |
| p2_toolbox | 0 | 60 | 0 | 80.3 | 84.6 | 14.0 |
| p2_toolbox | 1 | 60 | 0 | 74.4 | 61.2 | 8.0 |
| p3_managed | 0 | 60 | 0 | 182.2 | 177.2 | 22.0 |
| p3_managed | 1 | 60 | 0 | 55.2 | 79.7 | 7.0 |
| p3_toolbox | 0 | 60 | 0 | 86.1 | 91.1 | 16.5 |
| p3_toolbox | 1 | 60 | 0 | 37.7 | 59.6 | 7.0 |
| p4_bq_ca | 0 | 60 | 0 | 57.1 | 46.4 | 3.0 |
| p4_bq_ca | 1 | 60 | 0 | 32.0 | 29.5 | 2.0 |
| p4_looker_ca | 0 | 60 | 0 | 172.6 | 135.0 | 2.0 |
| p4_looker_ca | 1 | 60 | 0 | 64.5 | 93.3 | 1.0 |

## Cost

| config | tier | tokens (median) | IQR | thoughts | MiB billed | USD (mean) | unmeasured spend |
|---|---|---|---|---|---|---|---|
| p1_managed | 0 | 574009 | 661614 | 2720 | -- | -- | -- |
| p1_managed | 1 | 193756 | 569720 | 907 | -- | -- | -- |
| p1_toolbox | 0 | 75790 | 96604 | 1106 | -- | -- | -- |
| p1_toolbox | 1 | 29762 | 61535 | 674 | -- | -- | -- |
| p2_managed | 0 | 94122 | 131108 | 1538 | -- | -- | -- |
| p2_managed | 1 | 32444 | 21496 | 628 | -- | -- | -- |
| p2_toolbox | 0 | 62615 | 102254 | 1609 | -- | -- | -- |
| p2_toolbox | 1 | 30074 | 36230 | 683 | -- | -- | -- |
| p3_managed | 0 | 985792 | 1241469 | 3378 | -- | -- | -- |
| p3_managed | 1 | 233069 | 660862 | 784 | -- | -- | -- |
| p3_toolbox | 0 | 178437 | 222143 | 1390 | -- | -- | -- |
| p3_toolbox | 1 | 56280 | 123822 | 760 | -- | -- | -- |
| p4_bq_ca | 0 | 12206 | 14496 | 412 | -- | -- | -- |
| p4_bq_ca | 1 | 4428 | 5372 | 340 | -- | -- | -- |
| p4_looker_ca | 0 | 16202 | 29947 | 291 | -- | -- | -- |
| p4_looker_ca | 1 | 4817 | 6958 | 241 | -- | -- | -- |

Prices: cloud.google.com/bigquery/pricing, US multi-region on-demand list price (verified 2026-09-03). Token rates are unset unless a `prices.json` supplies them, so a `--` in the USD column means *unpriced*, not free. A `yes` in the last column means the arm also spent money this sweep cannot see: Conversational Analytics runs its own Gemini calls and does not report them.

## Semantic adherence (judged)

| config | tier | n | governed | partial | invented | unclear |
|---|---|---|---|---|---|---|

## Equivalence

| config A | config B | pairs | same tool sequence | same value | same verdict |
|---|---|---|---|---|---|
| p1_managed | p1_toolbox | 120 | 0% | 68% | 93% |
| p2_managed | p2_toolbox | 120 | 7% | 92% | 96% |
| p3_managed | p3_toolbox | 120 | 0% | 68% | 98% |
| p4_bq_ca | p4_looker_ca | 120 | 0% | 38% | 68% |
