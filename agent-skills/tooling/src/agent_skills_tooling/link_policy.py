"""Enforce the outward-link policy on a source project (`bq-ml`, `bq-ai-functions`).

These projects are the canonical source of truth for BigQuery ML and BigQuery AI
Functions, and their content is copied into distributable agent skills. A reference
that points outside the project cannot travel with the skill, so the policy is:

A link may target
  1. the project itself (relative),
  2. the sibling project (`../bq-ml/...`, `../bq-ai-functions/...`),
  3. public documentation or public data (`https://...`).

Anything else -- elsewhere in this repo, or outside it -- is a violation.

Two distinctions matter:

*Links* (``[text](target)``) are followable, so an outward one is always a violation.
An in-project link that names a ``#anchor`` is also checked against the headings the
target file actually offers -- a link to a heading that was renamed or moved still
resolves to the file, so nothing else catches it.
*Mentions* (a backticked path in prose) are only a violation when the target still
exists somewhere outside the project: that is a live pointer a reader will chase.
A mention of a path that no longer exists is retirement provenance -- it records
where content came from and there is nothing to follow -- so it is allowed.

Exemptions:
  - ``PLANS.md`` is forward-looking, repo-bound, and never shipped in a skill. It may
    cite anything, including sources outside the repo.
  - ``README.md`` may link to ``agent-skills/``, the artifact built from the project.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from agent_skills_tooling.markdown_anchors import anchors_of

_LINK_RE = re.compile(r"\[([^\]]*)\]\(((?:[^()\s]|\([^()]*\))+)\)")
_MENTION_RE = re.compile(r"`([^`\n]+)`")
_SKIP_DIRS = {".venv", ".ipynb_checkpoints", "__pycache__", ".git", "node_modules"}
_SCANNED_SUFFIXES = {".ipynb", ".md", ".sql", ".py"}
_EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "gs://", "bq://")
_PATH_SUFFIXES = {".ipynb", ".md", ".sql", ".py", ".json", ".csv", ".yaml", ".yml", ".txt"}

EXEMPT_ANY_TARGET = {"PLANS.md"}
README_ALLOWED_PREFIX = "agent-skills"


@dataclass
class Violation:
    file: Path
    cell: int | None
    line: int
    kind: str  # "link", "anchor", or "mention"
    target: str
    reason: str

    def format(self, project_root: Path) -> str:
        where = str(self.file.relative_to(project_root))
        # For a notebook the line is relative to the cell, which is how an
        # editor working through the cell's source sees it.
        where += f" cell {self.cell}:{self.line}" if self.cell is not None else f":{self.line}"
        return f"{where}: {self.reason} [{self.kind}] {self.target}"


@dataclass
class PolicyResult:
    project_root: Path
    violations: list[Violation] = field(default_factory=list)
    scanned: int = 0

    @property
    def ok(self) -> bool:
        return not self.violations


def _sources(path: Path):
    """Yield (cell_index_or_None, text) for a scannable file."""
    if path.suffix == ".ipynb":
        try:
            notebook = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError):
            return
        for index, cell in enumerate(notebook.get("cells", [])):
            yield index, "".join(cell.get("source", []))
    else:
        try:
            yield None, path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _looks_like_path(candidate: str) -> bool:
    if "/" not in candidate or candidate.startswith(_EXTERNAL_SCHEMES):
        return False
    if any(ch in candidate for ch in "{}$*<>|"):
        return False
    return Path(candidate).suffix in _PATH_SUFFIXES


def _resolve(target: str, base: Path) -> Path:
    cleaned = target.split("#")[0].replace("%20", " ").replace("%28", "(").replace("%29", ")")
    return (base / cleaned).resolve()


def _classify(resolved: Path, project_root: Path, sibling_roots: list[Path], repo_root: Path) -> str:
    """Return "" when allowed, else a reason string."""
    if resolved.is_relative_to(project_root):
        return ""
    for sibling in sibling_roots:
        if resolved.is_relative_to(sibling):
            return ""
    if not resolved.is_relative_to(repo_root):
        return "points outside the repository"
    return "points elsewhere in the repository"


def check_project(
    project_root: Path,
    sibling_roots: list[Path],
    repo_root: Path,
) -> PolicyResult:
    project_root = project_root.resolve()
    sibling_roots = [s.resolve() for s in sibling_roots]
    repo_root = repo_root.resolve()
    result = PolicyResult(project_root=project_root)

    for path in sorted(project_root.rglob("*")):
        if not path.is_file() or path.suffix not in _SCANNED_SUFFIXES:
            continue
        if _SKIP_DIRS & set(path.parts):
            continue
        # PLANS.md is exempt from the *outward-target* policy, not from having its
        # links resolve: a citation pointing at a heading that no longer exists is
        # broken wherever it lives.
        policy_exempt = path.name in EXEMPT_ANY_TARGET
        result.scanned += 1
        is_readme = path.name == "README.md"

        for cell, text in _sources(path):
            for match in _LINK_RE.finditer(text):
                target = match.group(2)
                if target.startswith(_EXTERNAL_SCHEMES):
                    continue
                if target.startswith("#"):
                    if target[1:] not in anchors_of(path):
                        line = _line_of(text, match.start())
                        result.violations.append(
                            Violation(path, cell, line, "anchor", target, "no heading matches this anchor")
                        )
                    continue
                resolved = _resolve(target, path.parent)
                skip_policy = policy_exempt or (
                    is_readme and resolved.is_relative_to(repo_root / README_ALLOWED_PREFIX)
                )
                reason = "" if skip_policy else _classify(resolved, project_root, sibling_roots, repo_root)
                if not reason and not resolved.exists():
                    reason = "" if policy_exempt else "link target does not exist"
                if reason:
                    line = _line_of(text, match.start())
                    result.violations.append(Violation(path, cell, line, "link", target, reason))
                    continue

                anchor = target.partition("#")[2]
                if not anchor or resolved.suffix not in {".md", ".ipynb"} or not resolved.exists():
                    continue
                if anchor not in anchors_of(resolved):
                    line = _line_of(text, match.start())
                    result.violations.append(
                        Violation(path, cell, line, "anchor", target, "no heading matches this anchor")
                    )

            if policy_exempt:
                continue

            for match in _MENTION_RE.finditer(text):
                candidate = match.group(1).strip()
                if not _looks_like_path(candidate):
                    continue
                for base in (path.parent, repo_root):
                    resolved = _resolve(candidate, base)
                    # A mention only offends when it still resolves to live content
                    # outside the project; a dangling one is retirement provenance.
                    if not resolved.exists():
                        continue
                    if is_readme and resolved.is_relative_to(repo_root / README_ALLOWED_PREFIX):
                        break
                    reason = _classify(resolved, project_root, sibling_roots, repo_root)
                    if reason:
                        line = _line_of(text, match.start())
                        result.violations.append(Violation(path, cell, line, "mention", candidate, reason))
                    break

    # Report in reading order so a fix pass can work straight down the list.
    result.violations.sort(key=lambda v: (str(v.file), v.cell if v.cell is not None else -1, v.line))
    return result
