"""Tests for the pinned-models check and the sweep's project discovery.

Run from agent-skills/tooling:  uv run pytest -q
"""
import json
from pathlib import Path

from agent_skills_tooling.manifest import MANIFEST_FILENAME, source_projects
from agent_skills_tooling.pinned_models import check_pinned_models, is_placeholder, load_allow_list


def _write_notebook(path: Path, sources: list[str]) -> None:
    nb = {
        "cells": [{"cell_type": "code", "source": s, "metadata": {}, "outputs": [], "execution_count": None} for s in sources],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(nb))


def _make_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    project.mkdir()
    _write_notebook(project / "a.ipynb", [
        "SELECT AI.GENERATE('x', endpoint => 'gemini-2.5-flash')",
        "SELECT * FROM AI.FORECAST(TABLE t, data_col => 'y', timestamp_col => 'd', model => 'TimesFM 2.0')",
        "bbq.ai.forecast(df, data_col='y', timestamp_col='d', model='TimesFM 2.5')",
        "query = f\"... endpoint => '{ENDPOINT}' ...\"",
    ])
    (project / "b.sql").write_text("SELECT AI.EMBED('x', endpoint => 'text-embedding-005');\n")
    (project / "ref.md").write_text(
        "Prose that mentions gemini-9.9-ultra is not a pin.\n\n```sql\nSELECT AI.GENERATE('x', endpoint => 'ENDPOINT');\nSELECT AI.GENERATE('x', endpoint => 'gemini-2.5-pro');\n```\n"
    )
    (project / ".venv").mkdir()
    _write_notebook(project / ".venv" / "ignored.ipynb", ["endpoint => 'should-not-be-scanned'"])
    return project


def test_inventory_counts_every_real_pin_and_skips_placeholders(tmp_path):
    project = _make_project(tmp_path)
    result = check_pinned_models(project, allowed=set())
    assert result.counts == {
        "gemini-2.5-flash": 1,
        "TimesFM 2.0": 1,
        "TimesFM 2.5": 1,
        "text-embedding-005": 1,
        "gemini-2.5-pro": 1,
    }
    assert result.ok  # no allow list -> inventory only, nothing is "unlisted"


def test_unlisted_pin_fails_and_names_the_file_and_cell(tmp_path):
    project = _make_project(tmp_path)
    allowed = {"gemini-2.5-flash", "TimesFM 2.5", "text-embedding-005", "gemini-2.5-pro"}
    result = check_pinned_models(project, allowed)
    assert not result.ok
    assert [p.value for p in result.unlisted] == ["TimesFM 2.0"]
    assert result.unlisted[0].format(project) == "a.ipynb (cell 1): model => 'TimesFM 2.0'"


def test_placeholder_rules():
    assert is_placeholder("ENDPOINT")
    assert is_placeholder("MODEL")
    assert is_placeholder("{ENDPOINT}")
    assert is_placeholder("projects/PROJECT_ID/locations/us/processors/PROCESSOR_ID")
    assert not is_placeholder("gemini-2.5-flash")
    assert not is_placeholder("TimesFM 3.0")
    assert not is_placeholder("multimodalembedding@001")


def test_allow_list_merges_star_and_project_keys(tmp_path):
    repo = tmp_path
    project = repo / "data+ai" / "proj"
    project.mkdir(parents=True)
    allow = repo / "pinned-models.json"
    allow.write_text(json.dumps({"*": ["text-embedding-005"], "data+ai/proj": ["TimesFM 2.5"], "data+ai/other": ["nope"]}))
    assert load_allow_list(allow, project, repo) == {"text-embedding-005", "TimesFM 2.5"}


def test_source_projects_discovered_from_manifests(tmp_path):
    skills = tmp_path / "skills"
    for name, project in (("a", "data+ai/x"), ("b", "data+ai/y"), ("c", None), ("d", "data+ai/x")):
        (skills / name).mkdir(parents=True)
        (skills / name / MANIFEST_FILENAME).write_text(json.dumps({"name": name, "source_project": project}))
    assert source_projects(skills) == ["data+ai/x", "data+ai/y"]


def test_allow_file_found_through_symlinked_skills_root(tmp_path):
    """Repo layout: agent-skills/.agents/skills/<skill> is real; .agents/skills/<skill> at the repo root
    is a symlink into it. The allow list sits beside the real collection. Walking up from the symlink
    root alone never reaches it (that was the bug); walking up from a resolved skill does."""
    from agent_skills_tooling.pinned_models import find_allow_file

    repo = tmp_path
    real_root = repo / "agent-skills" / ".agents" / "skills"
    (real_root / "some-skill").mkdir(parents=True)
    (repo / "agent-skills" / "pinned-models.json").write_text("{}")
    link_root = repo / ".agents" / "skills"
    link_root.mkdir(parents=True)
    (link_root / "some-skill").symlink_to(real_root / "some-skill", target_is_directory=True)

    assert find_allow_file(real_root) == repo / "agent-skills" / "pinned-models.json"
    assert find_allow_file(link_root) == repo / "agent-skills" / "pinned-models.json"


def test_allow_file_absent_returns_none(tmp_path):
    from agent_skills_tooling.pinned_models import find_allow_file

    root = tmp_path / "skills"
    (root / "a").mkdir(parents=True)
    assert find_allow_file(root) is None
