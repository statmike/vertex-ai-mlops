"""Invariants for the report tables.

Almost all of these are one rule stated in different places: **a number that was
never measured must not print as 0**. A zero in an accuracy table is a claim the
arm got everything wrong; a zero in a cost table is a claim it was free. Both
were produced by earlier drafts of this module, and both looked completely
normal in a rendered markdown table.
"""

import cost
import judge
import report
import scoring
import service_tokens
import traces


def _score(key, config="p1_managed", tier=1, **kwargs):
    return scoring.Score(
        cell_key=key, config=config, tier=tier, question_id="q", category="direct", **kwargs
    )


def test_unmeasured_prints_as_a_dash_not_a_zero():
    assert report.fmt(None) == report.DASH
    assert report.fmt(0.0) == "0.00"


def test_headline_usage_survives_without_the_cost_pass():
    # `--no-cost` must still produce a usage table. An earlier draft divided an
    # empty cost list and printed `0 tokens / correct` for every arm. Tokens and
    # seconds are copied onto the Score off the capture for exactly this reason;
    # only the warehouse columns depend on the BigQuery attribution pass. A later
    # draft re-sourced the token columns from CellCost and silently undid it.
    scores = {
        "a": _score("a", answered=True, correct=True,
                    prompt_tokens=800, output_tokens=200, latency_s=6.0),
        "b": _score("b", answered=True, correct=False,
                    prompt_tokens=2400, output_tokens=600, latency_s=10.0),
    }
    table = report.headline(scores, {})
    assert "3200" in table  # input tokens, one correct answer
    assert "800" in table  # output tokens
    assert "16" in table  # seconds
    # BQ jobs, MiB and coverage are the only things the cost pass owns.
    assert "| -- | -- | -- |" in table


def test_headline_reports_dash_not_infinity_when_nothing_was_correct():
    # Dividing by zero correct answers yields `inf`, which sorts to the *bottom*
    # of a "most expensive" list and reads as the opposite of what happened.
    scores = {"a": _score("a", answered=True, correct=False, total_tokens=5000)}
    row = report.headline(scores, {}).splitlines()[-1]
    assert "inf" not in row
    assert row.count(report.DASH) >= 3


def test_coverage_distinguishes_unpriced_from_incomplete():
    priced = [cost.CellCost(cell_key="a", config="p1_toolbox", tier=1)]
    opaque = [cost.CellCost(cell_key="a", config="p4_bq_ca", tier=1,
                            service_side_unmeasured=True)]
    assert report._coverage([]) == report.DASH
    assert report._coverage(priced) == "full"
    assert report._coverage(opaque) == "floor"
    assert report._coverage(priced, no_local_model=True) == report.SERVICE_ONLY


def test_an_arm_with_no_local_model_turn_reports_dashes_not_zero_tokens():
    # The direct-API arms never call a model in this process, so `usage.py`
    # honestly records 0. Printing that 0 would put the arm at the top of every
    # "cheapest" sort while its entire model bill sits on a meter this report
    # cannot read — the exact inversion `cost.py` exists to prevent.
    direct = {
        f"c{i}": _score(f"c{i}", config="p4_bq_direct", answered=True, correct=True,
                        model_calls=0, total_tokens=0, prompt_tokens=0, output_tokens=0)
        for i in range(4)
    }
    costs = {
        key: cost.CellCost(cell_key=key, config="p4_bq_direct", tier=1,
                           service_side_unmeasured=True)
        for key in direct
    }
    spend = report.spend(direct, costs, cost.DEFAULT_PRICES)
    row = [line for line in spend.splitlines() if line.startswith("| p4_bq_direct")][0]
    assert row.count(report.DASH) >= 3, row
    assert report.SERVICE_ONLY in row
    assert report.SERVICE_ONLY in spend, "the legend must explain the state it printed"

    headline = report.headline(direct, costs)
    tokens_in, tokens_out = headline.splitlines()[-1].split("|")[4:6]
    assert tokens_in.strip() == report.DASH
    assert tokens_out.strip() == report.DASH


def test_a_capture_that_never_recorded_model_calls_keeps_its_token_numbers():
    # `model_calls=None` is *not recorded*; only 0 means "no local turn". The
    # first cut defaulted the field to 0, so re-rendering the published
    # scores.json — written before the field existed — blanked the token columns
    # on all twenty arm/tier rows while every underlying number was intact.
    legacy = {
        f"c{i}": _score(f"c{i}", answered=True, correct=True, model_calls=None,
                        total_tokens=5000, prompt_tokens=4000, output_tokens=1000)
        for i in range(4)
    }
    assert not report._no_local_model(list(legacy.values()))
    spend = report.spend(legacy, {}, cost.DEFAULT_PRICES)
    assert "5000" in spend
    assert report.SERVICE_ONLY not in spend, "a legend for an absent state is noise"


def test_headline_note_names_the_floor_arms_and_stays_silent_without_them():
    # The note exists because the floor arms' numbers are the smallest on the
    # page precisely *because* they are incomplete, so the table reads as a
    # ranking that is upside down at the top. It must name whichever arms are
    # actually floors in this capture, not a list written down once.
    full = {"a": cost.CellCost(cell_key="a", config="p1_toolbox", tier=1)}
    assert report.headline_note(full) == ""
    assert report.headline_note({}) == ""

    mixed = full | {
        "b": cost.CellCost(cell_key="b", config="p4_bq_ca", tier=1,
                           service_side_unmeasured=True),
        "c": cost.CellCost(cell_key="c", config="p4_looker_ca", tier=0,
                           service_side_unmeasured=True),
    }
    note = report.headline_note(mixed)
    assert "`p4_bq_ca`" in note and "`p4_looker_ca`" in note
    assert "`p1_toolbox`" not in note, "a full-coverage arm must not be caveated"
    assert f"{service_tokens.MEASURED_UNDERSTATEMENT}x" in note


def test_accuracy_denominator_is_cells_attempted():
    # An arm that crashes on half its cells and aces the rest is a 50% arm, not
    # a 100% arm (DESIGN §9.4).
    scores = {
        "a": _score("a", answered=True, correct=True),
        "b": _score("b", answered=False, correct=False),
    }
    row = report.accuracy(scores).splitlines()[-1]
    assert "| 2 | 50% |" in row


def test_opaque_arm_shows_dashes_not_zeroes_for_acquisition():
    # Path 4 cannot be inspected for acquisition. Printing 0% would rank it below
    # every other arm on a metric it was never eligible for.
    scores = {
        "a": _score("a", config="p4_bq_ca", answered=True,
                    rules_required=["net-revenue"], acquisition_observable=False),
    }
    row = report.acquisition(scores).splitlines()[-1]
    assert row.endswith(f"| 100% | {report.DASH} | {report.DASH} |")


def test_latency_excludes_quota_retried_cells_and_says_how_many():
    # A retried cell carries up to ~300s of backoff sleep. Pooling it with clean
    # cells publishes a fake number.
    scores = {
        "a": _score("a", answered=True, attempts=1, latency_s=30.0),
        "b": _score("b", answered=True, attempts=3, latency_s=330.0),
    }
    row = report.latency(scores).splitlines()[-1]
    assert "| 1 | 1 | 30.0 |" in row


def test_iqr_is_withheld_below_four_points():
    # `statistics.quantiles` happily returns a spread for three points. Printing
    # it implies a dispersion estimate the sample cannot support.
    assert report.median_iqr([1.0, 2.0, 3.0])[1] is None
    assert report.median_iqr([1.0, 2.0, 3.0, 4.0])[1] is not None
    assert report.median_iqr([]) == (None, None)


def test_report_renders_with_every_optional_pass_skipped():
    # The cheapest, most-used invocation. It must not raise on empty judge and
    # cost inputs, because that is what anyone reproducing this runs first.
    scores = {"a": _score("a", answered=True, correct=True, total_tokens=10)}
    cells = {
        "a": traces.Cell(cell_key="a", question_id="q", category="direct", question="?",
                         config="p1_managed", tier=1, run=1, answer="42"),
    }
    text = report.build(cells, scores, {}, {}, cost.Prices(), {"agent_model": "m"})
    assert "# Results" in text
    assert "## Headline" in text


def test_adherence_covers_every_verdict_value():
    scores = {"a": _score("a", answered=True)}
    verdicts = {"a": judge.Verdict(cell_key="a", adherence="governed")}
    table = report.adherence(scores, verdicts)
    for value in judge.ADHERENCE_VALUES:
        assert value in table


def test_a_single_run_capture_still_prints_its_one_commit():
    line = report._provenance({"git_commit": "834421c3", "started": "2026-09-05T02:07:23+00:00"})
    assert line == "commit `834421c3`, started 2026-09-05T02:07:23+00:00"


def test_a_merged_capture_attributes_each_arm_to_the_code_that_ran_it():
    # Printing the first commit for all of them would say code that never
    # touched the direct arms produced their numbers.
    line = report._provenance({
        "git_commit": "834421c3",  # present but stale; merged_from wins
        "started": "2026-09-05T02:07:23+00:00",
        "merged_from": [
            {"git_commit": "834421c3", "started": "2026-09-05T02:07:23+00:00",
             "configs": ["p1_managed"]},
            {"git_commit": "b987b497", "started": "2026-09-07T14:26:18+00:00",
             "configs": ["p4_bq_direct", "p4_bq_direct_ctx"]},
        ],
    })
    assert line.startswith("merged from 2 runs:")
    assert "`b987b497` (p4_bq_direct, p4_bq_direct_ctx, started 2026-09-07T14:26:18+00:00)" in line
    assert "`834421c3` (p1_managed, started 2026-09-05T02:07:23+00:00)" in line


def test_scan_state_keeps_unmeasured_distinct_from_absent():
    # Three states, not two. A capture written before the field existed did not
    # look; reporting that as "absent" would be an unmeasured thing reported as
    # a zero, which is the mistake this project exists to avoid.
    assert report._scan_state({"quality_scans": True}) == "present"
    assert report._scan_state({"quality_scans": False}) == "absent"
    assert report._scan_state({"quality_scans": None}) == "not recorded"
    assert report._scan_state({}) == "not recorded"


def test_a_capture_that_cannot_say_carries_the_path3_warning():
    # With the scans in place `lookup_context` adds a `qualityStatus` line on
    # every Path 3 arm, so an unlabelled capture must say it cannot tell.
    assert "Path 3 comparability" in report._scan_note({})
    assert "Path 3 comparability" in report._scan_note({"quality_scans": None})
    # ...and a capture that does say needs no caveat.
    assert report._scan_note({"quality_scans": True}) == ""
    assert report._scan_note({"quality_scans": False}) == ""


def test_scored_records_survive_the_scores_json_round_trip():
    # `build_results.py --from-scores` rebuilds report.md from a previous run's
    # scores.json instead of paying for a judge pass. That only stays honest if
    # asdict() -> json -> **kwargs is lossless; a field that serializes to
    # something its constructor will not take turns a free re-render into a
    # silently different report.
    import dataclasses
    import json as json_module

    import cost as cost_module
    import judge as judge_module
    import scoring as scoring_module

    originals = [
        scoring_module.Score(
            cell_key="k", config="p3_toolbox", tier=1, question_id="q", category="governed-logic",
            answered=True, correct=True, rules_required=["net-revenue"], rules_acquired=[],
            notes=["a note"],
        ),
        cost_module.CellCost(cell_key="k", config="p3_toolbox", tier=1, bq_jobs=3),
        judge_module.Verdict(cell_key="k", adherence="adheres", rationale="r", stated_value="1"),
    ]
    for original in originals:
        revived = type(original)(
            **json_module.loads(json_module.dumps(dataclasses.asdict(original), default=str))
        )
        assert revived == original, f"{type(original).__name__} does not round-trip"
