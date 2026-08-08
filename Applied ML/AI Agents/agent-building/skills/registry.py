"""Publish and manage skill bundles in the platform Skill Registry.

The **Skill Registry** (`client.skills`) is a platform-managed, semantically
searchable repository of *skill bundles* — a SKILL.md plus reference/asset files
that package a reusable capability. An agent (or a developer) can then discover
the right skill for a task by semantic query instead of hard-wiring it.

This is distinct from the A2A **AgentCard.skills** we set in
`agent_discovery/skills.py`: that field advertises *one agent's* capabilities on
its card; the Skill Registry is a *shared catalog* of packaged skills, uploaded
and retrieved through the platform API, versioned and searchable across agents.

    uv run python skills/registry.py publish     # upload every bundle under SKILLS_SOURCE_DIR
    uv run python skills/registry.py list         # list registered skills
    uv run python skills/registry.py retrieve "how do I forecast in BigQuery?"
    uv run python skills/registry.py delete <skill_id>

This demo reuses the sibling `agent-skills/` project's bundles (see
config.SKILLS_SOURCE_DIR) rather than authoring throwaway ones.

**Region matters.** Unlike loss clustering (global-only), the Skill Registry is
served only in a few regions (us-central1, europe-west4, us-east5); the `global`
endpoint returns INTERNAL. This script pins the client to
config.SKILL_REGISTRY_LOCATION (default us-central1). The built-in
`gcp-skill-registry` skill always appears in `list`/`retrieve` — that's expected.

Docs: https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/skill-registry
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _client():
    import vertexai

    from config import GOOGLE_CLOUD_PROJECT, SKILL_REGISTRY_LOCATION

    if not GOOGLE_CLOUD_PROJECT:
        print("Error: GOOGLE_CLOUD_PROJECT not set.")
        raise SystemExit(1)
    # The registry is regional; global returns INTERNAL (see module docstring).
    return vertexai.Client(project=GOOGLE_CLOUD_PROJECT, location=SKILL_REGISTRY_LOCATION)


def publish() -> None:
    """Upload every discovered bundle, creating or replacing each skill."""
    from config import SKILLS_SOURCE_DIR
    from skills.bundles import discover_bundles

    bundles = discover_bundles(SKILLS_SOURCE_DIR)
    if not bundles:
        print(f"No skill bundles (a dir with SKILL.md) found under {SKILLS_SOURCE_DIR}")
        raise SystemExit(1)

    client = _client()
    existing = {_short_id(s.name) for s in _safe_list(client)}

    print(f"Publishing {len(bundles)} skill bundle(s) from {SKILLS_SOURCE_DIR}:")
    for bundle in bundles:
        # Re-publishing is an update: delete-then-create keeps the content fresh
        # (create rejects a duplicate id), so a changed bundle actually re-uploads.
        if bundle.skill_id in existing:
            _delete_one(client, bundle.skill_id, quiet=True)
        try:
            skill = client.skills.create(
                display_name=bundle.name,
                description=bundle.description,
                config={
                    "local_path": str(bundle.path),
                    "skill_id": bundle.skill_id,
                    "wait_for_completion": True,
                },
            )
            print(f"  ✓ {bundle.skill_id}  ({skill.state})")
        except Exception as e:  # noqa: BLE001 — preview API; report and continue
            print(f"  ✗ {bundle.skill_id}: {e}")

    print("\nRegistered skills:")
    _print_list(client)


def list_skills() -> None:
    client = _client()
    print("Registered skills:")
    _print_list(client)


def retrieve(query: str) -> None:
    """Semantically match registered skills to a natural-language task."""
    if not query:
        print("Usage: skills/registry.py retrieve \"<query>\"")
        raise SystemExit(1)
    client = _client()
    print(f'Skills matching: "{query}"')
    try:
        resp = client.skills.retrieve(query=query, config={"top_k": 5})
    except Exception as e:  # noqa: BLE001 — preview API
        print(f"  retrieve failed: {e}")
        raise SystemExit(1) from e
    matches = getattr(resp, "retrieved_skills", None) or []
    if not matches:
        print("  (no matches)")
        return
    for rs in matches:
        print(f"  • {_short_id(rs.skill_name)}")
        if rs.description:
            print(f"      {rs.description[:100]}")


def delete(skill_id: str) -> None:
    if not skill_id:
        print("Usage: skills/registry.py delete <skill_id>")
        raise SystemExit(1)
    client = _client()
    _delete_one(client, skill_id)


# --- helpers ---------------------------------------------------------------


def _short_id(name: str | None) -> str:
    """Last path segment of a full skill resource name (the skill id)."""
    return (name or "").rsplit("/", 1)[-1]


def _safe_list(client) -> list:
    try:
        return list(client.skills.list())
    except Exception:  # noqa: BLE001 — treat an unreadable registry as empty
        return []


def _print_list(client) -> None:
    skills = _safe_list(client)
    if not skills:
        print("  (none)")
        return
    for s in skills:
        builtin = " [built-in]" if _short_id(s.name) == "gcp-skill-registry" else ""
        print(f"  • {_short_id(s.name)}  ({s.state}){builtin}")


def _delete_one(client, skill_id: str, quiet: bool = False) -> None:
    from config import GOOGLE_CLOUD_PROJECT, SKILL_REGISTRY_LOCATION

    name = (
        f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{SKILL_REGISTRY_LOCATION}"
        f"/skills/{skill_id}"
    )
    try:
        client.skills.delete(name=name)
        if not quiet:
            print(f"Deleted {skill_id}")
    except Exception as e:  # noqa: BLE001 — preview API
        if not quiet:
            print(f"Delete {skill_id} failed: {e}")


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    command = argv[0] if argv else "list"
    arg = argv[1] if len(argv) > 1 else ""

    if command == "publish":
        publish()
    elif command == "list":
        list_skills()
    elif command == "retrieve":
        retrieve(arg)
    elif command == "delete":
        delete(arg)
    else:
        print(__doc__)
        print(f"Unknown command: {command!r}. Use publish | list | retrieve | delete.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
