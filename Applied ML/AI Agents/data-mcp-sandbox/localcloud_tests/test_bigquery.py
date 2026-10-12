"""Exercise sandbox provisioning and its golden oracle over native LocalCloud REST."""

import pytest
from google.cloud import bigquery

import bq_setup
import config
import corpus
import golden


def test_dataset_provisioning(bq_client: bigquery.Client) -> None:
    for tier in config.TIERS:
        dataset = bq_client.get_dataset(config.dataset_ref(tier), timeout=30)
        assert dataset.project == config.PROJECT_ID
        assert dataset.dataset_id == config.tier_dataset(tier)
        assert dataset.description == bq_setup.DATASET_DESCRIPTION
        assert dataset.location == config.BQ_LOCATION


@pytest.mark.parametrize("tier", [0, 1])
def test_corpus_row_counts(bq_client: bigquery.Client, tier: int) -> None:
    counts = bq_setup.row_counts(bq_client, tier)
    assert counts == dict.fromkeys(corpus.TABLE_NAMES, 3)
    assert all(type(value) is int for value in counts.values())


@pytest.mark.parametrize("tier", [0, 1])
def test_oracle_counts(bq_client: bigquery.Client, tier: int) -> None:
    users = golden.resolve(bq_client, "total_users", tier)
    events = golden.resolve(bq_client, "distinct_event_types", tier)
    assert users.value == 3.0
    assert events.value == 2.0
    assert type(users.value) is float
    assert type(events.value) is float


@pytest.mark.parametrize("tier", [0, 1])
def test_refund_exclusion_and_gross_revenue_trap(bq_client: bigquery.Client, tier: int) -> None:
    resolved = golden.resolve(bq_client, "net_revenue_all_time", tier)
    assert resolved.value == 30.0
    assert resolved.trap_value == 105.0
    assert type(resolved.value) is float
    assert type(resolved.trap_value) is float
    assert golden.matches(resolved, 30.0)
    assert not golden.matches(resolved, 105.0)
    assert golden.trap_sprung(resolved, 105.0) == resolved.trap_name
