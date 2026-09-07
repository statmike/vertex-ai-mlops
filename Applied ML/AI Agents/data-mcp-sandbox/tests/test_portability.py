"""Invariants for running this on someone else's project.

Four things have to hold for a reader to pick this up: they must be able to run
it without Looker, to know the cost before they spend it, to re-score our
published capture without a project of their own, and to actually open every file
this repo points them at. Each of those has a way of failing quietly, and each is
pinned here.
"""

import gzip
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import config
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


def test_every_shipped_arm_is_estimated_from_its_own_measurement():
    # Stronger than "has a rate". Two arms were once priced by analogy to their
    # managed twins, and the sweep put `p1_matched` at 78,003 tokens against the
    # 554,528 the analogy predicted — a 7x over-estimate in the number someone
    # reads before deciding to spend money. Every arm now has its own row, and
    # this fails if a future arm is shipped on a guess.
    #
    # An arm that has never been swept is allowed exactly one escape, and it is a
    # named one: `PENDING_MEASUREMENT`. That is not a loophole in the property —
    # such an arm is priced at the worst observed rate, never at a twin's — it is
    # the ledger of what still owes a measurement.
    for key in mcp_clients.CONFIG_KEYS:
        for tier in (0, 1):
            _rate, basis = estimate.rate_for(key, tier)
            if key in estimate.PENDING_MEASUREMENT:
                assert basis == "unmeasured", f"{key} tier {tier} is priced by {basis}"
                continue
            assert basis == "measured", f"{key} tier {tier} is priced by {basis}"


def test_a_never_swept_arm_is_priced_at_the_worst_arm_not_at_a_twin():
    # `p4_bq_direct` has an obvious twin in `p4_bq_ca` and must not borrow it.
    # The twin pays for a local ADK loop the direct arm does not run, so its
    # rate is not a conservative prior — it is a cheap one, in the direction that
    # gets money spent.
    for key in estimate.PENDING_MEASUREMENT:
        rate, basis = estimate.rate_for(key, 0)
        assert basis == "unmeasured"
        assert rate.tokens == max(r.tokens for r in estimate.OBSERVED.values())


def test_an_unknown_arm_over_estimates_rather_than_under():
    # A config added after the rate table was written must not price as cheap.
    # Under-estimating is the dangerous direction: it is the number someone reads
    # before deciding to spend money.
    rate, basis = estimate.rate_for("p9_invented", 1)
    assert basis == "unknown"
    assert rate.tokens == max(r.tokens for r in estimate.OBSERVED.values())


def test_estimate_reports_how_many_cells_are_guesses(monkeypatch):
    # BY_ANALOGY is empty today because every shipped arm got measured, but the
    # mechanism has to keep working for the next arm added before a sweep runs.
    # Exercised through a patched mapping rather than a real arm, so that
    # measuring an arm cannot quietly delete this coverage — which is exactly
    # what happened when this test named `p1_matched`.
    monkeypatch.setitem(estimate.BY_ANALOGY, "p9_new", "p1_managed")
    total = estimate.estimate([("p1_managed", 1), ("p9_new", 1), ("p9_invented", 1)])
    assert (total.measured, total.by_analogy, total.unknown) == (1, 1, 1)
    rendered = estimate.render(total)
    assert "by analogy" in rendered
    assert "unknown" in rendered


def test_estimate_prints_no_dollars_without_a_rate():
    # A rate invented to fill a column is worse than an empty column.
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


def _real_identifiers() -> dict[str, str]:
    """The project-specific strings the export scrubs, read without a network call.

    `export_capture.substitutions()` resolves the project *number* through the
    Resource Manager API, which is fine for an export and wrong for a test. These
    two come straight out of `.env` and cover the identifiers that actually turn
    up in prose: the project id and the Looker host.
    """
    host = urlparse(config.LOOKER_BASE_URL).netloc if config.LOOKER_BASE_URL else ""
    return {
        value: name
        for name, value in (("PROJECT_ID", config.PROJECT_ID), ("LOOKER_BASE_URL", host))
        if value  # an unset var would otherwise match every file
    }


def _doc_text() -> dict[str, str]:
    """Tracked prose: markdown, plus notebook *source* but not notebook output."""
    root = Path(config.PROJECT_ROOT)
    listing = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "*.md", "*.ipynb"],
        cwd=root, capture_output=True, text=True, check=True,
    )
    out = {}
    for name in listing.stdout.split():
        path = root / name
        if not path.exists():
            continue
        if path.suffix == ".ipynb":
            cells = json.loads(path.read_text())["cells"]
            out[name] = "\n".join("".join(cell["source"]) for cell in cells)
        else:
            out[name] = path.read_text()
    return out


def test_no_doc_names_the_project_the_capture_scrubs():
    # The export replaces the project id and Looker host before publishing, on the
    # grounds that a published file naming a live instance invites traffic to it.
    # A doc that spells the same identifiers out undoes that for no benefit, and
    # it is also the portability bug: a reader copying a command with someone
    # else's project baked into it gets a 403 rather than a prompt to set `.env`.
    #
    # Notebook *outputs* are deliberately exempt. They are the record of a real
    # run against a real project, and rewriting them would make the evidence say
    # something that did not happen.
    real = _real_identifiers()
    assert real, "no identifiers configured - this test would pass vacuously"
    found = [
        f"{name} names {real[value]}"
        for name, text in _doc_text().items()
        for value in real
        if value in text
    ]
    assert not found, f"use the export's placeholders instead: {found}"


# --- Every file this repo points at is a file a reader can open ---------------

# Paths a reader creates themselves, or that a command generates. Naming one of
# these is an instruction, not a broken pointer, so they are exempt.
LOCAL_BY_DESIGN = {
    ".env",              # cp .env.example .env
    "prices.json",       # cp prices.example.json prices.json
    "looker.ini",        # written by looker_provision.py, 0600, never committed
    "tools.yaml",        # rendered at run time by toolbox_server.py
    "settings.local.json",  # per-developer agent config, explicitly not shared
}

# Directories whose contents are generated, not authored. `results/raw/` holds
# multi-MB sweep captures; the scrubbed, publishable one is what gets committed.
GENERATED_DIRS = ("results/raw/", "bin/")

# `.gitignore` names ignored files as its entire job.
NOT_POINTERS = {".gitignore"}

# Extensions worth checking. Anything that looks like a repo file rather than a
# BigQuery table, a Python module reference, or a hostname.
_PATHLIKE = re.compile(r"\b[\w./-]+\.(?:md|py|json|yaml|yml|toml|lkml|ini|sh|cfg|txt)\b")


def _tracked_text() -> dict[str, str]:
    """Every tracked file whose contents a reader might follow a pointer out of."""
    root = Path(config.PROJECT_ROOT)
    listing = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
    )
    out = {}
    for name in listing.stdout.split():
        path = root / name
        if not path.exists() or path.suffix not in {".md", ".py", ".toml", ".ipynb", ".mk", ""}:
            continue
        try:
            out[name] = path.read_text()
        except UnicodeDecodeError:
            continue
    return out


def test_no_tracked_file_points_at_an_untracked_one():
    """A pointer to a gitignored file works for us and 404s for everyone else.

    This is the failure that is invisible from inside the repo: the author has the
    harness design doc sitting right there, so citing it by name and section reads
    as helpful rather than as a dead link. Forty-one of those had accumulated
    across 24 files before this test existed — all pointing into the agent
    harness, which is deliberately local-only for a monorepo cell.

    Scoped to names that *resolve to something on disk which is not tracked*,
    because that is exactly the trap. A name resolving to nothing is a different
    thing — a generated artifact, or a file the reader creates — and the two
    exemption lists above cover the ones that are real instructions.
    """
    root = Path(config.PROJECT_ROOT)
    tracked = set(
        subprocess.run(
            ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
        ).stdout.split()
    )

    dead = []
    for name, text in _tracked_text().items():
        if name in NOT_POINTERS:
            continue
        for match in set(_PATHLIKE.findall(text)):
            if Path(match).name in LOCAL_BY_DESIGN:
                continue
            # Both spellings occur: repo-relative (`docs/paths.md`) and relative
            # to the citing file (`paths.md` inside docs/, `../docs/x.md` above
            # it). Resolve each, and judge trackedness on what it resolved to.
            here = (root / name).parent
            for base in (root, here):
                target = (base / match.lstrip("./")).resolve()
                if not target.exists():
                    continue
                rel = str(target.relative_to(root.resolve()))
                if rel in tracked or rel.startswith(GENERATED_DIRS):
                    break
                dead.append(f"{name} -> {match}")
                break

    assert not dead, (
        "tracked files point at paths that exist locally but are not committed, "
        f"so they are dead for anyone who clones: {sorted(dead)}"
    )


def _github_slug(heading: str) -> str:
    """The anchor GitHub generates for a heading.

    Faithful to `github-slugger`, and the order matters: **trim first, then strip
    punctuation, and never collapse runs of hyphens.** A heading opening with an
    emoji trims to nothing, loses the emoji, and is left with a leading space that
    becomes a leading hyphen — so `## ⚠️ Note` is `#-note`, not `#note`. Getting
    the order wrong the other way produces a checker that reports working links as
    broken, which is worse than no checker: the fix looks like editing the link.
    """
    text = heading.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return text.replace(" ", "-")


def test_every_markdown_link_resolves():
    """Relative links and `#anchors` in tracked markdown point at something real.

    Anchors rot in a way plain links do not: renaming a heading leaves every
    pointer to it silently landing at the top of the page instead of 404ing, so
    nothing ever surfaces it.
    """
    root = Path(config.PROJECT_ROOT).resolve()
    docs = [
        name
        for name in subprocess.run(
            ["git", "ls-files", "*.md"], cwd=root, capture_output=True, text=True, check=True
        ).stdout.split()
    ]
    anchors = {
        name: {
            _github_slug(m.group(1))
            for m in re.finditer(r"^#{1,6}\s+(.*)$", (root / name).read_text(), re.M)
        }
        for name in docs
    }

    broken = []
    for name in docs:
        here = (root / name).parent
        for match in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", (root / name).read_text()):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            path, _, anchor = target.partition("#")
            resolved = (here / path).resolve() if path else (root / name).resolve()
            if not resolved.exists():
                broken.append(f"{name} -> {target} (no such file)")
                continue
            rel = str(resolved.relative_to(root))
            if anchor and rel in anchors and anchor not in anchors[rel]:
                broken.append(f"{name} -> {target} (no such heading)")

    assert not broken, f"broken markdown links: {sorted(broken)}"


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
