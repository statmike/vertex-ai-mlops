"""Inventory the model and endpoint literals a project pins, and flag any that are not on the allow list.

Why this exists. A project that teaches `endpoint => 'gemini-2.5-flash'` or `model => 'TimesFM 2.0'`
in dozens of notebooks has no cheap way to answer "where do we still name a version that just got
retired?" — the October 2026 sweep answered it with ad-hoc greps across .ipynb, .sql and .md files.
This check makes that inventory a one-liner and, with an allow list, turns a retirement into a
failing check instead of a reader's surprise.

What counts as a pin. Any string literal passed as `endpoint => '...'` or `model => '...'` in SQL
(inside notebooks' code cells, .sql files and fenced code in markdown), plus the Python keyword forms
`endpoint='...'` / `model='...'` that the BigFrames wrappers use. Markdown prose that merely
*mentions* a model name is deliberately not a pin — prose is the README/reference layer's job and is
covered by reading, not by this check.

The allow list is a JSON object keyed by repo-relative project path; the special key `"*"` applies to
every project:

    {"*": ["text-embedding-005"], "data+ai/bq-ai-functions": ["gemini-2.5-flash", "TimesFM 2.5"]}

Literals containing `{` (f-string placeholders such as `{ENDPOINT}`) and documentation placeholders
(`'ENDPOINT'`, `'MODEL'`, `'projects/PROJECT_ID/...'`) are skipped — they are not pins.
Files under `.venv/`, `.ipynb_checkpoints/` and `node_modules/` are ignored.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

SKIP_PARTS = {".venv", ".ipynb_checkpoints", "node_modules", "__pycache__"}

# SQL named arguments: endpoint => 'x' / model => "x"; Python keywords: endpoint='x' / model="x".
_PIN_RE = re.compile(
    r"""\b(?P<kind>endpoint|model)\s*(?:=>|=)\s*(?P<quote>['"])(?P<value>[^'"\n]*)(?P=quote)""",
    re.IGNORECASE,
)
_FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
_PLACEHOLDER_TOKEN_RE = re.compile(r"\b(?:PROJECT_ID|PROJECT_NUM|PROJECT_NUMBER|LOCATION|REGION|ENDPOINT_ID|PROCESSOR_ID|MODEL_ID|CONNECTION_ID|DATASET_ID|ENDPOINT|MODEL)\b")


def is_placeholder(value: str) -> bool:
    """True for syntax-table placeholders rather than real pins: f-string holes, ALL_CAPS tokens,
    and URL/path templates with PROJECT_ID-style segments."""
    if not value or "{" in value:
        return True
    if value.lower() in {"endpoint", "model"}:
        return True
    if re.fullmatch(r"[A-Z0-9_]+", value):
        return True
    return bool(_PLACEHOLDER_TOKEN_RE.search(value))


@dataclass
class Pin:
    path: Path
    location: str  # "cell 12" or "line 40"
    kind: str
    value: str

    def format(self, project_root: Path) -> str:
        return f"{self.path.relative_to(project_root)} ({self.location}): {self.kind} => '{self.value}'"


@dataclass
class PinnedModelsResult:
    project_root: Path
    scanned: int = 0
    pins: list[Pin] = field(default_factory=list)
    unlisted: list[Pin] = field(default_factory=list)

    @property
    def counts(self) -> Counter:
        return Counter(p.value for p in self.pins)

    @property
    def ok(self) -> bool:
        return not self.unlisted


def _pins_in_text(text: str, path: Path, location: str) -> list[Pin]:
    out: list[Pin] = []
    for m in _PIN_RE.finditer(text):
        value = m.group("value").strip()
        if is_placeholder(value):
            continue
        out.append(Pin(path=path, location=location, kind=m.group("kind").lower(), value=value))
    return out


def _pins_in_notebook(path: Path) -> list[Pin]:
    nb = json.loads(path.read_text(encoding="utf-8"))
    out: list[Pin] = []
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        out.extend(_pins_in_text(source, path, f"cell {idx}"))
    return out


def _pins_in_markdown(path: Path) -> list[Pin]:
    text = path.read_text(encoding="utf-8")
    out: list[Pin] = []
    for m in _FENCE_RE.finditer(text):
        line_no = text.count("\n", 0, m.start()) + 1
        out.extend(_pins_in_text(m.group(1), path, f"line {line_no}"))
    return out


def _pins_in_plain(path: Path) -> list[Pin]:
    text = path.read_text(encoding="utf-8")
    out: list[Pin] = []
    for m in _PIN_RE.finditer(text):
        value = m.group("value").strip()
        if is_placeholder(value):
            continue
        line_no = text.count("\n", 0, m.start()) + 1
        out.append(Pin(path=path, location=f"line {line_no}", kind=m.group("kind").lower(), value=value))
    return out


def iter_project_files(project_root: Path):
    for path in sorted(project_root.rglob("*")):
        if not path.is_file() or SKIP_PARTS & set(path.parts):
            continue
        if path.suffix in {".ipynb", ".sql", ".md", ".py"}:
            yield path


def check_pinned_models(project_root: Path, allowed: set[str]) -> PinnedModelsResult:
    result = PinnedModelsResult(project_root=project_root)
    for path in iter_project_files(project_root):
        result.scanned += 1
        if path.suffix == ".ipynb":
            pins = _pins_in_notebook(path)
        elif path.suffix == ".md":
            pins = _pins_in_markdown(path)
        else:
            pins = _pins_in_plain(path)
        result.pins.extend(pins)
    if allowed:
        result.unlisted = [p for p in result.pins if p.value not in allowed]
    return result


def load_allow_list(allow_file: Path, project_root: Path, repo_root: Path) -> set[str]:
    data = json.loads(allow_file.read_text(encoding="utf-8"))
    try:
        key = str(project_root.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        key = str(project_root)
    allowed: set[str] = set(data.get("*", []))
    allowed |= set(data.get(key, []))
    return allowed
