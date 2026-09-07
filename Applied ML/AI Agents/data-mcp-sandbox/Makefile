.PHONY: help install toolbox check lint types test setup teardown golden lookml probe \
	preflight \
	identities identities-down verify-isolation looker-plan looker-apply \
	bootstrap apis plan smoke pilot sweep report export service-tokens

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
export:
	uv run python scripts/export_capture.py

# Compare two captures that differ on one declared axis. Refuses rather than
# subtracting captures that disagree on anything else (Amendment C.0).
compare:
	uv run python scripts/compare_captures.py --base $(BASE) --against $(AGAINST) --axis $(AXIS)
