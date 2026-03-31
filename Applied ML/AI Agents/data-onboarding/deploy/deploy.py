"""Deploy data-onboarding agents to Vertex AI Agent Engine.

Uses the new client-based SDK (v1.112.0+) with source-file deployment.

Recommended: deploy only the chat agent. The orchestrator runs long batch
pipelines (20-60 min) best suited to local execution via `uv run adk web`.

Usage:
    uv run python deploy/deploy.py chat                      # deploy chat agent
    uv run python deploy/deploy.py chat --test               # test deployed agent
    uv run python deploy/deploy.py chat --update             # update existing
    uv run python deploy/deploy.py chat --delete             # delete
    uv run python deploy/deploy.py chat --info               # show deployment info
    uv run python deploy/deploy.py chat --skip-local-test

Auto-enabled on Agent Engine (no config needed):
    - Persistent session management (cloud-based)
    - Cloud Monitoring (metrics dashboard)
    - Cloud Logging (runtime event logs)

Enabled via env vars in deployment config:
    - Cloud Trace: GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
    - Prompt/response logging: OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
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

# Project root is one level up from deploy/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEPLOY_DIR = Path(__file__).resolve().parent

# Load .env
dotenv.load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# Ensure project root is on sys.path for agent imports
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Suppress experimental warnings from Vertex AI SDK
warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*")

# --- Agent configurations ---

AGENT_CONFIGS = {
    "orchestrator": {
        "entrypoint_module": "deploy.entrypoint_orchestrator",
        "entrypoint_object": "app",
        "display_name": "data-onboarding-orchestrator",
        "description": "Orchestrates data onboarding into BigQuery through a pipeline of specialized agents.",
        "deployment_file": DEPLOY_DIR / "orchestrator" / "deployment.json",
        "test_message": "What can you do?",
    },
    "chat": {
        "entrypoint_module": "deploy.entrypoint_chat",
        "entrypoint_object": "app",
        "display_name": "data-onboarding-chat",
        "description": "Conversational analytics over onboarded BigQuery data with catalog exploration.",
        "deployment_file": DEPLOY_DIR / "chat" / "deployment.json",
        "test_message": "What tables are available?",
    },
}

# ADK class methods spec — required for source-file deployment.
# These are the standard AdkApp methods that Agent Engine exposes as API endpoints.
# Generated from AdkApp introspection (see vertexai._genai._agent_engines_utils).
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
        "name": "streaming_agent_run_with_events",
        "api_mode": "async_stream",
        "parameters": {
            "type": "object",
            "required": ["request_json"],
            "properties": {"request_json": {"type": "string"}},
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

# Env vars that Agent Engine sets automatically — never pass these.
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
    parser = argparse.ArgumentParser(
        description="Deploy data-onboarding agents to Vertex AI Agent Engine.",
    )
    parser.add_argument(
        "agent",
        choices=list(AGENT_CONFIGS.keys()),
        help="Which agent to deploy: orchestrator or chat",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--update", action="store_true", help="Update existing deployment")
    group.add_argument("--delete", action="store_true", help="Delete deployment")
    group.add_argument("--info", action="store_true", help="Show current deployment info")
    group.add_argument("--test", action="store_true", help="Test deployed agent")
    parser.add_argument(
        "--skip-local-test", action="store_true", help="Skip local test before deploying"
    )
    return parser.parse_args()


# --- Deployment metadata ---

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


# --- Source packages ---

def _get_source_packages() -> list[str]:
    """List all agent_* directories plus deploy/ to include as source packages."""
    packages = []
    for item in sorted(PROJECT_ROOT.iterdir()):
        if item.is_dir() and item.name.startswith("agent_") and (item / "__init__.py").exists():
            packages.append(item.name)
    # Include deploy/ directory for entrypoint modules
    packages.append("deploy")
    return packages


def _write_requirements_file() -> Path:
    """Generate requirements.txt at project root from pyproject.toml dependencies.

    The file must be at the project root so it can be included in source_packages
    and referenced by Agent Engine at build time. Returns the Path object.
    """
    pyproject = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    deps = data.get("project", {}).get("dependencies", [])

    req_path = PROJECT_ROOT / "requirements.txt"
    req_path.write_text("\n".join(deps) + "\n")
    return req_path


# --- Env vars ---

def _get_env_vars() -> dict[str, str]:
    """Collect env vars to pass to the deployed agent.

    Reads all non-empty vars from .env, filters out reserved ones,
    and ensures telemetry is enabled.
    """
    env_vars = {}

    # Read from .env file directly to get the declared vars (not all of os.environ)
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        declared = dotenv.dotenv_values(env_path)
        for key, val in declared.items():
            if val and key not in RESERVED_ENV_VARS and not key.startswith("GOOGLE_CLOUD_AGENT_ENGINE"):
                env_vars[key] = val

    # Always enable telemetry
    env_vars["GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY"] = "true"
    env_vars["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"

    return env_vars


# --- Client helper ---

def _get_client():
    """Create a vertexai.Client for the configured project and location."""
    import vertexai

    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    if not project:
        print("Error: GOOGLE_CLOUD_PROJECT not set.")
        sys.exit(1)

    # vertexai.init still needed for some internal SDK paths
    vertexai.init(project=project, location=location)
    return vertexai.Client(project=project, location=location)


def _console_url(resource_name: str) -> str:
    """Build a Cloud Console URL from a resource name."""
    parts = resource_name.split("/")
    if len(parts) >= 6:
        project = parts[1]
        location = parts[3]
        engine_id = parts[5]
        return (
            f"https://console.cloud.google.com/vertex-ai/agents/"
            f"locations/{location}/reasoning-engines/{engine_id}"
            f"?project={project}"
        )
    return ""


# --- Local test ---

def _local_test(agent_name: str) -> bool:
    """Run a local smoke test with AdkApp. Returns True if successful."""
    from vertexai.agent_engines import AdkApp

    config = AGENT_CONFIGS[agent_name]

    # Import the root_agent dynamically
    import importlib
    mod = importlib.import_module(config["entrypoint_module"])
    root_agent = getattr(mod, config["entrypoint_object"])

    print(f"\nRunning local test for {agent_name}...")
    app = AdkApp(agent=root_agent, enable_tracing=True)

    async def _test():
        responses = []
        async for event in app.async_stream_query(
            user_id="deploy_test_user",
            message=config["test_message"],
        ):
            content = event.get("content")
            if content:
                responses.append(content)

        # Clean up test session
        sessions = await app.async_list_sessions(user_id="deploy_test_user")
        for session in sessions.sessions:
            await app.async_delete_session(
                user_id="deploy_test_user", session_id=session.id,
            )

        return len(responses) > 0

    try:
        success = asyncio.run(_test())
        if success:
            print("Local test passed.")
        else:
            print("Local test returned no responses.")
        return success
    except Exception as e:
        print(f"Local test failed: {e}")
        return False


# --- Commands ---

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
    """Test a deployed agent with a simple query."""
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
            user_id="deploy_test_user",
            session_id=session_id,
            message=config["test_message"],
        ):
            content = event.get("content")
            if content:
                print(f"    {content}")

        await remote_agent.async_delete_session(
            user_id="deploy_test_user", session_id=session_id,
        )

    asyncio.run(_test())
    print("\nTest complete.")


def cmd_update(agent_name: str) -> None:
    meta = _load_deployment(agent_name)
    resource_name = meta.get("resource_name", "")
    if not resource_name:
        print(f"No active deployment to update for {agent_name}. Run without --update to create one.")
        return

    client = _get_client()
    config = AGENT_CONFIGS[agent_name]
    source_packages = _get_source_packages()
    env_vars = _get_env_vars()

    print(f"\nUpdating {agent_name} deployment: {resource_name}")
    print(f"  Source packages: {source_packages}")

    # Generate requirements.txt at project root (included in source_packages)
    req_path = _write_requirements_file()
    all_packages = source_packages + [req_path.name]

    original_cwd = os.getcwd()
    os.chdir(str(PROJECT_ROOT))
    try:
        client.agent_engines.update(
            name=resource_name,
            config={
                "source_packages": all_packages,
                "entrypoint_module": config["entrypoint_module"],
                "entrypoint_object": config["entrypoint_object"],
                "requirements_file": req_path.name,
                "class_methods": ADK_CLASS_METHODS,
                "display_name": config["display_name"],
                "description": config["description"],
                "env_vars": env_vars,
            },
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

    # Check for existing deployment
    if resource_name:
        try:
            remote = client.agent_engines.get(name=resource_name)
            print(f"\nExisting {agent_name} deployment found: {resource_name}")
            print("Use --update to update or --delete to remove it.")
            return
        except Exception:
            print(f"Previous deployment {resource_name} not found, creating new one.")

    # Local test
    if not skip_local_test:
        if not _local_test(agent_name):
            print("\nLocal test failed. Use --skip-local-test to deploy anyway.")
            sys.exit(1)

    source_packages = _get_source_packages()
    env_vars = _get_env_vars()

    # Generate requirements.txt at project root (included in source_packages)
    req_path = _write_requirements_file()
    all_packages = source_packages + [req_path.name]

    print(f"\nDeploying {agent_name} to Agent Engine...")
    print(f"  Display name: {config['display_name']}")
    print(f"  Entry point: {config['entrypoint_module']}:{config['entrypoint_object']}")
    print(f"  Source packages: {all_packages}")
    print(f"  Env vars: {list(env_vars.keys())}")

    original_cwd = os.getcwd()
    os.chdir(str(PROJECT_ROOT))
    try:
        remote_agent = client.agent_engines.create(
            config={
                "source_packages": all_packages,
                "entrypoint_module": config["entrypoint_module"],
                "entrypoint_object": config["entrypoint_object"],
                "requirements_file": req_path.name,
                "class_methods": ADK_CLASS_METHODS,
                "display_name": config["display_name"],
                "description": config["description"],
                "env_vars": env_vars,
                "agent_framework": "google-adk",
            },
        )
    finally:
        os.chdir(original_cwd)
        req_path.unlink(missing_ok=True)

    # Save metadata
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
    print("  - Persistent session management (cloud-based)")
    print("  - Cloud Monitoring (metrics dashboard)")
    print("  - Cloud Logging (runtime event logs)")
    print("  - Cloud Trace (distributed tracing)")
    print("  - Prompt/response logging (GenAI content capture)")
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
