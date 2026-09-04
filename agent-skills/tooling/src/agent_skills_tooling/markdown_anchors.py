"""Resolve markdown heading anchors the way GitHub does.

Shared by the anchor check in `link_policy` and the index check in
`reference_structure`. Both need the same two things: the set of anchors a file
offers, and the slug GitHub will generate for a heading. Getting either subtly
wrong turns the check into noise, so they live in one place.

Fence-awareness is the part that is easy to get wrong: a `# TensorFlow SavedModel`
line inside a ```sql block is a comment, not a heading, and treating it as one
invents anchors that do not exist.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_INLINE_HTML_RE = re.compile(r"<[^>]*>")
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def slugify(title: str) -> str:
    """GitHub's heading-anchor algorithm: lowercase, drop punctuation, spaces to hyphens."""
    text = title.strip().lower()
    text = _INLINE_HTML_RE.sub("", text)
    text = text.replace("`", "")
    text = _MARKDOWN_LINK_RE.sub(r"\1", text)
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return text.replace(" ", "-")


def headings(text: str) -> list[tuple[int, str]]:
    """[(level, title)] for every ATX heading outside a fenced code block."""
    found: list[tuple[int, str]] = []
    in_fence = False
    marker = None
    for line in text.split("\n"):
        fence = _FENCE_RE.match(line)
        if fence:
            token = fence.group(1)[0] * 3
            if not in_fence:
                in_fence, marker = True, token
            elif token == marker:
                in_fence, marker = False, None
            continue
        if in_fence:
            continue
        heading = _HEADING_RE.match(line)
        if heading:
            found.append((len(heading.group(1)), heading.group(2)))
    return found


def markdown_sources(path: Path) -> list[str]:
    """Markdown text of a file: the whole file, or a notebook's markdown cells."""
    if path.suffix != ".ipynb":
        return [path.read_text(encoding="utf-8", errors="replace")]
    try:
        notebook = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return []
    return ["".join(c.get("source", [])) for c in notebook.get("cells", []) if c.get("cell_type") == "markdown"]


def anchors_of(path: Path) -> set[str]:
    """Every anchor a reader can link to in this file.

    Repeated headings are the subtle part. GitHub keeps anchors unique by suffixing
    each repeat in document order -- four "When do you need one?" headings become
    `when-do-you-need-one`, `-1`, `-2`, `-3` (verified against GitHub's renderer on
    `bq-ai-functions/setup/README.md`, which has exactly that). Collapsing them to one
    slug would report a perfectly good link to `#...-2` as broken, so the count is
    carried across the whole document -- across cells too, since GitHub renders a
    notebook as one page.
    """
    seen: dict[str, int] = {}
    anchors = set()
    for text in markdown_sources(path):
        for _, title in headings(text):
            base = slugify(title)
            count = seen.get(base, 0)
            anchors.add(base if count == 0 else f"{base}-{count}")
            seen[base] = count + 1
    return anchors
