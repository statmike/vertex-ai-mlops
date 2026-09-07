"""Turn a capture back into scores — the deterministic pass, reusable.

Lifted out of `examples/build_results.py` when Amendment C.0 gave it a second
caller. Cross-capture comparison needs exactly this and nothing else from the
scorer: resolve the oracle each capture froze at its own sweep start, then grade
every cell against it.

Deliberately **judge-free**. The judge is a model call with a measured ~1.3%
verdict wobble, so putting it in a comparison path would let two captures differ
because they were graded twice rather than because they measured different
things. Everything downstream of here uses `Score.correct`, which is arithmetic.
"""

import json
from typing import Any

from google.cloud import bigquery

import battery
import config
import golden
import scoring
import traces


def resolve_goldens(
    cells: dict[str, traces.Cell], meta: dict[str, Any]
) -> dict[tuple[str, int], dict[str, golden.Resolved]]:
    """The oracle for every (arm, tier) in the capture, frozen if the file carries it.

    A capture written by `export_capture.py` embeds the goldens as they stood
    when the sweep ran. Preferring those is not just an optimization: it is what
    lets a reader with no corpus, no project, and no credentials re-run this
    rubric and argue with it. Otherwise resolve live, which is right for the
    operator because the corpus anchors its timestamps to build time and a stored
    number rots as the sandbox ages (`golden.py`).

    Keyed by arm and not only by tier because a merged capture holds cells from
    runs on different days, and four of this corpus's oracle values are trailing
    windows that move with the calendar. Every arm of an unmerged capture maps to
    the same block, so nothing changes for one.

    A merged run that froze no oracle is refused rather than resolved live: live
    would be today's answer applied to cells captured whenever that run happened,
    which is precisely the rot the freezing exists to prevent.
    """
    present = {cell.config for cell in cells.values()}
    frozen = traces.goldens_by_config(meta, present)
    if frozen:
        missing = sorted(present - set(frozen))
        if missing:
            raise SystemExit(
                f"This capture freezes an oracle for some arms but not {missing}. "
                "Scoring them against another run's frozen values, or against "
                "today's, would grade trailing-window answers against the wrong "
                "day. Export each run before merging."
            )
        blocks = {json.dumps(block, sort_keys=True) for block in frozen.values()}
        print(
            f"using goldens frozen into the capture "
            f"({len(blocks)} oracle{'s' if len(blocks) > 1 else ''} "
            f"across {len(frozen)} arms)"
        )
        return {
            (config_key, int(tier)): {
                key: golden.Resolved(**value) for key, value in entries.items()
            }
            for config_key, block in frozen.items()
            for tier, entries in block.items()
        }

    client = bigquery.Client(project=config.PROJECT_ID)
    live = {
        tier: golden.resolve_all(client, tier) for tier in sorted({c.tier for c in cells.values()})
    }
    return {(cell.config, cell.tier): live[cell.tier] for cell in cells.values()}


def score_all(
    cells: dict[str, traces.Cell], resolved: dict[tuple[str, int], dict[str, golden.Resolved]]
) -> dict[str, scoring.Score]:
    """Deterministic scoring for every cell against the resolved oracle."""
    questions = {question.id: question for question in battery.load_questions()}
    scores = {}
    for key, cell in cells.items():
        question = questions.get(cell.question_id)
        if question is None:
            continue
        scores[key] = scoring.score_cell(
            cell, question.evidence, resolved[(cell.config, cell.tier)].get(question.golden_key)
        )
    return scores
