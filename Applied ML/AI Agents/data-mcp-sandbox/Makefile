.PHONY: help install toolbox check lint types test setup teardown golden lookml probe \
	preflight \
	identities identities-down verify-isolation looker-plan looker-apply \
	bootstrap apis plan smoke pilot sweep sweep-thinking report export service-tokens \
	sweep-ladder sweep-ladder-control \
	compare compare-aa

help:
	@echo "Start here"
	@echo "  make preflight  Can you provision this? Read-only, free. Run this first."
	@echo "  make bootstrap  Everything below, in order, from an empty project"
	@echo "  make plan       What a full sweep would cost, in time and tokens. Free."
	@echo ""
	@echo "Setup"
	@echo "  make install    Sync the environment (uv)"
	@echo "  make validate   Check corpus/oracle/questions agree. Offline, free."
	@echo "  make apis       Enable the Google Cloud APIs the sandbox needs"
	@echo "  make toolbox    Download the pinned MCP Toolbox binary into bin/"
	@echo "  make identities Create the per-tier service accounts (one-time, privileged)"
	@echo "  make setup      Provision both tiers, catalog governance, Looker check"
	@echo "  make lookml     Regenerate looker/ (files are pasted by hand, see its README)"
	@echo "  make looker-plan   Dry run: what Looker objects would be created"
	@echo "  make looker-apply  Create them (needs ADMIN LOOKERSDK_* credentials)"
	@echo "  make teardown   Delete every resource setup created"
	@echo "  make identities-down  Delete the per-tier service accounts"
	@echo ""
	@echo "Quality"
	@echo "  make check      lint + types + test"
	@echo "  make lint       ruff"
	@echo "  make types      mypy"
	@echo "  make test       pytest"
	@echo ""
	@echo "Evaluate  (each step costs more than the last — walk down it)"
	@echo "  make smoke      12 cells, one per arm. ~10 min, ~2.5M tokens."
	@echo "  make pilot      One replicate of everything: 288 cells. ~5h, ~79M tokens."
	@echo "  make sweep      The full 1,440-cell battery. ~26h, ~397M tokens."
	@echo "  make report     Score the capture and write results/report.md"
	@echo "  make service-tokens  Meter CA's off-book server-side model spend"
	@echo "  make export     Scrub + freeze goldens into a publishable capture"
	@echo ""
	@echo "  Add SKIP_LOOKER=1 to any of the above to run BigQuery-only arms."
	@echo ""
	@echo "Vary one axis instead of re-running everything"
	@echo "  make sweep-thinking MODE=FAST|THINKING|DEFAULT   240 cells, ~40 min."
	@echo "  LADDER=1 make sweep-ladder   Governance one channel at a time. 1,800 cells."
	@echo "  LADDER=1 make sweep-ladder-control   Rung 0 again, last. The temporal control."
	@echo "  make compare BASE=.. AGAINST=.. AXIS=..   Delta on one declared axis"
	@echo "  make compare-aa BASE=.. AGAINST=..        Noise floor from two identical runs"
	@echo "      Add TIER=\"0 1\" to either, to compare captures that ran different tiers"
	@echo ""
	@echo "Inspect"
	@echo "  make golden     Print live golden-truth values for every tier"
	@echo "  make probe      Print the real tool inventory of every MCP server"
	@echo "  make verify-isolation  Prove tier 0 cannot reach tier 1"

# Two read-only IAM calls, no mutations. Answers "will make bootstrap be allowed
# to do this?" before it creates anything billable. Only fails on a permission
# that blocks *provisioning* — a gap in cost attribution is reported, not fatal.
preflight:
	uv run python scripts/preflight.py

install:
	uv sync

toolbox:
	uv run python scripts/install_toolbox.py

lint:
	uv run ruff check .

types:
	uv run mypy

test:
	uv run pytest

check: lint types validate test

# Offline coherence check on the files that describe the experiment: corpus.py
# (the tables), golden.py (the right answers), questions.json (what to ask),
# scoring.py (which rule each question needs) and lookml.py (the Path 2 views).
# They are joined by name, so a rename in one is silent in the others until a
# sweep scores it wrong. Run this after every edit while adapting the sandbox.
validate:
	uv run python scripts/validate.py $(LOOKER_FLAG)

setup:
	uv run python scripts/setup.py

lookml:
	uv run python scripts/generate_lookml.py

# Additive only, and refuses any name outside the sandbox namespace — this runs
# against a SHARED Looker instance. Always read the plan before applying.
looker-plan:
	uv run python scripts/looker_provision.py

looker-apply:
	uv run python scripts/looker_provision.py --apply

teardown:
	uv run python scripts/cleanup.py

golden:
	uv run python scripts/show_golden.py

probe:
	uv run python examples/probe_tool_inventory.py

# One-time and privileged: creates identities and edits project-level IAM.
# Shell rather than Python on purpose — see the header of the script.
identities:
	bash scripts/bootstrap_identities.sh

identities-down:
	bash scripts/teardown_identities.sh

verify-isolation:
	uv run python examples/verify_isolation.py

# --- Portability ------------------------------------------------------------
#
# SKIP_LOOKER=1 drops the three arms needing a Looker instance, which is the only
# component behind an annual-commitment purchase. Seven arms still run, including
# both governance tiers and both Path 4 halves' BigQuery side, so the central
# T1-vs-T0 result survives without it.
LOOKER_FLAG := $(if $(SKIP_LOOKER),--skip-looker,)

# One command from an empty project. Deliberately does NOT create a Looker
# instance: that is an annual charge, and no setup script should be able to start
# one. Looker is set up by hand — docs/looker_setup.md — or skipped entirely.
bootstrap:
	$(MAKE) install
	$(MAKE) preflight
	$(MAKE) apis
	$(MAKE) toolbox
	$(MAKE) identities
	$(MAKE) setup
	@echo ""
	@echo "Provisioned. Now: make verify-isolation, then make plan, then make smoke."

apis:
	bash scripts/enable_apis.sh

# Free. Prints the cell list and a measured time/token estimate — the number to
# look at before deciding whether to run any of the three below.
plan:
	uv run python examples/run_battery.py --dry-run $(LOOKER_FLAG)

# --- The three rungs, cheapest first -----------------------------------------
#
# Each is the same harness at a different size, so a failure shows up on the
# ~15-minute rung rather than the ~26-hour one. Walk down them in order.

# One cell per arm, governed tier only. Proves credentials, MCP connectivity, the
# model endpoint, and the capture format. Writes to its own file so it can never
# be mistaken for, or overwrite, a real sweep.
smoke:
	uv run python examples/run_battery.py --questions direct-q1 --tiers 1 --runs 1 \
		--out results/raw/smoke.json $(LOOKER_FLAG)

# One replicate of the whole factorial. Enough to see every arm answer every
# question at both tiers; not enough to measure variance.
pilot:
	uv run python examples/run_battery.py --runs 1 \
		--out results/raw/pilot.json $(LOOKER_FLAG)

# The full factorial: live model calls against live services, ~26h. `make plan`
# first, and never before `make smoke` has passed.
sweep:
	uv run python examples/run_battery.py $(LOOKER_FLAG)

# The `thinking_mode` axis (Amendment C.4). 240 cells, ~40m, no local tokens —
# the direct arms spend their model budget inside the service. Its own capture
# file, never merged: a different thinking mode is a different experiment, and
# `make compare AXIS=ca_thinking_mode` is how it is read against the published
# capture. MODE is FAST or THINKING; unset is the published default, which is
# already measured and does not need re-running.
#
# MODE=DEFAULT sends no thinking_mode, reproducing the published direct arms. It
# is not redundant with the published capture: run in the same window as FAST and
# THINKING, it is the temporal control that separates "this is what the default
# resolves to" from "the service was differently loaded a day ago".
#
#     make sweep-thinking MODE=FAST
#     make sweep-thinking MODE=THINKING
#     make sweep-thinking MODE=DEFAULT
sweep-thinking:
	@test -n "$(MODE)" || { echo "MODE=FAST, THINKING, or DEFAULT"; exit 1; }
	CA_THINKING_MODE=$(if $(filter DEFAULT,$(MODE)),,$(MODE)) \
	uv run python examples/run_battery.py \
		--configs p4_bq_direct p4_bq_direct_ctx \
		--out results/raw/thinking-$(shell echo $(MODE) | tr A-Z a-z).json

# The governance ladder (Amendment C.2). Five rungs across six arms, 1,800 cells,
# 24h21m estimated. Needs LADDER=1 on `make identities` and `make setup` first —
# the three intermediate rungs are real datasets with real service accounts, and
# a sweep against unprovisioned rungs measures an empty dataset rather than
# failing.
#
# `p2_*` and `p4_looker_ca` are excluded by design: LookML arrives as one lump at
# the top rung and laddering it means semantic-model surgery on a shared Looker
# instance this project is a guest on.
#
#     LADDER=1 make identities && LADDER=1 make setup
#     LADDER=1 make plan     # check the number before spending a day on it
#     LADDER=1 make sweep-ladder
LADDER_ARMS = p1_managed p1_matched p3_managed p3_matched p3_toolbox p4_bq_ca

sweep-ladder:
	@test "$(LADDER)" = "1" || { echo "Set LADDER=1 — the rungs must be provisioned first."; exit 1; }
	uv run python examples/run_battery.py \
		--configs $(LADDER_ARMS) --out results/raw/ladder.json

# The temporal control: rung 0 again, at the END of the ladder. Its own capture,
# because re-running the same cells into `ladder.json` would collide on cell keys.
# Read with `make compare-aa` against the ladder's own rung 0 — anything the pair
# disagrees on is drift accumulated over the sweep's day, not governance, and it
# is the only thing that can tell the two apart.
#
# 360 cells but 7h59m, not the 4.3h a sixth of the ladder suggests: rung 0 is the
# *expensive* condition. Ungoverned, the agent explores, and `p3_managed` spends
# 207k tokens at tier 0 against 34k at tier 1. Budget the control off its own
# measured rate, never off the ladder's average.
sweep-ladder-control:
	@test "$(LADDER)" = "1" || { echo "Set LADDER=1 — the rungs must be provisioned first."; exit 1; }
	uv run python examples/run_battery.py \
		--configs $(LADDER_ARMS) --tiers 0 --out results/raw/ladder-rung0-last.json

report:
	uv run python examples/build_results.py

# The one cost component `build_results.py` cannot see: the Gemini tokens
# Conversational Analytics spends server-side and never returns. Read back from
# Cloud Monitoring, which attributes by time block rather than per cell — so it
# is a separate target, not a column in the report.
service-tokens:
	uv run python examples/service_tokens.py

# Freeze goldens into the capture and scrub project identifiers, so the file can
# be published and the rubric re-run by someone with no project of their own.
# Defaults to the main capture. Override both for a sibling capture in the C
# family — every capture must be exported before it can be compared against a
# published one, because the scrub rewrites `project` and `project` is a
# MUST_AGREE field.
#
#     make export RESULTS=results/raw/thinking-fast.json OUT=results/capture-thinking-fast.json.gz
export:
	uv run python scripts/export_capture.py \
		$(if $(RESULTS),--results $(RESULTS)) $(if $(OUT),--out $(OUT))

# Compare two captures that differ on one declared axis. Refuses rather than
# subtracting captures that disagree on anything else (Amendment C.0).
compare:
	uv run python scripts/compare_captures.py --base $(BASE) --against $(AGAINST) --axis $(AXIS) \
		$(foreach t,$(TIER),--tier $(t))

# Measure the noise floor: two captures that varied NOTHING, differenced. This
# is where `compare.NOISE_FLOOR` comes from, and re-running it in your own
# project is how you find out whether ours travels there.
#
#     make compare-aa BASE=results/capture.json.gz \
#                     AGAINST=results/capture-thinking-default.json.gz
#
# TIER="0 1" narrows both sides to those tiers, which is how the ladder capture
# is read against the published two-tier one — otherwise the `tiers` header
# differs and the comparison is refused.
#
#     make compare-aa BASE=results/capture.json.gz \
#                     AGAINST=results/capture-ladder.json.gz TIER="0 1"
compare-aa:
	uv run python scripts/compare_captures.py --base $(BASE) --against $(AGAINST) --aa \
		$(foreach t,$(TIER),--tier $(t))
