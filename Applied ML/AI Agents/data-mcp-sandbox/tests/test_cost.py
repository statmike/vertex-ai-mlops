"""Offline invariants for cost attribution. No BigQuery — window logic and pricing.

The live half is verified separately and recorded in DEV_NOTES: a Path 4 cell's
window contained exactly one job, under the tier-1 service account, running CA's
own generated net-revenue SQL. What is tested here is everything that could turn
that into a wrong number without erroring.
"""

from datetime import UTC, datetime, timedelta

import pytest

import cost
import traces


def _cell(key, config="p1_managed", start=0, end=30, usage=None):
    base = datetime(2026, 9, 3, 12, 0, 0, tzinfo=UTC)
    return traces.Cell(
        cell_key=key, question_id="q", category="direct", question="?",
        config=config, tier=1, run=1, answer="42", usage=usage or {},
        started_at=(base + timedelta(seconds=start)).isoformat(timespec="seconds"),
        ended_at=(base + timedelta(seconds=end)).isoformat(timespec="seconds"),
    )


def _job(offset_s, bytes_billed=10 * 2**20):
    base = datetime(2026, 9, 3, 12, 0, 0, tzinfo=UTC)
    return cost.Job(
        job_id=f"j{offset_s}", user_email="mcp-sandbox-t1@x.iam.gserviceaccount.com",
        created=base + timedelta(seconds=offset_s),
        bytes_billed=bytes_billed, statement_type="SELECT",
    )


def test_jobs_land_in_the_cell_that_was_running():
    cells = [_cell("a", start=0, end=30), _cell("b", start=40, end=70)]
    result = cost.attribute(cells, [_job(10), _job(50), _job(55)])
    assert len(result.by_cell["a"]) == 1
    assert len(result.by_cell["b"]) == 2
    assert not result.unattributed


def test_a_job_between_cells_is_reported_not_spread_around():
    # Setup, teardown and the schema-measurement pass all issue jobs outside any
    # cell. Silently dividing them among cells would inflate every arm equally
    # and hide that they happened at all.
    cells = [_cell("a", start=0, end=30), _cell("b", start=40, end=70)]
    result = cost.attribute(cells, [_job(35, bytes_billed=999)])
    assert result.by_cell["a"] == []
    assert result.unattributed_bytes == 999


def test_unpriced_is_none_not_zero():
    # The whole reason this module exists: a zero in a cost column is a claim
    # that something was free, and CA's service-side model calls are not free.
    entry = cost.cell_costs(
        [_cell("a", usage={"prompt_tokens": 1000, "output_tokens": 500})],
        cost.attribute([_cell("a")], [_job(10)]),
        cost.Prices(),
    )["a"]
    assert entry.model_usd is None
    assert entry.warehouse_usd is None
    assert entry.total_usd is None
    assert entry.bytes_billed > 0  # the physical unit is still measured


def test_warehouse_price_applies_without_token_prices():
    entry = cost.cell_costs(
        [_cell("a")], cost.attribute([_cell("a")], [_job(10, bytes_billed=cost.TIB)]),
        cost.Prices(bq_per_tib_usd=6.25),
    )["a"]
    assert entry.warehouse_usd == pytest.approx(6.25)
    assert entry.model_usd is None
    assert entry.total_usd == pytest.approx(6.25)


def test_thoughts_are_not_billed_twice():
    # `usage.py` reports thought_tokens as a *component* of output_tokens. On a
    # reasoning model thoughts often dominate, so adding them again would be the
    # single largest error the cost table could contain.
    usage = {"prompt_tokens": 0, "output_tokens": 1000, "thought_tokens": 800}
    entry = cost.cell_costs(
        [_cell("a", usage=usage)], cost.Attribution(by_cell={"a": []}),
        cost.Prices(input_per_mtok_usd=1.0, output_per_mtok_usd=1000.0),
    )["a"]
    assert entry.model_usd == pytest.approx(1.0)


def test_path_4_is_marked_as_having_unmeasured_spend():
    attribution = cost.Attribution(by_cell={"a": [], "b": []})
    costs = cost.cell_costs(
        [_cell("a", config="p4_bq_ca"), _cell("b", config="p1_toolbox")],
        attribution, cost.Prices(),
    )
    assert costs["a"].service_side_unmeasured
    assert not costs["b"].service_side_unmeasured


def test_a_capture_without_timestamps_refuses_rather_than_reports_zero():
    # The M3 capture predates the instrumentation. Attributing it would produce a
    # table of zeros indistinguishable from "these paths used no warehouse".
    stale = traces.Cell(
        cell_key="k", question_id="q", category="direct", question="?",
        config="p1_managed", tier=1, run=1, answer="42",
    )
    with pytest.raises(ValueError, match="predates the cost instrumentation"):
        cost.window([stale])


def test_default_prices_are_dated_and_sourced():
    # A price with no provenance cannot be re-checked, and list prices move.
    assert cost.DEFAULT_PRICES.verified
    assert cost.DEFAULT_PRICES.source
    # Token rates are deliberately absent — they could not be verified.
    assert cost.DEFAULT_PRICES.input_per_mtok_usd is None


def test_jobs_view_follows_the_configured_region():
    # A sandbox built in the EU has no `region-us` view at all.
    assert "INFORMATION_SCHEMA.JOBS_BY_PROJECT" in cost.JOBS_VIEW
    assert cost.JOBS_VIEW.startswith("`region-")
