"""Authentication for the A2A hop to the Discovery agent.

Locally, Discovery is a plain uvicorn server on ``localhost`` and needs no auth.
Once Discovery is deployed to Agent Runtime, its A2A endpoint lives under
``*-aiplatform.googleapis.com`` and every call must carry a Google Cloud access
token that refreshes before it expires.

``authed_httpx_client_for(url)`` returns:
    - ``None`` for a local URL — ``RemoteA2aAgent`` then builds its own plain client.
    - an ``httpx.AsyncClient`` wired to a refreshing token for a Runtime URL.

Keeping this in one file means ``agent.py`` stays declarative: it just asks for
"the right client for this URL" and never touches credentials.
"""

from __future__ import annotations

import httpx

# Google Cloud endpoints that require an authenticated bearer token.
_GOOGLE_APIS_HOST = "googleapis.com"
_CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"


class _GoogleAuth(httpx.Auth):
    """httpx auth that injects a fresh Google Cloud access token per request.

    A static bearer token would expire mid-session; this refreshes on demand via
    Application Default Credentials, so long-lived agents keep working.
    """

    def __init__(self) -> None:
        import google.auth

        self._credentials, _ = google.auth.default(scopes=[_CLOUD_PLATFORM_SCOPE])

    def auth_flow(self, request: httpx.Request):
        import google.auth.transport.requests

        if not self._credentials.valid:
            self._credentials.refresh(google.auth.transport.requests.Request())
        request.headers["Authorization"] = f"Bearer {self._credentials.token}"
        yield request


def authed_httpx_client_for(url: str, timeout: float = 600.0) -> httpx.AsyncClient | None:
    """Return an authenticated client for a Runtime URL, or None for a local one."""
    if _GOOGLE_APIS_HOST not in url:
        return None
    return httpx.AsyncClient(auth=_GoogleAuth(), timeout=httpx.Timeout(timeout))
