"""Deploy agent-building agents to Agent Runtime (formerly Agent Engine).

Two independently-deployable targets — this is the Scale pillar in action:

    concierge  — the root router + its in-process sub-agents + observability plugin
    discovery  — the standalone A2A agent (Claude on Vertex)

They deploy in two *different* modes, because they play two different roles:

    concierge  — SOURCE mode: an ``AdkApp`` shipped as source packages. Agent
                 Runtime serves the standard ADK class-methods (stream_query,
                 sessions, memory) as the app's API.
    discovery  — OBJECT mode: an ``A2aAgent`` template instance (see
                 entrypoint_discovery.py). It is cloudpickled and deployed as an
                 object; Agent Runtime reads its ``register_operations()`` and
                 serves the **A2A protocol natively** (message/task RPCs + an
                 authenticated agent card) instead of stream_query. This native
                 A2A surface is the whole reason the project runs on ADK 2.x —
                 the A2aAgent template needs A2A protocol v1.0 (a2a-sdk 1.x),
                 which ADK only allows at 2.5.0+.

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
        # Source mode: ship packages + entrypoint, Runtime serves ADK class-methods.
        "deploy_mode": "source",
        "entrypoint_module": "deploy.entrypoint_concierge",
        "entrypoint_object": "app",
        "display_name": "agent-building-concierge",
        "description": "Retail concierge that routes to catalog, analytics, and discovery specialists.",
        "deployment_file": DEPLOY_DIR / "concierge" / "deployment.json",
        "test_message": "What can you help me with?",
    },
    "discovery": {
        # Object mode: cloudpickle the A2aAgent, Runtime serves A2A natively.
        "deploy_mode": "object",
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


def _read_dependencies() -> list[str]:
    """Project runtime dependencies from pyproject.toml."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    return data.get("project", {}).get("dependencies", [])


def _write_requirements_file() -> Path:
    """Generate requirements.txt at the project root from pyproject dependencies.

    Must live at the root so it can be included in source_packages and referenced
    by Agent Runtime at build time (source mode). Returns the Path (caller unlinks).
    """
    req_path = PROJECT_ROOT / "requirements.txt"
    req_path.write_text("\n".join(_read_dependencies()) + "\n")
    return req_path


def _get_object_extra_packages() -> list[str]:
    """Local packages the cloudpickled object needs importable on the remote.

    Object mode (discovery) doesn't ship an entrypoint or class-methods spec —
    the A2aAgent is pickled by reference, so the modules it imports must travel
    as extra_packages. Discovery only needs its own package and the shared
    config.py (paths are relative to PROJECT_ROOT, which we chdir into).
    """
    return ["agent_discovery", "config.py"]


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
    """Run a local smoke test before deploying. Returns True on any response.

    Source mode (concierge) exercises the exact AdkApp that gets deployed.
    Object mode (discovery) can't be driven through AdkApp — the deployable is an
    A2aAgent, so we run its underlying ADK agent through an InMemoryRunner, which
    proves the agent + tools import and answer end-to-end.
    """
    config = AGENT_CONFIGS[agent_name]
    print(f"\nRunning local test for {agent_name}...")

    if config["deploy_mode"] == "object":
        result = _local_test_object(agent_name)
    else:
        result = _local_test_source(agent_name)

    if result:
        print("Local test passed.")
    return result


def _local_test_source(agent_name: str) -> bool:
    import importlib

    from vertexai.agent_engines import AdkApp

    config = AGENT_CONFIGS[agent_name]
    mod = importlib.import_module(config["entrypoint_module"])
    app: AdkApp = getattr(mod, config["entrypoint_object"])

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
            return True
        print("Local test returned no responses.")
        return False
    except Exception as e:
        print(f"Local test failed: {e}")
        return False


def _local_test_object(agent_name: str) -> bool:
    """Drive the object agent's underlying ADK agent via InMemoryRunner."""
    from google.adk.runners import InMemoryRunner
    from google.genai import types as genai_types

    from agent_discovery.agent import root_agent

    config = AGENT_CONFIGS[agent_name]
    runner = InMemoryRunner(agent=root_agent, app_name=root_agent.name)

    async def _test():
        session = await runner.session_service.create_session(
            app_name=root_agent.name, user_id="deploy_test_user"
        )
        message = genai_types.Content(
            role="user", parts=[genai_types.Part(text=config["test_message"])]
        )
        responses = []
        async for event in runner.run_async(
            user_id="deploy_test_user", session_id=session.id, new_message=message
        ):
            if event.content and event.content.parts:
                responses.append(event.content.parts)
        return len(responses) > 0

    try:
        if asyncio.run(_test()):
            return True
        print("Local test returned no responses.")
        return False
    except Exception as e:
        print(f"Local test failed: {e}")
        return False


# --- Deploy config assembly ----------------------------------------------

def _staging_bucket() -> str:
    """STAGING_BUCKET, normalized to a ``gs://`` URI (object-mode create requires it)."""
    bucket = os.getenv("STAGING_BUCKET", "").strip()
    if bucket and not bucket.startswith("gs://"):
        bucket = f"gs://{bucket}"
    return bucket


def _bake_discovery_card(env_vars: dict[str, str]) -> None:
    """Resolve the deployed discovery card and bake it into the concierge's env.

    The deployed concierge can't read the discovery card from the Runtime resource
    at startup — its service agent lacks ``aiplatform.reasoningEngines.get``, and a
    control-plane call on every cold start would be fragile. The card is static per
    deployment, so we resolve it here (with the deployer's admin creds) and pass it
    as ``DISCOVERY_A2A_CARD``; the deployed concierge just parses that env var. A
    no-op unless DISCOVERY_A2A_URL points at a deployed (googleapis.com) endpoint.
    """
    from agent_concierge.utils.a2a import DISCOVERY_A2A_CARD_ENV, deployed_agent_card_json

    base_url = os.getenv("DISCOVERY_A2A_URL", "").strip().rstrip("/")
    if "googleapis.com" not in base_url:
        return
    print("  Baking deployed discovery card into DISCOVERY_A2A_CARD...")
    env_vars[DISCOVERY_A2A_CARD_ENV] = deployed_agent_card_json(base_url)


def _source_deploy_config(agent_name: str, req_name: str, packages: list[str]) -> dict:
    """Config for SOURCE-mode deployment (concierge / AdkApp)."""
    config = AGENT_CONFIGS[agent_name]
    env_vars = _get_env_vars()
    if agent_name == "concierge":
        _bake_discovery_card(env_vars)
    cfg = {
        "source_packages": packages,
        "entrypoint_module": config["entrypoint_module"],
        "entrypoint_object": config["entrypoint_object"],
        "requirements_file": req_name,
        "class_methods": ADK_CLASS_METHODS,
        "display_name": config["display_name"],
        "description": config["description"],
        "env_vars": env_vars,
        "agent_framework": "google-adk",
    }
    staging_bucket = _staging_bucket()
    if staging_bucket:
        cfg["staging_bucket"] = staging_bucket
    return cfg


def _object_deploy_config(agent_name: str) -> dict:
    """Config for OBJECT-mode deployment (discovery / A2aAgent).

    No entrypoint/class-methods/source_packages: the object is cloudpickled and
    its own register_operations() defines the served API (the A2A extension).
    We pass the dependency list and the local packages it imports instead.
    """
    config = AGENT_CONFIGS[agent_name]
    cfg = {
        "requirements": _read_dependencies(),
        "extra_packages": _get_object_extra_packages(),
        "display_name": config["display_name"],
        "description": config["description"],
        "env_vars": _get_env_vars(),
    }
    staging_bucket = _staging_bucket()
    if staging_bucket:
        cfg["staging_bucket"] = staging_bucket
    return cfg


def _load_agent_object(agent_name: str):
    """Import and return the deployable object for OBJECT-mode agents."""
    import importlib

    config = AGENT_CONFIGS[agent_name]
    mod = importlib.import_module(config["entrypoint_module"])
    return getattr(mod, config["entrypoint_object"])


def _grant_a2a_invoke_permission(discovery_resource_name: str) -> None:
    """Let the concierge's Runtime service agent invoke discovery over A2A.

    Agent-to-agent A2A on Agent Runtime is a control-plane ``:query`` call, which
    needs ``aiplatform.reasoningEngines.query`` — a permission the stock
    ``roles/aiplatform.reasoningEngineServiceAgent`` (what every deployed agent
    runs as) does NOT include. Without this grant the concierge's A2A hop to
    discovery fails with 403 on ``.../a2a/message:send``.

    We grant it at the *resource* level (only on the discovery engine, not the
    whole project) via the reasoningEngines IAM policy — least privilege. The
    caller is the project's shared Runtime service agent, so this covers the
    concierge (and any future in-project A2A caller of discovery). Idempotent:
    re-adding an existing binding is a no-op.
    """
    import google.auth
    import google.auth.transport.requests
    import httpx

    # The resource name carries the project NUMBER (projects/{number}/...), which
    # is exactly what the service-agent email needs — no separate lookup required.
    parts = discovery_resource_name.split("/")
    number = parts[parts.index("projects") + 1]
    sa = f"service-{number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
    role = "roles/aiplatform.viewer"  # only predefined role with reasoningEngines.query
    location = _location_from_resource(discovery_resource_name)

    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    base = f"https://{location}-aiplatform.googleapis.com/v1/{discovery_resource_name}"
    headers = {"Authorization": f"Bearer {creds.token}"}

    get = httpx.post(f"{base}:getIamPolicy", headers=headers, json={}, timeout=60.0)
    get.raise_for_status()
    policy = get.json()
    bindings = policy.get("bindings", [])
    member = f"serviceAccount:{sa}"
    for b in bindings:
        if b.get("role") == role and member in b.get("members", []):
            print(f"  A2A invoke permission already granted to {sa}.")
            return
    for b in bindings:
        if b.get("role") == role:
            b.setdefault("members", []).append(member)
            break
    else:
        bindings.append({"role": role, "members": [member]})
    policy["bindings"] = bindings

    set_ = httpx.post(
        f"{base}:setIamPolicy", headers=headers, json={"policy": policy}, timeout=60.0
    )
    set_.raise_for_status()
    print(f"  Granted A2A invoke ({role}) to {sa} on discovery.")


def _location_from_resource(resource_name: str) -> str:
    parts = resource_name.split("/")
    return parts[parts.index("locations") + 1] if "locations" in parts else "us-central1"


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


def _a2a_url_for(resource_name: str) -> str:
    """Deployed A2A base URL for a reasoningEngine resource name.

    The region is parsed from the resource name (``.../locations/{region}/...``),
    not from GOOGLE_CLOUD_LOCATION — importing the agent packages rewrites that
    env var to the model-serving location (often ``global``), which is not where
    the Runtime resource lives.
    """
    parts = resource_name.split("/")
    location = parts[parts.index("locations") + 1] if "locations" in parts else "us-central1"
    return f"https://{location}-aiplatform.googleapis.com/v1beta1/{resource_name}/a2a"


def cmd_test(agent_name: str) -> None:
    meta = _load_deployment(agent_name)
    resource_name = meta.get("resource_name", "")
    if not resource_name:
        print(f"No active deployment to test for {agent_name}.")
        return
    config = AGENT_CONFIGS[agent_name]
    print(f"\nTesting deployed {agent_name}: {resource_name}")

    if config["deploy_mode"] == "object":
        _test_object(agent_name, resource_name)
    else:
        _test_source(agent_name, resource_name)
    print("\nTest complete.")


def _test_source(agent_name: str, resource_name: str) -> None:
    client = _get_client()
    config = AGENT_CONFIGS[agent_name]
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


def _test_object(agent_name: str, resource_name: str) -> None:
    """Test a deployed A2aAgent by making the real authenticated A2A hop.

    This exercises exactly what the concierge does in production: read the card
    embedded in the deployed resource (the Runtime serves no fetchable card),
    retarget it to the live endpoint, then run a turn over the A2A protocol.
    """
    from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
    from google.adk.runners import InMemoryRunner
    from google.genai import types as genai_types

    from agent_concierge.utils.a2a import _fetch_deployed_agent_card
    from agent_concierge.utils.auth import authed_httpx_client_for

    config = AGENT_CONFIGS[agent_name]
    base_url = _a2a_url_for(resource_name)
    card = _fetch_deployed_agent_card(base_url)
    print(f"  A2A endpoint: {base_url}")

    remote = RemoteA2aAgent(
        name=agent_name,
        description=config["description"],
        agent_card=card,
        httpx_client=authed_httpx_client_for(base_url),
        use_legacy=False,
    )
    runner = InMemoryRunner(agent=remote, app_name=agent_name)

    async def _test():
        session = await runner.session_service.create_session(
            app_name=agent_name, user_id="deploy_test_user"
        )
        message = genai_types.Content(
            role="user", parts=[genai_types.Part(text=config["test_message"])]
        )
        print(f"  Message: {config['test_message']}")
        print("  Response:")
        async for event in runner.run_async(
            user_id="deploy_test_user", session_id=session.id, new_message=message
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        print(f"    {part.text}")

    asyncio.run(_test())


def cmd_update(agent_name: str) -> None:
    meta = _load_deployment(agent_name)
    resource_name = meta.get("resource_name", "")
    if not resource_name:
        print(f"No active deployment to update for {agent_name}. Run without --update to create one.")
        return
    client = _get_client()
    mode = AGENT_CONFIGS[agent_name]["deploy_mode"]

    print(f"\nUpdating {agent_name} deployment: {resource_name}")

    original_cwd = os.getcwd()
    os.chdir(str(PROJECT_ROOT))
    try:
        if mode == "object":
            print(f"  Extra packages: {_get_object_extra_packages()}")
            client.agent_engines.update(
                name=resource_name,
                agent=_load_agent_object(agent_name),
                config=_object_deploy_config(agent_name),
            )
        else:
            source_packages = _get_source_packages()
            print(f"  Source packages: {source_packages}")
            req_path = _write_requirements_file()
            try:
                all_packages = source_packages + [req_path.name]
                client.agent_engines.update(
                    name=resource_name,
                    config=_source_deploy_config(agent_name, req_path.name, all_packages),
                )
            finally:
                req_path.unlink(missing_ok=True)
    finally:
        os.chdir(original_cwd)

    meta["last_updated_at"] = datetime.now().isoformat()
    _save_deployment(agent_name, meta)
    print("Deployment updated.")

    if agent_name == "discovery":
        _grant_a2a_invoke_permission(resource_name)


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

    mode = config["deploy_mode"]
    print(f"\nDeploying {agent_name} to Agent Runtime ({mode} mode)...")
    print(f"  Display name: {config['display_name']}")

    original_cwd = os.getcwd()
    os.chdir(str(PROJECT_ROOT))
    try:
        if mode == "object":
            print(f"  Extra packages: {_get_object_extra_packages()}")
            print("  API: A2A protocol (native), served from register_operations()")
            remote_agent = client.agent_engines.create(
                agent=_load_agent_object(agent_name),
                config=_object_deploy_config(agent_name),
            )
        else:
            source_packages = _get_source_packages()
            req_path = _write_requirements_file()
            try:
                all_packages = source_packages + [req_path.name]
                print(f"  Entry point: {config['entrypoint_module']}:{config['entrypoint_object']}")
                print(f"  Source packages: {all_packages}")
                remote_agent = client.agent_engines.create(
                    config=_source_deploy_config(agent_name, req_path.name, all_packages),
                )
            finally:
                req_path.unlink(missing_ok=True)
    finally:
        os.chdir(original_cwd)

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
        _grant_a2a_invoke_permission(new_meta["resource_name"])
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
