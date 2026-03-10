"""Scale Vertex AI endpoint replicas and verify health.

Uses google-auth + requests (no extra dependencies) to call the Vertex AI
REST API directly. Designed for benchmark phases where we need fixed replica
counts with no autoscaling.

Usage:
  uv run python scripts/scale_endpoint.py --replicas 1
  uv run python scripts/scale_endpoint.py --replicas 14
  uv run python scripts/scale_endpoint.py --replicas 1 --machine-type g2-standard-8
  uv run python scripts/scale_endpoint.py --show
"""

import argparse
import json
import sys
import time

import google.auth
import google.auth.transport.requests
import requests


def load_env(path=".env"):
    """Parse KEY=VALUE lines from .env file."""
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def get_access_token():
    """Get an access token using application default credentials."""
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


def get_endpoint(project, region, endpoint_id, token):
    """Get endpoint details from the Vertex AI API."""
    url = (
        f"https://{region}-aiplatform.googleapis.com/v1/"
        f"projects/{project}/locations/{region}/endpoints/{endpoint_id}"
    )
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()


def mutate_deployed_model(project, region, endpoint_id, deployed_model_id,
                          min_replicas, max_replicas, token):
    """Update replica count via mutateDeployedModel API."""
    url = (
        f"https://{region}-aiplatform.googleapis.com/v1/"
        f"projects/{project}/locations/{region}/endpoints/{endpoint_id}"
        f":mutateDeployedModel"
    )

    body = {
        "deployedModel": {
            "id": deployed_model_id,
            "dedicatedResources": {
                "minReplicaCount": min_replicas,
                "maxReplicaCount": max_replicas,
            },
        },
        "updateMask": "dedicatedResources.minReplicaCount,"
                      "dedicatedResources.maxReplicaCount",
    }
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
    )
    if not resp.ok:
        print(f"  ERROR: {resp.status_code} — {resp.text}", flush=True)
    resp.raise_for_status()
    return resp.json()


def undeploy_model(project, region, endpoint_id, deployed_model_id, token):
    """Undeploy a model from the endpoint."""
    url = (
        f"https://{region}-aiplatform.googleapis.com/v1/"
        f"projects/{project}/locations/{region}/endpoints/{endpoint_id}"
        f":undeployModel"
    )
    body = {"deployedModelId": deployed_model_id}
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
    )
    if not resp.ok:
        print(f"  ERROR: {resp.status_code} — {resp.text}", flush=True)
    resp.raise_for_status()
    return resp.json()


def deploy_model(project, region, endpoint_id, model_name, display_name,
                 machine_spec, min_replicas, max_replicas, token):
    """Deploy a model to the endpoint with the given machine spec."""
    url = (
        f"https://{region}-aiplatform.googleapis.com/v1/"
        f"projects/{project}/locations/{region}/endpoints/{endpoint_id}"
        f":deployModel"
    )
    body = {
        "deployedModel": {
            "model": model_name,
            "displayName": display_name,
            "dedicatedResources": {
                "machineSpec": machine_spec,
                "minReplicaCount": min_replicas,
                "maxReplicaCount": max_replicas,
            },
        },
    }
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
    )
    if not resp.ok:
        print(f"  ERROR: {resp.status_code} — {resp.text}", flush=True)
    resp.raise_for_status()
    return resp.json()


def poll_operation(operation_name, token, timeout_minutes=30):
    """Poll a long-running operation until completion."""
    # operation_name format: projects/P/locations/R/endpoints/E/operations/O
    parts = operation_name.split("/")
    if len(parts) < 4 or parts[2] != "locations":
        raise ValueError(
            f"Unexpected operation_name format: {operation_name}. "
            f"Expected projects/P/locations/R/..."
        )
    region = parts[3]
    url = f"https://{region}-aiplatform.googleapis.com/v1/{operation_name}"

    deadline = time.time() + timeout_minutes * 60
    while time.time() < deadline:
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        resp.raise_for_status()
        op = resp.json()
        if op.get("done"):
            if "error" in op:
                raise RuntimeError(f"Operation failed: {op['error']}")
            return op
        time.sleep(15)
        elapsed = int(time.time() - (deadline - timeout_minutes * 60))
        print(f"  Waiting for scaling operation... ({elapsed}s)", flush=True)

    raise TimeoutError("Scaling operation timed out")


def health_check(project, region, endpoint_id, token, attempts=5, endpoint_dns=""):
    """Send test predictions to verify the endpoint is healthy."""
    host = endpoint_dns if endpoint_dns else f"{region}-aiplatform.googleapis.com"
    url = (
        f"https://{host}/v1/"
        f"projects/{project}/locations/{region}/endpoints/{endpoint_id}"
        f":predict"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {"instances": [{"text": "health check test transaction"}]}

    for i in range(attempts):
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=30)
            if resp.status_code == 200:
                print(f"  Health check passed (attempt {i + 1})", flush=True)
                return True
            print(
                f"  Health check attempt {i + 1}: status {resp.status_code}",
                flush=True,
            )
        except requests.RequestException as e:
            print(f"  Health check attempt {i + 1}: {e}", flush=True)
        time.sleep(10)

    print("  WARNING: Health check failed after all attempts", flush=True)
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Scale Vertex AI endpoint replicas for benchmark"
    )
    parser.add_argument(
        "--replicas",
        type=int,
        default=None,
        help="Number of replicas (sets both min and max, disabling autoscaling)",
    )
    parser.add_argument(
        "--machine-type",
        type=str,
        default=None,
        help="Change endpoint machine type (e.g., g2-standard-8). "
             "Keeps GPU accelerator unchanged.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Print current endpoint machine spec as JSON and exit (no mutation).",
    )
    parser.add_argument(
        "--env_file",
        default=".env",
        help="Path to .env file (default: .env)",
    )
    parser.add_argument(
        "--skip_health_check",
        action="store_true",
        help="Skip health check after scaling",
    )
    args = parser.parse_args()

    if not args.show and args.replicas is None and args.machine_type is None:
        parser.error("--replicas and/or --machine-type required (unless --show)")

    env = load_env(args.env_file)
    project = env["PROJECT_ID"]
    region = env["REGION"]
    endpoint_id = env["VERTEX_ENDPOINT_ID"]

    if not endpoint_id:
        print("ERROR: VERTEX_ENDPOINT_ID not set in .env", file=sys.stderr)
        sys.exit(1)

    token = get_access_token()

    # Get current endpoint state
    endpoint = get_endpoint(project, region, endpoint_id, token)
    deployed_models = endpoint.get("deployedModels", [])
    if not deployed_models:
        print("ERROR: No models deployed to endpoint", file=sys.stderr)
        sys.exit(1)

    dm = deployed_models[0]
    deployed_model_id = dm["id"]
    current_resources = dm.get("dedicatedResources", {})
    current_min = current_resources.get("minReplicaCount", 1)
    current_max = current_resources.get("maxReplicaCount", 1)
    machine_spec = current_resources.get("machineSpec", {})

    # --show: print current spec and exit
    if args.show:
        show_data = {
            "endpoint_id": endpoint_id,
            "deployed_model_id": deployed_model_id,
            "machine_spec": machine_spec,
            "min_replicas": current_min,
            "max_replicas": current_max,
        }
        print(json.dumps(show_data, indent=2))
        return

    target_replicas = args.replicas if args.replicas is not None else current_min

    print(f"Scaling endpoint {endpoint_id}...", flush=True)
    print(f"  Deployed model: {deployed_model_id}", flush=True)
    print(f"  Machine spec: {json.dumps(machine_spec)}", flush=True)
    print(f"  Current replicas: min={current_min}, max={current_max}", flush=True)
    if args.machine_type:
        print(f"  New machine type: {args.machine_type}", flush=True)
    print(f"  Target replicas: {target_replicas}", flush=True)

    # Check if any change is needed
    replicas_unchanged = (current_min == target_replicas and
                          current_max == target_replicas)
    machine_unchanged = (args.machine_type is None or
                         machine_spec.get("machineType") == args.machine_type)

    if replicas_unchanged and machine_unchanged:
        print(f"  Already at target state, skipping mutation.", flush=True)
    elif not machine_unchanged:
        # Machine type change requires undeploy + redeploy
        # (mutateDeployedModel does not support machineSpec changes)
        model_name = dm.get("model", "")
        display_name = dm.get("displayName", "benchmark-model")
        new_spec = dict(machine_spec)
        new_spec["machineType"] = args.machine_type

        print(f"  Machine type change: {machine_spec.get('machineType')} -> "
              f"{args.machine_type}", flush=True)
        print(f"  Undeploying model {deployed_model_id}...", flush=True)
        result = undeploy_model(
            project, region, endpoint_id, deployed_model_id, token,
        )
        op_name = result.get("name", "")
        if op_name:
            poll_operation(op_name, token, timeout_minutes=15)
        print(f"  Undeploy complete.", flush=True)

        # Redeploy with new machine spec
        print(f"  Redeploying with machine spec: {json.dumps(new_spec)}",
              flush=True)
        token = get_access_token()  # refresh after undeploy wait
        result = deploy_model(
            project, region, endpoint_id, model_name, display_name,
            machine_spec=new_spec,
            min_replicas=target_replicas,
            max_replicas=target_replicas,
            token=token,
        )
        op_name = result.get("name", "")
        if op_name:
            poll_operation(op_name, token, timeout_minutes=30)
        print(f"  Redeploy complete.", flush=True)

        # Verify new state
        token = get_access_token()
        endpoint = get_endpoint(project, region, endpoint_id, token)
        dm = endpoint["deployedModels"][0]
        new_resources = dm.get("dedicatedResources", {})
        final_spec = new_resources.get("machineSpec", {})
        print(
            f"  New replicas: min={new_resources.get('minReplicaCount')}, "
            f"max={new_resources.get('maxReplicaCount')}",
            flush=True,
        )
        print(f"  New machine spec: {json.dumps(final_spec)}", flush=True)
    else:
        # Replica count change only — use mutateDeployedModel
        result = mutate_deployed_model(
            project, region, endpoint_id, deployed_model_id,
            min_replicas=target_replicas,
            max_replicas=target_replicas,
            token=token,
        )

        # Wait for the operation to complete
        operation_name = result.get("name", "")
        if operation_name:
            print(f"  Operation: {operation_name}", flush=True)
            poll_operation(operation_name, token)
            print(f"  Scaling complete.", flush=True)
        else:
            print("  No operation returned (change may have been immediate).",
                  flush=True)

        # Verify new state
        token = get_access_token()  # refresh in case it expired
        endpoint = get_endpoint(project, region, endpoint_id, token)
        dm = endpoint["deployedModels"][0]
        new_resources = dm.get("dedicatedResources", {})
        new_spec = new_resources.get("machineSpec", {})
        print(
            f"  New replicas: min={new_resources.get('minReplicaCount')}, "
            f"max={new_resources.get('maxReplicaCount')}",
            flush=True,
        )
        print(f"  New machine spec: {json.dumps(new_spec)}", flush=True)

    # Health check
    if not args.skip_health_check:
        print("\nRunning health check...", flush=True)
        token = get_access_token()
        endpoint_dns = env.get("VERTEX_ENDPOINT_DNS", "")
        if health_check(project, region, endpoint_id, token, endpoint_dns=endpoint_dns):
            print("Endpoint is healthy and ready for benchmarking.", flush=True)
        else:
            print("WARNING: Endpoint may not be fully healthy.", flush=True)
            sys.exit(1)

    print("Done.", flush=True)


if __name__ == "__main__":
    main()
