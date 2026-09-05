# Results

Model `gemini-3.7-flash` at temperature 0.0, 5 replicates, tier fence on, commit `834421c3`, started 2026-09-05T02:07:23+00:00. Dataplex quality scans: not recorded.

> **Path 3 comparability.** This capture predates the `quality_scans` header field, so it cannot state whether this sandbox's Dataplex data-quality scans existed when it ran. That matters for Path 3 only: `search_dq_scans` is bound on `p3_toolbox` and returns a different list either side of those scans being provisioned. Do not merge Path 3 cells from this capture with cells from a fresh `make setup`, which now creates them. See `docs/reproducing.md`.

1200 cells scored across 20 arm/tier pairs.

## Headline

| config | tier | accuracy (mean) | tokens in / correct | tokens out / correct | sec / correct | BQ jobs / correct | MiB / correct | coverage |
|---|---|---|---|---|---|---|---|---|
| p1_managed | 0 | 37% | 1673836 | 5487 | 273 | 34.4 | 297.7 | full |
| p1_managed | 1 | 67% | 566836 | 2142 | 85 | 11.7 | 134.8 | full |
| p1_toolbox | 0 | 33% | 245109 | 3504 | 212 | 26.0 | 213.0 | full |
| p1_toolbox | 1 | 75% | 44167 | 1180 | 63 | 5.1 | 65.3 | full |
| p2_managed | 0 | 33% | 350525 | 4459 | 269 | 23.3 | 226.5 | full |
| p2_managed | 1 | 73% | 54658 | 963 | 62 | 4.1 | 55.5 | full |
| p2_toolbox | 0 | 32% | 467996 | 4898 | 279 | 25.5 | 193.2 | full |
| p2_toolbox | 1 | 75% | 81864 | 1000 | 44 | 3.9 | 50.0 | full |
| p3_managed | 0 | 35% | 3139118 | 7281 | 341 | 38.9 | 322.4 | full |
| p3_managed | 1 | 75% | 621429 | 2035 | 80 | 6.3 | 75.8 | full |
| p3_toolbox | 0 | 33% | 574456 | 4111 | 287 | 27.5 | 229.0 | full |
| p3_toolbox | 1 | 75% | 121638 | 1330 | 69 | 5.6 | 68.4 | full |
| p1_matched | 0 | 35% | 332553 | 4180 | 226 | 30.7 | 232.4 | full |
| p1_matched | 1 | 67% | 92038 | 1722 | 91 | 10.2 | 116.0 | full |
| p3_matched | 0 | 35% | 763580 | 5152 | 297 | 32.5 | 260.5 | full |
| p3_matched | 1 | 75% | 113687 | 1591 | 91 | 5.5 | 66.2 | full |
| p4_bq_ca | 0 | 23% | 50918 | 2509 | 287 | 16.4 | 160.7 | floor |
| p4_bq_ca | 1 | 75% | 7596 | 668 | 54 | 2.6 | 35.3 | floor |
| p4_looker_ca | 0 | 15% | 177682 | 2170 | 1113 | 16.6 | 184.4 | floor |
| p4_looker_ca | 1 | 35% | 23467 | 677 | 240 | 3.1 | 46.7 | floor |

**Do not sort this table by the cost columns.** `p4_bq_ca`, `p4_looker_ca` carry `floor` coverage: they spend model tokens server-side that the API never reports, so their figures are lower bounds and every other arm's are totals. Comparing them directly compares two different quantities. The gap is not small — `make service-tokens` meters `p4_looker_ca` from Cloud Monitoring at 392,158 tokens per cell against the 18,045 recorded here, a 22x understatement that moves it from the cheapest arm to the third most expensive. The floors are left uncorrected in the table on purpose: the meter attributes by time block, not per cell, and splitting a block across cells that vary in turn count would invent a distribution. Two honest numbers in two places beat one fused number that hides which half was inferred.

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

Prices: cloud.google.com/bigquery/pricing, US multi-region on-demand list price (verified 2026-09-03). Token rates are unset unless a `prices.json` supplies them, so a `--` in the USD column means *unpriced*, not free. Dollars are the only derived number in this report and the only one that depends on a rate card, which is why every other column is in units consumed.

The last column is how complete the picture is. **full** means everything this sweep spent, it saw. **floor** means the arm also spent model tokens server-side that the API never reported back — Conversational Analytics runs its own Gemini loop on our behalf. A floor is a lower bound, not a total, and it is not small: `make service-tokens` meters it from Cloud Monitoring and finds `p4_looker_ca` consumed 22x the tokens recorded here.

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
