"""Mint per-tier credentials by impersonation. No keys, ever.

Tier isolation is an IAM problem, not a prompting problem — `config.py` explains
why. This module is the mechanism: it turns "tier 0" into a set of credentials
that physically cannot read tier 1, and hands them to the two kinds of MCP
client the sandbox drives.

- **Managed MCP** takes a bearer token in a header, so `token(tier)` is enough.
- **Toolbox** never comes through here at all: it names the target account in
  its own rendered YAML (`impersonateServiceAccount`, on both the `bigquery` and
  `dataplex` sources) and performs the exchange itself. No credential file is
  written for it — see `toolbox_server._impersonation`.

Everything degrades to plain ADC when `config.USE_TIER_SA` is false.
"""

from typing import Any

import google.auth
import google.auth.impersonated_credentials
import google.auth.transport.requests

import config

CLOUD_PLATFORM = "https://www.googleapis.com/auth/cloud-platform"

# Impersonated credentials mint a short-lived token and refresh it themselves,
# so one object per tier is reused for the whole sweep.
_credentials: dict[int, Any] = {}


def credentials(tier: int) -> Any:  # noqa: ANN401 - google.auth has no shared base type
    """Credentials for one tier: impersonated when enabled, plain ADC when not."""
    if not config.USE_TIER_SA:
        source, _ = google.auth.default(scopes=[CLOUD_PLATFORM])
        return source

    if tier not in _credentials:
        source, _ = google.auth.default(scopes=[CLOUD_PLATFORM])
        _credentials[tier] = google.auth.impersonated_credentials.Credentials(  # type: ignore[no-untyped-call]
            source_credentials=source,
            target_principal=config.tier_service_account(tier),
            target_scopes=[CLOUD_PLATFORM],
        )
    return _credentials[tier]


def token(tier: int) -> str:
    """A fresh access token for one tier, refreshed on demand."""
    creds = credentials(tier)
    if not creds.valid:
        creds.refresh(google.auth.transport.requests.Request())
    return str(creds.token)


def describe(tier: int) -> str:
    """One line naming the identity a tier runs as, for provisioning output."""
    if not config.USE_TIER_SA:
        return "caller ADC (USE_TIER_SA off — isolation relies on one-tier-at-a-time)"
    return config.tier_service_account(tier)
