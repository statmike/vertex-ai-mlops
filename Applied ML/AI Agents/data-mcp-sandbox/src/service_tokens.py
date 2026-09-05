"""The Gemini tokens Conversational Analytics spends on our behalf and never reports.

`cost.py` publishes Path 4 as a *floor* because the CA API returns no usage block:
the tokens it burns running its own agent loop are invisible to the caller. They
are not invisible to Cloud Monitoring. `geminidataanalytics.googleapis.com` emits
`chat/input_token_count` and `chat/output_token_count`, and this module reads them
back over each arm's time block to turn that floor into a measurement.

It changes the headline. On the M6 capture `p4_looker_ca` recorded 18,045 tokens
per cell and actually consumed 392,158 — a 22x understatement that moves it from
the cheapest arm to the third most expensive, behind only the two managed MCP
endpoints. The user-visible thrift was the agent loop moving server-side, exactly
where the bill stops being itemised.

**Three limits, none of which can be engineered away from here:**

1. *The metric is project-wide.* Its only labels are `model_name` and `status` —
   there is no conversation, agent, or caller dimension — so attribution is by
   time window, not by cell. Anything else in the project talking to CA during a
   sweep lands in our numbers. `baseline()` is here to make that checkable rather
   than assumed: run it over a quiet week and see what the floor looks like.
2. *It needs contiguous blocks.* `blocks()` refuses to attribute a config/tier
   whose cells interleave with another arm's, because a 60s-aligned series cannot
   be split finer than the runs are. The sweep is sequential (DESIGN.md §7) so
   this holds today; a parallel runner would silently break it, hence the check.
3. *It does not cover `p4_bq_ca`.* That arm reaches CA through Toolbox's
   `bigquery-conversational-analytics` and emits **nothing** on this metric — a
   measured zero across its whole 2h08m block, against 44.9M tokens from the
   Looker arm in the same sweep. Zero here means *not attributable by this
   metric*, never *free*; see `docs/paths.md` for the mechanisms that fit.
"""

from dataclasses import dataclass

import google.auth
import google.auth.transport.requests
import requests

import config
import mcp_clients
import traces

MONITORING_API = "https://monitoring.googleapis.com/v3"

# 60s is the finest alignment the API offers, and it is what makes per-arm
# attribution possible at all: the two Path 4 arms hand off mid-hour, so hourly
# buckets blend them. Anything coarser silently reassigns tokens between arms.
ALIGNMENT_SECONDS = 60

INPUT_METRIC = "geminidataanalytics.googleapis.com/chat/input_token_count"
OUTPUT_METRIC = "geminidataanalytics.googleapis.com/chat/output_token_count"
TURN_METRIC = "geminidataanalytics.googleapis.com/chat/turn_count"
INVOCATION_METRIC = "geminidataanalytics.googleapis.com/chat/model/invocation_count"


@dataclass
class ServiceUsage:
    """One arm's server-side spend over its block. Zero is not the same as absent."""

    config: str
    tier: int
    started_at: str
    ended_at: str
    input_tokens: int = 0
    output_tokens: int = 0
    turns: int = 0
    model_calls: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def attributed(self) -> bool:
        """Did this metric see the arm at all?

        Keyed on `turns`, not tokens, because a token count alone cannot tell a
        real result from spillover. Blocks abut to the second — `p4_bq_ca` tier 1
        ends 2s before `p4_looker_ca` tier 0 begins — and the finest alignment the
        API offers is 60s, so the bucket containing a handoff is credited to both
        neighbours. That showed up as 1,725 tokens and 2 model calls against
        *zero* turns, which reads as a 1x understatement and is really the next
        arm's first minute. A block that ran no CA turn did no CA work.

        False means the arm's server-side work is still unmeasured — it went
        somewhere this metric does not watch. It does not mean the arm was free.
        """
        return self.turns > 0


@dataclass
class Block:
    """A contiguous run of one (config, tier) — the unit attribution works on."""

    config: str
    tier: int
    started_at: str
    ended_at: str
    cells: int


def _is_ca(config_key: str) -> bool:
    """Does this arm reach a service that runs its own model calls? (Path 4.)"""
    spec = mcp_clients.CONFIGS.get(config_key)
    return spec is not None and spec.path == 4


def blocks(cells: list[traces.Cell]) -> list[Block]:
    """Contiguous (config, tier) runs, in capture order.

    Raises if a *Path 4* arm's cells are not contiguous. Attribution here is
    purely temporal, so a split CA block would hand one arm's tokens to whatever
    ran in the gap and look perfectly plausible doing it — better to refuse than
    to publish that.

    The check is deliberately not applied to the other arms. They make no CA
    calls, so their placement cannot move a token between CA blocks, and they do
    get split in practice: the M6 sweep ends with a retry pass that backfills a
    handful of failed MCP cells hours later, long after Path 4 finished. Failing
    the whole attribution over that would be a false alarm.
    """
    stamped = sorted(
        (c for c in cells if c.started_at and c.ended_at), key=lambda c: c.started_at
    )
    found: list[Block] = []
    for cell in stamped:
        last = found[-1] if found else None
        if last and last.config == cell.config and last.tier == cell.tier:
            last.ended_at = max(last.ended_at, cell.ended_at)
            last.cells += 1
            continue
        found.append(Block(cell.config, cell.tier, cell.started_at, cell.ended_at, 1))

    seen: set[tuple[str, int]] = set()
    for block in found:
        key = (block.config, block.tier)
        if key in seen and _is_ca(block.config):
            raise ValueError(
                f"{block.config} tier {block.tier} appears in more than one block - "
                "the sweep interleaved Path 4 arms, so server-side tokens cannot be "
                "attributed by time window"
            )
        seen.add(key)
    return found


def _session() -> tuple[requests.Session, str]:
    """ADC only. This module reads metrics; it never needs a key file."""
    credentials, project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/monitoring.read"]
    )
    # google-auth ships no annotations for `refresh`, so mypy sees an untyped call
    # inside a typed module. The alternative is dropping strictness for the file.
    credentials.refresh(google.auth.transport.requests.Request())  # type: ignore[no-untyped-call]
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {credentials.token}"
    return session, project or config.PROJECT_ID


def series_total(session: requests.Session, project: str, metric: str, start: str, end: str) -> int:
    """Sum one DELTA metric over [start, end).

    Summing the aligned points rather than asking the API for one bucket is
    deliberate. A single alignment period longer than the interval gets *widened*
    by the API to a whole bucket, which quietly pulls in traffic from outside the
    window — two adjacent windows then return byte-identical totals and look like
    a correct answer. 60s points summed locally cannot do that.
    """
    response = session.get(
        f"{MONITORING_API}/projects/{project}/timeSeries",
        params={
            "filter": f'metric.type="{metric}"',
            "interval.startTime": start,
            "interval.endTime": end,
            "aggregation.alignmentPeriod": f"{ALIGNMENT_SECONDS}s",
            "aggregation.perSeriesAligner": "ALIGN_SUM",
            "aggregation.crossSeriesReducer": "REDUCE_SUM",
        },
        timeout=60,
    )
    response.raise_for_status()
    return sum(
        int(point["value"].get("int64Value", 0))
        for entry in response.json().get("timeSeries", [])
        for point in entry["points"]
    )


def measure(cells: list[traces.Cell]) -> list[ServiceUsage]:
    """Server-side CA spend per Path 4 arm, read back from Cloud Monitoring.

    Only Path 4 arms are queried. Every other arm's model calls happen in this
    process and are already counted by `usage.py`; asking Monitoring about them
    would double-count against a project-wide series.
    """
    session, project = _session()
    measured: list[ServiceUsage] = []
    for block in blocks(cells):
        spec = mcp_clients.CONFIGS.get(block.config)
        if spec is None or spec.path != 4:
            continue
        window = (block.started_at, block.ended_at)
        measured.append(
            ServiceUsage(
                config=block.config,
                tier=block.tier,
                started_at=block.started_at,
                ended_at=block.ended_at,
                input_tokens=series_total(session, project, INPUT_METRIC, *window),
                output_tokens=series_total(session, project, OUTPUT_METRIC, *window),
                turns=series_total(session, project, TURN_METRIC, *window),
                model_calls=series_total(session, project, INVOCATION_METRIC, *window),
            )
        )
    return measured


def baseline(start: str, end: str) -> ServiceUsage:
    """CA usage in this project over an arbitrary window, for a quiet-period check.

    The point of running this over the week *before* a sweep is to find out
    whether anything else in the project uses CA. If this comes back large, the
    sweep numbers are contaminated and should not be published as measured.
    """
    session, project = _session()
    return ServiceUsage(
        config="(project baseline)",
        tier=-1,
        started_at=start,
        ended_at=end,
        input_tokens=series_total(session, project, INPUT_METRIC, start, end),
        output_tokens=series_total(session, project, OUTPUT_METRIC, start, end),
        turns=series_total(session, project, TURN_METRIC, start, end),
        model_calls=series_total(session, project, INVOCATION_METRIC, start, end),
    )
