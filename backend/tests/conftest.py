"""One isolated SQLite database and mocked provider boundaries per test."""

from datetime import date
import os
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# app.ml loads private model artifacts at import time. Replace only that boundary;
# analysis orchestration, feature building, policy checks, and persistence stay real.
ml = ModuleType("app.ml")
ml.predict_fraud = Mock(side_effect=AssertionError("Mock fraud inference in this test"))
ml.classify_claim_description = Mock(side_effect=AssertionError("Mock NLP inference in this test"))
sys.modules["app.ml"] = ml
os.environ["DATABASE_URL"] = "sqlite://"
with patch("dotenv.load_dotenv", return_value=False):
    from app.main import app
    from app.db.database import Base, get_db
    from app.db.models import Claim, Customer, Policy, User
    from app.schemas import ClaimRead


@compiles(JSONB, "sqlite")
def sqlite_jsonb(element, compiler, **kw):
    # JSONB storage is enough for these tests; no PostgreSQL JSON operators are used.
    return "JSON"


@pytest.fixture(autouse=True)
def external_services(monkeypatch):
    def unexpected_call(*args, **kwargs):
        raise AssertionError("External service must be mocked by the test")
    # Prevent accidental provider calls; individual tests replace these boundaries.
    monkeypatch.setattr("app.auth.authenticate_request", unexpected_call)
    monkeypatch.setattr("app.rag.policy_rag.get_llm", unexpected_call)
    monkeypatch.setattr("app.rag.policy_rag.retrieve_for_claim", unexpected_call)
    monkeypatch.setattr("app.services.claim_similarity.get_embeddings", unexpected_call)


@pytest.fixture
def db():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    with Session(engine, autoflush=False) as session:
        for customer_id in ("C1", "C2"):
            session.add(Customer(
                customer_id=customer_id, name="Test", date_of_birth=date(1990, 1, 1),
                sex="unknown", education_level="unknown", occupation="unknown",
                hobbies="unknown", relationship="unknown", zip_code="00000",
            ))
        session.flush()
        session.add(Policy(
            policy_id="P1", customer_id="C1", policy_number="1",
            policy_bind_date=date(2020, 1, 1), policy_state="OH", policy_csl="100/300",
            deductible=100, annual_premium=100, umbrella_limit=0,
        ))
        session.flush()
        session.add(Claim(
            claim_id="CLM-001", customer_id="C1", policy_id="P1",
            incident_date=date(2026, 1, 1), incident_type="collision",
            incident_location="Original location", number_of_vehicles_involved=1,
            bodily_injuries=0, witnesses=0, total_claim_amount=100,
            claim_description="Test claim", status="submitted",
        ))
        session.add(User(user_id="test-employee", clerk_user_id="user_employee", role="employee"))
        session.commit()
        yield session
    engine.dispose()


@pytest.fixture
def clerk_verifier(monkeypatch):
    def verify(request, options):
        subject = request.headers.get("Authorization", "").removeprefix("Bearer ")
        valid = subject in {"user_client", "user_other", "user_employee"}
        return SimpleNamespace(is_signed_in=valid, payload={"sub": subject} if valid else None)
    verifier = Mock(side_effect=verify)
    monkeypatch.setattr("app.config.CLERK_SECRET_KEY", "test-only-not-a-real-key")
    monkeypatch.setattr("app.auth.authenticate_request", verifier)
    return verifier


@pytest.fixture
def client(db, clerk_verifier):
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


@pytest.fixture
def employee_client(client):
    client.headers["Authorization"] = "Bearer user_employee"
    return client


@pytest.fixture
def authenticated_client(client, db):
    db.add(User(clerk_user_id="user_client", role="client", customer_id="C1"))
    db.commit()
    client.headers["Authorization"] = "Bearer user_client"
    return client


@pytest.fixture
def claim_payload(db):
    return ClaimRead.model_validate(db.get(Claim, "CLM-001")).model_dump(
        mode="json", exclude={"claim_id", "created_at", "status"},
    )


@pytest.fixture
def claim_case(request, db, employee_client):
    # Keep the existing unittest regression assertions while sharing pytest setup.
    request.instance.db = db
    request.instance.engine = db.bind
    request.instance.client = employee_client
    request.instance.url = "/api/v1/claims/CLM-001"
