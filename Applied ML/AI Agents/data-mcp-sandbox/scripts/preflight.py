"""Check you can provision this sandbox before `make bootstrap` creates anything.

    uv run python scripts/preflight.py

Two read-only calls and no mutations: `projects.testIamPermissions` for every
permission the setup path needs, and a real token exchange against each tier
service account if they already exist.

The failure this exists to prevent: getting through API enablement and corpus
generation on a shared or org-managed project, then being denied at
`make identities` — after billable objects exist, and with an error naming one
API call rather than the capability you are missing.

Exit 0 when nothing blocks provisioning, 1 otherwise.
"""

import sys

import _bootstrap  # noqa: F401 - import for the sys.path side effect

import preflight


def main() -> int:
    return 0 if preflight.check() else 1


if __name__ == "__main__":
    sys.exit(main())
