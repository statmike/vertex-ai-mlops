"""Turn a private capture into one that can be published and re-scored.

    uv run python scripts/export_capture.py --results results/raw/results.json
    uv run python scripts/export_capture.py --check results/capture-m6.json

Two jobs, and the file is worthless without either:

**Embed the goldens.** `build_results.py` normally resolves the oracle against
live BigQuery, because the corpus anchors its timestamps to build time and a
stored number rots. That is right for the operator and useless for a reader, who
has no corpus at all. Exporting freezes the goldens *as they were when the sweep
ran* into the header, so anyone can re-run the rubric, disagree with it, and
change it — which is the entire reason `traces.Cell` holds no scores (DESIGN §7).

**Scrub the project.** Tool results are stored nearly whole and are full of
`project.dataset.table`, service-account emails, and the Looker host. None of
that is secret, but none of it is anyone else's business either, and a published
file that names a live instance invites traffic to it.

Scrubbing is verified rather than assumed: `--check` re-reads the written file
and fails if any original identifier survived. A substitution that silently
missed one place would look exactly like a successful export.
"""

import argparse
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import _bootstrap  # noqa: F401 - import for the sys.path side effect
from google.cloud import bigquery

import battery
import config
import golden
import traces

# What the real identifiers become. Chosen to stay obviously fake and to remain
# valid-shaped, so a reader's JSON tooling and regexes still work on the result.
PLACEHOLDER_PROJECT = "example-project"
PLACEHOLDER_LOOKER = "looker.example.com"
PLACEHOLDER_NUMBER = "000000000000"

# Anything `json.loads` can hand back. Recursive, because a capture is tool
# results inside cells inside a list inside the document, and the scrubber has to
# reach all the way down.
Json = str | int | float | bool | None | dict[str, "Json"] | list["Json"]

# `.gz` by default: the uncompressed file is ~28 MB and the compressed one ~3 MB,
# and only one of those belongs in a repo. `traces.read_text` unpacks it, so
# `build_results.py --results results/capture.json.gz` needs no extra step.
DEFAULT_OUT = Path(config.PROJECT_ROOT) / "results" / "capture.json.gz"


def substitutions() -> dict[str, str]:
    """Every project-specific string to replace, longest first.

    Order matters. The project number must be replaced before anything that
    contains it, and the bare host before any URL built from it, or a partial
    match leaves a fragment of the original behind.
    """
    pairs: dict[str, str] = {}
    if config.PROJECT_ID:
        pairs[config.PROJECT_ID] = PLACEHOLDER_PROJECT
    if config.looker_configured():
        host = urlparse(config.LOOKER_BASE_URL).netloc or config.LOOKER_BASE_URL
        pairs[host.rstrip("/")] = PLACEHOLDER_LOOKER
    number = _project_number()
    if number:
        pairs[number] = PLACEHOLDER_NUMBER
    return dict(sorted(pairs.items(), key=lambda item: -len(item[0])))


def _project_number() -> str:
    """The numeric project id, which appears in resource names alongside the string one.

    Best effort: a reader exporting someone else's capture may not hold
    `resourcemanager.projects.get`, and a missing number is not worth failing an
    export over — `--check` is what proves the scrub, and it checks whatever this
    returned.
    """
    try:
        from google.cloud import resourcemanager_v3
    except ImportError:
        return ""
    try:
        client = resourcemanager_v3.ProjectsClient()
        project = client.get_project(name=f"projects/{config.PROJECT_ID}")
        return str(project.name).split("/")[-1]
    except Exception:  # noqa: BLE001 - an absent number degrades the scrub, never blocks it
        return ""


def _replace(text: str, pairs: dict[str, str]) -> str:
    """Every substitution applied to one string, longest identifier first."""
    for original, replacement in pairs.items():
        text = text.replace(original, replacement)
    return text


def scrub(payload: Json, pairs: dict[str, str]) -> Json:
    """Replace every identifier everywhere, including inside dict keys.

    Recurses over the parsed document rather than regexing the serialized text,
    because a raw text pass would also rewrite the identifier where it appears
    inside an escaped SQL string and produce invalid JSON offsets. Keys are
    rewritten too: `cell_key` values are safe, but tool arguments are not, and a
    dataset id can appear as a key in a schema dump.
    """
    if isinstance(payload, str):
        return _replace(payload, pairs)
    if isinstance(payload, dict):
        return {_replace(k, pairs): scrub(v, pairs) for k, v in payload.items()}
    if isinstance(payload, list):
        return [scrub(item, pairs) for item in payload]
    return payload


def freeze_goldens(cells: dict[str, traces.Cell]) -> dict[str, dict[str, dict[str, Any]]]:
    """Resolve the oracle against live BigQuery, once per tier in the capture."""
    client = bigquery.Client(project=config.require_project())
    frozen = {}
    for tier in sorted({cell.tier for cell in cells.values()}):
        resolved = golden.resolve_all(client, tier)
        frozen[str(tier)] = {key: asdict(value) for key, value in resolved.items()}
        print(f"    tier {tier}: froze {len(resolved)} golden values")
    return frozen


def check(path: Path, pairs: dict[str, str]) -> int:
    """Fail loudly if any original identifier survived into the exported file.

    Reads the file as text, not as JSON, so an identifier hiding in a key, a
    number, or an escape sequence is still caught.
    """
    text = traces.read_text(path)
    leaked = {
        original: len(re.findall(re.escape(original), text)) for original in pairs
    }
    leaked = {k: v for k, v in leaked.items() if v}
    if leaked:
        for original, count in leaked.items():
            print(f"  LEAK {original!r} appears {count} times")
        print(f"\n{path} is NOT safe to publish.")
        return 1

    payload = json.loads(text)
    goldens = payload.get("header", {}).get("goldens", {})
    if not goldens:
        print(f"  {path} carries no frozen goldens - a reader cannot re-score it.")
        return 1
    print(f"  clean: none of {len(pairs)} identifiers present; "
          f"goldens frozen for tier(s) {', '.join(sorted(goldens))}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--results", type=Path, default=battery.RESULTS_PATH,
                        help="Capture to export (default: results/raw/results.json).")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="Where to write the publishable capture.")
    parser.add_argument("--check", type=Path, default=None,
                        help="Verify an already-exported file instead of writing one.")
    args = parser.parse_args()

    pairs = substitutions()
    if not pairs:
        print("Nothing to scrub - GOOGLE_CLOUD_PROJECT is unset. Refusing to guess.")
        return 1

    if args.check:
        print(f"Checking {args.check}")
        return check(args.check, pairs)

    if not args.results.exists():
        print(f"No capture at {args.results}")
        return 1

    raw = json.loads(traces.read_text(args.results))
    cells = traces.load(args.results)
    print(f"Exporting {len(cells)} cells from {args.results}")

    print("  freezing goldens against live BigQuery:")
    raw.setdefault("header", {})["goldens"] = freeze_goldens(cells)

    print(f"  scrubbing {len(pairs)} identifiers")
    # The substitution map itself must not be scrubbed away, so it goes back in
    # afterwards — a reader needs to know a rewrite happened and what shape the
    # placeholders are, without being told the original values.
    exported = scrub(raw, pairs)
    exported["header"]["scrubbed"] = sorted(pairs.values())

    args.out.parent.mkdir(parents=True, exist_ok=True)
    traces.write_text(args.out, json.dumps(exported, indent=2))
    size = args.out.stat().st_size / 2**20
    print(f"  wrote {args.out} ({size:.1f} MiB)\n")

    print(f"Verifying {args.out}")
    return check(args.out, pairs)


if __name__ == "__main__":
    sys.exit(main())
