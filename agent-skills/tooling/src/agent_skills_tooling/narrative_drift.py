"""Detect stale `narrative/*.md` by regenerating them and diffing.

`narrative/` is `convert-notebook` output. It goes stale the moment a source
notebook's markdown changes -- and nothing fails, warns, or looks different, so
the staleness survives until someone happens to read both copies side by side.
A markdown-only edit (a cross-link pass, a rename sweep) is the easy one to miss,
because it feels like it has nothing to do with the skills.

Regenerating all of them and diffing takes seconds. That is the whole check.

Which project a skill draws from comes from `source_project` in the skill's
manifest, so the command needs no arguments beyond the skills root. A skill
without that field, or without a `narrative/` folder, is skipped.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from agent_skills_tooling.convert_notebook import convert_notebook
from agent_skills_tooling.manifest import MANIFEST_FILENAME

NARRATIVE_DIRNAME = "narrative"
_SKIP_DIRS = {".venv", ".ipynb_checkpoints", "__pycache__", ".git", "node_modules"}


@dataclass
class DriftResult:
    skill_name: str
    stale: list[str] = field(default_factory=list)
    missing_source: list[str] = field(default_factory=list)
    checked: int = 0

    @property
    def ok(self) -> bool:
        return not self.stale and not self.missing_source


def _find_notebook(project_root: Path, stem: str) -> Path | None:
    for candidate in sorted(project_root.rglob(f"{stem}.ipynb")):
        if not _SKIP_DIRS & set(candidate.parts):
            return candidate
    return None


def check_skill_narratives(skill_dir: Path, repo_root: Path) -> DriftResult | None:
    """None when the skill declares no source project or carries no narratives."""
    result = DriftResult(skill_name=skill_dir.name)
    manifest_path = skill_dir / MANIFEST_FILENAME
    narrative_dir = skill_dir / NARRATIVE_DIRNAME
    if not manifest_path.exists() or not narrative_dir.exists():
        return None

    source_project = json.loads(manifest_path.read_text()).get("source_project")
    if not source_project:
        return None
    project_root = (repo_root / source_project).resolve()

    for narrative in sorted(narrative_dir.glob("*.md")):
        result.checked += 1
        notebook = _find_notebook(project_root, narrative.stem)
        if notebook is None:
            result.missing_source.append(narrative.name)
            continue
        # Match how convert_notebook_to_file writes it, trailing newline included.
        regenerated = convert_notebook(notebook_path=notebook, subproject_root=project_root) + "\n"
        if regenerated != narrative.read_text():
            result.stale.append(narrative.name)

    return result


def check_all_narratives(skills_root: Path, repo_root: Path) -> dict[str, DriftResult]:
    results = {}
    for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
        result = check_skill_narratives(skill_dir, repo_root)
        if result is not None:
            results[skill_dir.name] = result
    return results
