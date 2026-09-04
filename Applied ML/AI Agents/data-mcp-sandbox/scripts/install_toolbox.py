"""Download the MCP Toolbox binary into `bin/`.

    uv run python scripts/install_toolbox.py

Toolbox is a Go binary, not a Python package, so `uv add` cannot install it. The
version is pinned in `src/toolbox_server.py` so a sweep is reproducible — a
newer Toolbox can change the tool inventory, which is one of the things being
measured.
"""

import platform
import subprocess
import sys
import urllib.request

import _bootstrap  # noqa: F401 - import for the sys.path side effect

import toolbox_server

# The project was renamed googleapis/genai-toolbox -> googleapis/mcp-toolbox, and
# the release bucket moved with it. The old `genai-toolbox` bucket still serves
# builds but stops at v1.1.0, so a version bump against it 404s.
BUCKET = "https://storage.googleapis.com/mcp-toolbox-for-databases"

ARCHITECTURES = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}


def download_url() -> str:
    """Resolve the release URL for this machine."""
    system = platform.system().lower()
    if system not in ("linux", "darwin"):
        raise RuntimeError(f"No Toolbox build for {system}; see the genai-toolbox releases.")
    machine = platform.machine().lower()
    if machine not in ARCHITECTURES:
        raise RuntimeError(f"Unsupported architecture {machine}")
    return f"{BUCKET}/v{toolbox_server.TOOLBOX_VERSION}/{system}/{ARCHITECTURES[machine]}/toolbox"


def installed_version() -> str | None:
    """The version of the binary already in `bin/`, or None if there isn't one.

    Checked rather than assumed: an existing file is not the *pinned* file, and
    silently keeping a stale binary after a version bump defeats the pin.
    """
    if not toolbox_server.BINARY.exists():
        return None
    result = subprocess.run(  # noqa: S603 - fixed binary, no shell, no user input
        [str(toolbox_server.BINARY), "--version"], capture_output=True, text=True, check=False
    )
    # Output looks like: `toolbox version 1.1.0+binary.linux.amd64.da6f5f8`
    words = result.stdout.split()
    return words[2].split("+")[0] if len(words) > 2 else "unknown"


def main() -> int:
    target = toolbox_server.BINARY
    current = installed_version()
    if current == toolbox_server.TOOLBOX_VERSION:
        print(f"Already installed: v{current} at {target}")
        return 0
    if current is not None:
        print(f"Replacing v{current} with pinned v{toolbox_server.TOOLBOX_VERSION}")

    url = download_url()
    print(f"Downloading {url}")
    target.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, target)  # noqa: S310 - fixed https bucket URL
    target.chmod(0o755)
    print(f"Installed Toolbox v{toolbox_server.TOOLBOX_VERSION} at {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
