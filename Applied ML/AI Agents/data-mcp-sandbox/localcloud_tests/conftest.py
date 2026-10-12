"""Opt-in native BigQuery fixtures for the supplied LocalCloud runtime."""

import json
import os
from collections.abc import Iterator
from typing import Any
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest
from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import NotFound
from google.auth.credentials import AnonymousCredentials
from google.cloud import bigquery

import bq_setup
import config
import corpus


@pytest.fixture(scope="module")
def bq_client() -> Iterator[bigquery.Client]:
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    gateway = (
        os.environ.get("LOCALCLOUD_GATEWAY_URL")
        or os.environ["CLOUD_RESOURCE_MANAGER_EMULATOR_HOST"]
    ).rstrip("/")

    def request(path: str) -> dict[str, Any]:
        req = Request(
            gateway + path,
            headers={
                "X-LocalCloud-Project": project,
                "X-LocalCloud-User": os.environ.get("LOCALCLOUD_USER", "local-developer"),
            },
        )
        with urlopen(req, timeout=30) as response:
            return json.load(response)

    services = request("/services")["services"]
    service = next(item for item in services if item["id"] == "bigquery")
    assert service["enabled"] and service["callable"]
    assert request("/readiness?services=bigquery")["ready"] is True
    assert request("/coverage/bigquery")["coverage_status"] == "supported"
    assert request("/identity/status")["iamMode"] == "open"
    endpoints = request("/env?format=json")
    endpoint = os.environ.get("BIGQUERY_EMULATOR_HOST") or endpoints["BIGQUERY_EMULATOR_HOST"]
    parsed = urlparse(endpoint)
    assert parsed.scheme == "http", "This fixture requires an advertised plaintext REST listener"
    assert parsed.hostname and not parsed.hostname.endswith("googleapis.com")

    query = urlencode({"project": project})

    def request_count() -> int:
        usage = request("/usage?" + query)
        return next(item["request_count"] for item in usage["services"] if item["id"] == "bigquery")

    before = request_count()
    client = bigquery.Client(
        project=project,
        client_options=ClientOptions(api_endpoint=endpoint),
        credentials=AnonymousCredentials(),
    )
    assert endpoint == client._connection.API_BASE_URL
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(config, "PROJECT_ID", project)
        patch.setattr(config, "RESOURCE_PREFIX", "localcloud_" + uuid4().hex[:12])
        patch.setattr(config, "USE_TIER_SA", False)
        datasets = [config.dataset_ref(tier) for tier in config.TIERS]
        try:
            bq_setup.create_datasets(client)
            rows = {
                corpus.USERS.name: [
                    {"user_id": "u1", "is_active": True, "region": "North"},
                    {"user_id": "u2", "is_active": True, "region": "South"},
                    {"user_id": "u3", "is_active": False, "region": "North"},
                ],
                corpus.TRANSACTIONS.name: [
                    {
                        "txn_id": "t1",
                        "user_id": "u1",
                        "txn_amt_x2": 10.0,
                        "revenue_amount": 15.0,
                        "status_flg": False,
                    },
                    {
                        "txn_id": "t2",
                        "user_id": "u2",
                        "txn_amt_x2": 20.0,
                        "revenue_amount": 30.0,
                        "status_flg": False,
                    },
                    {
                        "txn_id": "t3",
                        "user_id": "u3",
                        "txn_amt_x2": 40.0,
                        "revenue_amount": 60.0,
                        "status_flg": True,
                    },
                ],
                corpus.RAW_EVENTS.name: [
                    {"event_id": "e1", "user_id": "u1", "event_type": "click"},
                    {"event_id": "e2", "user_id": "u2", "event_type": "page_view"},
                    {"event_id": "e3", "user_id": "u1", "event_type": "click"},
                ],
            }
            for tier in config.TIERS:
                for table in corpus.CORPUS:
                    reference = config.table_ref(tier, table.name)
                    schema = [
                        bigquery.SchemaField(column.name, column.type) for column in table.columns
                    ]
                    saved = client.create_table(
                        bigquery.Table(reference, schema=schema), timeout=30
                    )
                    assert not client.insert_rows_json(saved, rows[table.name], timeout=30)
            browse = request("/browse/bigquery?" + query)
            assert not browse.get("error")
            for tier in config.TIERS:
                assert config.tier_dataset(tier) in json.dumps(browse)
            print(f"LocalCloud BigQuery: project={project}, endpoint={endpoint}")
            yield client
        finally:
            try:
                for dataset in datasets:
                    client.delete_dataset(
                        dataset, delete_contents=True, not_found_ok=True, timeout=30
                    )
                    with pytest.raises(NotFound):
                        client.get_dataset(dataset, retry=None, timeout=30)
                after = request_count()
                assert after > before
                print(f"BigQuery request_count: {before} -> {after}; owned datasets deleted")
            finally:
                client.close()
