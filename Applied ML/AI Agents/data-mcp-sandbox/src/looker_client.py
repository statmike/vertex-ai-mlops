"""One place that builds a Looker SDK client, so credentials resolve identically.

TWO AUTH SYSTEMS, AND THEY ARE NOT THE SAME ONE
------------------------------------------------
It is easy — and was, here — to assume ADC covers everything because it covers
the interesting part. It does not:

* **Looker → BigQuery** (the data plane) uses ADC plus per-tier impersonation.
  No keys. That is the fence Path 2 is measured behind.
* **Us → Looker** (the control plane) uses API3 `client_id`/`client_secret`.
  Looker API 4.0 has no ADC or Google-OAuth equivalent; the "OAuth" in Looker's
  API docs is CORS for browser apps, not a substitute credential type. Requests
  run *as* the Looker user the key belongs to, which is exactly why the sweep's
  own keys are non-admin and model-set scoped.

So an API3 key pair is unavoidable. It lives in a project-local, gitignored
`looker.ini` — never a path into another project, so this repo has no credential
dependency outside itself.

THREE IDENTITIES, ONE FILE
--------------------------
The ini carries a section per identity, and which one you ask for is a
correctness question, not a convenience:

* `[Looker]` — admin. Used **only** by `scripts/looker_provision.py`.
* `[t0]`, `[t1]` — the sweep's non-admin, model-set-scoped users, written by that
  script at `--apply` time.

The sweep must never authenticate as the admin. An admin sees every model on the
instance regardless of model set, so admin credentials would silently hand Path 2
a neighbour's production model as a candidate — and would make the containment
assertion in `looker_check` unfailable-by-construction rather than meaningful.
"""

import configparser
import os
from typing import Any

import looker_sdk
from looker_sdk.sdk.api40.methods import Looker40SDK

import config

ADMIN_SECTION = "Looker"


def ini_path() -> str:
    """Absolute path to the credentials file; relative values resolve to the repo."""
    path = config.LOOKER_INI
    if not os.path.isabs(path):
        path = os.path.join(config.PROJECT_ROOT, path)
    return path


def tier_section(tier: int) -> str:
    """Ini section holding the sweep credentials for one tier."""
    return f"t{tier}"


def describe_source() -> str:
    """Where credentials are coming from — printed by scripts before they act."""
    path = ini_path()
    if os.path.isfile(path):
        return os.path.relpath(path, config.PROJECT_ROOT)
    if os.getenv("LOOKERSDK_CLIENT_ID"):
        return "LOOKERSDK_* environment variables"
    return f"{path} (missing) — copy looker.ini.template and fill it in"


def has_section(section: str) -> bool:
    """True when the ini exists and carries a usable client_id for this section."""
    path = ini_path()
    if not os.path.isfile(path):
        return False
    parser = configparser.ConfigParser()
    parser.read(path)
    return parser.has_section(section) and bool(parser.get(section, "client_id", fallback=""))


def sdk(section: str = ADMIN_SECTION) -> Looker40SDK:
    """An authenticated client for one ini section, or a raised, explanatory error."""
    path = ini_path()
    kwargs: dict[str, Any] = {}
    if os.path.isfile(path):
        kwargs["config_file"] = path
        kwargs["section"] = section
    elif section != ADMIN_SECTION:
        raise FileNotFoundError(
            f"No credentials file at {path}, so section '{section}' cannot be read. "
            f"Run scripts/looker_provision.py --apply to create the sweep users."
        )
    return looker_sdk.init40(**kwargs)


# One live session per section. The SDK renews an expired token on its own, so
# reusing the session keeps a 1,440-cell sweep from logging in once per request —
# Looker rate-limits `/login`, and a fresh session per cell would find it.
_sessions: dict[str, Looker40SDK] = {}


def auth_header(section: str) -> dict[str, str]:
    """A live `Authorization: Bearer` header for one ini section.

    This is what the **MCP** clients need, and it is a different credential from
    the GCP token every other server in this sandbox takes. Looker's `/mcp`
    endpoint authenticates Looker users, so a GCP access token is rejected —
    though only on `tools/call`. `tools/list` answers 200 with the full tool
    inventory to any bearer at all, which makes a misconfigured Path 2 look
    healthy in `make probe` right up until it runs (DEV_NOTES 2026-09-01).
    """
    if section not in _sessions:
        _sessions[section] = sdk(section)
    return dict(_sessions[section].auth.authenticate({}))


def credentials(section: str) -> tuple[str, str]:
    """The raw API3 pair for one ini section, for handing to a subprocess.

    Toolbox's looker source takes `clientId`/`clientSecret` rather than a token,
    so it cannot use `auth_header`. Returned as values and passed through the
    child's environment — never written into the rendered YAML, which lands on
    disk.
    """
    path = ini_path()
    if os.path.isfile(path):
        parser = configparser.ConfigParser()
        parser.read(path)
        if parser.has_section(section):
            client_id = parser.get(section, "client_id", fallback="")
            client_secret = parser.get(section, "client_secret", fallback="")
            if client_id and client_secret:
                return client_id, client_secret
    raise FileNotFoundError(
        f"No Looker API3 credentials for section '{section}' in {path}. "
        f"Run scripts/looker_provision.py --apply to create the sweep users."
    )


def write_section(section: str, base_url: str, client_id: str, client_secret: str) -> str:
    """Store freshly minted credentials in the ini, creating it if needed.

    Written rather than printed on purpose: a secret echoed to a terminal ends up
    in scrollback, CI logs, and any transcript of the session. This keeps it in
    one 0600 file that git already ignores.
    """
    path = ini_path()
    parser = configparser.ConfigParser()
    if os.path.isfile(path):
        parser.read(path)
    if not parser.has_section(section):
        parser.add_section(section)
    parser.set(section, "base_url", base_url)
    parser.set(section, "client_id", client_id)
    parser.set(section, "client_secret", client_secret)
    parser.set(section, "verify_ssl", "true")

    with open(path, "w") as handle:
        parser.write(handle)
    os.chmod(path, 0o600)
    return path
