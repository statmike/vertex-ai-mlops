"""Deploy the data-onboarding web UI to Cloud Run.

Builds the container via Cloud Build (source-based deploy) and deploys
to Cloud Run with the chat agent in agent_engine mode and voice running
locally inside the container.

Usage:
    uv run python deploy/deploy_ui.py                # deploy
    uv run python deploy/deploy_ui.py --update       # update existing
    uv run python deploy/deploy_ui.py --delete       # delete
    uv run python deploy/deploy_ui.py --info         # show deployment info
    uv run python deploy/deploy_ui.py --test         # health check deployed URL
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEPLOY_DIR = Path(__file__).resolve().parent
UI_DIR = PROJECT_ROOT / "ui"

dotenv.load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

SERVICE_NAME = "data-onboarding-ui"
DEPLOYMENT_FILE = DEPLOY_DIR / "ui" / "deployment.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deploy the data-onboarding web UI to Cloud Run.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--update", action="store_true", help="Update existing deployment")
    group.add_argument("--delete", action="store_true", help="Delete deployment")
    group.add_argument("--info", action="store_true", help="Show current deployment info")
    group.add_argument("--test", action="store_true", help="Health check the deployed URL")
    return parser.parse_args()


# --- Config ---


def _get_project() -> str:
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    if not project:
        print("Error: GOOGLE_CLOUD_PROJECT not set in .env")
        sys.exit(1)
    return project


def _get_region() -> str:
    return os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")


def _get_project_number(project: str) -> str:
    result = subprocess.run(
        ["gcloud", "projects", "describe", project, "--format=value(projectNumber)"],
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        print(f"Error getting project number: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def _get_env_vars() -> dict[str, str]:
    """Collect env vars to pass to the Cloud Run service."""
    project = _get_project()
    region = _get_region()

    env_vars = {
        "GOOGLE_CLOUD_PROJECT": project,
        "GOOGLE_CLOUD_LOCATION": region,
        "AGENT_MODE": "agent_engine",
    }

    optional = {
        "AGENT_ENGINE_RESOURCE_ID": os.getenv("AGENT_ENGINE_RESOURCE_ID", ""),
        "VOICE_MODEL": os.getenv("VOICE_MODEL", ""),
        "CHAT_SCOPE": os.getenv("CHAT_SCOPE", ""),
    }
    for key, val in optional.items():
        if val:
            env_vars[key] = val

    return env_vars


# --- Deployment metadata ---


def _load_deployment() -> dict:
    if DEPLOYMENT_FILE.exists():
        try:
            return json.loads(DEPLOYMENT_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_deployment(metadata: dict) -> None:
    DEPLOYMENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEPLOYMENT_FILE.write_text(json.dumps(metadata, indent=2) + "\n")


# --- Staging directory ---


def _assemble_staging() -> Path:
    """Create a temporary directory with only the files Cloud Build needs."""
    staging = Path(tempfile.mkdtemp(prefix="deploy-ui-"))

    shutil.copy2(UI_DIR / "Dockerfile", staging / "Dockerfile")
    shutil.copy2(UI_DIR / "pyproject.toml", staging / "pyproject.toml")
    shutil.copy2(UI_DIR / "uv.lock", staging / "uv.lock")

    shutil.copytree(UI_DIR / "backend", staging / "backend")
    shutil.copytree(UI_DIR / "frontend", staging / "frontend")
    shutil.copytree(
        PROJECT_ROOT / "agent_voice", staging / "agent_voice",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests"),
    )

    return staging


# --- gcloud helpers ---


def _run(cmd: list[str], check: bool = True, quiet: bool = False) -> subprocess.CompletedProcess:
    """Run a subprocess command, printing it first."""
    if not quiet:
        print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if check and result.returncode != 0:
        stderr = result.stderr.strip()
        if not quiet:
            print(f"  Error: {stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result


def _enable_apis(project: str) -> None:
    """Enable required GCP APIs (idempotent)."""
    print("\nEnabling required APIs...")
    _run([
        "gcloud", "services", "enable",
        "run.googleapis.com",
        "cloudbuild.googleapis.com",
        "artifactregistry.googleapis.com",
        "orgpolicy.googleapis.com",
        f"--project={project}",
        "--quiet",
    ])


def _grant_permissions(project: str, project_number: str) -> None:
    """Grant required IAM roles to the compute service account."""
    print("\nGranting IAM permissions...")
    sa = f"{project_number}-compute@developer.gserviceaccount.com"
    roles = [
        "roles/cloudbuild.builds.builder",
        "roles/aiplatform.user",
    ]
    for role in roles:
        _run([
            "gcloud", "projects", "add-iam-policy-binding", project,
            f"--member=serviceAccount:{sa}",
            f"--role={role}",
            "--condition=None",
            "--quiet",
        ], quiet=True)


def _override_org_policy(project: str, project_number: str) -> None:
    """Override org policy to allow unauthenticated Cloud Run invocations."""
    print("\nOverriding org policy for unauthenticated access...")
    policy = (
        f"name: projects/{project_number}/policies/run.managed.requireInvokerIam\n"
        "spec:\n"
        "  rules:\n"
        "  - enforce: false\n"
    )
    try:
        result = subprocess.run(
            ["gcloud", "org-policies", "set-policy", f"--project={project}", "/dev/stdin"],
            input=policy, capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0 and "not found" not in result.stderr.lower():
            print(f"  Warning: org policy override failed: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("  Warning: org policy override timed out (non-fatal)")


def _get_service_url(project: str, region: str) -> str:
    """Retrieve the URL of the deployed Cloud Run service."""
    result = _run([
        "gcloud", "run", "services", "describe", SERVICE_NAME,
        f"--project={project}",
        f"--region={region}",
        "--format=value(status.url)",
    ], quiet=True)
    return result.stdout.strip()


# --- Commands ---


def cmd_deploy() -> None:
    meta = _load_deployment()
    if meta.get("service_url"):
        print(f"\nExisting deployment found: {meta['service_url']}")
        print("Use --update to update or --delete to remove it.")
        return

    project = _get_project()
    region = _get_region()
    project_number = _get_project_number(project)
    env_vars = _get_env_vars()

    print(f"\n=== Deploying {SERVICE_NAME} to Cloud Run ===")
    print(f"  Project: {project}")
    print(f"  Region:  {region}")
    print(f"  Env vars: {list(env_vars.keys())}")

    _enable_apis(project)
    _grant_permissions(project, project_number)
    _override_org_policy(project, project_number)

    staging = _assemble_staging()
    try:
        print(f"\nBuilding and deploying from staging directory...")
        env_str = ",".join(f"{k}={v}" for k, v in env_vars.items())
        _run([
            "gcloud", "run", "deploy", SERVICE_NAME,
            f"--source={staging}",
            f"--project={project}",
            f"--region={region}",
            "--allow-unauthenticated",
            "--memory=1Gi",
            "--cpu=1",
            "--timeout=300",
            f"--set-env-vars={env_str}",
            "--quiet",
        ])
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    service_url = _get_service_url(project, region)
    new_meta = {
        "service_name": SERVICE_NAME,
        "service_url": service_url,
        "project": project,
        "region": region,
        "deployed_at": datetime.now().isoformat(),
    }
    _save_deployment(new_meta)

    print(f"\n=== Deployment Complete ===")
    print(f"  URL: {service_url}")
    print(f"  Metadata saved to {DEPLOYMENT_FILE.relative_to(PROJECT_ROOT)}")


def cmd_update() -> None:
    meta = _load_deployment()
    if not meta.get("service_url"):
        print("No active deployment to update. Run without --update to create one.")
        return

    project = _get_project()
    region = _get_region()
    env_vars = _get_env_vars()

    print(f"\n=== Updating {SERVICE_NAME} ===")

    staging = _assemble_staging()
    try:
        env_str = ",".join(f"{k}={v}" for k, v in env_vars.items())
        _run([
            "gcloud", "run", "deploy", SERVICE_NAME,
            f"--source={staging}",
            f"--project={project}",
            f"--region={region}",
            "--allow-unauthenticated",
            "--memory=1Gi",
            "--cpu=1",
            "--timeout=300",
            f"--set-env-vars={env_str}",
            "--quiet",
        ])
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    service_url = _get_service_url(project, region)
    meta["service_url"] = service_url
    meta["last_updated_at"] = datetime.now().isoformat()
    _save_deployment(meta)

    print(f"\n=== Update Complete ===")
    print(f"  URL: {service_url}")


def cmd_delete() -> None:
    meta = _load_deployment()
    if not meta.get("service_name"):
        print("No active deployment to delete.")
        return

    project = _get_project()
    region = _get_region()

    print(f"\nDeleting {SERVICE_NAME}...")
    _run([
        "gcloud", "run", "services", "delete", SERVICE_NAME,
        f"--project={project}",
        f"--region={region}",
        "--quiet",
    ])

    _save_deployment({})
    print("Deployment deleted.")


def cmd_info() -> None:
    meta = _load_deployment()
    if not meta or not meta.get("service_url"):
        print("No active deployment found.")
        return

    print(f"\nDeployment info for {SERVICE_NAME}:")
    for key, val in meta.items():
        print(f"  {key}: {val}")


def cmd_test() -> None:
    meta = _load_deployment()
    url = meta.get("service_url", "")
    if not url:
        print("No active deployment to test. Deploy first.")
        return

    print(f"\nHealth-checking {url} ...")
    try:
        import urllib.request
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            print(f"  Status: {status}")
            if 200 <= status < 400:
                print("  Health check passed.")
            else:
                print(f"  Unexpected status: {status}")
    except Exception as e:
        print(f"  Health check failed: {e}")


def main() -> None:
    args = _parse_args()

    if args.info:
        cmd_info()
    elif args.delete:
        cmd_delete()
    elif args.test:
        cmd_test()
    elif args.update:
        cmd_update()
    else:
        cmd_deploy()


if __name__ == "__main__":
    main()
