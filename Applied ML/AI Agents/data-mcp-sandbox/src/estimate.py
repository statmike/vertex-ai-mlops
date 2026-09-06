"""What a sweep will cost, before it is run.

`--dry-run` prints this. The point is that the expensive decision — commit to
1,200 live model calls, or not — should be made against measured numbers rather
than against a shrug, and that a reader on someone else's project can see the
order of magnitude before their first cell.

Every rate here is a **median observed on the published capture** (1,200 cells,
`gemini-3.7-flash` @ `global`, this corpus, 2026-09-05), not a vendor figure and
not a guess. Medians rather than means because the token distribution has a long
right tail: a handful of cells where the agent looped burn 10x the typical cell,
and a mean lets those set an expectation almost no cell meets.

Treat the output as an order of magnitude. Three known reasons it will be wrong:

* **Arm-to-arm spread is 220x**, so the mix of configs matters far more than the
  cell count. A 200-cell sweep of `p3_managed` tier 0 costs more than a
  1,000-cell sweep of any Path 4 arm — by a factor of forty.
* **Path 4's rates are floors.** Conversational Analytics runs its own Gemini
  loop server-side and reports none of it, so the two `p4_*` rows predict what
  your capture will *record*, not what the service will spend. Metering it
  separately put `p4_looker_ca` 22x above its recorded figure. A Path 4 sweep is
  the one case where this estimate under-states rather than over-states.
* **Quota backoff is not modelled.** A cell retried through dynamic shared quota
  contention carries up to ~300s of sleep that no rate table can predict. The
  seconds below are medians over cells that never retried, for that reason.

Checked against the sweep it was built from, this under-predicts by about 21%:
20h02m and 173.3M tokens estimated, 25.5h and 237.7M actually spent. Both gaps
are the same thing — summing medians drops the long right tail, and the excluded
retries are real time someone waits. Under-estimating is the dangerous direction
for a go/no-go number, so **add a quarter to whatever this prints.**
"""

from dataclasses import dataclass

MEASURED_ON = "published capture, 1,200 cells, gemini-3.7-flash @ global, 2026-09-05"

# Empty, and worth keeping empty rather than deleting. The matched arms once sat
# here mapped to their managed twins, on the assumption that copying a tool
# surface copies its cost. The sweep measured them and the assumption was wrong
# by 7x: `p1_matched` tier 0 was predicted at 554,528 tokens and came in at
# 78,003, right next to `p1_toolbox`. That is Amendment A.3.3's question
# answered — the cost lives in the schema text, not in the endpoint's name — and
# it is why an analogy is a placeholder for a measurement, never a substitute.
BY_ANALOGY: dict[str, str] = {}


@dataclass(frozen=True)
class Rate:
    """Median per-cell consumption for one (config, tier) arm."""

    seconds: float
    tokens: int


# Medians straight out of the published report's latency and cost tables. Seconds
# are over cells that never hit a quota retry, matching `report.latency`; tokens
# are over every scored cell.
OBSERVED: dict[tuple[str, int], Rate] = {
    ("p1_managed", 0): Rate(76.7, 554_528),
    ("p1_managed", 1): Rate(35.1, 198_442),
    ("p1_toolbox", 0): Rate(64.3, 79_841),
    ("p1_toolbox", 1): Rate(35.2, 25_619),
    ("p2_managed", 0): Rate(76.1, 79_744),
    ("p2_managed", 1): Rate(38.5, 32_313),
    ("p2_toolbox", 0): Rate(64.0, 71_361),
    ("p2_toolbox", 1): Rate(33.3, 24_894),
    ("p3_managed", 0): Rate(96.4, 930_883),
    ("p3_managed", 1): Rate(37.6, 265_727),
    ("p3_toolbox", 0): Rate(82.3, 193_550),
    ("p3_toolbox", 1): Rate(39.8, 54_732),
    ("p1_matched", 0): Rate(71.9, 78_003),
    ("p1_matched", 1): Rate(29.1, 22_884),
    ("p3_matched", 0): Rate(89.7, 207_233),
    ("p3_matched", 1): Rate(32.3, 34_489),
    # Floors. See the module docstring: CA's server-side spend is not in here.
    ("p4_bq_ca", 0): Rate(62.4, 8_867),
    ("p4_bq_ca", 1): Rate(32.8, 4_634),
    ("p4_looker_ca", 0): Rate(146.0, 16_829),
    ("p4_looker_ca", 1): Rate(59.4, 4_228),
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
        # Never print a dollar figure off an invented rate. BigQuery
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
    # The caveat belongs in the output, not only in the docstring. This is read
    # by someone deciding whether to spend, and it reads low: measured against
    # the sweep it was built from, it came in 21% under on both time and tokens.
    lines.append("           excludes quota backoff; sequential, so wall clock is the sum")
    lines.append("           runs ~21% low against the sweep it was measured on - budget above it")
    return "\n".join(lines)
