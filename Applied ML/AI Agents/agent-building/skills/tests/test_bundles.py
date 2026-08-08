"""Offline tests for skill-bundle discovery and SKILL.md front-matter parsing.

These cover the pure core in `skills/bundles.py` — no cloud, no SDK. The cloud
round-trip (create/list/retrieve) lives in `registry.py` and is verified live.
"""

from pathlib import Path

from skills.bundles import (
    SkillBundle,
    _parse_front_matter,
    discover_bundles,
    load_bundle,
)

FRONT_MATTER = """\
---
name: BigQuery AI Functions
description: "When to reach for AI.GENERATE, ML.GENERATE_TEXT and friends."
license: Apache-2.0
---

# BigQuery AI Functions

Body text the parser must ignore.
"""


def _write_bundle(root: Path, skill_id: str, skill_md: str) -> Path:
    d = root / skill_id
    d.mkdir()
    (d / "SKILL.md").write_text(skill_md)
    return d


def test_parse_front_matter_reads_scalar_fields():
    fields = _parse_front_matter(FRONT_MATTER)
    assert fields["name"] == "BigQuery AI Functions"
    assert fields["description"].startswith("When to reach for AI.GENERATE")
    assert fields["license"] == "Apache-2.0"


def test_parse_front_matter_strips_quotes():
    fields = _parse_front_matter(FRONT_MATTER)
    # The quoted description must have its surrounding quotes removed.
    assert not fields["description"].startswith('"')


def test_parse_front_matter_missing_block_returns_empty():
    assert _parse_front_matter("# No front matter here\n\nJust prose.") == {}


def test_parse_front_matter_ignores_indented_continuation():
    text = "---\nname: Thing\ndescription: line one\n  still going\n---\n"
    fields = _parse_front_matter(text)
    assert fields == {"name": "Thing", "description": "line one"}


def test_load_bundle_reads_front_matter(tmp_path):
    d = _write_bundle(tmp_path, "bigquery-ai-functions", FRONT_MATTER)
    bundle = load_bundle(d)
    assert isinstance(bundle, SkillBundle)
    assert bundle.skill_id == "bigquery-ai-functions"
    assert bundle.name == "BigQuery AI Functions"
    assert bundle.description.startswith("When to reach for")
    assert bundle.path == d


def test_load_bundle_falls_back_when_front_matter_absent(tmp_path):
    d = _write_bundle(tmp_path, "bare-skill", "# Bare\n\nNo front matter.")
    bundle = load_bundle(d)
    assert bundle is not None
    # id is the directory name; name/description fall back so it's still publishable.
    assert bundle.skill_id == "bare-skill"
    assert bundle.name == "bare-skill"
    assert "bare-skill" in bundle.description


def test_load_bundle_without_skill_md_returns_none(tmp_path):
    d = tmp_path / "not-a-bundle"
    d.mkdir()
    assert load_bundle(d) is None


def test_discover_bundles_finds_and_sorts(tmp_path):
    _write_bundle(tmp_path, "zeta", FRONT_MATTER)
    _write_bundle(tmp_path, "alpha", FRONT_MATTER)
    (tmp_path / "loose_file.txt").write_text("ignored")  # non-dir is skipped
    (tmp_path / "empty_dir").mkdir()  # dir without SKILL.md is skipped
    bundles = discover_bundles(tmp_path)
    assert [b.skill_id for b in bundles] == ["alpha", "zeta"]


def test_discover_bundles_missing_dir_is_empty():
    assert discover_bundles("/nonexistent/path/for/skills") == []
