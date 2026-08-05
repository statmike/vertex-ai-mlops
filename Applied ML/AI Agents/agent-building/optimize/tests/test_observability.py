"""Tests for the observability SQL builders (offline — no BigQuery)."""

import pytest

from optimize.harness.observability import (
    _validate_table_id,
    agent_activity_sql,
    event_summary_sql,
)

GOOD = "my-project.retail_analytics.agent_events"


def test_validate_accepts_well_formed_id():
    assert _validate_table_id(GOOD) == GOOD


@pytest.mark.parametrize(
    "bad",
    [
        "only.two",
        "a.b.c.d",
        "proj..table",
        "proj.dataset.",
        "proj.data set.table",  # space
        "proj.dataset.tab`le",  # backtick — would break out of the quoted id
        "proj.dataset.tab;le",  # statement separator
    ],
)
def test_validate_rejects_bad_ids(bad):
    with pytest.raises(ValueError):
        _validate_table_id(bad)


def test_event_summary_sql_shape():
    sql = event_summary_sql(GOOD, days=3)
    assert f"`{GOOD}`" in sql
    assert "INTERVAL 3 DAY" in sql
    assert "event_type" in sql
    assert "COUNTIF(status = 'ERROR')" in sql


def test_agent_activity_sql_shape():
    sql = agent_activity_sql(GOOD, days=14)
    assert f"`{GOOD}`" in sql
    assert "INTERVAL 14 DAY" in sql
    assert "COUNT(DISTINCT session_id)" in sql


def test_days_is_coerced_to_int():
    # A string that looks numeric must not leak into the SQL as-is.
    sql = event_summary_sql(GOOD, days="5")  # type: ignore[arg-type]
    assert "INTERVAL 5 DAY" in sql


def test_builders_reject_bad_table_id():
    with pytest.raises(ValueError):
        event_summary_sql("bad;drop", days=7)
    with pytest.raises(ValueError):
        agent_activity_sql("bad;drop", days=7)
