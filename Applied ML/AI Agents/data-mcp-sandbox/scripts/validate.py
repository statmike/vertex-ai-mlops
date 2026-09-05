"""Check that the files describing the experiment still agree with each other.

    uv run python scripts/validate.py [--skip-looker]

Offline and free — no project, no credentials, no BigQuery. Run it after every
edit while adapting the sandbox to your own tables; it catches the renames and
typos that would otherwise surface as silently-wrong scores at the end of a
sweep. `scripts/setup.py` runs it first and will not provision if it fails.

`--skip-looker` drops the corpus -> LookML checks, which only Path 2 and
`p4_looker_ca` depend on. Use it if you are running BigQuery-only arms.

Exit 0 when they agree, 1 otherwise.
"""

import argparse
import sys

import _bootstrap  # noqa: F401 - import for the sys.path side effect

import validate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-looker", action="store_true", help="Skip the corpus -> LookML checks"
    )
    args = parser.parse_args()

    print("Checking corpus / oracle / questions:")
    return 0 if validate.report(include_looker=not args.skip_looker) else 1


if __name__ == "__main__":
    sys.exit(main())
