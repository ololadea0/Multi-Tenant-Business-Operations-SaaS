from datetime import datetime, timedelta, timezone


def test_sync_push_accepts_and_replays_idempotently(authenticated_client, organization):
    payload = {
        "operations": [
            {
                "operation_id": "op-001",
                "entity_type": "products",
                "entity_id": 101,
                "action": "create",
                "base_version": 0,
                "payload": {"name": "Offline Product", "sku": "OFF-001"},
            }
        ]
    }

    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/sync/push",
        json=payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] == 1
    assert data["duplicates"] == 0
    assert data["results"][0]["operation_id"] == "op-001"

    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/sync/push",
        json=payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] == 0
    assert data["duplicates"] == 1
    assert data["results"][0]["status"] == "duplicate"


def test_sync_push_rejects_stale_version(authenticated_client, organization):
    first = {
        "operations": [
            {
                "operation_id": "op-101",
                "entity_type": "products",
                "entity_id": 202,
                "action": "create",
                "base_version": 0,
                "payload": {"name": "Widget", "sku": "WGT-001"},
            }
        ]
    }

    first_response = authenticated_client.post(
        f"/api/organizations/{organization.id}/sync/push",
        json=first,
    )
    assert first_response.status_code == 200

    stale = {
        "operations": [
            {
                "operation_id": "op-102",
                "entity_type": "products",
                "entity_id": 202,
                "action": "update",
                "base_version": 0,
                "payload": {"name": "Updated Widget"},
            }
        ]
    }

    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/sync/push",
        json=stale,
    )

    assert response.status_code == 409
    assert "Stale sync version" in response.json()["detail"]


def test_sync_changes_returns_recently_queued_records(authenticated_client, organization):
    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/sync/push",
        json={
            "operations": [
                {
                    "operation_id": "op-201",
                    "entity_type": "customers",
                    "entity_id": 301,
                    "action": "create",
                    "base_version": 0,
                    "payload": {"name": "Jane Doe"},
                }
            ]
        },
    )

    assert response.status_code == 200

    since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    response = authenticated_client.get(
        f"/api/organizations/{organization.id}/sync/changes",
        params={"since": since},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"]
    assert any(item["operation_id"] == "op-201" for item in data["items"])
