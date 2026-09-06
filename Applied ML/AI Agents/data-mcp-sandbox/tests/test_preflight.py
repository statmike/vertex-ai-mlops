"""Preflight has to be right about a denial before anyone trusts it.

A preflight that passes everything is worse than none: it converts "check first"
into "check, then hit the same wall anyway", and the reader has now created
billable objects on its say-so. So the failure rendering is pinned here, and the
permission strings are checked against the live API when credentials exist.
"""

import os

import pytest
from google.api_core.exceptions import GoogleAPIError, InvalidArgument

import config
import preflight


def test_every_bootstrap_step_declares_at_least_one_permission():
    # A step with an empty tuple can never fail, so it would render a permanent
    # green tick beside an operation nobody checked.
    for step in preflight.STEPS:
        assert step.permissions, f"{step.target} declares no permissions"


def test_permissions_look_like_permissions():
    # The API rejects a malformed string for the whole batch, so a typo here
    # takes out every check rather than one. Cheap shape guard, offline.
    for permission in preflight.ALL_PERMISSIONS:
        service, _, rest = permission.partition(".")
        assert service and rest.count(".") == 1, permission


def test_a_missing_permission_is_named_and_fails_the_step(monkeypatch):
    held = set(preflight.ALL_PERMISSIONS) - {"iam.roles.create"}
    monkeypatch.setattr(preflight, "held_permissions", lambda: held)
    monkeypatch.setattr(preflight, "impersonation", lambda: {0: "ok", 1: "ok"})

    assert preflight.check() is False


def test_a_gap_in_a_later_step_does_not_block_provisioning(monkeypatch):
    # `bigquery.jobs.listAll` buys the cost columns and nothing else. Denying a
    # reader the whole sandbox over a report feature they never asked for is a
    # false block, and it is the way an over-eager preflight does real damage.
    held = set(preflight.ALL_PERMISSIONS) - {"bigquery.jobs.listAll"}
    monkeypatch.setattr(preflight, "held_permissions", lambda: held)
    monkeypatch.setattr(preflight, "impersonation", lambda: {0: "ok", 1: "ok"})

    assert preflight.check() is True


def test_every_step_bootstrap_runs_is_marked_as_such():
    # The split is what makes the two cases above different, and it is a hand-kept
    # boolean: a new provisioning step defaulting to the wrong side would either
    # block on nothing or let a real denial through.
    bootstrap_steps = {step.target for step in preflight.STEPS if step.in_bootstrap}
    assert bootstrap_steps == {
        "make apis",
        "make identities",
        "make setup (BigQuery)",
        "make setup (catalog)",
    }


def test_render_separates_a_later_gap_from_a_blocking_one():
    text = preflight.render({"make report": ["bigquery.jobs.listAll"]}, {0: "ok", 1: "ok"})

    assert "[FAIL] make report" in text
    assert "Provisioning is fine" in text
    assert "Blocked before provisioning" not in text


def test_render_marks_only_the_blocked_step():
    missing = {"make identities": ["iam.roles.create"]}
    text = preflight.render(missing, {0: "ok", 1: "ok"})

    assert "[FAIL] make identities" in text
    assert "missing: iam.roles.create" in text
    assert "[ ok ] make apis" in text
    assert "Blocked before provisioning" in text


def test_an_uncreated_service_account_is_not_a_warning():
    # Before `make identities` the accounts do not exist. Flagging that would
    # train the reader to ignore the one line that matters.
    text = preflight.render({}, {0: "not created yet", 1: "not created yet"})

    assert "WARN" not in text
    assert "Nothing blocks provisioning" in text


def test_an_unimpersonatable_service_account_warns_without_blocking():
    # The dangerous case: it exists, it will not mint, and the sweep runs anyway
    # with no tier fence. Must warn loudly and must not be read as a hard block,
    # because provisioning itself is still possible.
    text = preflight.render({}, {0: "ok", 1: "cannot impersonate: denied (403)"})

    assert "WARN" in text
    assert "tier control is gone" in text
    assert "Nothing blocks provisioning" in text


def test_tier_sa_disabled_is_reported_rather_than_passing_silently(monkeypatch):
    # With USE_TIER_SA off, `identity.token` returns the caller's own ADC token
    # for every tier, so a naive check reports two cheerful "ok"s for a sandbox
    # that has no isolation at all.
    monkeypatch.setattr(config, "USE_TIER_SA", False)
    states = preflight.impersonation()

    assert set(states) == set(config.TIERS)
    assert all("no fence" in state for state in states.values())
    assert not any(state in preflight.BENIGN_TIER_STATES for state in states.values())


@pytest.mark.skipif(
    not os.getenv("GOOGLE_CLOUD_PROJECT"), reason="needs a project and ADC"
)
def test_every_permission_string_is_valid_for_a_project():
    """The one check that cannot be done offline, and the one that rots.

    `testIamPermissions` raises `InvalidArgument` naming the offending string
    rather than reporting it as denied — good, because a typo cannot masquerade
    as "your project said no" — but it fails the entire batch, so a single stale
    name disables preflight completely. Skipped without credentials.
    """
    try:
        preflight.held_permissions()
    except InvalidArgument as e:
        pytest.fail(f"preflight.STEPS names a permission a project does not have: {e}")
    except GoogleAPIError as e:
        pytest.skip(f"cannot reach Resource Manager: {e}")
