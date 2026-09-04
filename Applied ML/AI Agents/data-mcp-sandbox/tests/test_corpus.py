"""Offline invariants for the corpus and its configuration.

No cloud calls — these guard the properties that make the experiment valid, so
they must run without credentials.
"""

import pytest

import config
import corpus
import golden


def test_every_tier_has_a_distinct_dataset():
    datasets = [config.tier_dataset(t) for t in config.TIERS]
    assert len(set(datasets)) == len(datasets)


def test_scope_resolves_to_exactly_one_tier_dataset():
    # Scoring matches on short table name, so a scope spanning tiers would make
    # candidates collide silently across tiers.
    assert config.SCOPE in {config.tier_dataset(t) for t in config.TIERS}


def test_set_active_tier_rejects_unknown_tier():
    with pytest.raises(ValueError, match="Unknown tier"):
        config.set_active_tier(99)


def test_set_active_tier_moves_scope():
    original = config.ACTIVE_TIER
    try:
        for tier in config.TIERS:
            config.set_active_tier(tier)
            assert config.tier_dataset(tier) == config.SCOPE
    finally:
        config.set_active_tier(original)


def test_bounded_ids_are_dataplex_valid():
    for tier in config.TIERS:
        for table in corpus.TABLE_NAMES:
            scan_id = config.profile_scan_id(tier, table)
            assert len(scan_id) <= 63
            assert scan_id[0].isalpha()
            assert scan_id[-1].isalnum()
            assert set(scan_id) <= set("abcdefghijklmnopqrstuvwxyz0123456789-")


def test_link_ids_are_unique_across_tiers():
    ids = [
        config.definition_link_id(tier, term.term_id, table, column)
        for tier in config.TIERS
        for term in corpus.GLOSSARY_TERMS
        for table, columns in term.columns.items()
        for column in columns
    ]
    assert len(set(ids)) == len(ids)


def test_every_table_has_a_guideline():
    assert set(corpus.GUIDELINES) == set(corpus.TABLE_NAMES)


def test_glossary_terms_reference_real_columns():
    for term in corpus.GLOSSARY_TERMS:
        for table, columns in term.columns.items():
            known = corpus.columns_with_descriptions(table)
            assert set(columns) <= set(known), f"{term.term_id} -> {table}"


def test_every_column_has_a_description():
    for table in corpus.CORPUS:
        for column in table.columns:
            assert column.description.strip(), f"{table.name}.{column.name}"


def test_traps_and_decoys_exist():
    roles = {c.role for t in corpus.CORPUS for c in t.columns}
    assert "trap" in roles
    assert "decoy" in roles
    assert corpus.decoy_columns() == ["revenue_amount"]


def test_guidelines_name_the_columns_they_govern():
    # The rule text is what reaches the model; if it stops naming the column,
    # the agent has no way to act on it.
    assert "txn_amt_x2" in corpus.NET_REVENUE_RULE
    assert "revenue_amount" in corpus.NET_REVENUE_RULE
    assert "status_flg" in corpus.NET_REVENUE_RULE
    assert "is_active" in corpus.ACTIVE_USER_RULE
    assert str(corpus.ACTIVE_WINDOW_DAYS) in corpus.ACTIVE_USER_RULE


def test_golden_keys_are_unique():
    keys = [g.key for g in golden.GOLDENS]
    assert len(set(keys)) == len(keys)


def test_golden_sql_builds_for_every_tier():
    for g in golden.GOLDENS:
        for tier in config.TIERS:
            sql = g.sql(tier)
            assert config.tier_dataset(tier) in sql
            if g.trap_sql:
                assert config.tier_dataset(tier) in g.trap_sql(tier)


def test_goldens_with_a_trap_name_it():
    for g in golden.GOLDENS:
        assert bool(g.trap_sql) == bool(g.trap_name), g.key


def test_tolerance_cannot_swallow_the_gross_trap():
    # The narrowest correct-vs-trap gap in the corpus is the gross/net spread.
    gap = corpus.GROSS_MULTIPLIER - 1
    assert gap / 2 > golden.DEFAULT_TOLERANCE


def test_matches_and_sprang_trap_are_mutually_exclusive():
    resolved = golden.Resolved(
        key="x", value=100.0, trap_value=125.0, tolerance=0.005, trap_name="t"
    )
    assert golden.matches(resolved, 100.2)
    assert not golden.matches(resolved, 125.0)
    assert golden.sprang_trap(resolved, 125.0)
    assert not golden.sprang_trap(resolved, 100.0)
