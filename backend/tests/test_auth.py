"""Clerk verification is mocked; mapping and authorization checks are real."""

from sqlalchemy import select

from app import config
from app.db.models import User


def test_unauthenticated_request_rejected(client, clerk_verifier):
    for path in ["/claims", "/claims/CLM-001", "/claims/CLM-001/analysis", "/auth/me"]:
        assert client.get("/api/v1" + path).status_code == 401
    clerk_verifier.assert_not_called()


def test_invalid_clerk_token_rejected(client, clerk_verifier):
    client.headers["Authorization"] = "Bearer invalid"
    assert client.get("/api/v1/auth/me").status_code == 401
    options = clerk_verifier.call_args.args[1]
    assert options.authorized_parties == [config.FRONTEND_ORIGIN]
    assert options.accepts_token == ["session_token"]


def test_unmapped_identity_requires_linking(client):
    client.headers["Authorization"] = "Bearer user_client"
    assert client.get("/api/v1/auth/me").status_code == 403
    assert client.get("/api/v1/claims/CLM-001").status_code == 403
    assert client.post("/api/v1/auth/link", json={"customer_id": "missing"}).status_code == 400


def test_client_linking(client, db):
    client.headers["Authorization"] = "Bearer user_client"
    response = client.post("/api/v1/auth/link", json={"customer_id": "C1"})
    assert response.status_code == 201
    assert response.json()["role"] == "client"
    assert set(response.json()) == {"user_id", "clerk_user_id", "role", "customer_id"}
    assert client.get("/api/v1/auth/me").json()["customer_id"] == "C1"
    assert client.post("/api/v1/auth/link", json={"customer_id": "C2"}).status_code == 409
    assert db.scalar(select(User).where(User.clerk_user_id == "user_client")).customer_id == "C1"


def test_public_linking_cannot_assign_role_or_identity(client):
    client.headers["Authorization"] = "Bearer user_client"
    for extra in [{"role": "employee"}, {"clerk_user_id": "user_employee"}]:
        assert client.post("/api/v1/auth/link", json={"customer_id": "C1", **extra}).status_code == 422
    client.headers["Authorization"] = "Bearer user_employee"
    assert client.post("/api/v1/auth/link", json={"customer_id": "C1"}).status_code == 409
    assert client.get("/api/v1/auth/me").json()["role"] == "employee"


def test_client_cannot_access_other_claim(client):
    client.headers["Authorization"] = "Bearer user_other"
    assert client.post("/api/v1/auth/link", json={"customer_id": "C2"}).status_code == 201
    assert client.get("/api/v1/claims").json() == []
    assert client.get("/api/v1/claims/CLM-001").status_code == 404
    assert client.get("/api/v1/claims?customer_id=C1").status_code == 403
    assert client.get("/api/v1/customers/C1").status_code == 404
    assert client.get("/api/v1/customers/C2").status_code == 200


def test_client_cannot_use_employee_endpoints(authenticated_client):
    url = "/api/v1/claims/CLM-001"
    for suffix in ["context", "history", "analysis", "similar"]:
        assert authenticated_client.get(url + "/" + suffix).status_code == 403
    assert authenticated_client.post(url + "/analyze").status_code == 403
    assert authenticated_client.post(url + "/review-action", json={"action": "start_review"}).status_code == 403
    assert authenticated_client.patch(url, json={"status": "approved"}).status_code == 403
    assert authenticated_client.delete(url).status_code == 403


def test_claim_creation_checks_customer_and_policy(client, claim_payload):
    client.headers["Authorization"] = "Bearer user_other"
    client.post("/api/v1/auth/link", json={"customer_id": "C2"})
    assert client.post("/api/v1/claims", json=claim_payload).status_code == 403
    claim_payload["customer_id"] = "C2"  # Policy P1 still belongs to C1.
    assert client.post("/api/v1/claims", json=claim_payload).status_code == 403


def test_employee_can_access_claim(employee_client):
    assert employee_client.get("/api/v1/claims/CLM-001").status_code == 200
    response = employee_client.post("/api/v1/claims/CLM-001/review-action", json={"action": "start_review"})
    assert response.status_code == 200
    history = employee_client.get("/api/v1/claims/CLM-001/history").json()
    assert history[0]["actor_id"] == "test-employee"
    assert history[0]["actor_type"] == "employee"
