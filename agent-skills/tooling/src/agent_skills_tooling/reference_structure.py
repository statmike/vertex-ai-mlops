"""Check that a project's `RESOURCES.md` index and its `reference/` pages agree.

`RESOURCES.md` is the entry point 400+ links across this repository point at. It
no longer holds the reference itself -- each top-level section is a page under
`reference/` -- which means the index is now load-bearing: a page it does not
list is a page nobody finds, and a page it lists that does not exist is a dead
end at the top of the reference.

Neither failure breaks a build or shows up in `check-links`, and both are the
natural result of adding a section and forgetting one line. Hence this check.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from agent_skills_tooling.markdown_anchors import headings, slugify

INDEX_FILENAME = "RESOURCES.md"
REFERENCE_DIRNAME = "reference"

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


@dataclass
class ReferenceResult:
    project_root: Path
    errors: list[str] = field(default_factory=list)
    checked: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def _index_targets(index_path: Path) -> set[str]:
    """Filenames under reference/ that the index links to."""
    targets = set()
    for match in _LINK_RE.finditer(index_path.read_text()):
        target = match.group(1).split("#")[0]
        if target.startswith(f"{REFERENCE_DIRNAME}/") and target.endswith(".md"):
            targets.add(Path(target).name)
    return targets


def check_reference(project_root: Path) -> ReferenceResult:
    project_root = project_root.resolve()
    result = ReferenceResult(project_root=project_root)

    index_path = project_root / INDEX_FILENAME
    reference_dir = project_root / REFERENCE_DIRNAME
    if not index_path.exists():
        result.errors.append(f"{INDEX_FILENAME} not found")
        return result
    if not reference_dir.exists():
        # A project may legitimately keep a single-file reference.
        return result

    pages = {p.name for p in reference_dir.glob("*.md")}
    linked = _index_targets(index_path)
    result.checked = len(pages)

    for orphan in sorted(pages - linked):
        result.errors.append(f"{REFERENCE_DIRNAME}/{orphan} exists but {INDEX_FILENAME} does not link to it")
    for missing in sorted(linked - pages):
        result.errors.append(f"{INDEX_FILENAME} links to {REFERENCE_DIRNAME}/{missing}, which does not exist")

    # A page is one top-level section, and its filename is that section's slug with
    # hyphen runs collapsed. Holding to that is what lets a reader guess a filename.
    for page in sorted(pages & linked):
        page_headings = headings((reference_dir / page).read_text())
        titles = [title for level, title in page_headings if level == 1]
        if len(titles) != 1:
            result.errors.append(f"{REFERENCE_DIRNAME}/{page} has {len(titles)} top-level headings, expected exactly 1")
            continue
        expected = re.sub(r"-{2,}", "-", slugify(titles[0])).strip("-") + ".md"
        if page != expected:
            result.errors.append(f"{REFERENCE_DIRNAME}/{page} is titled '{titles[0]}', so it should be named {expected}")

    return result
