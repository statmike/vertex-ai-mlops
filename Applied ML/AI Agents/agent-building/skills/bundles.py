"""Discover skill bundles and read their SKILL.md front matter — offline core.

A *skill bundle* is a directory with a ``SKILL.md`` at its root (plus optional
``reference/``, ``narrative/``, assets). The platform Skill Registry wants a
``display_name`` and ``description`` for each; both live in the SKILL.md YAML
front matter (``name`` / ``description``). This module finds the bundles and
parses that front matter so ``registry.py`` can publish them without re-deriving
metadata — and it's pure (no cloud, no SDK), so it's unit-tested offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkillBundle:
    """A publishable skill bundle discovered on disk.

    ``skill_id`` is the registry id (the directory name); ``name`` and
    ``description`` come from the SKILL.md front matter and default to sensible
    fallbacks if the front matter is missing a field.
    """

    skill_id: str
    name: str
    description: str
    path: Path


def _parse_front_matter(skill_md: str) -> dict[str, str]:
    """Extract simple ``key: value`` pairs from a SKILL.md YAML front-matter block.

    The block is delimited by ``---`` lines at the top of the file. We only need
    scalar ``name`` and ``description`` values, so this is a deliberately small
    parser — no external YAML dependency, and it tolerates a missing block by
    returning an empty mapping. A value may be wrapped in quotes; they're
    stripped. Keys after the first blank continuation are ignored (descriptions
    here are single-line).
    """
    lines = skill_md.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line or line.startswith((" ", "\t")):
            # Skip continuation/indented lines — front matter here is flat scalars.
            continue
        key, _, value = line.partition(":")
        value = value.strip().strip('"').strip("'")
        if key.strip() and value:
            fields[key.strip()] = value
    return fields


def load_bundle(path: Path) -> SkillBundle | None:
    """Build a SkillBundle from a directory, or None if it has no SKILL.md.

    The registry id is the directory name; name/description come from the
    SKILL.md front matter, falling back to the id and a generic description so a
    bundle missing front-matter fields is still publishable.
    """
    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        return None
    fields = _parse_front_matter(skill_md.read_text())
    skill_id = path.name
    return SkillBundle(
        skill_id=skill_id,
        name=fields.get("name", skill_id),
        description=fields.get("description", f"Skill bundle: {skill_id}"),
        path=path,
    )


def discover_bundles(source_dir: str | Path) -> list[SkillBundle]:
    """Find every skill bundle under ``source_dir`` (one level of subdirectories).

    A bundle is any immediate subdirectory containing a SKILL.md. Returns them
    sorted by skill_id for a stable publish order. A non-existent source dir
    yields an empty list (the caller reports it).
    """
    root = Path(source_dir)
    if not root.is_dir():
        return []
    bundles = []
    for child in sorted(root.iterdir()):
        if child.is_dir():
            bundle = load_bundle(child)
            if bundle is not None:
                bundles.append(bundle)
    return bundles
