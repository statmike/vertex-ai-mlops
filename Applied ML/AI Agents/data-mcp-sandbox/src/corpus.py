"""The trap corpus — single source of truth for tables, traps, and governance.

Imported by provisioning (`bq_setup`, `catalog_setup`), by the golden-truth
oracle, and by the report generator, so documentation can never drift from what
`scripts/setup.py` actually creates.

Three tables, four deliberate traps. Every trap is a case where the naive read of
the raw schema produces a *plausible but wrong* answer, and only governed context
(catalog aspects or the LookML semantic layer) gets it right. See docs/questions.md.
"""

from dataclasses import dataclass, field

# --- Trap calibration --------------------------------------------------------
# These drive both the generated data and the prose in GUIDELINES, so a change
# here propagates to the published governance automatically.

N_USERS = 5_000
PCT_ACTIVE_FLAG = 70  # share of users with is_active = TRUE
PCT_DORMANT = 20  # share of users with no event in the trailing 30 days (T3)
PCT_REFUNDED = 12  # share of transactions refunded (T2)
PCT_NULL_REVENUE = 7  # share of txn_amt_x2 that is NULL (T4)
GROSS_MULTIPLIER = 1.25  # revenue_amount = net x this (T1 decoy)
OUTLIERS_PER_1000 = 5  # revenue_amount outliers (T4)
ACTIVE_WINDOW_DAYS = 30  # trailing window in the governed "Active" definition
HISTORY_DAYS = 400  # how far back events and transactions are generated


@dataclass(frozen=True)
class Column:
    """One column, plus the description published only at tier 1."""

    name: str
    type: str
    description: str
    role: str = "plain"  # plain | trap | decoy


@dataclass(frozen=True)
class Table:
    name: str
    description: str
    columns: list[Column] = field(default_factory=list)


# --- The corpus --------------------------------------------------------------

USERS = Table(
    name="users",
    description="Registered users. The is_active flag is NOT the governed definition of Active.",
    columns=[
        Column("user_id", "STRING", "Unique user identifier."),
        Column(
            "is_active",
            "BOOL",
            "Raw account-status flag. NOT the governed definition of an Active user — "
            "see the Active User business rule.",
            role="trap",
        ),
        Column("signup_date", "DATE", "Date the user registered."),
        Column("region", "STRING", "Sales region: North, South, East, or West."),
    ],
)

TRANSACTIONS = Table(
    name="transactions_v2_final",
    description=(
        "Transaction records. Net revenue lives in txn_amt_x2. The column named "
        "revenue_amount is gross list price, not revenue."
    ),
    columns=[
        Column("txn_id", "STRING", "Unique transaction identifier."),
        Column("user_id", "STRING", "References users.user_id."),
        Column(
            "txn_amt_x2",
            "FLOAT64",
            "Net revenue for the transaction. THIS is the revenue column. "
            "Nullable — a NULL means revenue was never recorded.",
            role="trap",
        ),
        Column(
            "revenue_amount",
            "FLOAT64",
            "MISNAMED. Despite the name this is NOT revenue — it is the gross list "
            "price before discounts, kept from a legacy schema. Do not sum it to "
            "report revenue; use txn_amt_x2.",
            role="decoy",
        ),
        Column(
            "status_flg",
            "BOOL",
            "Refund status. TRUE means the transaction was refunded. Refunded rows "
            "must be excluded from net revenue.",
            role="trap",
        ),
        Column("txn_ts", "TIMESTAMP", "When the transaction occurred."),
    ],
)

RAW_EVENTS = Table(
    name="raw_events_2026",
    description="Raw clickstream events. Used to determine whether a user is genuinely active.",
    columns=[
        Column("event_id", "STRING", "Unique event identifier."),
        Column("user_id", "STRING", "References users.user_id."),
        Column("event_type", "STRING", "One of: page_view, click, add_to_cart, search."),
        Column("event_ts", "TIMESTAMP", "When the event occurred."),
    ],
)

CORPUS: list[Table] = [USERS, TRANSACTIONS, RAW_EVENTS]

TABLE_NAMES: list[str] = [t.name for t in CORPUS]


# --- Governance published at tier 1 only -------------------------------------
# Attached to the Knowledge Catalog entry as the system `guidelines` aspect, so
# it surfaces in the lookup_context capsule. Mirrored by the LookML measures and
# by the golden-truth oracle, which are the only three places these rules live.

NET_REVENUE_RULE = (
    "Net Revenue is SUM(txn_amt_x2) over transactions_v2_final, and MUST exclude "
    "refunded transactions (status_flg = TRUE). Do not use revenue_amount — despite "
    "its name that column is gross list price before discounts. It overstates each "
    "transaction by roughly "
    f"{int((GROSS_MULTIPLIER - 1) * 100)}%, and far more in aggregate because a small "
    "number of revenue_amount rows carry data-quality outliers. NULL txn_amt_x2 "
    "means revenue was never recorded and is excluded from the sum."
)

ACTIVE_USER_RULE = (
    "An Active User is a user whose is_active flag is TRUE AND who has at least one "
    f"event in raw_events_2026 within the trailing {ACTIVE_WINDOW_DAYS} days. The "
    "is_active flag alone is NOT sufficient — roughly "
    f"{PCT_DORMANT}% of flagged users are dormant and must be excluded."
)

GUIDELINES: dict[str, str] = {
    TRANSACTIONS.name: NET_REVENUE_RULE,
    USERS.name: ACTIVE_USER_RULE,
    RAW_EVENTS.name: (
        "Event recency determines whether a user counts as Active. See the Active "
        f"User rule: an event within the trailing {ACTIVE_WINDOW_DAYS} days is required."
    ),
}

@dataclass(frozen=True)
class GlossaryTerm:
    """A business term, linked to the columns it defines."""

    term_id: str
    display: str
    description: str
    columns: dict[str, list[str]]  # table -> columns the term defines


# Real glossary terms. There is no glossary *tool* on any MCP surface, but the
# definitions still reach the model: `lookup_context` renders each linked column
# with a `terms:` field carrying the term and its full text, so at tier 1 a rule
# arrives both here and in the overview aspect (docs/paths.md). Keep the wording
# aligned with the aspect above — scoring treats them as one rule, not two.
GLOSSARY_TERMS: list[GlossaryTerm] = [
    GlossaryTerm(
        term_id="net-revenue",
        display="Net Revenue",
        description=NET_REVENUE_RULE,
        columns={TRANSACTIONS.name: ["txn_amt_x2", "status_flg"]},
    ),
    GlossaryTerm(
        term_id="active-user",
        display="Active User",
        description=ACTIVE_USER_RULE,
        columns={USERS.name: ["is_active"], RAW_EVENTS.name: ["event_ts"]},
    ),
]


def columns_with_descriptions(table: str) -> dict[str, str]:
    """Column -> description for one table (applied at tier 1 only)."""
    for t in CORPUS:
        if t.name == table:
            return {c.name: c.description for c in t.columns}
    raise KeyError(f"Unknown table: {table}")


def decoy_columns() -> list[str]:
    """Columns a naive agent is expected to reach for and should not."""
    return [c.name for t in CORPUS for c in t.columns if c.role == "decoy"]
