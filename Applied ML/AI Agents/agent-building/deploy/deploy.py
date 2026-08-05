"""Deploy agent-building agents to Agent Runtime (formerly Agent Engine).

Two independently-deployable targets — this is the Scale pillar in action:

    concierge  — the root router + its in-process sub-agents + observability plugin
    discovery  — the standalone A2A agent (Claude on Vertex)

Deploy each separately, then point the concierge's DISCOVERY_A2A_URL at the
deployed discovery endpoint to complete the cross-Runtime A2A hop.

Usage:
    uv run python deploy/deploy.py concierge                 # create
    uv run python deploy/deploy.py concierge --test          # query the deployed agent
    uv run python deploy/deploy.py concierge --update        # update existing
    uv run python deploy/deploy.py concierge --info          # show info + console URL
    uv run python deploy/deploy.py concierge --delete        # tear down
    uv run python deploy/deploy.py discovery                 # same commands for discovery
    uv run python deploy/deploy.py concierge --skip-local-test

Auto-enabled on Agent Runtime (no config needed):
    - Managed sessions (cloud-based, persistent)
    - Memory Bank (VertexAiMemoryBankService, same Runtime instance)
    - Cloud Monitoring / Logging
Enabled via env vars below:
    - Cloud Trace:               GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
    - Prompt/response capture:   OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tomllib
import warnings
from datetime import datetime
from pathlib import Path

import dotenv

# Project root is one level up from deploy/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEPLOY_DIR = Path(__file__).resolve().parent

dotenv.load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# Ensure the project root is importable (config.py + agent_* packages live there).
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*")

# --- Agent configurations -------------------------------------------------

AGENT_CONFIGS = {
    "concierge": {
        "entrypoint_module": "deploy.entrypoint_concierge",
        "entrypoint_object": "app",
        "display_name": "agent-building-concierge",
        "description": "Retail concierge that routes to catalog, analytics, and discovery specialists.",
        "deployment_file": DEPLOY_DIR / "concierge" / "deployment.json",
        "test_message": "What can you help me with?",
    },
    "discovery": {
        "entrypoint_module": "deploy.entrypoint_discovery",
        "entrypoint_object": "app",
        "display_name": "agent-building-discovery",
        "description": "Standalone A2A agent that searches theLook's data catalog.",
        "deployment_file": DEPLOY_DIR / "discovery" / "deployment.json",
        "test_message": "What tables do you have about orders?",
    },
}

# ADK class-methods spec — required for source-file deployment. These are the
# standard AdkApp methods Agent Runtime exposes as API endpoints (sessions +
# Memory Bank included).
ADK_CLASS_METHODS = [
    {
        "name": "async_stream_query",
        "api_mode": "async_stream",
        "parameters": {
            "type": "object",
            "required": ["message", "user_id"],
            "properties": {
                "message": {"anyOf": [{"type": "string"}, {"type": "object", "additionalProperties": True}]},
                "user_id": {"type": "string"},
                "session_id": {"type": "string", "nullable": True},
                "session_events": {"type": "array", "nullable": True},
                "run_config": {"type": "object", "nullable": True},
            },
        },
    },
    {
        "name": "stream_query",
        "api_mode": "stream",
        "parameters": {
            "type": "object",
            "required": ["message", "user_id"],
            "properties": {
                "message": {"anyOf": [{"type": "string"}, {"type": "object", "additionalProperties": True}]},
                "user_id": {"type": "string"},
                "session_id": {"type": "string", "nullable": True},
                "run_config": {"type": "object", "nullable": True},
            },
        },
    },
    {
        "name": "create_session",
        "api_mode": "",
        "parameters": {
            "type": "object",
            "required": ["user_id"],
            "properties": {
                "user_id": {"type": "string"},
                "session_id": {"type": "string", "nullable": True},
                "state": {"type": "object", "nullable": True},
            },
        },
    },
    {
        "name": "get_session",
        "api_mode": "",
        "parameters": {
            "type": "object",
            "required": ["user_id", "session_id"],
            "properties": {"user_id": {"type": "string"}, "session_id": {"type": "string"}},
        },
    },
    {
        "name": "list_sessions",
        "api_mode": "",
        "parameters": {
            "type": "object",
            "required": ["user_id"],
            "properties": {"user_id": {"type": "string"}},
        },
    },
    {
        "name": "delete_session",
        "api_mode": "",
        "parameters": {
            "type": "object",
            "required": ["user_id", "session_id"],
            "properties": {"user_id": {"type": "string"}, "session_id": {"type": "string"}},
        },
    },
    {
        "name": "async_create_session",
        "api_mode": "async",
        "parameters": {
            "type": "object",
            "required": ["user_id"],
            "properties": {
                "user_id": {"type": "string"},
                "session_id": {"type": "string", "nullable": True},
                "state": {"type": "object", "nullable": True},
            },
        },
    },
    {
        "name": "async_get_session",
        "api_mode": "async",
        "parameters": {
            "type": "object",
            "required": ["user_id", "session_id"],
            "properties": {"user_id": {"type": "string"}, "session_id": {"type": "string"}},
        },
    },
    {
        "name": "async_list_sessions",
        "api_mode": "async",
        "parameters": {
            "type": "object",
            "required": ["user_id"],
            "properties": {"user_id": {"type": "string"}},
        },
    },
    {
        "name": "async_delete_session",
        "api_mode": "async",
        "parameters": {
            "type": "object",
            "required": ["user_id", "session_id"],
            "properties": {"user_id": {"type": "string"}, "session_id": {"type": "string"}},
        },
    },
    {
        "name": "async_add_session_to_memory",
        "api_mode": "async",
        "parameters": {
            "type": "object",
            "required": ["session"],
            "properties": {"session": {"type": "object", "additionalProperties": True}},
        },
    },
    {
        "name": "async_search_memory",
        "api_mode": "async",
        "parameters": {
            "type": "object",
            "required": ["user_id", "query"],
            "properties": {"user_id": {"type": "string"}, "query": {"type": "string"}},
        },
    },
]

# Env vars Agent Runtime sets automatically — never pass these ourselves.
RESERVED_ENV_VARS = {
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_QUOTA_PROJECT",
    "GOOGLE_CLOUD_LOCATION",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "PORT",
    "K_SERVICE",
    "K_REVISION",
    "K_CONFIGURATION",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy agent-building agents to Agent Runtime.")
    parser.add_argument("agent", choices=list(AGENT_CONFIGS.keys()), help="Which agent to deploy")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--update", action="store_true", help="Update existing deployment")
    group.add_argument("--delete", action="store_true", help="Delete deployment")
    group.add_argument("--info", action="store_true", help="Show current deployment info")
    group.add_argument("--test", action="store_true", help="Test deployed agent")
    parser.add_argument("--skip-local-test", action="store_true", help="Skip local test before deploying")
    return parser.parse_args()


# --- Deployment metadata --------------------------------------------------

def _load_deployment(agent_name: str) -> dict:
    path = AGENT_CONFIGS[agent_name]["deployment_file"]
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_deployment(agent_name: str, metadata: dict) -> None:
    path = AGENT_CONFIGS[agent_name]["deployment_file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2) + "\n")


# --- Source packages ------------------------------------------------------

def _get_source_packages() -> list[str]:
    """Source to ship: every agent_* package, deploy/, and the root config.py.

    Unlike sibling projects that keep config inside each agent package, this
    project has a single root-level config.py that every agent imports — it MUST
    travel with the source or imports fail at build time.
    """
    packages = []
    for item in sorted(PROJECT_ROOT.iterdir()):
        if item.is_dir() and item.name.startswith("agent_") and (item / "__init__.py").exists():
            packages.append(item.name)
    packages.append("deploy")
    packages.append("config.py")  # root module shared by all agents
    return packages


def _write_requirements_file() -> Path:
    """Generate requirements.txt at the project root from pyproject dependencies.

    Must live at the root so it can be included in source_packages and referenced
    by Agent Runtime at build time. Returns the Path (caller unlinks it).
    """
    pyproject = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    deps = data.get("project", {}).get("dependencies", [])

    req_path = PROJECT_ROOT / "requirements.txt"
    req_path.write_text("\n".join(deps) + "\n")
    return req_path


# --- Env vars -------------------------------------------------------------

def _get_env_vars() -> dict[str, str]:
    """Env vars to pass to the deployed agent: declared .env vars + telemetry."""
    env_vars = {}
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        declared = dotenv.dotenv_values(env_path)
        for key, val in declared.items():
            if val and key not in RESERVED_ENV_VARS and not key.startswith("GOOGLE_CLOUD_AGENT_ENGINE"):
                env_vars[key] = val

    env_vars["GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"] = "true"
    env_vars["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"
    return env_vars


# --- Client helper --------------------------------------------------------

def _get_client():
    import vertexai

    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    if not project:
        print("Error: GOOGLE_CLOUD_PROJECT not set.")
        sys.exit(1)

    vertexai.init(project=project, location=location)
    return vertexai.Client(project=project, location=location)


def _console_url(resource_name: str) -> str:
    parts = resource_name.split("/")
    if len(parts) >= 6:
        project, location, engine_id = parts[1], parts[3], parts[5]
        return (
            f"https://console.cloud.google.com/vertex-ai/agents/"
            f"locations/{location}/reasoning-engines/{engine_id}?project={project}"
        )
    return ""


# --- Local test -----------------------------------------------------------

def _local_test(agent_name: str) -> bool:
    """Run a local smoke test with AdkApp. Returns True on any response."""
    import importlib

    from vertexai.agent_engines import AdkApp

    config = AGENT_CONFIGS[agent_name]
    mod = importlib.import_module(config["entrypoint_module"])
    # The entrypoint already builds an AdkApp; reuse it so the test exercises the
    # exact object that gets deployed (plugins, tracing, and all).
    app: AdkApp = getattr(mod, config["entrypoint_object"])

    print(f"\nRunning local test for {agent_name}...")

    async def _test():
        responses = []
        async for event in app.async_stream_query(
            user_id="deploy_test_user",
            message=config["test_message"],
        ):
            if event.get("content"):
                responses.append(event["content"])

        sessions = await app.async_list_sessions(user_id="deploy_test_user")
        for session in sessions.sessions:
            await app.async_delete_session(user_id="deploy_test_user", session_id=session.id)
        return len(responses) > 0

    try:
        if asyncio.run(_test()):
            print("Local test passed.")
            return True
        print("Local test returned no responses.")
        return False
    except Exception as e:
        print(f"Local test failed: {e}")
        return False


# --- Deploy config assembly ----------------------------------------------

def _deploy_config(agent_name: str, req_name: str, packages: list[str]) -> dict:
    config = AGENT_CONFIGS[agent_name]
    cfg = {
        "source_packages": packages,
        "entrypoint_module": config["entrypoint_module"],
        "entrypoint_object": config["entrypoint_object"],
        "requirements_file": req_name,
        "class_methods": ADK_CLASS_METHODS,
        "display_name": config["display_name"],
        "description": config["description"],
        "env_vars": _get_env_vars(),
        "agent_framework": "google-adk",
    }
    staging_bucket = os.getenv("STAGING_BUCKET", "")
    if staging_bucket:
        cfg["staging_bucket"] = staging_bucket
    return cfg


# --- Commands -------------------------------------------------------------

def cmd_info(agent_name: str) -> None:
    meta = _load_deployment(agent_name)
    if not meta or not meta.get("resource_name"):
        print(f"No active deployment found for {agent_name}.")
        return
    print(f"\nDeployment info for {agent_name}:")
    for key, val in meta.items():
        print(f"  {key}: {val}")
    url = _console_url(meta["resource_name"])
    if url:
        print(f"\n  Console URL: {url}")


def cmd_delete(agent_name: str) -> None:
    meta = _load_deployment(agent_name)
    resource_name = meta.get("resource_name", "")
    if not resource_name:
        print(f"No active deployment to delete for {agent_name}.")
        return
    client = _get_client()
    print(f"\nDeleting {agent_name} deployment: {resource_name}")
    client.agent_engines.delete(name=resource_name, force=True)
    print("Deployment deleted.")
    _save_deployment(agent_name, {})
    print(f"Cleared {AGENT_CONFIGS[agent_name]['deployment_file'].name}.")


def cmd_test(agent_name: str) -> None:
    meta = _load_deployment(agent_name)
    resource_name = meta.get("resource_name", "")
    if not resource_name:
        print(f"No active deployment to test for {agent_name}.")
        return
    client = _get_client()
    config = AGENT_CONFIGS[agent_name]

    print(f"\nTesting deployed {agent_name}: {resource_name}")
    remote_agent = client.agent_engines.get(name=resource_name)

    async def _test():
        session = await remote_agent.async_create_session(user_id="deploy_test_user")
        session_id = session["id"]
        print(f"  Session: {session_id}")
        print(f"  Message: {config['test_message']}")
        print("  Response:")
        async for event in remote_agent.async_stream_query(
            user_id="deploy_test_user", session_id=session_id, message=config["test_message"],
        ):
            if event.get("content"):
                print(f"    {event['content']}")
        await remote_agent.async_delete_session(user_id="deploy_test_user", session_id=session_id)

    asyncio.run(_test())
    print("\nTest complete.")


def cmd_update(agent_name: str) -> None:
    meta = _load_deployment(agent_name)
    resource_name = meta.get("resource_name", "")
    if not resource_name:
        print(f"No active deployment to update for {agent_name}. Run without --update to create one.")
        return
    client = _get_client()
    source_packages = _get_source_packages()

    print(f"\nUpdating {agent_name} deployment: {resource_name}")
    print(f"  Source packages: {source_packages}")

    req_path = _write_requirements_file()
    all_packages = source_packages + [req_path.name]

    original_cwd = os.getcwd()
    os.chdir(str(PROJECT_ROOT))
    try:
        client.agent_engines.update(
            name=resource_name,
            config=_deploy_config(agent_name, req_path.name, all_packages),
        )
    finally:
        os.chdir(original_cwd)
        req_path.unlink(missing_ok=True)

    meta["last_updated_at"] = datetime.now().isoformat()
    _save_deployment(agent_name, meta)
    print("Deployment updated.")


def cmd_deploy(agent_name: str, skip_local_test: bool) -> None:
    meta = _load_deployment(agent_name)
    resource_name = meta.get("resource_name", "")
    client = _get_client()
    config = AGENT_CONFIGS[agent_name]

    if resource_name:
        try:
            client.agent_engines.get(name=resource_name)
            print(f"\nExisting {agent_name} deployment found: {resource_name}")
            print("Use --update to update or --delete to remove it.")
            return
        except Exception:
            print(f"Previous deployment {resource_name} not found, creating new one.")

    if not skip_local_test and not _local_test(agent_name):
        print("\nLocal test failed. Use --skip-local-test to deploy anyway.")
        sys.exit(1)

    source_packages = _get_source_packages()
    req_path = _write_requirements_file()
    all_packages = source_packages + [req_path.name]

    print(f"\nDeploying {agent_name} to Agent Runtime...")
    print(f"  Display name: {config['display_name']}")
    print(f"  Entry point: {config['entrypoint_module']}:{config['entrypoint_object']}")
    print(f"  Source packages: {all_packages}")

    original_cwd = os.getcwd()
    os.chdir(str(PROJECT_ROOT))
    try:
        remote_agent = client.agent_engines.create(
            config=_deploy_config(agent_name, req_path.name, all_packages),
        )
    finally:
        os.chdir(original_cwd)
        req_path.unlink(missing_ok=True)

    new_meta = {
        "resource_name": remote_agent.api_resource.name,
        "deployed_at": datetime.now().isoformat(),
        "display_name": config["display_name"],
        "description": config["description"],
    }
    _save_deployment(agent_name, new_meta)

    print(f"\nDeployment created: {new_meta['resource_name']}")
    url = _console_url(new_meta["resource_name"])
    if url:
        print(f"Console URL: {url}")
    print("\nAuto-enabled features:")
    print("  - Managed sessions + Memory Bank")
    print("  - Cloud Monitoring / Logging / Trace")
    print("  - Prompt/response capture")
    if agent_name == "discovery":
        print("\nNext: set DISCOVERY_A2A_URL in .env to this agent's A2A endpoint,")
        print("      then deploy or update the concierge to complete the A2A hop.")
    dep_file = AGENT_CONFIGS[agent_name]["deployment_file"]
    print(f"\nMetadata saved to {dep_file.relative_to(PROJECT_ROOT)}")


def main() -> None:
    args = _parse_args()
    if args.info:
        cmd_info(args.agent)
    elif args.delete:
        cmd_delete(args.agent)
    elif args.test:
        cmd_test(args.agent)
    elif args.update:
        cmd_update(args.agent)
    else:
        cmd_deploy(args.agent, skip_local_test=args.skip_local_test)


if __name__ == "__main__":
    main()
