"""Render a standalone ``report.pdf`` from ``readme.md`` + ``examples/results.md``.

The PDF is a self-contained findings report for a reader who does not have the
repo: it keeps the substantive narrative (challenge, experiment, approaches,
full results, caveats) and drops repo-specific plumbing — the GitHub/share
header, install/setup/cleanup commands, configuration, and project structure.

The two sources are stitched so the report reads top-to-bottom:

    readme.md   → title + intro, The Challenge, The Experiment, The Five
                  Approaches, then Caveats & Future Directions
    results.md  → spliced in whole (headline finding, tables, embedded plots)
                  where the README's short "Results" digest sits

Both sources are generated/maintained elsewhere (``build_results.py`` refreshes
results.md + the README digest), so this script only *reads* them — regenerate
the PDF after any docs change.

WeasyPrint + Markdown are heavy and preview-irrelevant to the project, so they
are pulled ephemerally rather than added to ``pyproject.toml``. Run from the
project root::

    uv run --with weasyprint --with markdown python examples/build_report.py

Output: ``report.pdf`` in the project root (next to ``readme.md``).
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
README = PROJECT_ROOT / "readme.md"
RESULTS_MD = Path(__file__).parent / "results.md"
OUTPUT_PDF = PROJECT_ROOT / "report.pdf"

# The report title (the README H1 doubles as this).
DOC_TITLE = "BigQuery Context — NL2SQL Table-Discovery Benchmark"

# Level-2 (``## ``) README sections to drop as repo-specific plumbing. Matched
# on the heading text after "## ". Everything else from the H1 onward is kept.
DROP_SECTIONS = {
    "Prerequisites",
    "Cleanup",
    "Configuration",
    "Project Structure",
}

# The README's "Results" section is a short digest that points at results.md;
# we replace it in place with the full results.md body.
RESULTS_SECTION = "Results"


def _split_sections(md: str) -> list[tuple[str, str]]:
    """Split markdown from its first H1 into (heading_text, block) pairs.

    The intro block (H1 + text before the first ``## ``) is returned with an
    empty heading_text so callers can treat it as always-kept.
    """
    # Start at the H1 title, discarding any header/front-matter above it.
    h1 = re.search(r"^# .+$", md, flags=re.MULTILINE)
    body = md[h1.start():] if h1 else md

    sections: list[tuple[str, str]] = []
    parts = re.split(r"(?m)^(## .+)$", body)
    # parts[0] = intro (H1 + lead text); then alternating (heading, content).
    sections.append(("", parts[0]))
    for i in range(1, len(parts), 2):
        heading_line = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ""
        title = heading_line[len("## "):].strip()
        sections.append((title, heading_line + content))
    return sections


def _results_body() -> str:
    """The full results.md, demoted so its H1 becomes an H2 under the report."""
    text = RESULTS_MD.read_text()
    # Drop the results H1 (its content is reintroduced as "## Results" below);
    # promote nothing else — the internal ## / ### structure is preserved.
    text = re.sub(r"^# .+\n", "", text, count=1, flags=re.MULTILINE)
    # The results.md intro points at readme.md/GROUND_TRUTH.md for context that
    # is *above* this section (or absent) in the standalone PDF — drop that line
    # so the report doesn't dangle a broken cross-reference.
    text = re.sub(
        r"^Five table-discovery approaches.*grading rubric\.\n",
        "",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    return "## Results\n" + text


def build_markdown() -> str:
    """Assemble the stitched, plumbing-free markdown source for the PDF."""
    sections = _split_sections(README.read_text())
    out: list[str] = []
    for title, block in sections:
        if title in DROP_SECTIONS:
            continue
        if title == RESULTS_SECTION:
            out.append(_results_body())
            continue
        out.append(block)
    return "\n".join(out)


def _resolve_image_paths(html: str) -> str:
    """Rewrite results.md's ``results/plots/*.png`` refs to absolute file URIs.

    results.md paths are relative to ``examples/``; the PDF is rendered with the
    project root as base, so point them at the real files on disk.
    """
    plots_dir = (Path(__file__).parent / "results" / "plots").resolve()

    def repl(m: re.Match) -> str:
        fname = Path(m.group(1)).name
        return f'src="{(plots_dir / fname).as_uri()}"'

    return re.sub(r'src="[^"]*results/plots/([^"]+)"', repl, html)


CSS = """
@page { size: A4; margin: 1.8cm 1.6cm; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 10pt;
       line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 20pt; color: #0b3d64; border-bottom: 3px solid #0b3d64;
     padding-bottom: 6px; }
h2 { font-size: 14pt; color: #0b3d64; margin-top: 1.4em;
     border-bottom: 1px solid #cbd5e0; padding-bottom: 3px; }
h3 { font-size: 11.5pt; color: #22577a; margin-top: 1.1em; }
p, li { font-size: 10pt; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.5pt;
       background: #f2f4f7; padding: 1px 4px; border-radius: 3px; }
pre { background: #f2f4f7; padding: 8px 10px; border-radius: 5px;
      font-size: 8.5pt; overflow-wrap: break-word; white-space: pre-wrap; }
blockquote { border-left: 4px solid #b8c4d0; margin: 1em 0; padding: 2px 12px;
             color: #33475b; background: #f7f9fb; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0;
        font-size: 7.5pt; table-layout: fixed; }
th, td { border: 1px solid #cbd5e0; padding: 4px 5px; text-align: left;
         vertical-align: top; overflow-wrap: break-word; word-break: break-word; }
th { background: #0b3d64; color: #fff; font-weight: 600; }
tr:nth-child(even) td { background: #f5f7fa; }
img { max-width: 100%; margin: 0.6em 0; }
a { color: #22577a; text-decoration: none; }
"""


def main() -> None:
    import markdown
    from weasyprint import CSS as WeasyCSS
    from weasyprint import HTML

    md_source = build_markdown()
    body_html = markdown.markdown(
        md_source,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
    )
    body_html = _resolve_image_paths(body_html)
    full_html = (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>{DOC_TITLE}</title></head><body>{body_html}</body></html>"
    )

    HTML(string=full_html, base_url=str(PROJECT_ROOT)).write_pdf(
        str(OUTPUT_PDF), stylesheets=[WeasyCSS(string=CSS)]
    )
    size_kb = OUTPUT_PDF.stat().st_size / 1024
    print(f"Wrote {OUTPUT_PDF} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
