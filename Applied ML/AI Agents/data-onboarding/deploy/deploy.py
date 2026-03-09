"""Deploy the data-onboarding agent to Vertex AI Agent Engine.

Follows the concept-bq deployment pattern as a CLI script.

Usage:
    python deploy/deploy.py                  # deploy (or show existing)
    python deploy/deploy.py --update         # update existing deployment
    python deploy/deploy.py --delete         # delete deployment
    python deploy/deploy.py --info           # show current deployment info
    python deploy/deploy.py --skip-local-test  # skip local test before deploying

Auto-enabled on Agent Engine (no config needed):
    - Persistent session management (cloud-based sessions)
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
import warnings
from datetime import datetime
from pathlib import Path

import dotenv

# Project root is one level up from deploy/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEPLOYMENT_FILE = Path(__file__).resolve().parent / "deployment.json"

# Load .env
dotenv.load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# Ensure project root is on sys.path for agent imports
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Suppress experimental warnings from Vertex AI SDK
warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deploy data-onboarding agent to Vertex AI Agent Engine.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--update", action="store_true", help="Update existing deployment")
    group.add_argument("--delete", action="store_true", help="Delete deployment")
    group.add_argument("--info", action="store_true", help="Show current deployment info")
    parser.add_argument(
        "--skip-local-test", action="store_true", help="Skip local test before deploying"
    )
    return parser.parse_args()


def _load_deployment() -> dict:
    """Load deployment metadata from deployment.json."""
    if DEPLOYMENT_FILE.exists():
        try:
            return json.loads(DEPLOYMENT_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_deployment(metadata: dict) -> None:
    """Save deployment metadata to deployment.json."""
    DEPLOYMENT_FILE.write_text(json.dumps(metadata, indent=2) + "\n")


def _get_gcs_staging_path() -> str:
    """Build GCS staging path following monorepo convention."""
    from agent_orchestrator.config import GCS_STAGING_ROOT

    return f"{GCS_STAGING_ROOT}/agent_orchestrator/staging"


def _get_env_vars() -> dict[str, str]:
    """Env vars to set on the deployed agent for telemetry."""
    env_vars = {}
    # Pass through telemetry env vars if set locally
    for key in [
        "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY",
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT",
    ]:
        val = os.getenv(key)
        if val:
            env_vars[key] = val
    # Always enable telemetry on Agent Engine
    env_vars.setdefault("GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY", "true")
    env_vars.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "true")
    return env_vars


def _get_requirements() -> list[str]:
    """Read requirements from pyproject.toml dependencies."""
    import tomllib

    pyproject = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    return data.get("project", {}).get("dependencies", [])


def _get_extra_packages() -> list[str]:
    """List agent packages to include in deployment."""
    packages = []
    for item in sorted(PROJECT_ROOT.iterdir()):
        if item.is_dir() and item.name.startswith("agent_") and (item / "__init__.py").exists():
            packages.append(item.name)
    return packages


def _local_test(root_agent) -> bool:
    """Run a local test with AdkApp. Returns True if successful."""
    from vertexai import agent_engines

    print("\nRunning local test...")
    app = agent_engines.AdkApp(agent=root_agent, enable_tracing=True)

    async def _test():
        responses = []
        async for event in app.async_stream_query(
            user_id="deploy_test_user",
            message="What can you do?",
        ):
            content = event.get("content")
            if content:
                responses.append(content)

        # Clean up test session
        sessions = await app.async_list_sessions(user_id="deploy_test_user")
        for session in sessions.sessions:
            await app.async_delete_session(
                user_id="deploy_test_user", session_id=session.id
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


def _init_vertexai() -> None:
    """Initialize Vertex AI SDK."""
    import vertexai

    from agent_orchestrator.config import (
        GOOGLE_CLOUD_LOCATION,
        GOOGLE_CLOUD_PROJECT,
        GOOGLE_CLOUD_STORAGE_BUCKET,
    )

    vertexai.init(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        staging_bucket=GOOGLE_CLOUD_STORAGE_BUCKET,
    )


def cmd_info() -> None:
    """Show current deployment info."""
    meta = _load_deployment()
    if not meta or not meta.get("resource_id"):
        print("No active deployment found.")
        return

    print("\nCurrent deployment:")
    for key, val in meta.items():
        print(f"  {key}: {val}")

    # Build console URL
    resource_id = meta["resource_id"]
    parts = resource_id.split("/")
    if len(parts) >= 6:
        project = parts[1]
        location = parts[3]
        engine_id = parts[5]
        console_url = (
            f"https://console.cloud.google.com/vertex-ai/agents/"
            f"locations/{location}/reasoning-engines/{engine_id}"
            f"?project={project}"
        )
        print(f"\n  Console URL: {console_url}")


def cmd_delete() -> None:
    """Delete the deployed agent."""
    meta = _load_deployment()
    resource_id = meta.get("resource_id", "")
    if not resource_id:
        print("No active deployment to delete.")
        return

    _init_vertexai()
    from vertexai import agent_engines

    print(f"\nDeleting deployment: {resource_id}")
    agent_engines.delete(resource_name=resource_id, force=True)
    print("Deployment deleted.")

    _save_deployment({})
    print("Cleared deployment.json.")


def cmd_update() -> None:
    """Update existing deployment with latest code."""
    meta = _load_deployment()
    resource_id = meta.get("resource_id", "")
    if not resource_id:
        print("No active deployment to update. Run without --update to create one.")
        return

    _init_vertexai()
    from vertexai import agent_engines

    from agent_orchestrator.agent import root_agent

    requirements = _get_requirements()
    extra_packages = _get_extra_packages()

    print(f"\nUpdating deployment: {resource_id}")
    print(f"  Requirements: {len(requirements)} packages")
    print(f"  Extra packages: {extra_packages}")

    # Change to project root for relative paths
    original_cwd = os.getcwd()
    os.chdir(str(PROJECT_ROOT))
    try:
        agent_engines.update(
            resource_name=resource_id,
            agent_engine=root_agent,
            requirements=requirements,
            extra_packages=extra_packages,
        )
    finally:
        os.chdir(original_cwd)

    meta["last_updated_at"] = datetime.now().isoformat()
    _save_deployment(meta)
    print("Deployment updated.")


def cmd_deploy(skip_local_test: bool) -> None:
    """Deploy agent to Agent Engine (or show existing)."""
    meta = _load_deployment()
    resource_id = meta.get("resource_id", "")

    _init_vertexai()
    from vertexai import agent_engines

    # Check for existing deployment
    if resource_id:
        try:
            remote_app = agent_engines.get(resource_name=resource_id)
            print(f"\nExisting deployment found: {remote_app.resource_name}")
            print("Use --update to update or --delete to remove it.")
            return
        except Exception:
            print(f"Previous deployment {resource_id} not found, creating new one.")

    from agent_orchestrator.agent import root_agent

    # Local test
    if not skip_local_test:
        if not _local_test(root_agent):
            print("\nLocal test failed. Use --skip-local-test to deploy anyway.")
            sys.exit(1)

    requirements = _get_requirements()
    extra_packages = _get_extra_packages()
    gcs_path = _get_gcs_staging_path()
    env_vars = _get_env_vars()

    print(f"\nDeploying to Agent Engine...")
    print(f"  Agent: {root_agent.name}")
    print(f"  Requirements: {len(requirements)} packages")
    print(f"  Extra packages: {extra_packages}")
    print(f"  GCS staging: {gcs_path}")
    print(f"  Env vars: {list(env_vars.keys())}")

    # Change to project root for relative paths
    original_cwd = os.getcwd()
    os.chdir(str(PROJECT_ROOT))
    try:
        remote_app = agent_engines.create(
            agent_engine=root_agent,
            requirements=requirements,
            extra_packages=extra_packages,
            gcs_dir_name=gcs_path,
            display_name=root_agent.name,
            description=root_agent.description,
            env_vars=env_vars,
        )
    finally:
        os.chdir(original_cwd)

    # Save metadata
    new_meta = {
        "resource_id": remote_app.resource_name,
        "deployed_at": datetime.now().isoformat(),
        "display_name": root_agent.name,
        "description": root_agent.description,
    }
    _save_deployment(new_meta)

    # Print results
    print(f"\nDeployment created: {remote_app.resource_name}")
    parts = remote_app.resource_name.split("/")
    if len(parts) >= 6:
        project = parts[1]
        location = parts[3]
        engine_id = parts[5]
        console_url = (
            f"https://console.cloud.google.com/vertex-ai/agents/"
            f"locations/{location}/reasoning-engines/{engine_id}"
            f"?project={project}"
        )
        print(f"Console URL: {console_url}")

    print("\nAuto-enabled features:")
    print("  - Persistent session management (cloud-based)")
    print("  - Cloud Monitoring (metrics dashboard)")
    print("  - Cloud Logging (runtime event logs)")
    print("  - Cloud Trace (distributed tracing)")
    print("  - Prompt/response logging (GenAI content capture)")
    print("\nMetadata saved to deploy/deployment.json")


def main() -> None:
    args = _parse_args()

    if args.info:
        cmd_info()
    elif args.delete:
        cmd_delete()
    elif args.update:
        cmd_update()
    else:
        cmd_deploy(skip_local_test=args.skip_local_test)


if __name__ == "__main__":
    main()
