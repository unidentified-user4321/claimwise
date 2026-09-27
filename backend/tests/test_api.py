"""Core HTTP contracts with real routes and isolated persistence."""

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from unittest.mock import Mock

from app.db.models import Claim, ClaimAnalysis, Vehicle


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_claim(authenticated_client, db, claim_payload):
    response = authenticated_client.post("/api/v1/claims", json=claim_payload)
    assert response.status_code == 201
    result = response.json()
    assert result["claim_id"].startswith("CLM-")
    assert result["customer_id"] == "C1"
    assert result["status"] == "submitted"
    assert db.get(Claim, result["claim_id"]).policy_id == "P1"


def test_get_claim(authenticated_client):
    response = authenticated_client.get("/api/v1/claims/CLM-001")
    assert response.status_code == 200
    assert response.json()["customer_id"] == "C1"
    assert response.json()["claim_description"] == "Test claim"
    assert [claim["claim_id"] for claim in authenticated_client.get("/api/v1/claims").json()] == ["CLM-001"]


def test_delete_claim(employee_client, db):
    response = employee_client.delete("/api/v1/claims/CLM-001")
    assert response.status_code == 204
    assert response.content == b""
    assert db.get(Claim, "CLM-001") is None
    assert employee_client.get("/api/v1/claims/CLM-001").status_code == 404


@pytest.mark.parametrize("method,payload", [("get", None), ("patch", {"incident_location": "Updated"}), ("delete", None)])
def test_missing_claim(employee_client, method, payload):
    kwargs = {"json": payload} if payload is not None else {}
    response = employee_client.request(method, "/api/v1/claims/missing", **kwargs)
    assert response.status_code == 404


def test_invalid_claim(authenticated_client, db, claim_payload):
    claim_payload["total_claim_amount"] = -1
    response = authenticated_client.post("/api/v1/claims", json=claim_payload)
    assert response.status_code == 422
    assert len(db.scalars(select(Claim)).all()) == 1


@pytest.fixture
def analysis_providers(db, monkeypatch):
    db.add(Vehicle(customer_id="C1", policy_id="P1", make="Test", model="Car", year=2020))
    db.commit()
    fraud = Mock(return_value={"fraud_probability": 0.2, "fraud_prediction": 0})
    nlp = Mock(return_value={"predicted_incident_type": "collision", "confidence": 0.9})
    policy = Mock(return_value={"coverage_decision": "covered", "explanation": "Mock policy evidence"})
    monkeypatch.setattr("app.services.analysis.predict_fraud", fraud)
    monkeypatch.setattr("app.services.analysis.classify_claim_description", nlp)
    monkeypatch.setattr("app.services.analysis.analyze_policy_with_llm", policy)
    return policy


def test_analyze_claim(employee_client, db, analysis_providers):
    response = employee_client.post("/api/v1/claims/CLM-001/analyze")
    assert response.status_code == 200
    result = response.json()
    assert result["claim_id"] == "CLM-001"
    assert result["fraud_analysis"] == {"probability": 0.2, "prediction": 0}
    assert result["nlp_analysis"]["incident_type_match"] is True
    assert result["policy_checks"]["vehicle_matches_policy"] is True
    assert result["policy_analysis"]["coverage_decision"] == "covered"
    analysis_providers.assert_called_once()
    assert len(db.scalars(select(ClaimAnalysis)).all()) == 1
    stored = employee_client.get("/api/v1/claims/CLM-001/analysis")
    assert stored.status_code == 200
    assert stored.json()["analysis_id"].startswith("ANL-")
    for key in ("fraud_analysis", "nlp_analysis", "policy_checks", "policy_analysis"):
        assert stored.json()[key] == result[key]


def test_analysis_missing_claim(employee_client, analysis_providers):
    assert employee_client.post("/api/v1/claims/missing/analyze").status_code == 404
    assert employee_client.get("/api/v1/claims/CLM-001/analysis").status_code == 404
    analysis_providers.assert_not_called()


def test_analysis_provider_error(employee_client, db, analysis_providers):
    analysis_providers.side_effect = HTTPException(503, "Policy service unavailable")
    response = employee_client.post("/api/v1/claims/CLM-001/analyze")
    assert response.status_code == 503
    assert response.json()["detail"] == "Policy service unavailable"
    assert db.scalars(select(ClaimAnalysis)).all() == []
