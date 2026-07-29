"""Convert a project notebook into a lean, agent-readable narrative markdown file.

Strips only cells that are provably generic execution ceremony (the tracker/badge
header, the shared `install()` helper, the Colab-only auth shim) and the trailing
Cleanup section. Everything else in Setup/Environment is kept, since it can carry
real technique-specific requirements (a connection, a reservation, an IAM grant).

Relative links into the source repo (e.g. `../../RESOURCES.md`) are rewritten as
plain, repo-relative code-formatted text rather than left as clickable relative
links, since they won't resolve once this file lives inside a skill's `narrative/`
folder. External (http/https) links are left untouched.
"""

from __future__ import annotations

import re
from pathlib import Path

import nbformat

MAGIC_LANG_MAP = {
    "%%bigquery": "sql",
    "%%bash": "bash",
    "%%sh": "bash",
    "%%writefile": "python",
}

_HEADER_TABLE_MARKERS = ("tracker", "header table")
_LINK_RE = re.compile(r"\[([^\]]+)\]\((?!https?://)([^)]+)\)")


def _is_header_table(cell) -> bool:
    if cell.cell_type != "markdown":
        return False
    source_lower = cell.source.lower()
    return all(marker in source_lower for marker in _HEADER_TABLE_MARKERS)


def _is_generic_install_helper(cell) -> bool:
    return cell.cell_type == "code" and "def install(" in cell.source


def _is_generic_colab_auth(cell) -> bool:
    return (
        cell.cell_type == "code"
        and "from google.colab import auth" in cell.source
        and "authenticate_user" in cell.source
    )


def _is_cleanup_start(cell) -> bool:
    if cell.cell_type != "markdown":
        return False
    return bool(re.search(r"^#+\s*cleanup", cell.source.strip(), re.IGNORECASE | re.MULTILINE))


def _detect_lang(source: str) -> str:
    stripped = source.lstrip()
    for magic, lang in MAGIC_LANG_MAP.items():
        if stripped.startswith(magic):
            return lang
    return "python"


def _resolve_relative_path(notebook_dir: str, relative_path: str) -> str:
    """Resolve a link relative to the notebook's directory into a subproject-root-relative path."""
    combined = f"{notebook_dir}/{relative_path}" if notebook_dir else relative_path
    parts: list[str] = []
    for part in combined.split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part and part != ".":
            parts.append(part)
    return "/".join(parts)


def _fix_links(markdown_text: str, notebook_dir: str) -> str:
    def repl(match: re.Match) -> str:
        text, target = match.group(1), match.group(2)
        if target.startswith("#"):
            return match.group(0)  # in-page anchor, leave alone
        resolved = _resolve_relative_path(notebook_dir, target)
        return f"`{resolved}` ({text})"

    return _LINK_RE.sub(repl, markdown_text)


def convert_notebook(notebook_path: Path, subproject_root: Path) -> str:
    """Return the extracted narrative markdown for one notebook.

    `notebook_path` must be inside `subproject_root`; relative links found in
    markdown cells are rewritten relative to `subproject_root`.
    """
    notebook_path = notebook_path.resolve()
    subproject_root = subproject_root.resolve()
    notebook_dir = str(notebook_path.parent.relative_to(subproject_root))
    if notebook_dir == ".":
        notebook_dir = ""

    nb = nbformat.read(notebook_path, as_version=4)

    blocks: list[str] = []
    for cell in nb.cells:
        if _is_header_table(cell) or _is_generic_install_helper(cell) or _is_generic_colab_auth(cell):
            continue
        if _is_cleanup_start(cell):
            break
        if cell.cell_type == "markdown":
            blocks.append(_fix_links(cell.source.rstrip(), notebook_dir))
        elif cell.cell_type == "code":
            source = cell.source.rstrip()
            if not source:
                continue
            lang = _detect_lang(source)
            blocks.append(f"```{lang}\n{source}\n```")

    return "\n\n".join(blocks)


def convert_notebook_to_file(notebook_path: Path, subproject_root: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(convert_notebook(notebook_path, subproject_root) + "\n")
