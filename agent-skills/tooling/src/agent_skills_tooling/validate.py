"""Lint a skill directory against this project's Agent Skill spec.

Checks:
- SKILL.md exists with valid frontmatter (`name`, `description` present and within spec limits).
- SKILL.md stays under the ~500-line progressive-disclosure budget.
- Any markdown file over ~100 lines gets flagged to carry a table of contents.
- Every non-http(s) markdown link in the skill resolves to a real file relative to the link's own file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_NAME_RE = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
_DESCRIPTION_RE = re.compile(r"^description:\s*(.+)$", re.MULTILINE)
_VALID_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_LINK_RE = re.compile(r"\[([^\]]+)\]\((?!https?://)([^)#]+)\)")

SKILL_MD_LINE_BUDGET = 500
REFERENCE_FILE_LINE_BUDGET = 100


@dataclass
class ValidationResult:
    skill_dir: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _check_frontmatter(skill_md_text: str, result: ValidationResult) -> None:
    match = _FRONTMATTER_RE.match(skill_md_text)
    if not match:
        result.errors.append("SKILL.md is missing YAML frontmatter (--- ... ---)")
        return
    frontmatter = match.group(1)

    name_match = _NAME_RE.search(frontmatter)
    if not name_match:
        result.errors.append("frontmatter missing 'name'")
    else:
        name = name_match.group(1).strip()
        if len(name) > 64:
            result.errors.append(f"name '{name}' exceeds 64 chars")
        if not _VALID_NAME_RE.match(name):
            result.errors.append(f"name '{name}' must be lowercase letters/digits/hyphens only")
        if "claude" in name or "anthropic" in name:
            result.errors.append(f"name '{name}' must not contain 'claude' or 'anthropic'")

    description_match = _DESCRIPTION_RE.search(frontmatter)
    if not description_match:
        result.errors.append("frontmatter missing 'description'")
    else:
        description = description_match.group(1).strip()
        if not description:
            result.errors.append("description is empty")
        if len(description) > 1024:
            result.errors.append(f"description exceeds 1024 chars ({len(description)})")


def _has_toc(text: str) -> bool:
    head = "\n".join(text.splitlines()[:10])
    return "contents:" in head.lower() or bool(re.search(r"\]\(#", head))


def _check_line_budget(path: Path, budget: int, result: ValidationResult) -> None:
    text = path.read_text()
    line_count = len(text.splitlines())
    if line_count <= budget:
        return
    if budget == REFERENCE_FILE_LINE_BUDGET:
        if not _has_toc(text):
            result.warnings.append(f"{path.name} is {line_count} lines (budget {budget}) — should carry a table of contents")
    else:
        result.warnings.append(f"{path.name} is {line_count} lines (budget {budget}) — should stay under budget")


def _check_links(path: Path, skill_dir: Path, result: ValidationResult) -> None:
    text = path.read_text()
    for match in _LINK_RE.finditer(text):
        link_text, target = match.group(1), match.group(2)
        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            result.errors.append(f"{path.relative_to(skill_dir)}: broken link [{link_text}]({target})")


def validate_skill(skill_dir: Path) -> ValidationResult:
    result = ValidationResult(skill_dir=skill_dir)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        result.errors.append("SKILL.md not found")
        return result

    _check_frontmatter(skill_md.read_text(), result)
    _check_line_budget(skill_md, SKILL_MD_LINE_BUDGET, result)
    _check_links(skill_md, skill_dir, result)

    reference_dir = skill_dir / "reference"
    if reference_dir.exists():
        for md_file in sorted(reference_dir.glob("*.md")):
            _check_line_budget(md_file, REFERENCE_FILE_LINE_BUDGET, result)
            _check_links(md_file, skill_dir, result)

    # narrative/ files are full notebook walkthroughs meant to be read sequentially —
    # the reference-file line budget (which exists to force a lookup-table TOC) doesn't apply.
    narrative_dir = skill_dir / "narrative"
    if narrative_dir.exists():
        for md_file in sorted(narrative_dir.glob("*.md")):
            _check_links(md_file, skill_dir, result)

    return result


def validate_all(skills_root: Path) -> dict[str, ValidationResult]:
    results = {}
    for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
        results[skill_dir.name] = validate_skill(skill_dir)
    return results
