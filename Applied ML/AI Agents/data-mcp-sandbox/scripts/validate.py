"""Check that corpus.py, golden.py and questions.json still describe one experiment.

    uv run python scripts/validate.py

Offline and free — no project, no credentials, no BigQuery. Run it after every
edit while adapting the sandbox to your own tables; it catches the renames and
typos that would otherwise surface as silently-wrong scores at the end of a
sweep. `scripts/setup.py` runs it first and will not provision if it fails.

Exit 0 when the three agree, 1 otherwise.
"""

import sys

import _bootstrap  # noqa: F401 - import for the sys.path side effect

import validate


def main() -> int:
    print("Checking corpus / oracle / questions:")
    return 0 if validate.report() else 1


if __name__ == "__main__":
    sys.exit(main())
