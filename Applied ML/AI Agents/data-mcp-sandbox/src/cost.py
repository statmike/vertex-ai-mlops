"""What each cell actually consumed — client tokens, warehouse bytes, and the gap.

The naive reading of the M3 capture was that the Conversational Analytics arms
are the cheapest paths by a wide margin. They are the cheapest *in tokens this
process was billed for*, which is not the same thing: CA runs its own Gemini
calls and its own BigQuery jobs on the caller's behalf. Treating an unmeasured
component as a zero would have published exactly the wrong procurement finding.

So cost is reported in three parts, and they are never silently summed:

| Component | Attributed how | Status |
|-----------|----------------|--------|
| Client tokens | `usage.py`, per cell, from the ADK event stream | measured |
| Warehouse | `INFORMATION_SCHEMA.JOBS_BY_PROJECT`, tier SA + time window | measured |
| Service-side model | CA's own Gemini usage; the API reports none of it | **not here** |

That third row stays a floor *in this module* and is no longer a dead end. The API
reports nothing, but Cloud Monitoring meters the same spend on
`geminidataanalytics.googleapis.com/chat/*`, and `service_tokens.py` reads it back
per arm. It is kept separate rather than folded in here for two reasons: it
attributes by *time block*, not per cell, so it cannot populate a `CellCost`
without inventing a distribution; and it is project-wide, so it is only valid
after a baseline check. Summing it into `total_usd` would bury both caveats. What
it found is not a footnote — `p4_looker_ca` understates its tokens by 22x and is
the third most expensive arm, not the cheapest (`docs/paths.md`).

The warehouse component is the one that makes the comparison fair, and it works
because the sweep hands CA a tier service account: CA's queries run under *our*
identity and land in our jobs table like any other. Validated on live M6 cells —
288 of 290 jobs in the sweep window landed inside a cell's `[started_at,
ended_at]`, and all 26 cells matched at least one job. The two strays fall
between cells and are reported as unattributed rather than spread around.

**Money is opt-in.** Token prices could not be verified against a live pricing
page at build time, and another team's rates differ by region, edition, and
committed-use discount anyway. Physical units are always reported; dollars only
appear when a price is supplied. An unpriced component reads `None`, never 0.0.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from google.cloud import bigquery

import config
import mcp_clients
import traces

# The jobs view is regional and named after the BigQuery location, which is why
# this is derived rather than hardcoded — a sandbox built in EU has no
# `region-us` view at all and would fail with a confusing "not found".
JOBS_VIEW = f"`region-{config.BQ_LOCATION.lower()}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT"

# Only the sweep's own service accounts. Filtering by identity rather than by
# time alone keeps a human running an ad-hoc query in the console during the
# sweep — which happened repeatedly while building this — out of the numbers.
TIER_SA_PREFIX = "mcp-sandbox-t"

PRICES_PATH = Path(config.PROJECT_ROOT) / "prices.json"

TIB = 2**40
MTOK = 1_000_000


@dataclass(frozen=True)
class Prices:
    """Unit prices. `None` means *unpriced*, and must never be read as free."""

    bq_per_tib_usd: float | None = None
    input_per_mtok_usd: float | None = None
    output_per_mtok_usd: float | None = None
    source: str = ""
    verified: str = ""

    @property
    def priced(self) -> bool:
        return any(
            value is not None
            for value in (
                self.bq_per_tib_usd, self.input_per_mtok_usd, self.output_per_mtok_usd
            )
        )


# BigQuery on-demand analysis, US multi-region. Left as the only default because
# it is a stable published list price; the Gemini token rates are deliberately
# absent because they could not be confirmed against the live pricing page when
# this was written, and a guessed rate in a cost table is worse than no rate.
# Override everything by dropping a `prices.json` next to this repo's root.
DEFAULT_PRICES = Prices(
    bq_per_tib_usd=6.25,
    source="cloud.google.com/bigquery/pricing, US multi-region on-demand list price",
    verified="2026-09-03",
)


def load_prices(path: Path = PRICES_PATH) -> Prices:
    """Read `prices.json` if present, else the defaults.

    Not committed, because it is the one input that is genuinely local to
    whoever runs the sweep — list price, negotiated rate, or nothing at all.
    """
    if not path.exists():
        return DEFAULT_PRICES
    payload = json.loads(path.read_text())
    known = {f for f in Prices.__dataclass_fields__}
    return Prices(**{k: v for k, v in payload.items() if k in known})


@dataclass
class Job:
    """One BigQuery job, as far as cost attribution cares."""

    job_id: str
    user_email: str
    created: datetime
    bytes_billed: int
    statement_type: str


@dataclass
class CellCost:
    """One cell's consumption. Physical units always; dollars only if priced."""

    cell_key: str
    config: str
    tier: int

    prompt_tokens: int = 0
    output_tokens: int = 0
    thought_tokens: int = 0
    model_calls: int = 0

    bq_jobs: int = 0
    bytes_billed: int = 0

    model_usd: float | None = None
    warehouse_usd: float | None = None
    # Set on any cell that reached a service that does its own model calls
    # without reporting them. The total is therefore a *floor*, not a total.
    service_side_unmeasured: bool = False

    @property
    def total_usd(self) -> float | None:
        """Measured spend only. `None` if nothing is priced."""
        parts = [p for p in (self.model_usd, self.warehouse_usd) if p is not None]
        return sum(parts) if parts else None


def window(cells: list[traces.Cell]) -> tuple[str, str]:
    """The [first start, last end] of a capture, for one bounded jobs query."""
    stamped = [cell for cell in cells if cell.started_at and cell.ended_at]
    if not stamped:
        raise ValueError(
            "no cell carries started_at/ended_at - this capture predates the cost "
            "instrumentation and cannot be attributed per cell"
        )
    return (
        min(cell.started_at for cell in stamped),
        max(cell.ended_at for cell in stamped),
    )


def fetch_jobs(client: bigquery.Client, start: str, end: str) -> list[Job]:
    """Every tier-SA BigQuery job in the sweep window, in one query.

    One query for the whole window rather than one per cell: 1,200 metadata
    queries would cost more to run than the sweep they are measuring, and would
    themselves show up in the jobs table.
    """
    sql = f"""
        SELECT job_id, user_email, creation_time, total_bytes_billed, statement_type
        FROM {JOBS_VIEW}
        WHERE creation_time BETWEEN @start AND @end
          AND STARTS_WITH(user_email, @prefix)
        ORDER BY creation_time
    """
    params = [
        bigquery.ScalarQueryParameter("start", "TIMESTAMP", start),
        bigquery.ScalarQueryParameter("end", "TIMESTAMP", end),
        bigquery.ScalarQueryParameter("prefix", "STRING", TIER_SA_PREFIX),
    ]
    rows = client.query(
        sql, job_config=bigquery.QueryJobConfig(query_parameters=params)
    ).result()
    return [
        Job(
            job_id=row.job_id,
            user_email=row.user_email,
            created=row.creation_time,
            bytes_billed=int(row.total_bytes_billed or 0),
            statement_type=row.statement_type or "",
        )
        for row in rows
    ]


@dataclass
class Attribution:
    """Jobs mapped to cells, plus what did not map."""

    by_cell: dict[str, list[Job]] = field(default_factory=dict)
    unattributed: list[Job] = field(default_factory=list)

    @property
    def unattributed_bytes(self) -> int:
        return sum(job.bytes_billed for job in self.unattributed)


def attribute(cells: list[traces.Cell], jobs: list[Job]) -> Attribution:
    """Assign each job to the cell whose window contains it.

    Unambiguous only because the sweep is strictly sequential (docs/method.md) —
    with two cells in flight, a job's timestamp would name two possible owners
    and the whole approach would collapse. Timestamps are recorded to the
    second, so a job landing exactly on a boundary can go either way; the sweep's
    ~57s cells make that a rounding error, but jobs matching *no* cell are kept
    and reported rather than quietly discarded.
    """
    ordered = sorted(
        (cell for cell in cells if cell.started_at and cell.ended_at),
        key=lambda cell: cell.started_at,
    )
    spans = [
        (
            datetime.fromisoformat(cell.started_at),
            datetime.fromisoformat(cell.ended_at),
            cell.cell_key,
        )
        for cell in ordered
    ]

    result = Attribution(by_cell={cell.cell_key: [] for cell in ordered})
    for job in jobs:
        owner = next((key for start, end, key in spans if start <= job.created <= end), None)
        if owner is None:
            result.unattributed.append(job)
        else:
            result.by_cell[owner].append(job)
    return result


def cell_costs(
    cells: list[traces.Cell], attribution: Attribution, prices: Prices
) -> dict[str, CellCost]:
    """Per-cell consumption, priced where a price exists."""
    costs: dict[str, CellCost] = {}
    for cell in cells:
        jobs = attribution.by_cell.get(cell.cell_key, [])
        usage = cell.usage
        entry = CellCost(
            cell_key=cell.cell_key,
            config=cell.config,
            tier=cell.tier,
            prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
            output_tokens=int(usage.get("output_tokens", 0) or 0),
            thought_tokens=int(usage.get("thought_tokens", 0) or 0),
            model_calls=int(usage.get("model_calls", 0) or 0),
            bq_jobs=len(jobs),
            bytes_billed=sum(job.bytes_billed for job in jobs),
            service_side_unmeasured=mcp_clients.has_unmeasured_service(cell.config),
        )

        if prices.bq_per_tib_usd is not None:
            entry.warehouse_usd = entry.bytes_billed / TIB * prices.bq_per_tib_usd
        if prices.input_per_mtok_usd is not None and prices.output_per_mtok_usd is not None:
            # Thought tokens bill at the output rate and are already inside
            # `output_tokens`; adding them again would double-count the single
            # largest component on a reasoning model.
            entry.model_usd = (
                entry.prompt_tokens / MTOK * prices.input_per_mtok_usd
                + entry.output_tokens / MTOK * prices.output_per_mtok_usd
            )
        costs[cell.cell_key] = entry
    return costs


def measure(cells: list[traces.Cell], prices: Prices | None = None) -> tuple[
    dict[str, CellCost], Attribution
]:
    """Full pass: query the jobs table, attribute, and price. Needs BigQuery."""
    prices = prices or load_prices()
    start, end = window(cells)
    client = bigquery.Client(project=config.PROJECT_ID)
    jobs = fetch_jobs(client, start, end)
    attribution = attribute(cells, jobs)
    return cell_costs(cells, attribution, prices), attribution
