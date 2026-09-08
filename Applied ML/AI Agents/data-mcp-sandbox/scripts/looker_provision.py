"""Provision this sandbox's Looker objects on a shared instance. Additive only.

    uv run python scripts/looker_provision.py                    # dry run, changes nothing
    uv run python scripts/looker_provision.py --apply             # create what is missing
    uv run python scripts/looker_provision.py --rotate-keys --apply   # reissue sweep API3 keys

Needs ADMIN API3 credentials in the `[Looker]` section of `looker.ini`. The sweep's
own credentials cannot do this and must not be able to — they are deliberately
non-admin, and this script is what creates them.

WHY THIS EXISTS
---------------
`docs/looker_setup.md` used to say none of this was scriptable. That was wrong for
everything except LookML file contents: the Looker admin API creates connections,
model configurations, model sets, permission sets, roles, users, API3 credentials,
and OAuth client apps. Only the LookML *files* have no write endpoint
(`all_project_files` and `project_file` are read-only), so those still arrive
through Git. Doing the rest by hand invited exactly the kind of quiet
misconfiguration — one stray model in a model set — that this experiment measures.

THE GUEST CONSTRAINT
--------------------
This instance hosts unrelated production content. The sandbox may add its own
objects; it may not touch anything already there. So this script:

  * only ever CREATES, never updates or deletes — an existing object is reported
    and left exactly as found, even if its settings look wrong. `--rotate-keys` is
    the one deliberate exception, and it deletes nothing but API3 credentials
    belonging to a user this script itself created (see `rotate_user_keys`);
  * refuses to act on any name outside the `config.RESOURCE_PREFIX` namespace,
    which is what stops a mistyped .env from pointing it at a neighbour's model;
  * is idempotent, so re-running after a partial failure is safe.

Generated API3 secrets go straight into the gitignored `looker.ini` (0600) and are
never echoed. A secret printed to a terminal survives in scrollback, CI logs, and
session transcripts; a secret written to one ignored file does not.
"""

import argparse
import sys
from dataclasses import dataclass, field

import _bootstrap  # noqa: F401 - import for the sys.path side effect
from looker_sdk.sdk.api40 import models as m
from looker_sdk.sdk.api40.methods import Looker40SDK

import config
import looker_client

# Looker's dialect id for BigQuery Standard SQL.
BIGQUERY_DIALECT = "bigquery_standard_sql"

# Enough to query the Explore and read field descriptions; nothing that can edit,
# and deliberately no `use_sql_runner` — an agent that can drop to raw SQL is not
# being measured on the semantic layer any more.
#
# The last two are what Path 4 needs. The Gemini Data Analytics CA API reads a
# Looker permission gap as `404 Looker resource not found` — byte-identical to the
# text you get for an explore that does not exist — so this was found by a variant
# matrix rather than by an error message (DEV_NOTES 2026-09-01). `gemini_in_looker`
# is provably necessary: `chat_with_explore` alone still 404s. Whether it is also
# *sufficient* alone is untested; both are kept because both are squarely within
# what Path 4 is meant to do, and neither widens the fence — cross-tier containment
# is the model set, not the permission set.
SWEEP_PERMISSIONS = [
    "access_data",
    "explore",
    "see_lookml",
    "chat_with_explore",
    "gemini_in_looker",
]

PERMISSION_SET = f"{config.RESOURCE_PREFIX}_sweep"
PROJECT_NAME = config.RESOURCE_PREFIX
OAUTH_APP_GUID = f"{config.RESOURCE_PREFIX}_agent"


@dataclass
class Report:
    """What happened, so a dry run and a real run print the same shape."""

    created: list[str] = field(default_factory=list)
    existing: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    manual: list[str] = field(default_factory=list)
    # (ini section, client_id) — the secret is never held here, only written to disk.
    secrets: list[tuple[str, str]] = field(default_factory=list)


def _guard(name: str) -> str:
    """Refuse any name outside our namespace — the last line against a bad .env."""
    if not name.startswith(config.RESOURCE_PREFIX):
        raise SystemExit(
            f"Refusing to provision '{name}': outside the '{config.RESOURCE_PREFIX}' "
            f"namespace. This sandbox is a guest on a shared instance and only "
            f"creates objects it owns. Check LOOKER_* names in .env."
        )
    return name


def ensure_connection(sdk: Looker40SDK, tier: int, apply: bool, report: Report) -> None:
    """One BigQuery connection per tier, ADC + impersonation of that tier's SA.

    This is the line that gives Path 2 the same fence as the other paths. Looker
    connects as the connection's identity, so a shared connection would leave the
    tier boundary to LookML alone; impersonating the tier SA turns a cross-tier
    read into the same IAM 403 the other paths get. Keyless, so CODE_STANDARDS §4
    holds — no service-account JSON is uploaded.
    """
    name = _guard(config.looker_connection(tier))
    sa = config.tier_service_account(tier)

    if any(c.name == name for c in sdk.all_connections()):
        report.existing.append(f"connection {name}")
        return
    if not apply:
        report.created.append(f"connection {name} (ADC, impersonates {sa})")
        return

    sdk.create_connection(
        m.WriteDBConnection(
            name=name,
            dialect_name=BIGQUERY_DIALECT,
            # For BigQuery, `host` is the UI's "Billing Project ID" and `database`
            # is the "Primary Dataset" — which must live inside that project.
            # Pointing `database` at the tier's own dataset means an unqualified
            # table name resolves inside the tier, not across it.
            host=config.require_project(),
            database=config.tier_dataset(tier),
            uses_application_default_credentials=True,
            impersonated_service_account=sa,
            # BigQuery can misreport a credential failure as a location error when
            # it has to auto-detect the dataset region. Pinning it keeps the real
            # error visible.
            jdbc_additional_params=f"Location={config.BQ_LOCATION}",
            # PDTs stay OFF, and not merely because we do not need them: a PDT is
            # materialised into a shared scratch dataset by the connection's own
            # identity, so it can expose rows to a reader who could not query the
            # source. That is precisely the fence this experiment measures.
        )
    )
    report.created.append(f"connection {name} (ADC, impersonates {sa})")


def ensure_project(sdk: Looker40SDK, apply: bool, report: Report) -> None:
    """The LookML project shell. Its *files* are not creatable from the API.

    Switch to the dev workspace BEFORE looking: a project with no deployed commit
    exists only in dev, so `all_projects()` in production reports it missing and
    the create then fails with "already exists". Checking in the same workspace we
    create in is what makes this idempotent.
    """
    name = _guard(PROJECT_NAME)
    if apply:
        sdk.update_session(m.WriteApiSession(workspace_id="dev"))

    if any(p.name == name for p in sdk.all_projects()):
        report.existing.append(f"project {name}")
    elif not apply:
        report.created.append(f"project {name}")
    else:
        sdk.create_project(m.WriteProject(name=name))
        report.created.append(f"project {name}")

    report.manual.append(
        f"Put the 9 LookML files in looker/ into project '{name}' and deploy to production. "
        f"There is no LookML file-write API — use the Looker IDE. See docs/looker_runbook.md."
    )


def ensure_git(sdk: Looker40SDK, apply: bool, report: Report) -> None:
    """Give the project a Looker-hosted bare Git repo, without which it is inert.

    `create_project` alone leaves a shell that the UI lists as *pending* and refuses
    to commit or deploy (`can.commit` and `can.deploy` are both false, and asking
    for its branches 404s). A human clicking through that state is offered "Add
    LookML", which opens the legacy generate-a-model flow and would write LookML
    from database tables over the hand-authored files this experiment depends on.
    Removing the manual step removes that trap.

    Bare rather than a remote on purpose: this LookML is generated by
    scripts/generate_lookml.py, so the repo of record is already this one and a
    GitHub remote would be a second copy to keep in sync. A remote would also need
    a deploy key installed before `update_project` would accept it, since Looker
    validates the connection whenever `git_remote_url` changes.
    """
    name = _guard(PROJECT_NAME)
    if sdk.project(name).uses_git:
        report.existing.append(f"git repo for {name}")
        return
    if not apply:
        report.created.append(f"bare git repo for {name}")
        return
    # Requires the dev workspace, which ensure_project has already selected.
    sdk.update_project(name, m.WriteProject(git_service_name="bare"))
    report.created.append(f"bare git repo for {name}")


def ensure_model(sdk: Looker40SDK, tier: int, apply: bool, report: Report) -> None:
    """Model configuration binding a model name to the project and its connection."""
    name = _guard(config.looker_model(tier))
    connection = config.looker_connection(tier)
    try:
        sdk.lookml_model(name)
        report.existing.append(f"model config {name}")
        return
    except Exception:  # noqa: BLE001 - absence is the normal case, not an error
        pass
    if not apply:
        report.created.append(f"model config {name} -> {connection}")
        return
    try:
        sdk.create_lookml_model(
            m.WriteLookmlModel(
                name=name,
                project_name=PROJECT_NAME,
                allowed_db_connection_names=[connection],
            )
        )
        report.created.append(f"model config {name} -> {connection}")
    except Exception as e:  # noqa: BLE001 - expected before the LookML files are deployed
        # Ordering, not a bug: a model configuration needs its .model.lkml file to
        # exist in production. Deliberately non-fatal so one run still creates the
        # roles, users, and credentials — then re-run after deploying.
        report.manual.append(
            f"model config {name} not created yet ({type(e).__name__}). Deploy "
            f"{name}.model.lkml to production, then re-run this script."
        )


def ensure_permission_set(sdk: Looker40SDK, apply: bool, report: Report) -> str | None:
    """One shared permission set; the tiers differ by model set, not by permission."""
    name = _guard(PERMISSION_SET)
    for ps in sdk.all_permission_sets():
        if ps.name == name:
            # Every other `ensure_*` here is create-only, on purpose: this is a
            # shared instance and re-running the provisioner must not rewrite state
            # someone is using. This one reconciles, because the set is ours by
            # prefix and a *stale* one fails in the worst possible way — Path 4
            # returns `404 Looker resource not found`, indistinguishable from a
            # typo'd explore name, so a missing permission reads as a broken config.
            missing = [p for p in SWEEP_PERMISSIONS if p not in (ps.permissions or [])]
            if missing:
                report.updated.append(f"permission set {name} += {missing}")
                if apply:
                    sdk.update_permission_set(
                        str(ps.id),
                        m.WritePermissionSet(name=name, permissions=SWEEP_PERMISSIONS),
                    )
            else:
                report.existing.append(f"permission set {name}")
            return ps.id
    report.created.append(f"permission set {name} {SWEEP_PERMISSIONS}")
    if not apply:
        return None
    created = sdk.create_permission_set(
        m.WritePermissionSet(name=name, permissions=SWEEP_PERMISSIONS)
    )
    return created.id


def ensure_model_set(sdk: Looker40SDK, tier: int, apply: bool, report: Report) -> str | None:
    """A model set holding EXACTLY one model — the containment check depends on it."""
    name = _guard(f"{config.looker_model(tier)}_only")
    for ms in sdk.all_model_sets():
        if ms.name == name:
            report.existing.append(f"model set {name}")
            return ms.id
    report.created.append(f"model set {name} -> [{config.looker_model(tier)}]")
    if not apply:
        return None
    created = sdk.create_model_set(
        m.WriteModelSet(name=name, models=[config.looker_model(tier)])
    )
    return created.id


def ensure_role(
    sdk: Looker40SDK,
    tier: int,
    permission_set_id: str | None,
    model_set_id: str | None,
    apply: bool,
    report: Report,
) -> str | None:
    name = _guard(f"{config.looker_model(tier)}_role")
    for role in sdk.all_roles():
        if role.name == name:
            report.existing.append(f"role {name}")
            return role.id
    report.created.append(f"role {name}")
    if not apply or not permission_set_id or not model_set_id:
        return None
    created = sdk.create_role(
        m.WriteRole(name=name, permission_set_id=permission_set_id, model_set_id=model_set_id)
    )
    return created.id


def ensure_user(
    sdk: Looker40SDK, tier: int, role_id: str | None, apply: bool, report: Report
) -> None:
    """A non-admin API3-only user per tier, with freshly issued credentials.

    Non-admin is load-bearing, not tidiness: an admin sees every model regardless
    of model set, so an admin sweep user would fail `looker_check`'s containment
    assertion by design — and would silently hand Path 2 a neighbour's model.
    """
    first, last = config.RESOURCE_PREFIX, f"t{tier}"
    label = f"{first} {last}"
    existing = sdk.search_users(first_name=first, last_name=last)
    if existing:
        report.existing.append(f"user {label} (id {existing[0].id})")
        return
    report.created.append(f"user {label} + API3 credentials")
    if not apply:
        return

    user = sdk.create_user(m.WriteUser(first_name=first, last_name=last, is_disabled=False))
    if user.id is None:
        raise SystemExit(f"Looker created user {label} without returning an id.")
    if role_id:
        sdk.set_user_roles(user.id, [role_id])
    creds = sdk.create_user_credentials_api3(user.id)

    # Straight to the gitignored ini, never to stdout — see looker_client.write_section.
    section = looker_client.tier_section(tier)
    looker_client.write_section(
        section=section,
        base_url=config.LOOKER_BASE_URL,
        client_id=creds.client_id or "",
        client_secret=creds.client_secret or "",
    )
    report.secrets.append((section, creds.client_id or ""))


def rotate_user_keys(sdk: Looker40SDK, tier: int, apply: bool, report: Report) -> None:
    """Reissue one tier's sweep API3 key pair, revoking whatever it had before.

    The only destructive operation in this script, so the blast radius is fenced
    twice. It looks the user up by `RESOURCE_PREFIX` + `t{tier}` rather than
    taking an id, and it deletes only `credentials_api3` records hanging off that
    user — never the user, never anything else on a shared instance. A neighbour's
    credentials are unreachable from here because their user never matches the
    name search.

    Rotation is delete-then-create because Looker has no "replace secret" call:
    `update_user_credentials_api3` toggles disabled state and does not mint a new
    secret. The old key stops working the moment it is deleted, so anything
    holding it — a running Toolbox subprocess, a live MCP session — breaks until
    `looker.ini` is re-read. Do not rotate mid-sweep.

    A secret is never returned or logged; `write_section` puts it straight into
    the 0600 ini. Only the non-secret `client_id` is reported.
    """
    first, last = config.RESOURCE_PREFIX, f"t{tier}"
    label = f"{first} {last}"
    found = sdk.search_users(first_name=first, last_name=last)
    if not found:
        report.manual.append(f"user {label} does not exist — nothing to rotate")
        return

    user = found[0]
    if user.id is None:
        report.manual.append(f"user {label} has no id — cannot rotate")
        return

    old = sdk.all_user_credentials_api3s(user.id)
    report.updated.append(
        f"user {label}: revoke {len(old)} API3 key(s), issue 1 new"
    )
    if not apply:
        return

    for credential in old:
        if credential.id is not None:
            sdk.delete_user_credentials_api3(user.id, credential.id)

    fresh = sdk.create_user_credentials_api3(user.id)
    section = looker_client.tier_section(tier)
    looker_client.write_section(
        section=section,
        base_url=config.LOOKER_BASE_URL,
        client_id=fresh.client_id or "",
        client_secret=fresh.client_secret or "",
    )
    report.secrets.append((section, fresh.client_id or ""))


def ensure_oauth_app(sdk: Looker40SDK, apply: bool, report: Report) -> None:
    """Pre-register the agent so the instance-hosted MCP endpoint will accept it."""
    guid = _guard(OAUTH_APP_GUID)
    try:
        sdk.oauth_client_app(guid)
        report.existing.append(f"oauth client app {guid}")
        return
    except Exception:  # noqa: BLE001 - absence is the normal case
        pass
    report.created.append(f"oauth client app {guid}")
    if apply:
        sdk.register_oauth_client_app(
            client_guid=guid,
            body=m.WriteOauthClientApp(
                redirect_uri="http://localhost:8080/oauth/callback",
                display_name="Data MCP Sandbox agent",
                description=(
                    "Path 2 / p4_looker_ca sweep client. "
                    "Created by scripts/looker_provision.py."
                ),
            ),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="actually create; default is a dry run"
    )
    parser.add_argument(
        "--rotate-keys",
        action="store_true",
        help="reissue the sweep users' API3 keys instead of provisioning; revokes the old ones",
    )
    args = parser.parse_args()

    if not config.looker_configured():
        print("LOOKER_BASE_URL is unset or still the placeholder. Nothing to do.")
        return 1

    print(f"Looker credentials: {looker_client.describe_source()}")
    try:
        sdk = looker_client.sdk()
    except Exception as e:  # noqa: BLE001 - surfaced verbatim; it is nearly always creds
        print(f"looker-sdk could not authenticate: {e}")
        print("Set LOOKER_INI to an existing looker-sdk ini, or export LOOKERSDK_*.")
        return 1

    try:
        who = sdk.me()
        print(f"Acting as: {who.display_name} (id {who.id})\n")
    except Exception as e:  # noqa: BLE001 - identity is worth knowing before mutating
        print(f"Authenticated but could not read own user: {e}\n")

    report = Report()
    if args.rotate_keys:
        # Rotation only. Running the provisioning pass as well would be harmless
        # but misleading: every object would report "already present" alongside a
        # credential revocation, and the one destructive line would be buried.
        for tier in config.LOOKER_TIERS:
            rotate_user_keys(sdk, tier, args.apply, report)
        _print_report(args.apply, report)
        return 0

    ensure_project(sdk, args.apply, report)
    ensure_git(sdk, args.apply, report)
    permission_set_id = ensure_permission_set(sdk, args.apply, report)
    # LOOKER_TIERS, not TIERS: the ladder's intermediate rungs have no Looker
    # model, and provisioning a user and role for one on a shared instance would
    # add content that nothing in this experiment ever reads.
    for tier in config.LOOKER_TIERS:
        ensure_connection(sdk, tier, args.apply, report)
        ensure_model(sdk, tier, args.apply, report)
        model_set_id = ensure_model_set(sdk, tier, args.apply, report)
        role_id = ensure_role(sdk, tier, permission_set_id, model_set_id, args.apply, report)
        ensure_user(sdk, tier, role_id, args.apply, report)
    ensure_oauth_app(sdk, args.apply, report)
    _print_report(args.apply, report)
    return 0


def _print_report(apply: bool, report: Report) -> None:
    """What happened, or what would have. Secrets are named, never shown."""
    verb = "Created" if apply else "Would create"
    print(f"\n{verb}:")
    for line in report.created or ["    (nothing)"]:
        print(f"    {line}")
    if report.updated:
        print(f"\n{'Updated' if apply else 'Would update'}:")
        for line in report.updated:
            print(f"    {line}")
    if report.existing:
        print("\nAlready present, left untouched:")
        for line in report.existing:
            print(f"    {line}")
    if report.manual:
        print("\nStill needs a human:")
        for line in report.manual:
            print(f"    {line}")

    if report.secrets:
        rel = looker_client.describe_source()
        print(f"\nAPI3 credentials written to {rel} (0600, gitignored):")
        for section, client_id in report.secrets:
            print(f"    [{section}]  client_id={client_id}  client_secret=<written, not shown>")

    if not apply:
        print("\nDry run — nothing changed. Re-run with --apply.")


if __name__ == "__main__":
    sys.exit(main())
