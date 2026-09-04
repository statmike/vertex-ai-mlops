"""What a sweep will cost, before it is run.

`--dry-run` prints this. The point is that the expensive decision — commit to
1,200 live model calls, or not — should be made against measured numbers rather
than against a shrug, and that a reader on someone else's project can see the
order of magnitude before their first cell.

Every rate here is a **median observed on the M3 capture** (960 cells,
`gemini-3.7-flash` @ `global`, this corpus, 2026-09-03), not a vendor figure and
not a guess. Medians rather than means because the token distribution has a long
right tail: a handful of cells where the agent looped burn 10x the typical cell,
and a mean lets those set an expectation almost no cell meets.

Treat the output as an order of magnitude. Two known reasons it will be wrong:

* **Arm-to-arm spread is 80x**, so the mix of configs matters more than the cell
  count. A 200-cell sweep of `p3_managed` costs more than a 1,000-cell sweep of
  `p4_bq_ca`.
* **Quota backoff is not modelled.** A cell retried through dynamic shared quota
  contention carries up to ~300s of sleep that no rate table can predict.
"""

from dataclasses import dataclass

MEASURED_ON = "M3 capture, 960 cells, gemini-3.7-flash @ global, 2026-09-03"

# Arms that did not exist when the rates were measured, mapped to the arm whose
# tool surface they copy. Amendment A.3.3 exists precisely because we do not know
# whether a matched arm behaves like its managed twin — so these are the honest
# starting guess and are counted and reported separately, never silently pooled.
BY_ANALOGY = {
    "p1_matched": "p1_managed",
    "p3_matched": "p3_managed",
}


@dataclass(frozen=True)
class Rate:
    """Median per-cell consumption for one (config, tier) arm."""

    seconds: float
    tokens: int


# Medians straight out of the M3 report's latency and cost tables.
OBSERVED: dict[tuple[str, int], Rate] = {
    ("p1_managed", 0): Rate(88.5, 574_009),
    ("p1_managed", 1): Rate(36.0, 193_756),
    ("p1_toolbox", 0): Rate(79.3, 75_790),
    ("p1_toolbox", 1): Rate(33.1, 29_762),
    ("p2_managed", 0): Rate(77.7, 94_122),
    ("p2_managed", 1): Rate(43.1, 32_444),
    ("p2_toolbox", 0): Rate(80.3, 62_615),
    ("p2_toolbox", 1): Rate(74.4, 30_074),
    ("p3_managed", 0): Rate(182.2, 985_792),
    ("p3_managed", 1): Rate(55.2, 233_069),
    ("p3_toolbox", 0): Rate(86.1, 178_437),
    ("p3_toolbox", 1): Rate(37.7, 56_280),
    ("p4_bq_ca", 0): Rate(57.1, 12_206),
    ("p4_bq_ca", 1): Rate(32.0, 4_428),
    ("p4_looker_ca", 0): Rate(172.6, 16_202),
    ("p4_looker_ca", 1): Rate(64.5, 4_817),
}

# Used only when an arm has neither a measurement nor an analogy — a config added
# after this table was written. Deliberately the *most* expensive observed arm, so
# an unknown arm over-estimates rather than under-estimates.
FALLBACK = max(OBSERVED.values(), key=lambda rate: rate.tokens)


@dataclass
class Estimate:
    """A sweep's predicted wall clock and token spend."""

    cells: int
    seconds: float
    tokens: int
    by_analogy: int = 0  # cells priced off a different arm's rate
    unknown: int = 0  # cells priced off FALLBACK

    @property
    def measured(self) -> int:
        return self.cells - self.by_analogy - self.unknown


def rate_for(config_key: str, tier: int) -> tuple[Rate, str]:
    """The rate to use for one arm, and how it was arrived at."""
    if (config_key, tier) in OBSERVED:
        return OBSERVED[(config_key, tier)], "measured"
    twin = BY_ANALOGY.get(config_key)
    if twin and (twin, tier) in OBSERVED:
        return OBSERVED[(twin, tier)], "analogy"
    return FALLBACK, "unknown"


def estimate(arms: list[tuple[str, int]]) -> Estimate:
    """Predict a sweep from its (config, tier) cells, one entry per cell."""
    total = Estimate(cells=len(arms), seconds=0.0, tokens=0)
    for config_key, tier in arms:
        rate, basis = rate_for(config_key, tier)
        total.seconds += rate.seconds
        total.tokens += rate.tokens
        if basis == "analogy":
            total.by_analogy += 1
        elif basis == "unknown":
            total.unknown += 1
    return total


def _duration(seconds: float) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes = remainder // 60
    return f"{hours}h{minutes:02d}m" if hours else f"{minutes}m"


def render(total: Estimate, usd_per_mtok: float | None = None) -> str:
    """A short block for `--dry-run`, honest about which cells are guesses."""
    lines = [
        f"Estimated: {_duration(total.seconds)} wall clock, "
        f"{total.tokens / 1e6:.1f}M tokens across {total.cells} cells",
    ]
    if usd_per_mtok is not None:
        # Priced entirely at the *input* rate. Output is under 1% of the total in
        # every arm measured — tool schemas resent each turn are what this costs —
        # so this understates by less than the arm-to-arm spread it is meant to
        # convey. `report.py` does the real split; this is a go/no-go number.
        lines.append(
            f"           ~${total.tokens / 1e6 * usd_per_mtok:.2f} in model spend, "
            f"all tokens at the input rate"
        )
    else:
        # Never print a dollar figure off an invented rate (DESIGN A.5). BigQuery
        # bytes are omitted for the same reason they are unpriced by default: this
        # sandbox's corpus is small enough that model tokens dominate, and another
        # project's will not be.
        lines.append("           model spend unpriced - supply rates in prices.json")
    basis = [f"{total.measured} measured"]
    if total.by_analogy:
        basis.append(f"{total.by_analogy} by analogy to a twin arm")
    if total.unknown:
        basis.append(f"{total.unknown} unknown, priced at the worst observed arm")
    lines.append(f"           from {', '.join(basis)} ({MEASURED_ON})")
    lines.append("           excludes quota backoff; sequential, so wall clock is the sum")
    return "\n".join(lines)
