"""Status/history integration tests; no external database or ML services needed."""

from datetime import date, datetime
import unittest
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.claims import router
from app.db.database import Base, get_db
from app.db.models import Claim, ClaimHistory, Customer, Policy
from app.services.claim_status import get_claim_history, update_claim_status


class ClaimStatusTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(
            self.engine,
            tables=[Customer.__table__, Policy.__table__, Claim.__table__, ClaimHistory.__table__],
        )
        self.db = Session(self.engine, autoflush=False)
        self.db.add(Customer(
            customer_id="C1", name="Test", date_of_birth=date(1990, 1, 1),
            sex="unknown", education_level="unknown", occupation="unknown",
            hobbies="unknown", relationship="unknown", zip_code="00000",
        ))
        self.db.flush()
        self.db.add(Policy(
            policy_id="P1", customer_id="C1", policy_number="1",
            policy_bind_date=date(2020, 1, 1), policy_state="OH", policy_csl="100/300",
            deductible=100, annual_premium=100, umbrella_limit=0,
        ))
        self.db.flush()
        self.db.add(Claim(
            claim_id="CLM-001", customer_id="C1", policy_id="P1",
            incident_date=date(2026, 1, 1), incident_type="collision",
            incident_location="Original location", number_of_vehicles_involved=1,
            bodily_injuries=0, witnesses=0, total_claim_amount=100,
            claim_description="Test claim", status="submitted",
        ))
        self.db.commit()

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)
        self.url = "/api/v1/claims/CLM-001"

    def tearDown(self):
        self.client.close()
        self.db.close()
        self.engine.dispose()

    def assert_state(self, expected_status, history_count):
        # Expire objects to check persisted values, not just Python attributes.
        self.db.expire_all()
        self.assertEqual(self.db.get(Claim, "CLM-001").status, expected_status)
        self.assertEqual(len(self.db.scalars(select(ClaimHistory)).all()), history_count)

    def test_submitted_to_under_review(self):
        with patch.object(self.db, "commit", wraps=self.db.commit) as commit:
            response = self.client.patch(self.url + "/status", json={
                "status": "under_review", "note": "Manual review started.",
                "actor_type": "admin", "actor_id": "untrusted",
            })
            self.assertEqual(commit.call_count, 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "claim_id": "CLM-001", "old_status": "submitted",
            "new_status": "under_review", "history_id": 1,
        })
        self.assert_state("under_review", 1)
        history = self.client.get(self.url + "/history").json()[0]
        self.assertEqual(history["action"], "status_change")
        self.assertEqual(history["old_status"], "submitted")
        self.assertEqual(history["new_status"], "under_review")
        self.assertEqual(history["note"], "Manual review started.")
        self.assertEqual(history["actor_type"], "reviewer")
        self.assertIsNone(history["actor_id"])
        self.assertIsInstance(history["created_at"], str)

    def test_under_review_to_approved(self):
        update_claim_status(self.db, "CLM-001", "under_review")
        update_claim_status(self.db, "CLM-001", "approved")
        self.assert_state("approved", 2)

    def test_under_review_to_rejected(self):
        update_claim_status(self.db, "CLM-001", "under_review")
        update_claim_status(self.db, "CLM-001", "rejected")
        self.assert_state("rejected", 2)

    def test_approved_and_rejected_can_close(self):
        for prior in ("approved", "rejected"):
            with self.subTest(prior=prior):
                self.db.get(Claim, "CLM-001").status = prior
                self.db.commit()
                update_claim_status(self.db, "CLM-001", "closed")
                self.assertEqual(self.db.get(Claim, "CLM-001").status, "closed")

    def test_invalid_transitions_do_not_write(self):
        for old, new in (
            ("submitted", "approved"), ("submitted", "rejected"),
            ("approved", "under_review"), ("closed", "under_review"),
            ("submitted", "submitted"), ("legacy_status", "under_review"),
        ):
            with self.subTest(old=old, new=new):
                self.db.get(Claim, "CLM-001").status = old
                self.db.commit()
                response = self.client.patch(self.url + "/status", json={"status": new})
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json()["detail"], f"Invalid status transition: {old} -> {new}")
                self.assert_state(old, 0)

    def test_unknown_status_is_bad_request(self):
        response = self.client.patch(self.url + "/status", json={"status": "unknown"})
        self.assertEqual(response.status_code, 400)
        self.assert_state("submitted", 0)

    def test_missing_claim(self):
        self.assertEqual(self.client.patch(
            "/api/v1/claims/missing/status", json={"status": "under_review"},
        ).status_code, 404)
        self.assertEqual(self.client.get("/api/v1/claims/missing/history").status_code, 404)
        with self.assertRaises(HTTPException) as error:
            get_claim_history(self.db, "missing")
        self.assertEqual(error.exception.status_code, 404)

    def test_empty_history(self):
        response = self.client.get(self.url + "/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_history_orders_by_time_then_id_and_filters_claim(self):
        for history_id, timestamp in (
            (1, datetime(2026, 1, 2)), (2, datetime(2026, 1, 1)),
            (3, datetime(2026, 1, 1)),
        ):
            self.db.add(ClaimHistory(
                history_id=history_id, claim_id="CLM-001", action="status_change",
                old_status="submitted", new_status="under_review",
                actor_type="reviewer", created_at=timestamp,
            ))
        other = Claim(
            claim_id="CLM-002", customer_id="C1", policy_id="P1",
            incident_date=date(2026, 1, 1), incident_type="collision",
            incident_location="Other", number_of_vehicles_involved=1,
            bodily_injuries=0, witnesses=0, total_claim_amount=100,
            claim_description="Other claim",
        )
        self.db.add(other)
        self.db.commit()
        update_claim_status(self.db, "CLM-002", "under_review")
        response = self.client.get(self.url + "/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["history_id"] for row in response.json()], [2, 3, 1])

    def test_failed_history_insert_rolls_back_status(self):
        # Fail a real INSERT after SQLAlchemy has issued the claim UPDATE.
        with self.assertRaises(IntegrityError):
            update_claim_status(self.db, "CLM-001", "under_review", actor_type=None)
        self.assert_state("submitted", 0)

    def test_generic_patch_status_is_audited_with_other_fields(self):
        with patch.object(self.db, "commit", wraps=self.db.commit) as commit:
            response = self.client.patch(self.url, json={
                "status": "under_review", "incident_location": "Updated location",
            })
            self.assertEqual(commit.call_count, 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["incident_location"], "Updated location")
        self.assertEqual(response.json()["status"], "under_review")
        self.assert_state("under_review", 1)

    def test_invalid_generic_status_does_not_update_other_fields(self):
        response = self.client.patch(self.url, json={
            "status": "approved", "incident_location": "Must not persist",
        })
        self.assertEqual(response.status_code, 409)
        self.assert_state("submitted", 0)
        self.assertEqual(self.db.get(Claim, "CLM-001").incident_location, "Original location")

    def test_failed_history_insert_rolls_back_generic_fields(self):
        with self.assertRaises(IntegrityError):
            update_claim_status(
                self.db, "CLM-001", "under_review", actor_type=None,
                claim_updates={"incident_location": "Must not persist"},
            )
        self.assert_state("submitted", 0)
        self.assertEqual(self.db.get(Claim, "CLM-001").incident_location, "Original location")

    def test_generic_patch_without_status_is_unchanged(self):
        response = self.client.patch(self.url, json={"incident_location": "Updated location"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["incident_location"], "Updated location")
        self.assert_state("submitted", 0)


if __name__ == "__main__":
    unittest.main()
