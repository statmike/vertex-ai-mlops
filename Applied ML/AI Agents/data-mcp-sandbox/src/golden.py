"""Golden-truth oracle — the correct numeric answer for every battery question.

Answers are **always recomputed live** against the corpus, never cached. The
generator anchors timestamps to build time (`bq_setup`), so a cached number would
silently rot as the sandbox ages.

Each entry pairs the governed-correct answer with the `trap` answer a naive agent
produces when it misses the governance. Scoring uses both: matching `value` is
correct, matching `trap_value` is a *diagnosed* failure ("sprang the trap") rather
than an undifferentiated wrong number, which is what makes the trap taxonomy in
DESIGN.md §6 legible in the results.

Windows are stated as **trailing N days**, not calendar months. "Last month" is
ambiguous between the two and the oracle cannot score an answer the question did
not pin down — battery questions must use the trailing-window phrasing.
"""

from collections.abc import Callable
from dataclasses import dataclass

from google.cloud import bigquery

import config
import corpus

# Relative tolerance for a numeric match. Generous enough to absorb rounding and
# float aggregation order, tight enough that a trap answer never passes: the
# smallest gap between a correct and a trap answer in this corpus is the 25%
# gross-vs-net spread.
DEFAULT_TOLERANCE = 0.005


@dataclass(frozen=True)
class Golden:
    """One oracle entry: the right answer, and the wrong one worth naming."""

    key: str
    description: str
    sql: Callable[[int], str]
    trap_sql: Callable[[int], str] | None = None
    trap_name: str = ""
    tolerance: float = DEFAULT_TOLERANCE


@dataclass(frozen=True)
class Resolved:
    """A golden entry evaluated against a live tier."""

    key: str
    value: float
    trap_value: float | None
    tolerance: float
    trap_name: str


def _t(tier: int, table: str) -> str:
    return f"`{config.table_ref(tier, table)}`"


def _txn(tier: int) -> str:
    return _t(tier, corpus.TRANSACTIONS.name)


def _users(tier: int) -> str:
    return _t(tier, corpus.USERS.name)


def _events(tier: int) -> str:
    return _t(tier, corpus.RAW_EVENTS.name)


def _recent(days: int = corpus.ACTIVE_WINDOW_DAYS) -> str:
    return f"TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)"


def _active_users_cte(tier: int) -> str:
    """The governed definition of Active: flagged AND seen in the trailing window."""
    return f"""
    SELECT u.user_id
    FROM {_users(tier)} u
    WHERE u.is_active
      AND EXISTS (
        SELECT 1 FROM {_events(tier)} e
        WHERE e.user_id = u.user_id AND e.event_ts >= {_recent()}
      )
    """


# --- The oracle --------------------------------------------------------------

GOLDENS: list[Golden] = [
    # direct — answerable from raw schema alone, no governance needed.
    Golden(
        key="total_users",
        description="Count of rows in users.",
        sql=lambda t: f"SELECT COUNT(*) AS v FROM {_users(t)}",
    ),
    Golden(
        key="distinct_event_types",
        description="Count of distinct event_type values in raw_events_2026.",
        sql=lambda t: f"SELECT COUNT(DISTINCT event_type) AS v FROM {_events(t)}",
    ),
    # semantic-ambiguity — needs txn_amt_x2 (T1) and the refund exclusion (T2).
    Golden(
        key="net_revenue_all_time",
        description="SUM(txn_amt_x2) over non-refunded transactions.",
        sql=lambda t: f"SELECT SUM(txn_amt_x2) AS v FROM {_txn(t)} WHERE NOT status_flg",
        trap_sql=lambda t: f"SELECT SUM(revenue_amount) AS v FROM {_txn(t)}",
        trap_name="summed gross list price instead of net revenue",
    ),
    Golden(
        key="net_revenue_trailing_30d",
        description="Net revenue over the trailing 30 days, refunds excluded.",
        sql=lambda t: (
            f"SELECT SUM(txn_amt_x2) AS v FROM {_txn(t)} "
            f"WHERE NOT status_flg AND txn_ts >= {_recent()}"
        ),
        trap_sql=lambda t: (
            f"SELECT SUM(txn_amt_x2) AS v FROM {_txn(t)} WHERE txn_ts >= {_recent()}"
        ),
        trap_name="included refunded transactions",
    ),
    Golden(
        key="net_revenue_top_region",
        description="Net revenue of the single highest-earning region.",
        sql=lambda t: f"""
            SELECT SUM(x.txn_amt_x2) AS v
            FROM {_txn(t)} x
            JOIN {_users(t)} u USING (user_id)
            WHERE NOT x.status_flg
            GROUP BY u.region
            ORDER BY v DESC
            LIMIT 1
        """,
        trap_sql=lambda t: f"""
            SELECT SUM(x.revenue_amount) AS v
            FROM {_txn(t)} x
            JOIN {_users(t)} u USING (user_id)
            GROUP BY u.region
            ORDER BY v DESC
            LIMIT 1
        """,
        trap_name="ranked regions by gross list price",
    ),
    # governed-logic — needs the governed definition of Active (T3).
    Golden(
        key="active_user_count",
        description="Users matching the governed Active definition.",
        sql=lambda t: f"SELECT COUNT(*) AS v FROM ({_active_users_cte(t)})",
        trap_sql=lambda t: f"SELECT COUNTIF(is_active) AS v FROM {_users(t)}",
        trap_name="trusted the raw is_active flag",
    ),
    Golden(
        key="avg_txn_value_active_users",
        description="Average net transaction value for governed-Active users.",
        sql=lambda t: f"""
            SELECT AVG(x.txn_amt_x2) AS v
            FROM {_txn(t)} x
            JOIN ({_active_users_cte(t)}) a USING (user_id)
            WHERE NOT x.status_flg
        """,
        trap_sql=lambda t: f"""
            SELECT AVG(x.txn_amt_x2) AS v
            FROM {_txn(t)} x
            JOIN {_users(t)} u USING (user_id)
            WHERE u.is_active
        """,
        trap_name="trusted the raw is_active flag",
    ),
    Golden(
        key="net_revenue_from_active_users",
        description="Net revenue attributable to governed-Active users.",
        sql=lambda t: f"""
            SELECT SUM(x.txn_amt_x2) AS v
            FROM {_txn(t)} x
            JOIN ({_active_users_cte(t)}) a USING (user_id)
            WHERE NOT x.status_flg
        """,
        trap_sql=lambda t: f"""
            SELECT SUM(x.txn_amt_x2) AS v
            FROM {_txn(t)} x
            JOIN {_users(t)} u USING (user_id)
            WHERE u.is_active AND NOT x.status_flg
        """,
        trap_name="trusted the raw is_active flag",
    ),
    # metadata — profiling and data quality (T4).
    Golden(
        key="null_revenue_count",
        description="Transactions with a NULL txn_amt_x2.",
        sql=lambda t: f"SELECT COUNTIF(txn_amt_x2 IS NULL) AS v FROM {_txn(t)}",
    ),
    Golden(
        key="refunded_txn_count",
        description="Transactions flagged as refunded.",
        sql=lambda t: f"SELECT COUNTIF(status_flg) AS v FROM {_txn(t)}",
    ),
    # trap — phrased to bait a decoy outright.
    Golden(
        key="list_price_outlier_count",
        description="Transactions whose revenue_amount is an extreme outlier.",
        sql=lambda t: f"""
            SELECT COUNTIF(revenue_amount > 100 * txn_amt_x2) AS v
            FROM {_txn(t)}
            WHERE txn_amt_x2 IS NOT NULL
        """,
    ),
    Golden(
        key="gross_minus_net_gap_pct",
        description=(
            "Percent by which naively summing revenue_amount overstates net revenue. "
            "Far above the 25% per-transaction spread, because the T4 list-price "
            "outliers dominate the aggregate — which is the point: the two traps "
            "compound, and an agent that dodges only the naming trap still lands here."
        ),
        sql=lambda t: f"""
            SELECT 100 * (SUM(revenue_amount) - SUM(IF(status_flg, 0, txn_amt_x2)))
                   / SUM(IF(status_flg, 0, txn_amt_x2)) AS v
            FROM {_txn(t)}
        """,
    ),
]

BY_KEY: dict[str, Golden] = {g.key: g for g in GOLDENS}


# --- Resolution --------------------------------------------------------------


def _scalar(client: bigquery.Client, sql: str) -> float:
    row = next(iter(client.query(sql).result()), None)
    if row is None or row["v"] is None:
        raise RuntimeError(f"Golden query returned no value:\n{sql}")
    return float(row["v"])


def resolve(client: bigquery.Client, key: str, tier: int) -> Resolved:
    """Evaluate one golden entry against a live tier."""
    if key not in BY_KEY:
        raise KeyError(f"Unknown golden key: {key}. Known: {sorted(BY_KEY)}")
    g = BY_KEY[key]
    return Resolved(
        key=key,
        value=_scalar(client, g.sql(tier)),
        trap_value=_scalar(client, g.trap_sql(tier)) if g.trap_sql else None,
        tolerance=g.tolerance,
        trap_name=g.trap_name,
    )


def resolve_all(client: bigquery.Client, tier: int) -> dict[str, Resolved]:
    """Evaluate every golden entry against a tier.

    Tier 0 and tier 1 hold identical data, so these numbers must agree across
    tiers — `scripts/setup.py` asserts that, since a divergence means the tiers
    are no longer a clean control.
    """
    return {g.key: resolve(client, g.key, tier) for g in GOLDENS}


def matches(resolved: Resolved, answer: float) -> bool:
    """True when an answer is within relative tolerance of the golden value."""
    return _within(answer, resolved.value, resolved.tolerance)


def sprang_trap(resolved: Resolved, answer: float) -> bool:
    """True when an answer matches the *wrong* number the trap is designed to produce."""
    if resolved.trap_value is None:
        return False
    return _within(answer, resolved.trap_value, resolved.tolerance)


def _within(actual: float, expected: float, tolerance: float) -> bool:
    if expected == 0:
        return abs(actual) <= tolerance
    return abs(actual - expected) / abs(expected) <= tolerance
