"""The tier custom roles decide which bound tools can answer at all.

`scripts/bootstrap_identities.sh` and `src/mcp_clients.py` are joined by nothing
but IAM: the shell script says what a tier identity may do, the Python says what
tools it is handed, and neither file mentions the other. When the two disagree
the tool still appears in the agent's schema, still costs prompt tokens every
turn, and returns `PermissionDenied` — which reads as an outage rather than as a
design decision.

That gap is currently real and deliberate. These tests pin it so that closing it
is a choice someone makes, not something that drifts.
"""

import re
from pathlib import Path

import mcp_clients

ROOT = Path(__file__).resolve().parent.parent
IDENTITIES = ROOT / "scripts" / "bootstrap_identities.sh"

# Permission families a tier identity is not granted, and the tools that need
# them. Measured live, both tiers, before and after quality scans were
# provisioned: 93 calls in the published capture, 93 failures.
DENIED_FAMILIES = {
    "dataplex.datascans": ("search_dq_scans", "get_data_profile", "get_data_quality_results"),
    "dataplex.dataProducts": ("list_data_products", "get_data_product"),
}


def _granted_permissions() -> set[str]:
    """Every permission either custom role grants, read out of the shell script.

    The `*_PERMS` assignments are backslash-continued comma lists, so this
    unwraps them rather than reading line by line.
    """
    text = IDENTITIES.read_text().replace("\\\n", "")
    granted: set[str] = set()
    for match in re.finditer(r'^\w*PERMS="([^"]*)"', text, flags=re.MULTILINE):
        granted |= {p.strip() for p in match.group(1).split(",") if p.strip()}
    return granted


def test_the_custom_roles_parse_at_all():
    # If the shell script is reformatted into a shape this regex misses, every
    # other test here passes vacuously by finding nothing granted.
    granted = _granted_permissions()
    assert len(granted) > 10, granted
    assert "dataplex.entries.get" in granted


def test_scan_tools_are_bound_but_their_permissions_are_not_granted():
    """The documented gap, asserted from both sides so it cannot half-change.

    If you grant `dataplex.datascans.*` to make these tools work, three published
    claims go stale in the same moment and this test is the reminder:

    - `docs/paths.md`  — "eleven of fifteen Dataplex tools ... return nothing"
    - `docs/reproducing.md` — the Path 3 comparability table (93 calls, 93 errors)
    - `src/catalog_setup.py` — why quality scans are treatment

    Granting them to *tier 0* is the worse mistake: data scans carry no per-tier
    ACL, so the control arm would be handed the governed tier's scan results, the
    way `roles/dataplex.catalogViewer` would have handed it the glossary.
    """
    granted = _granted_permissions()
    bound = set(mcp_clients.TOOLBOX_DATAPLEX_TOOLS)

    for family, tools in DENIED_FAMILIES.items():
        assert bound & set(tools), f"{family} tools are no longer bound: update DENIED_FAMILIES"
        leaked = {p for p in granted if p.startswith(f"{family}.")}
        assert not leaked, (
            f"{sorted(leaked)} is now granted, so {sorted(bound & set(tools))} can answer. "
            "Re-check the doc claims listed in this test's docstring."
        )


def test_catalog_tools_have_the_permissions_they_need():
    # The other side of the same join: these four are the Dataplex tools that do
    # work, and they work because the search role grants entry and aspect reads.
    granted = _granted_permissions()
    for permission in ("dataplex.entries.get", "dataplex.entries.list", "dataplex.projects.search"):
        assert permission in granted, f"{permission} withdrawn — the catalog arms go dark"
