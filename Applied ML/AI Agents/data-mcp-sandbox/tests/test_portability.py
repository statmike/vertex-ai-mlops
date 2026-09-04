"""Invariants for running this on someone else's project (DESIGN A.3.4).

Three things have to hold for a reader to pick this up: they must be able to run
it without Looker, to know the cost before they spend it, and to re-score our
published capture without a project of their own. Each of those has a way of
failing quietly, and each is pinned here.
"""

import gzip
import json
from pathlib import Path

import estimate
import export_capture
import mcp_clients
import traces

# --- Looker-optional ---------------------------------------------------------


def test_dropping_looker_leaves_both_tiers_on_five_of_seven_arms():
    kept, dropped = mcp_clients.drop_looker(list(mcp_clients.CONFIG_KEYS))
    assert set(dropped) == {"p2_managed", "p2_toolbox", "p4_looker_ca"}
    # The claim made in the Makefile and the docs: a Looker-free run still
    # compares governed against ungoverned on paths 1, 3 and 4-over-BigQuery.
    assert {mcp_clients.CONFIGS[key].path for key in kept} == {1, 3, 4}


def test_no_looker_arm_is_missed_when_a_config_is_added():
    # The failure this guards is a new Looker-backed config appearing in CONFIGS
    # while a hand-written skip list stays as it was: --skip-looker would then
    # keep an arm that cannot run, and the sweep dies partway through.
    for key, cfg in mcp_clients.CONFIGS.items():
        assert cfg.needs_looker == (key in mcp_clients.LOOKER_CONFIG_KEYS)


def test_dropping_looker_never_silently_empties_the_sweep():
    kept, dropped = mcp_clients.drop_looker(["p2_managed", "p4_looker_ca"])
    assert kept == []
    assert len(dropped) == 2


# --- Cost is knowable before it is spent -------------------------------------


def test_every_shipped_arm_can_be_estimated():
    for key in mcp_clients.CONFIG_KEYS:
        for tier in (0, 1):
            _rate, basis = estimate.rate_for(key, tier)
            assert basis in ("measured", "analogy"), f"{key} tier {tier} has no rate"


def test_an_unknown_arm_over_estimates_rather_than_under():
    # A config added after the rate table was written must not price as cheap.
    # Under-estimating is the dangerous direction: it is the number someone reads
    # before deciding to spend money.
    rate, basis = estimate.rate_for("p9_invented", 1)
    assert basis == "unknown"
    assert rate.tokens == max(r.tokens for r in estimate.OBSERVED.values())


def test_estimate_reports_how_many_cells_are_guesses():
    total = estimate.estimate([("p1_managed", 1), ("p1_matched", 1), ("p9_invented", 1)])
    assert (total.measured, total.by_analogy, total.unknown) == (1, 1, 1)
    assert "by analogy" in estimate.render(total)


def test_estimate_prints_no_dollars_without_a_rate():
    # DESIGN A.5: a rate invented to fill a column is worse than an empty column.
    text = estimate.render(estimate.estimate([("p1_managed", 1)]), usd_per_mtok=None)
    assert "$" not in text
    assert "unpriced" in text


# --- The published capture ---------------------------------------------------


def test_scrub_reaches_inside_keys_and_nested_tool_results():
    pairs = {"my-real-project": "example-project"}
    payload = {
        "my-real-project": [{"sql": "SELECT * FROM `my-real-project.ds.t`"}],
        "sa": "mcp-sandbox-t1@my-real-project.iam.gserviceaccount.com",
    }
    scrubbed = export_capture.scrub(payload, pairs)
    assert "my-real-project" not in json.dumps(scrubbed)
    assert "example-project" in next(iter(scrubbed))


def test_longer_identifiers_are_substituted_first(monkeypatch):
    # A project id that embeds the project number leaves a fragment of itself
    # behind if the short one is replaced first: "acme-123456" would become
    # "acme-000000000000" and no longer match the project rule at all.
    monkeypatch.setattr(export_capture.config, "PROJECT_ID", "acme-123456")
    monkeypatch.setattr(export_capture.config, "LOOKER_BASE_URL", "")
    monkeypatch.setattr(export_capture, "_project_number", lambda: "123456")

    pairs = export_capture.substitutions()
    assert list(pairs)[0] == "acme-123456"
    scrubbed = export_capture.scrub({"t": "acme-123456 and 123456"}, pairs)
    assert scrubbed["t"] == "example-project and 000000000000"


def test_check_fails_on_a_capture_with_no_frozen_goldens(tmp_path: Path):
    # A scrubbed file that a reader cannot re-score is not a published capture,
    # it is a large opaque blob. Both halves of the export have to be present.
    path = tmp_path / "capture.json"
    path.write_text(json.dumps({"header": {}, "cells": []}))
    assert export_capture.check(path, {"secret-project": "example-project"}) == 1


def test_check_fails_when_an_identifier_survived(tmp_path: Path):
    path = tmp_path / "capture.json"
    path.write_text(json.dumps({
        "header": {"goldens": {"1": {}}},
        "cells": [{"answer": "from secret-project.ds.t"}],
    }))
    assert export_capture.check(path, {"secret-project": "example-project"}) == 1


def test_check_passes_a_clean_capture(tmp_path: Path):
    path = tmp_path / "capture.json"
    path.write_text(json.dumps({"header": {"goldens": {"0": {}, "1": {}}}, "cells": []}))
    assert export_capture.check(path, {"secret-project": "example-project"}) == 0


def test_check_sees_through_compression(tmp_path: Path):
    # The scrub check reads text. If it did not decompress first, a `.gz` export
    # would pass trivially — no identifier is findable in a gzip stream.
    path = tmp_path / "capture.json.gz"
    traces.write_text(path, json.dumps({
        "header": {"goldens": {"1": {}}},
        "cells": [{"answer": "secret-project"}],
    }))
    assert gzip.decompress(path.read_bytes())  # really is compressed
    assert export_capture.check(path, {"secret-project": "example-project"}) == 1


def test_capture_round_trips_through_gzip(tmp_path: Path):
    cells = {
        "a": traces.Cell(cell_key="a", question_id="q", category="direct", question="?",
                         config="p1_managed", tier=1, run=1, answer="42"),
    }
    for name in ("results.json", "results.json.gz"):
        path = tmp_path / name
        traces.save(path, cells, {"agent_model": "m"})
        assert traces.load(path)["a"].answer == "42"
        assert traces.read_header(path)["agent_model"] == "m"
