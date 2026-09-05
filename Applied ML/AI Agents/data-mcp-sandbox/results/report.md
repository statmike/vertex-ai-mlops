# Results

Model `gemini-3.7-flash` at temperature 0.0, 5 replicates, tier fence on, commit `834421c3`, started 2026-09-05T02:07:23+00:00.

1200 cells scored across 20 arm/tier pairs.

## Headline

| config | tier | accuracy (mean) | tokens / correct | MiB / correct | USD / correct | coverage |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 37% | 1689323 | 297.7 | 0.00177 | full |
| p1_managed | 1 | 67% | 572233 | 134.8 | 0.00080 | full |
| p1_toolbox | 0 | 33% | 252921 | 213.0 | 0.00127 | full |
| p1_toolbox | 1 | 75% | 46428 | 65.3 | 0.00039 | full |
| p2_managed | 0 | 33% | 362823 | 226.5 | 0.00135 | full |
| p2_managed | 1 | 73% | 56688 | 55.5 | 0.00033 | full |
| p2_toolbox | 0 | 32% | 481595 | 193.2 | 0.00115 | full |
| p2_toolbox | 1 | 75% | 83898 | 50.0 | 0.00030 | full |
| p3_managed | 0 | 35% | 3159221 | 322.4 | 0.00192 | full |
| p3_managed | 1 | 75% | 626026 | 75.8 | 0.00045 | full |
| p3_toolbox | 0 | 33% | 583464 | 229.0 | 0.00136 | full |
| p3_toolbox | 1 | 75% | 124546 | 68.4 | 0.00041 | full |
| p1_matched | 0 | 35% | 344345 | 232.4 | 0.00139 | full |
| p1_matched | 1 | 67% | 96193 | 116.0 | 0.00069 | full |
| p3_matched | 0 | 35% | 777949 | 260.5 | 0.00155 | full |
| p3_matched | 1 | 75% | 117246 | 66.2 | 0.00039 | full |
| p4_bq_ca | 0 | 23% | 55464 | 160.7 | 0.00096 | floor |
| p4_bq_ca | 1 | 75% | 8807 | 35.3 | 0.00021 | floor |
| p4_looker_ca | 0 | 15% | 182560 | 184.4 | 0.00110 | floor |
| p4_looker_ca | 1 | 35% | 24874 | 46.7 | 0.00028 | floor |

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

**CA leak** is not a bug in the run — it is a property of the surface being measured. `ask_data_insights` ships inside the Toolbox BigQuery toolset, so `p1_toolbox` and `p3_toolbox` can reach Conversational Analytics and become Path 4 for that cell. The arms are reported as shipped rather than trimmed to be hermetic, so this column says how often it happened instead of hiding it.

## Accuracy

| config | tier | n | correct | sprang trap | used decoy |
|---|---|---|---|---|---|
| p1_managed | 0 | 60 | 37% | 33% | 50% |
| p1_managed | 1 | 60 | 67% | 8% | 30% |
| p1_toolbox | 0 | 60 | 33% | 18% | 50% |
| p1_toolbox | 1 | 60 | 75% | 0% | 13% |
| p2_managed | 0 | 60 | 33% | 33% | 50% |
| p2_managed | 1 | 60 | 73% | 0% | 0% |
| p2_toolbox | 0 | 60 | 32% | 32% | 50% |
| p2_toolbox | 1 | 60 | 75% | 0% | 2% |
| p3_managed | 0 | 60 | 35% | 33% | 50% |
| p3_managed | 1 | 60 | 75% | 0% | 18% |
| p3_toolbox | 0 | 60 | 33% | 12% | 50% |
| p3_toolbox | 1 | 60 | 75% | 0% | 5% |
| p1_matched | 0 | 60 | 35% | 33% | 50% |
| p1_matched | 1 | 60 | 67% | 8% | 18% |
| p3_matched | 0 | 60 | 35% | 33% | 50% |
| p3_matched | 1 | 60 | 75% | 0% | 12% |
| p4_bq_ca | 0 | 60 | 23% | 8% | 50% |
| p4_bq_ca | 1 | 60 | 75% | 0% | 7% |
| p4_looker_ca | 0 | 60 | 15% | 5% | 17% |
| p4_looker_ca | 1 | 60 | 35% | 0% | 3% |

## Acquisition vs application

| config | tier | n | opaque | acquired | application loss |
|---|---|---|---|---|---|
| p1_managed | 0 | 50 | 0% | 0% | 0% |
| p1_managed | 1 | 50 | 0% | 100% | 40% |
| p1_toolbox | 0 | 50 | 0% | 0% | 0% |
| p1_toolbox | 1 | 50 | 0% | 100% | 30% |
| p2_managed | 0 | 50 | 0% | 0% | 0% |
| p2_managed | 1 | 50 | 0% | 100% | 32% |
| p2_toolbox | 0 | 50 | 0% | 0% | 0% |
| p2_toolbox | 1 | 50 | 0% | 100% | 30% |
| p3_managed | 0 | 50 | 0% | 0% | 0% |
| p3_managed | 1 | 50 | 0% | 100% | 30% |
| p3_toolbox | 0 | 50 | 0% | 0% | 0% |
| p3_toolbox | 1 | 50 | 0% | 100% | 30% |
| p1_matched | 0 | 50 | 0% | 0% | 0% |
| p1_matched | 1 | 50 | 0% | 100% | 40% |
| p3_matched | 0 | 50 | 0% | 0% | 0% |
| p3_matched | 1 | 50 | 0% | 100% | 30% |
| p4_bq_ca | 0 | 50 | 100% | -- | -- |
| p4_bq_ca | 1 | 50 | 100% | -- | -- |
| p4_looker_ca | 0 | 50 | 100% | -- | -- |
| p4_looker_ca | 1 | 50 | 100% | -- | -- |

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

Prices: cloud.google.com/bigquery/pricing, US multi-region on-demand list price (verified 2026-09-03). Token rates are unset unless a `prices.json` supplies them, so a `--` in the USD column means *unpriced*, not free. A `yes` in the last column means the arm also spent money this sweep cannot see: Conversational Analytics runs its own Gemini calls and does not report them.

## Semantic adherence (judged)

| config | tier | n | governed | partial | invented | unclear |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 50 | 10% | 34% | 56% | 0% |
| p1_managed | 1 | 50 | 50% | 50% | 0% | 0% |
| p1_toolbox | 0 | 50 | 10% | 22% | 68% | 0% |
| p1_toolbox | 1 | 50 | 80% | 20% | 0% | 0% |
| p2_managed | 0 | 50 | 10% | 34% | 56% | 0% |
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
| p4_looker_ca | 0 | 50 | 0% | 12% | 58% | 30% |
| p4_looker_ca | 1 | 50 | 30% | 24% | 4% | 42% |

## Equivalence

| config A | config B | pairs | same tool sequence | same value | same verdict |
|---|---|---|---|---|---|
| p1_managed | p1_toolbox | 120 | 0% | 67% | 94% |
| p2_managed | p2_toolbox | 120 | 7% | 92% | 97% |
| p3_managed | p3_toolbox | 120 | 0% | 70% | 99% |
| p1_managed | p1_matched | 120 | 0% | 91% | 99% |
| p3_managed | p3_matched | 120 | 0% | 88% | 98% |
| p4_bq_ca | p4_looker_ca | 120 | 0% | 42% | 72% |

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
