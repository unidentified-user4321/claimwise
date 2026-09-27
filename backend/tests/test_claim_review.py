"""Human review integration tests using the Phase A isolated database fixture."""

import unittest
import pytest
from unittest.mock import patch

from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

from app.db.models import Claim
from app.services.claim_review import perform_review_action
from tests import test_claim_status as phase_a


@pytest.mark.usefixtures("claim_case")
class ClaimReviewTests(unittest.TestCase):
    assert_state = phase_a.ClaimStatusTests.assert_state

    def set_status(self, value):
        self.db.get(Claim, "CLM-001").status = value
        self.db.commit()

    def review(self, action, note=None):
        return self.client.post(self.url + "/review-action", json={
            "action": action, "note": note,
        })

    def check_action(self, old, action, new, note=None):
        self.set_status(old)
        with patch.object(self.db, "commit", wraps=self.db.commit) as commit:
            response = self.review(action, note)
            self.assertEqual(commit.call_count, 1)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {
            "claim_id": "CLM-001", "action": action, "old_status": old,
            "new_status": new, "history_id": 1,
        })
        self.assert_state(new, 1)
        history = self.client.get(self.url + "/history").json()[0]
        self.assertEqual(history["action"], action)
        self.assertEqual(history["old_status"], old)
        self.assertEqual(history["new_status"], new)
        self.assertEqual(history["note"], note)
        self.assertEqual(history["actor_type"], "employee")
        self.assertEqual(history["actor_id"], "test-employee")

    def test_start_review(self):
        self.check_action("submitted", "start_review", "under_review")

    def test_approve(self):
        self.check_action("under_review", "approve", "approved")

    def test_reject(self):
        self.check_action("under_review", "reject", "rejected", "Evidence inconsistent.")

    def test_request_information(self):
        self.check_action("under_review", "request_information", "under_review", "Provide police report.")

    def test_investigate(self):
        self.check_action("under_review", "investigate", "under_review", "Verify repair estimate.")

    def test_close_approved(self):
        self.check_action("approved", "close", "closed")

    def test_close_rejected(self):
        self.check_action("rejected", "close", "closed")

    def test_invalid_action_state_combinations(self):
        allowed = {
            "submitted": {"start_review"},
            "under_review": {"approve", "reject", "request_information", "investigate"},
            "approved": {"close"}, "rejected": {"close"}, "closed": set(),
        }
        actions = {"start_review", "approve", "reject", "request_information", "investigate", "close"}
        for old, valid_actions in allowed.items():
            for action in actions - valid_actions:
                with self.subTest(status=old, action=action):
                    self.set_status(old)
                    response = self.review(action, "Explanation.")
                    self.assertEqual(response.status_code, 409)
                    self.assertEqual(response.json()["detail"],
                        f"Action '{action}' is not allowed while claim is '{old}'")
                    self.assert_state(old, 0)

    def test_required_notes(self):
        self.set_status("under_review")
        for action in ("reject", "request_information", "investigate"):
            for note in (None, "", " \t\n"):
                with self.subTest(action=action, note=note):
                    response = self.review(action, note)
                    self.assertEqual(response.status_code, 400)
                    self.assertIn("non-blank note", response.json()["detail"])
                    self.assert_state("under_review", 0)

    def test_unknown_action(self):
        response = self.review("unknown")
        self.assertEqual(response.status_code, 400)
        self.assert_state("submitted", 0)

    def test_missing_claim(self):
        response = self.client.post("/api/v1/claims/missing/review-action", json={"action": "start_review"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Claim not found")

    def test_server_fields_are_rejected(self):
        for field, value in (
            ("actor_type", "admin"), ("actor_id", "fake"),
            ("old_status", "under_review"), ("new_status", "approved"),
        ):
            with self.subTest(field=field):
                response = self.client.post(self.url + "/review-action", json={
                    "action": "start_review", field: value,
                })
                self.assertEqual(response.status_code, 422)
                self.assert_state("submitted", 0)

    def test_unified_history_and_phase_a_noop_rule(self):
        response = self.client.patch(self.url + "/status", json={"status": "under_review"})
        self.assertEqual(response.status_code, 200)
        for action, note in (
            ("request_information", "Provide report."),
            ("investigate", "Verify evidence."), ("approve", None), ("close", None),
        ):
            self.assertEqual(self.review(action, note).status_code, 200)
        response = self.client.get(self.url + "/history")
        self.assertEqual(response.status_code, 200)
        rows = response.json()
        self.assertEqual([row["action"] for row in rows], [
            "status_change", "request_information", "investigate", "approve", "close",
        ])
        self.assertEqual(rows, sorted(rows, key=lambda row: (row["created_at"], row["history_id"])))
        self.assertEqual(self.client.patch(self.url + "/status", json={"status": "closed"}).status_code, 409)
        self.assert_state("closed", 5)

    def test_history_failure_rolls_back_status(self):
        with self.assertRaises(IntegrityError):
            perform_review_action(self.db, "CLM-001", "start_review", actor_type=None)
        self.assert_state("submitted", 0)

    def test_same_status_actions_do_not_issue_claim_update(self):
        self.set_status("under_review")
        statements = []

        def record_statement(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement.strip().upper())

        event.listen(self.engine, "before_cursor_execute", record_statement)
        try:
            for action in ("request_information", "investigate"):
                self.assertEqual(self.review(action, "Please verify evidence.").status_code, 200)
        finally:
            event.remove(self.engine, "before_cursor_execute", record_statement)
        self.assertFalse(any(sql.startswith("UPDATE CLAIMS") for sql in statements))
        self.assert_state("under_review", 2)
