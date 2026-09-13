# Results

Model `gemini-3.7-flash` at temperature 0.0, 3 replicates, tier fence on, commit `7de053cc`, started 2026-09-13T13:10:42+00:00. Dataplex quality scans: present.


144 cells scored across 4 arm/tier pairs.

## Headline

| config | tier | accuracy (mean) | tokens in / correct | tokens out / correct | sec / correct | BQ jobs / correct | MiB / correct | coverage |
|---|---|---|---|---|---|---|---|---|
| p2_managed | 0 | 44% | 282747 | 3331 | 171 | 19.0 | 180.8 | full |
| p2_managed | 1 | 100% | 55442 | 693 | 33 | 3.2 | 43.3 | full |
| p2_toolbox | 0 | 41% | 548021 | 3852 | 174 | 19.7 | 161.8 | full |
| p2_toolbox | 1 | 100% | 72185 | 815 | 35 | 3.1 | 35.6 | full |



## Capture health

| config | tier | attempted | scored | failed | quota-retried | CA leak |
|---|---|---|---|---|---|---|
| p2_managed | 0 | 36 | 36 | 0 | 0 | 0% |
| p2_managed | 1 | 36 | 36 | 0 | 0 | 0% |
| p2_toolbox | 0 | 36 | 36 | 0 | 0 | 0% |
| p2_toolbox | 1 | 36 | 36 | 0 | 0 | 0% |

**CA leak** is not a bug in the run — it is a property of the surface being measured. `ask_data_insights` ships inside the Toolbox BigQuery toolset, so `p1_toolbox` and `p3_toolbox` can reach Conversational Analytics and become Path 4 for that cell. The arms are reported as shipped rather than trimmed to be hermetic, so this column says how often it happened instead of hiding it.

## Accuracy

| config | tier | n | graded | correct | sprang trap | used decoy |
|---|---|---|---|---|---|---|
| p2_managed | 0 | 36 | 27 | 44% | 25% | 50% |
| p2_managed | 1 | 36 | 27 | 100% | 0% | 3% |
| p2_toolbox | 0 | 36 | 27 | 41% | 28% | 50% |
| p2_toolbox | 1 | 36 | 27 | 100% | 0% | 0% |

**36 of 144 cells are excluded from every rate above.** 3 of the battery's questions are worded so that two answers are equally defensible, which makes the oracle an arbiter of a coin-flip rather than a grader. The cells ran, are in the capture, and carry a `correct` a reader can inspect — they are *unmeasured*, not zero, the same way an opaque path's evidence reads `--`.

* `governed-q1` — The governed rule defines Active as "had an event in the trailing 30 days", which pins the window's length but not its anchor. The answer is a count - extensive, so the two defensible anchorings differ by more than the 0.5% tolerance. See semantic-q2.
* `governed-q3` — Inherits the Active definition's unpinned anchor from governed-q1, and sums over it. The answer is an extensive quantity twice over - which users count, and how much they spent - so the two defensible anchorings diverge well past the 0.5% tolerance. See semantic-q2.
* `semantic-q2` — "trailing 30 days" pins the window's length but not its anchor. Anchoring to the data's latest timestamp is as defensible as anchoring to now, and agents pick between them nondeterministically at temperature 0 - the same arm answered 2,699 and 2,804 in consecutive runs. The answer is an extensive quantity (a sum), so the two readings differ by more than the 0.5% tolerance and the oracle arbitrates a coin-flip.

## Acquisition vs application

| config | tier | n | opaque | acquired | application loss |
|---|---|---|---|---|---|
| p2_managed | 0 | 21 | 0% | 0% | 0% |
| p2_managed | 1 | 21 | 0% | 100% | 0% |
| p2_toolbox | 0 | 21 | 0% | 0% | 0% |
| p2_toolbox | 1 | 21 | 0% | 100% | 0% |

## Evidence

| config | tier | no query disclosed | recall (median) | IQR | precision |
|---|---|---|---|---|---|
| p2_managed | 0 | 0% | 1.00 | 0.15 | 0.92 |
| p2_managed | 1 | 0% | 1.00 | 0.00 | 1.00 |
| p2_toolbox | 0 | 0% | 1.00 | 0.00 | 0.92 |
| p2_toolbox | 1 | 0% | 1.00 | 0.00 | 1.00 |

## Latency

| config | tier | clean cells | excluded | median s | IQR | tool calls |
|---|---|---|---|---|---|---|
| p2_managed | 0 | 36 | 0 | 58.2 | 54.5 | 14.0 |
| p2_managed | 1 | 36 | 0 | 28.9 | 19.4 | 7.0 |
| p2_toolbox | 0 | 36 | 0 | 59.8 | 43.6 | 15.0 |
| p2_toolbox | 1 | 36 | 0 | 30.3 | 21.4 | 7.0 |

## Cost

| config | tier | tokens (median) | IQR | thoughts | MiB billed | USD (mean) | unmeasured spend |
|---|---|---|---|---|---|---|---|
| p2_managed | 0 | 85537 | 73400 | 1604 | 60.0 | 0.00045 | full |
| p2_managed | 1 | 33666 | 23255 | 572 | 30.0 | 0.00027 | full |
| p2_toolbox | 0 | 74448 | 157340 | 1630 | 50.0 | 0.00040 | full |
| p2_toolbox | 1 | 26870 | 37107 | 584 | 20.0 | 0.00023 | full |

Prices: cloud.google.com/bigquery/pricing, US multi-region on-demand list price (verified 2026-09-03). Token rates are unset unless a `prices.json` supplies them, so a `--` in the USD column means *unpriced*, not free. Dollars are the only derived number in this report and the only one that depends on a rate card, which is why every other column is in units consumed.

The last column is how complete the picture is. **full** means everything this sweep spent, it saw. **floor** means the arm also spent model tokens server-side that the API never reported back — Conversational Analytics runs its own Gemini loop on our behalf. A floor is a lower bound, not a total, and it is not small: `make service-tokens` meters it from Cloud Monitoring and finds `p4_looker_ca` consumed 22x the tokens recorded here.

## Semantic adherence (judged)

| config | tier | n | governed | partial | invented | unclear |
|---|---|---|---|---|---|---|

## Equivalence

| config A | config B | pairs | graded | same tool sequence | same value | same verdict |
|---|---|---|---|---|---|---|
| p2_managed | p2_toolbox | 72 | 54 | 3% | 94% | 98% |

## Tool surface

Schemas are re-sent on every turn, so their size is a per-call floor on prompt tokens. Measured live at sweep time, because a vendor can change them without notice.

| config | tools | schema chars |
|---|---|---|
| p2_managed | 7 | 11721 |
| p2_toolbox | 7 | 5602 |
