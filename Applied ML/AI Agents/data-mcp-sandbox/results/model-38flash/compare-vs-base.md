results/capture.json.gz: 1440 cells
using goldens frozen into the capture (2 oracles across 12 arms)
results/capture-model-38flash.json.gz: 720 cells
using goldens frozen into the capture (1 oracle across 10 arms)

# base vs model-38flash

**agent_model:** gemini-3.7-flash → gemini-3.8-flash
**runs:** 5 → 3

## Accuracy delta, on paired cells only

| arm | tier | pairs | graded | base | model-38flash | delta (pts) | resolved |
|---|---|---|---|---|---|---|---|
| p1_managed | 0 | 36 | 27 | 48% | 44% | -3.7 | < 8.9 pt floor |
| p1_managed | 1 | 36 | 27 | 89% | 93% | +3.7 | < 8.9 pt floor |
| p1_matched | 0 | 36 | 27 | 48% | 44% | -3.7 | < 8.9 pt floor |
| p1_matched | 1 | 36 | 27 | 89% | 89% | +0.0 | < 8.9 pt floor |
| p1_toolbox | 0 | 36 | 27 | 44% | 41% | -3.7 | < 8.9 pt floor |
| p1_toolbox | 1 | 36 | 27 | 100% | 100% | +0.0 | < 8.9 pt floor |
| p2_managed | 0 | 36 | 27 | 44% | 56% | +11.1 | yes |
| p2_managed | 1 | 36 | 27 | 100% | 100% | +0.0 | < 8.9 pt floor |
| p2_toolbox | 0 | 36 | 27 | 41% | 52% | +11.1 | yes |
| p2_toolbox | 1 | 36 | 27 | 100% | 100% | +0.0 | < 8.9 pt floor |
| p3_managed | 0 | 36 | 27 | 48% | 44% | -3.7 | < 8.9 pt floor |
| p3_managed | 1 | 36 | 27 | 100% | 100% | +0.0 | < 8.9 pt floor |
| p3_matched | 0 | 36 | 27 | 44% | 44% | +0.0 | < 8.9 pt floor |
| p3_matched | 1 | 36 | 27 | 100% | 100% | +0.0 | < 8.9 pt floor |
| p3_toolbox | 0 | 36 | 27 | 44% | 44% | +0.0 | < 8.9 pt floor |
| p3_toolbox | 1 | 36 | 27 | 100% | 100% | +0.0 | < 8.9 pt floor |
| p4_bq_ca | 0 | 36 | 27 | 33% | 37% | +3.7 | < 8.9 pt floor |
| p4_bq_ca | 1 | 36 | 27 | 100% | 100% | +0.0 | < 8.9 pt floor |
| p4_looker_ca | 0 | 36 | 27 | 15% | 15% | +0.0 | < 8.9 pt floor |
| p4_looker_ca | 1 | 36 | 27 | 44% | 56% | +11.1 | yes |

Unpaired cells excluded: 720 in base, 0 in model-38flash. Arms only in base: p4_bq_direct, p4_bq_direct_ctx.

## Rank stability

| tier | concordant | inverted | unresolved | tau (resolved only) |
|---|---|---|---|---|
| 0 | 10 | 0 | 35 | +1.00 |
| 1 | 16 | 0 | 29 | +1.00 |

**No ordering reversed** above the noise floor.

