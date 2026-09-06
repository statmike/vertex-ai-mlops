"""Can this caller actually stand the sandbox up? Ask before spending anything.

`make bootstrap` creates service accounts, custom roles, project IAM bindings,
datasets and Dataplex scans. A reader with only data access gets through API
enablement and corpus generation and *then* fails — after creating billable
objects, and with an error that names one API call rather than the capability
they are missing.

This asks first. Two read-only calls, no mutations, nothing created:

1. `projects.testIamPermissions` — the API returns the subset of a permission
   list that the caller holds, so one round trip covers every step.
2. A real impersonation exchange against each tier service account, when they
   already exist. Not a permission probe: `USE_TIER_SA` is the entire tier fence,
   and the thing worth knowing is whether a token actually mints.

**A permission the API does not recognize raises rather than reporting as
denied** (measured: `InvalidArgument`, naming the offending string). That is the
useful direction — a typo in the table below cannot masquerade as "your project
denied you" — but it means one bad entry fails the whole batch, so `check()`
reports an invalid name as a bug in *this file* rather than as a finding.

The table is derived from the operations the code performs, not from a
least-privilege run that has actually been stood up. Treat a clean preflight as
"nothing obviously blocks you", not as a proof.
"""

from dataclasses import dataclass, field

from google.api_core.exceptions import GoogleAPIError, InvalidArgument, NotFound
from google.cloud import resourcemanager_v3

import config
import identity


@dataclass(frozen=True)
class Step:
    """One `make` target, and the project-level permissions it needs to succeed."""

    target: str
    does: str
    permissions: tuple[str, ...] = field(default_factory=tuple)
    # Whether `make bootstrap` performs this step. Lacking a permission for a
    # *later* step is worth reporting and wrong to block on: you can provision
    # the sandbox perfectly well without `bigquery.jobs.listAll` and simply get
    # no cost columns. Blocking there would deny a reader over a report feature.
    in_bootstrap: bool = True


# Ordered as `make bootstrap` runs them, so the first failure is also the first
# thing to fix. Every string here is verified valid for a project resource by
# `tests/test_preflight.py` against the live API when credentials are present.
STEPS: tuple[Step, ...] = (
    Step("make apis", "enable 9-11 services", ("serviceusage.services.enable",)),
    Step(
        "make identities",
        "2 custom roles, 2 service accounts, project bindings",
        (
            "iam.roles.create",
            "iam.roles.update",
            "iam.serviceAccounts.create",
            "iam.serviceAccounts.setIamPolicy",
            "resourcemanager.projects.getIamPolicy",
            "resourcemanager.projects.setIamPolicy",
        ),
    ),
    Step(
        "make setup (BigQuery)",
        "2 datasets, 6 tables, per-tier dataset ACLs",
        (
            "bigquery.datasets.create",
            "bigquery.datasets.update",
            "bigquery.datasets.setIamPolicy",
            "bigquery.tables.create",
            "bigquery.tables.updateData",
            "bigquery.jobs.create",
        ),
    ),
    Step(
        "make setup (catalog)",
        "profile + quality scans, aspects, glossary, entry links",
        (
            "dataplex.datascans.create",
            "dataplex.datascans.run",
            "dataplex.entries.update",
            "dataplex.glossaries.create",
            "dataplex.glossaryTerms.create",
            "dataplex.entryLinks.create",
        ),
    ),
    Step(
        "make smoke / pilot / sweep",
        "Gemini calls",
        ("aiplatform.endpoints.predict",),
        in_bootstrap=False,
    ),
    Step(
        "make report",
        "INFORMATION_SCHEMA.JOBS cost attribution",
        ("bigquery.jobs.listAll",),
        in_bootstrap=False,
    ),
    Step(
        "make service-tokens",
        "read Cloud Monitoring",
        ("monitoring.timeSeries.list",),
        in_bootstrap=False,
    ),
)

ALL_PERMISSIONS: tuple[str, ...] = tuple(p for step in STEPS for p in step.permissions)


def held_permissions() -> set[str]:
    """The subset of `ALL_PERMISSIONS` this caller holds on the project.

    Raises `InvalidArgument` unchanged when a permission string is not valid for
    a project resource — that is a bug here, not a finding about the caller, and
    `check()` is where the two get told apart.
    """
    client = resourcemanager_v3.ProjectsClient()
    response = client.test_iam_permissions(
        resource=f"projects/{config.require_project()}", permissions=list(ALL_PERMISSIONS)
    )
    return set(response.permissions)


# States `impersonation()` reports that do not warrant a warning. "not created
# yet" is the expected answer before `make identities` has ever run.
BENIGN_TIER_STATES = ("ok", "not created yet")


def impersonation() -> dict[int, str]:
    """Whether a token really mints for each tier's service account.

    The outcome that matters is *the account exists and will not mint*, because
    `identity.credentials` falls back to plain ADC rather than raising — the
    sweep then runs with no tier fence, the control is gone, and the numbers look
    exactly as good as before.

    `google.auth` raises `RefreshError` for both "no such account" (404) and
    "you may not impersonate it" (403), so the HTTP code embedded in the message
    is the only thing separating them. When it cannot be read, this reports the
    warning rather than the benign state: a fence wrongly believed present is the
    expensive direction of the error.
    """
    if not config.USE_TIER_SA:
        return dict.fromkeys(config.TIERS, "USE_TIER_SA is off - no fence, tiers share your ADC")

    results = {}
    for tier in config.TIERS:
        try:
            identity.token(tier)
            results[tier] = "ok"
        except NotFound:
            results[tier] = "not created yet"
        except GoogleAPIError as e:
            results[tier] = f"cannot impersonate: {type(e).__name__}"
        except Exception as e:  # noqa: BLE001 - google.auth has its own hierarchy
            detail = str(e)
            if '"code": 404' in detail or "not found" in detail.lower():
                results[tier] = "not created yet"
            elif '"code": 403' in detail:
                results[tier] = "cannot impersonate: denied (403)"
            else:
                results[tier] = f"cannot impersonate: {type(e).__name__}"
    return results


def render(missing: dict[str, list[str]], tokens: dict[int, str]) -> str:
    """The report. Groups by `make` target, because that is the unit of blockage."""
    lines = [f"Preflight for project {config.require_project()}", ""]
    width = max(len(step.target) for step in STEPS)
    for step in STEPS:
        gaps = missing.get(step.target, [])
        mark = "FAIL" if gaps else " ok "
        lines.append(f"  [{mark}] {step.target:<{width}}  {step.does}")
        for permission in gaps:
            lines.append(f"           missing: {permission}")

    lines.append("")
    lines.append("  Tier service accounts (the isolation fence):")
    for tier, state in sorted(tokens.items()):
        mark = " ok " if state in BENIGN_TIER_STATES else "WARN"
        lines.append(f"    [{mark}] tier {tier}: {state}")
    if any(state not in BENIGN_TIER_STATES for state in tokens.values()):
        lines.append("           Impersonation failing does not fail the run: it falls back")
        lines.append("           to plain ADC, and the tier control is gone. Fix it, or read")
        lines.append("           the results as uncontrolled. `make verify-isolation` proves it.")

    lines.append("")
    blocked = [step.target for step in STEPS if step.in_bootstrap and step.target in missing]
    if blocked:
        lines.append("  Blocked before provisioning. Grant the roles behind the missing")
        lines.append("  permissions, or use a sandbox project you own — docs/reproducing.md")
        lines.append("  maps each one to a role.")
    elif missing:
        lines.append("  Provisioning is fine. The gaps above are in later steps, so you can")
        lines.append("  run the sandbox and will lose only what those steps produce.")
    else:
        lines.append("  Nothing blocks provisioning. Next: make bootstrap")
        lines.append("  (Derived from what the code calls, not from a least-privilege run.)")
    return "\n".join(lines)


def check() -> bool:
    """Run both checks and print the report.

    True when nothing blocks *provisioning*. A gap in a later step — cost
    attribution, say — is printed and does not fail: it costs the reader a report
    column, and denying them the whole sandbox over it would be wrong.
    """
    try:
        held = held_permissions()
    except InvalidArgument as e:
        print(f"Preflight is broken, not your project: {e}")
        print("A permission string in preflight.STEPS is not valid for a project resource.")
        return False
    except GoogleAPIError as e:
        print(f"Could not reach Resource Manager: {e}")
        print("Enable it with: gcloud services enable cloudresourcemanager.googleapis.com")
        return False

    missing = {
        step.target: [p for p in step.permissions if p not in held]
        for step in STEPS
        if any(p not in held for p in step.permissions)
    }
    print(render(missing, impersonation()))
    return not any(step.in_bootstrap and step.target in missing for step in STEPS)
