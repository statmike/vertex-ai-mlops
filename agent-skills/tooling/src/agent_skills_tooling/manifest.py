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


def build_manifest(skill_dir: Path, version: str = "0.1.0") -> dict:
    reference_files = sorted(p.name for p in (skill_dir / "reference").glob("*.md")) if (skill_dir / "reference").exists() else []
    narrative_files = sorted(p.name for p in (skill_dir / "narrative").glob("*.md")) if (skill_dir / "narrative").exists() else []

    existing_manifest_path = skill_dir / MANIFEST_FILENAME
    if existing_manifest_path.exists():
        version = json.loads(existing_manifest_path.read_text()).get("version", version)

    return {
        "name": skill_dir.name,
        "version": version,
        "generated_date": date.today().isoformat(),
        "source_commit": _git_short_hash(skill_dir),
        "reference_files": reference_files,
        "narrative_files": narrative_files,
    }


def write_manifest(skill_dir: Path, version: str = "0.1.0") -> Path:
    manifest = build_manifest(skill_dir, version=version)
    manifest_path = skill_dir / MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest_path
