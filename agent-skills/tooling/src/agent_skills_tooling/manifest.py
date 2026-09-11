"""Generate/update a per-skill manifest: version, source commit, and file inventory.

The manifest is a single source of truth for "what version of this skill is this,
and when was it last regenerated" — consumed later by the hub sync, the plugin
marketplace listing, and any PyPI packaging, so those don't each track this
independently and drift.
"""

from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path

MANIFEST_FILENAME = "skill.manifest.json"


def _git_short_hash(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


DEFAULT_VERSION = "0.1.0"


def build_manifest(skill_dir: Path, version: str | None = None, source_project: str | None = None) -> dict:
    """Build a manifest dict. `None` for a field means "keep whatever is already there".

    An explicit value always wins. Passing nothing preserves the existing manifest's
    value, falling back to DEFAULT_VERSION for a brand-new skill's version.

    `source_project` is the repo-relative project this skill is built from (e.g.
    `data+ai/bq-ml`). It is what lets the narrative drift check find the source
    notebooks without being told where they are.

    `narrative_sources` maps a narrative filename to its project-relative source
    notebook. It is only needed when the stem-based lookup is ambiguous or does
    not apply -- two folders sharing a name (`functions/feature_store/` and
    `workflows/feature_store/`), or a narrative deliberately renamed to keep them
    apart. Preserved as-is here; the drift check is what reads it.
    """
    reference_files = sorted(p.name for p in (skill_dir / "reference").glob("*.md")) if (skill_dir / "reference").exists() else []
    narrative_files = sorted(p.name for p in (skill_dir / "narrative").glob("*.md")) if (skill_dir / "narrative").exists() else []

    existing = {}
    existing_manifest_path = skill_dir / MANIFEST_FILENAME
    if existing_manifest_path.exists():
        existing = json.loads(existing_manifest_path.read_text())
    if version is None:
        version = existing.get("version", DEFAULT_VERSION)
    if source_project is None:
        source_project = existing.get("source_project")
    narrative_sources = existing.get("narrative_sources", {})

    return {
        "name": skill_dir.name,
        "version": version,
        "source_project": source_project,
        "narrative_sources": narrative_sources,
        "generated_date": date.today().isoformat(),
        "source_commit": _git_short_hash(skill_dir),
        "reference_files": reference_files,
        "narrative_files": narrative_files,
    }


def write_manifest(skill_dir: Path, version: str | None = None, source_project: str | None = None) -> tuple[Path, str]:
    manifest = build_manifest(skill_dir, version=version, source_project=source_project)
    manifest_path = skill_dir / MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest_path, manifest["version"]
