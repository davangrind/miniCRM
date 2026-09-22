# tests/test_flow.py
from fastapi.testclient import TestClient


def test_basic_lead_distribution_flow(client: TestClient):
    # 1. Create an operator.
    op_resp = client.post(
        "/api/operators/",
        json={
            "name": "Operator 1",
            "is_active": True,
            "max_active_contacts": 10,
        },
    )
    assert op_resp.status_code == 201
    operator = op_resp.json()
    operator_id = operator["id"]

    # 2. Create a source.
    src_resp = client.post(
        "/api/sources/",
        json={
            "name": "Source A",
            "code": "source_a",
        },
    )
    assert src_resp.status_code == 201
    source = src_resp.json()
    source_id = source["id"]

    # 3. Configure source-specific operator weights.
    weights_resp = client.put(
        f"/api/sources/{source_id}/operators",
        json={
            "operators": [
                {"operator_id": operator_id, "weight": 10},
            ]
        },
    )
    assert weights_resp.status_code == 200
    body = weights_resp.json()
    assert body["id"] == source_id
    assert len(body["operators"]) == 1
    assert body["operators"][0]["operator_id"] == operator_id

    # 4. Create a contact.
    contact_resp = client.post(
        "/api/contacts/",
        json={
            "external_lead_id": "lead-123",
            "source_id": source_id,
            "payload": "hello",
        },
    )
    assert contact_resp.status_code == 201
    contact = contact_resp.json()

    # The contact must be assigned to the operator.
    assert contact["operator_id"] == operator_id
    assert contact["source_id"] == source_id
    assert contact["payload"] == "hello"
    assert contact["status"] == "open"

    lead_id = contact["lead_id"]

    # 5. Verify that the lead exists and owns the contact.
    lead_resp = client.get(f"/api/leads/{lead_id}")
    assert lead_resp.status_code == 200
    lead = lead_resp.json()

    assert lead["id"] == lead_id
    assert lead["external_id"] == "lead-123"
    assert len(lead["contacts"]) == 1
    assert lead["contacts"][0]["id"] == contact["id"]
