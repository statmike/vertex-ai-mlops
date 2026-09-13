# base vs control-p2

**runs:** 5 → 3

## Accuracy delta, on paired cells only

| arm | tier | pairs | graded | base | control-p2 | delta (pts) | resolved |
|---|---|---|---|---|---|---|---|
| p2_managed | 0 | 36 | 27 | 44% | 44% | +0.0 | < 8.9 pt floor |
| p2_managed | 1 | 36 | 27 | 100% | 100% | +0.0 | < 8.9 pt floor |
| p2_toolbox | 0 | 36 | 27 | 41% | 41% | +0.0 | < 8.9 pt floor |
| p2_toolbox | 1 | 36 | 27 | 100% | 100% | +0.0 | < 8.9 pt floor |

Unpaired cells excluded: 1296 in base, 0 in control-p2. Arms only in base: p1_managed, p1_matched, p1_toolbox, p3_managed, p3_matched, p3_toolbox, p4_bq_ca, p4_bq_direct, p4_bq_direct_ctx, p4_looker_ca.

## Rank stability

| tier | concordant | inverted | unresolved | tau (resolved only) |
|---|---|---|---|---|
| 0 | 0 | 0 | 1 | -- |
| 1 | 0 | 0 | 1 | -- |

**No ordering reversed** above the noise floor.
