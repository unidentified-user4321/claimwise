"""Regression checks for ORM IDs, nullable policies, and provider parsing."""

from datetime import date
from decimal import Decimal
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from langchain_core.documents import Document

from app.db.models import Claim, Policy, PreviousClaim, Vehicle
from app.policy_checks import run_policy_checks
from app.rag.policy_rag import analyze_policy_with_llm
from app.schemas import PreviousClaimContextRead, VehicleContextRead


def context():
    return {
        "claim": Claim(
            claim_id="CLM-1", customer_id="C1", policy_id="P1",
            incident_date=date(2026, 6, 1), incident_type="collision",
            claim_description="Vehicle struck a wall.", total_claim_amount=Decimal("100"),
            bodily_injuries=0, witnesses=0,
        ),
        "policy": Policy(
            policy_id="P1", policy_status="active", product_code="MOTOR_STANDARD",
            policy_bind_date=date(2026, 1, 1), policy_end_date=date(2026, 12, 31),
            coverage_limit=Decimal("1000"), deductible=Decimal("20"),
        ),
        "vehicle": Vehicle(
            vehicle_id=7, customer_id="C1", policy_id="P1", make="A", model="B", year=2020,
        ),
    }


class OrmIdTests(unittest.TestCase):
    def test_vehicle_integer_id_serializes_from_orm(self):
        result = VehicleContextRead.model_validate(context()["vehicle"]).model_dump(mode="json")
        self.assertIs(type(result["vehicle_id"]), int)
        self.assertEqual(result["vehicle_id"], 7)
        self.assertEqual(result["customer_id"], "C1")
        self.assertEqual(result["policy_id"], "P1")

    def test_previous_claim_integer_id_serializes_from_orm(self):
        item = PreviousClaim(
            previous_claim_id=8, customer_id="C1", policy_id="P1",
            claim_date=date(2025, 1, 1), claim_amount=Decimal("50"),
            incident_type="collision", incident_severity="minor",
        )
        result = PreviousClaimContextRead.model_validate(item).model_dump(mode="json")
        self.assertIs(type(result["previous_claim_id"]), int)
        self.assertEqual(result["previous_claim_id"], 8)
        self.assertEqual(result["customer_id"], "C1")
        self.assertEqual(result["policy_id"], "P1")


class NullablePolicyTests(unittest.TestCase):
    def test_normal_values_unchanged(self):
        self.assertEqual(run_policy_checks(context()), {
            "policy_active": True, "incident_within_policy_period": True,
            "within_coverage_limit": True, "vehicle_matches_policy": True,
            "claim_amount": 100.0, "coverage_limit": 1000.0,
            "deductible": 20.0, "amount_after_deductible": 80.0, "issues": [],
        })

    def test_missing_end_date_is_unknown(self):
        data = context()
        data["policy"].policy_end_date = None
        result = run_policy_checks(data)
        self.assertIsNone(result["incident_within_policy_period"])
        self.assertTrue(result["within_coverage_limit"])
        self.assertEqual(result["issues"], [
            "Policy end date is unavailable; coverage period could not be determined.",
        ])

    def test_missing_limit_is_unknown(self):
        data = context()
        data["policy"].coverage_limit = None
        result = run_policy_checks(data)
        self.assertIsNone(result["coverage_limit"])
        self.assertIsNone(result["within_coverage_limit"])
        self.assertTrue(result["incident_within_policy_period"])
        self.assertEqual(result["issues"], [
            "Policy coverage limit is unavailable; amount check could not be determined.",
        ])

    def test_both_missing_values_serialize_as_null(self):
        data = context()
        data["policy"].policy_end_date = None
        data["policy"].coverage_limit = None
        result = json.loads(json.dumps(run_policy_checks(data)))
        self.assertIsNone(result["incident_within_policy_period"])
        self.assertIsNone(result["within_coverage_limit"])
        self.assertIsNone(result["coverage_limit"])
        self.assertEqual(len(result["issues"]), 2)

    def test_nonnull_failed_checks_and_zero_limit_unchanged(self):
        data = context()
        data["policy"].policy_end_date = date(2026, 5, 1)
        data["policy"].coverage_limit = Decimal("0")
        result = run_policy_checks(data)
        self.assertFalse(result["incident_within_policy_period"])
        self.assertFalse(result["within_coverage_limit"])
        self.assertEqual(result["coverage_limit"], 0.0)
        self.assertEqual(result["issues"], [
            "Incident date falls outside the policy coverage period.",
            "Claim amount exceeds the policy coverage limit.",
        ])


class GeminiParsingTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "summary": "Review required.",
            "coverage_analysis": {"status": "needs_review", "reasoning": "Check evidence."},
            "policy_requirements": [], "discrepancies": [], "missing_information": [],
            "risk_indicators": [], "recommended_review": "Review evidence.",
        }
        self.raw = json.dumps(self.payload)
        retrieval = patch("app.rag.policy_rag.retrieve_for_claim", return_value=[
            Document(page_content="Policy evidence", metadata={
                "product_code": "MOTOR_STANDARD", "source": "policy.md", "chunk_index": 0,
            }),
        ])
        retrieval.start()
        self.addCleanup(retrieval.stop)
        provider = patch("app.rag.policy_rag.get_llm")
        self.llm = provider.start().return_value
        self.addCleanup(provider.stop)

    def analyze(self, response):
        self.llm.invoke.return_value = response
        return analyze_policy_with_llm(context(), {}, {}, {})

    def assert_valid(self, content):
        self.assertEqual(self.analyze(SimpleNamespace(content=content)), {
            **self.payload,
            "retrieved_policy_chunks": [{
                "product_code": "MOTOR_STANDARD", "source": "policy.md", "chunk_index": 0,
            }],
        })

    def test_normal_text_block_preserves_result_and_citations(self):
        self.assert_valid([{"text": self.raw}])

    def test_plain_string_response(self):
        self.assert_valid(self.raw)

    def test_split_text_blocks_and_string_parts(self):
        middle = len(self.raw) // 2
        self.assert_valid([{"text": self.raw[:middle]}, self.raw[middle:]])

    def test_missing_empty_content_or_parts(self):
        for response in (None, SimpleNamespace(), SimpleNamespace(parts=[]),
                         SimpleNamespace(content=None), SimpleNamespace(content=""),
                         SimpleNamespace(content="  "), SimpleNamespace(content=[])):
            with self.subTest(response=response):
                with self.assertRaises(HTTPException) as error:
                    self.analyze(response)
                self.assertEqual(error.exception.status_code, 502)
                self.assertIn("no usable text", error.exception.detail)

    def test_missing_or_nontext_blocks(self):
        for content in ([{}], [{"text": None}], [{"text": 123}], [None], {"parts": []}):
            with self.subTest(content=content):
                with self.assertRaises(HTTPException) as error:
                    self.analyze(SimpleNamespace(content=content))
                self.assertEqual(error.exception.status_code, 502)

    def test_malformed_json_is_controlled_failure(self):
        with self.assertRaises(HTTPException) as error:
            self.analyze(SimpleNamespace(content=[{"text": "not JSON"}]))
        self.assertEqual(error.exception.status_code, 502)
        self.assertIn("invalid JSON", error.exception.detail)

    def test_unexpected_json_top_level_is_controlled_failure(self):
        for value in ([], [self.payload], None, True, 42, "text"):
            with self.subTest(value=value):
                with self.assertRaises(HTTPException) as error:
                    self.analyze(SimpleNamespace(content=json.dumps(value)))
                self.assertEqual(error.exception.status_code, 502)
                self.assertIn("unexpected JSON structure", error.exception.detail)


if __name__ == "__main__":
    unittest.main()
