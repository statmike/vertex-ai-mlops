"""Verify the Looker prerequisites for Path 2 and Path 4 (Looker + CA API).

This module **checks, it does not provision.** LookML lives in a Git-backed
Looker project, and the instance-hosted MCP endpoint requires an admin to
pre-register the agent as an OAuth client app — neither is creatable from a
client SDK. So setup verifies the human-performed steps and reports precisely
what is missing (DEV_NOTES: `IDEA.md` snippets are stale).

Two models are required, mirroring the governance tiers:

- `..._t0` — raw passthrough. Dimensions map 1:1 to columns, **no measures**.
  A Path 2 agent here sees the same bare schema as tier 0 everywhere else.
- `..._t1` — semantic. Adds `total_revenue` (net, refunds excluded) and
  `active_user_status` (the governed Active definition).

The two models are what makes Path 2 part of the tier experiment rather than a
single ungraded data point.

**Containment.** This sandbox runs on a shared Looker instance that hosts
unrelated production content, and it is confined to its own LookML project: it
must neither modify what is already there nor read any of it. That is not just
etiquette — `get_models` returns every model the caller can see, so a neighbour's
model is noise on the Path 2 agent's critical path, and a plausibly-named one
could change the answer.

Each tier is therefore checked **as its own non-admin sweep user**, and must see
exactly one model: its own. Admin credentials would make this test vacuous, since
an admin sees everything regardless of model set. Seeing the *other tier's* model
fails too — that would collapse the tier contrast the experiment measures, which
is a subtler corruption than a neighbour's model and easier to miss.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from looker_sdk.sdk.api40.methods import Looker40SDK
from looker_sdk.sdk.api40.models import LookmlModelExplore

import config
import looker_client

# Fields tier 1 must expose for the governed answers to be reachable through
# Looker at all. Absent these, Path 2 tier 1 is measuring nothing.
REQUIRED_T1_MEASURES = ("total_revenue",)
REQUIRED_T1_DIMENSIONS = ("active_user_status",)


@dataclass(frozen=True)
class LookerStatus:
    """What the checker found. `ok` gates Path 2 and `p4_looker_ca`."""

    ok: bool
    problems: list[str]
    models_found: list[str]


def _sdk(tier: int) -> Looker40SDK:
    """A client authenticated as the SWEEP user for one tier — never as admin.

    Checking with admin credentials would be checking the wrong thing: an admin
    sees every model on the instance, so the containment assertion below could
    never pass, and tier-1 fields would resolve even if the tier-0 role were
    misconfigured. The check has to run as the identity the sweep will use.
    """
    return looker_client.sdk(section=looker_client.tier_section(tier))


def _explore(sdk: Looker40SDK, model: str) -> LookmlModelExplore | None:
    try:
        return sdk.lookml_model_explore(model, config.LOOKER_EXPLORE)
    except Exception:  # noqa: BLE001 - any failure means "not usable", detail comes from caller
        return None


def _field_names(fields: Sequence[Any] | None) -> set[str]:
    """Short names from Looker's fully-qualified `view.field` naming."""
    return {f.name.split(".")[-1] for f in fields or []}


def _visible_models(sdk: Looker40SDK) -> set[str]:
    """Every LookML model these credentials can see — what `get_models` returns."""
    return {m.name for m in sdk.all_lookml_models() if m.name}


def _containment_problem(sdk: Looker40SDK, tier: int) -> str | None:
    """Flag any model this tier's sweep user can see beyond its own.

    The agent picks its model from whatever `get_models` returns, so visibility is
    capability. Each tier's role carries a model set holding exactly one model, so
    the correct answer here is "one" — its own. Anything else is either a
    neighbour's production model (a guest-rule violation and a decoy no other path
    faces) or the *other tier's* model, which would quietly collapse the tier
    contrast this whole experiment is built to measure.
    """
    ours = {config.looker_model(tier)}
    try:
        visible = _visible_models(sdk)
    except Exception as e:  # noqa: BLE001 - cannot prove containment, so do not claim it
        return f"tier {tier}: could not list visible models ({e}); containment unverified"
    foreign = sorted(visible - ours)
    if not foreign:
        return None
    shown = ", ".join(foreign[:5]) + (f", +{len(foreign) - 5} more" if len(foreign) > 5 else "")
    return (
        f"tier {tier} sweep user can see {len(foreign)} model(s) it should not: {shown}. "
        f"Its role must carry a model set containing only "
        f"'{config.looker_model(tier)}' — see docs/looker_setup.md."
    )


def check() -> LookerStatus:
    """Verify both LookML models resolve and tier 1 carries its semantic fields."""
    problems: list[str] = []
    found: list[str] = []

    if not config.LOOKER_BASE_URL:
        return LookerStatus(
            ok=False,
            problems=["LOOKER_BASE_URL is unset. Path 2 and p4_looker_ca cannot run."],
            models_found=[],
        )

    for tier in config.TIERS:
        model = config.looker_model(tier)
        section = looker_client.tier_section(tier)

        try:
            sdk = _sdk(tier)
        except Exception as e:  # noqa: BLE001 - surfaced to the operator verbatim
            problems.append(
                f"could not authenticate as the tier {tier} sweep user ([{section}] in "
                f"{looker_client.describe_source()}): {e}. "
                f"Run scripts/looker_provision.py --apply to create it."
            )
            continue

        contained = _containment_problem(sdk, tier)
        if contained:
            problems.append(contained)

        explore = _explore(sdk, model)
        if explore is None:
            problems.append(
                f"Model '{model}' has no explore '{config.LOOKER_EXPLORE}'. "
                f"Author it in the Looker project and deploy to production."
            )
            continue
        found.append(model)

        measures = _field_names(explore.fields.measures if explore.fields else [])
        dimensions = _field_names(explore.fields.dimensions if explore.fields else [])

        if tier == 0:
            # The control must stay bare — a stray measure here would leak
            # governance into the control and flatten the tier contrast.
            if measures:
                problems.append(
                    f"Control model '{model}' exposes measures {sorted(measures)}. "
                    f"Tier 0 must be a raw passthrough with no measures."
                )
        else:
            missing = [m for m in REQUIRED_T1_MEASURES if m not in measures]
            missing += [d for d in REQUIRED_T1_DIMENSIONS if d not in dimensions]
            if missing:
                problems.append(f"Model '{model}' is missing: {missing}")

    return LookerStatus(ok=not problems, problems=problems, models_found=found)


def report() -> bool:
    """Print the check result. Returns True when Looker is ready."""
    status = check()
    if status.ok:
        print(f"    Looker OK: {', '.join(status.models_found)}")
        return True
    for problem in status.problems:
        print(f"    Looker: {problem}")
    print("    Path 2 and p4_looker_ca will be skipped until these are resolved.")
    return False
