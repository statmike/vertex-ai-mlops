results/capture.json.gz: 1440 cells
using goldens frozen into the capture (2 oracles across 12 arms)
results/capture-model-38flash.json.gz: 720 cells
using goldens frozen into the capture (1 oracle across 10 arms)

# base vs model-38flash

**agent_model:** gemini-3.7-flash → gemini-3.8-flash
**runs:** 5 → 3

## Accuracy delta, on paired cells only

| arm | tier | pairs | base | model-38flash | delta (pts) | resolved |
|---|---|---|---|---|---|---|
| p1_managed | 0 | 36 | 36% | 33% | -2.8 | < 6.7 pt floor |
| p1_managed | 1 | 36 | 67% | 72% | +5.6 | < 6.7 pt floor |
| p1_matched | 0 | 36 | 36% | 33% | -2.8 | < 6.7 pt floor |
| p1_matched | 1 | 36 | 67% | 67% | +0.0 | < 6.7 pt floor |
| p1_toolbox | 0 | 36 | 33% | 31% | -2.8 | < 6.7 pt floor |
| p1_toolbox | 1 | 36 | 75% | 92% | +16.7 | yes |
| p2_managed | 0 | 36 | 33% | 42% | +8.3 | yes |
| p2_managed | 1 | 36 | 75% | 92% | +16.7 | yes |
| p2_toolbox | 0 | 36 | 31% | 39% | +8.3 | yes |
| p2_toolbox | 1 | 36 | 75% | 92% | +16.7 | yes |
| p3_managed | 0 | 36 | 36% | 33% | -2.8 | < 6.7 pt floor |
| p3_managed | 1 | 36 | 75% | 89% | +13.9 | yes |
| p3_matched | 0 | 36 | 33% | 33% | +0.0 | < 6.7 pt floor |
| p3_matched | 1 | 36 | 75% | 75% | +0.0 | < 6.7 pt floor |
| p3_toolbox | 0 | 36 | 33% | 33% | +0.0 | < 6.7 pt floor |
| p3_toolbox | 1 | 36 | 75% | 97% | +22.2 | yes |
| p4_bq_ca | 0 | 36 | 25% | 28% | +2.8 | < 6.7 pt floor |
| p4_bq_ca | 1 | 36 | 75% | 75% | +0.0 | < 6.7 pt floor |
| p4_looker_ca | 0 | 36 | 14% | 11% | -2.8 | < 6.7 pt floor |
| p4_looker_ca | 1 | 36 | 33% | 42% | +8.3 | yes |

Unpaired cells excluded: 720 in base, 0 in model-38flash. Arms only in base: p4_bq_direct, p4_bq_direct_ctx.

## Rank stability

| tier | concordant | inverted | unresolved | tau (resolved only) |
|---|---|---|---|---|
| 0 | 10 | 0 | 35 | +1.00 |
| 1 | 21 | 0 | 24 | +1.00 |

**No ordering reversed** above the noise floor.

