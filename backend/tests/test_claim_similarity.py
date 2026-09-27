"""Local similarity tests with deterministic mocked embeddings."""

from datetime import date
from types import SimpleNamespace
import unittest
import pytest
from unittest.mock import patch

from app.db.models import Claim, Vehicle
from app.services.claim_similarity import _cosine, _structured_similarity


@pytest.mark.usefixtures("claim_case")
class ClaimSimilarityTests(unittest.TestCase):
    def setUp(self):
        embeddings = patch('app.services.claim_similarity.get_embeddings')
        self.embedding_mock = embeddings.start()
        self.addCleanup(embeddings.stop)
        self.embedding_mock.return_value.embed_documents.side_effect = lambda texts: [
            [0.0, 1.0] if text == 'Different incident' else [1.0, 0.0] for text in texts
        ]

    def candidate(self, claim_id='CLM-002', **changes):
        values = dict(claim_id=claim_id, customer_id='C1', policy_id='P1',
                      incident_date=date(2026, 1, 1), incident_type='collision',
                      incident_location='Original location', number_of_vehicles_involved=1,
                      bodily_injuries=0, witnesses=0, total_claim_amount=100,
                      claim_description='A similar claim')
        values.update(changes)
        item = Claim(**values)
        self.db.add(item)
        self.db.commit()
        return item

    def matches(self, suffix=''):
        response = self.client.get(self.url + '/similar' + suffix)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['similar_claims']

    def test_current_claim_excluded_and_similar_description_scores_highly(self):
        self.candidate()
        rows = self.matches()
        self.assertEqual([row['claim_id'] for row in rows], ['CLM-002'])
        self.assertEqual(rows[0]['description_similarity'], 1)
        self.assertGreater(rows[0]['similarity_score'], .85)
        self.assertIn('Descriptions are highly semantically similar', rows[0]['reasons'])

    def test_customer_and_policy_increase_score(self):
        target = self.db.get(Claim, 'CLM-001')
        values = {field: getattr(target, field) for field in (
            'customer_id', 'policy_id', 'incident_type', 'incident_location',
            'collision_type', 'total_claim_amount', 'incident_date')}
        score, _ = _structured_similarity(target, SimpleNamespace(**values), {})
        for field, reason in [('customer_id', 'Same customer'), ('policy_id', 'Same policy')]:
            with self.subTest(field=field):
                less, reasons = _structured_similarity(target, SimpleNamespace(**{**values, field: 'other'}), {})
                self.assertAlmostEqual(score - less, .25)
                self.assertNotIn(reason, reasons)

    def test_unique_vehicle_increases_score_but_ambiguous_does_not(self):
        self.candidate()
        original = self.matches()[0]['similarity_score']
        self.db.add(Vehicle(vehicle_id=1, customer_id='C1', policy_id='P1', make='A', model='B', year=2020))
        self.db.commit()
        row = self.matches()[0]
        self.assertAlmostEqual(row['similarity_score'] - original, .08)
        self.assertTrue(any('Same insured vehicle' in reason for reason in row['reasons']))
        self.db.add(Vehicle(vehicle_id=2, customer_id='C1', policy_id='P1', make='A', model='C', year=2021))
        self.db.commit()
        row = self.matches()[0]
        self.assertEqual(row['similarity_score'], original)
        self.assertFalse(any('vehicle' in reason for reason in row['reasons']))

    def test_different_descriptions_below_threshold(self):
        self.candidate(claim_description='Different incident')
        self.assertEqual(self.matches(), [])

    def test_sorted_and_limit(self):
        self.candidate('CLM-LOW', incident_date=date(2025, 1, 1), total_claim_amount=1000)
        self.candidate('CLM-HIGH')
        rows = self.matches()
        self.assertEqual([row['claim_id'] for row in rows], ['CLM-HIGH', 'CLM-LOW'])
        self.assertGreater(rows[0]['similarity_score'], rows[1]['similarity_score'])
        self.assertEqual([row['claim_id'] for row in self.matches('?limit=1')], ['CLM-HIGH'])

    def test_unknown_claim_and_empty_database(self):
        self.assertEqual(self.client.get('/api/v1/claims/missing/similar').status_code, 404)
        self.db.delete(self.db.get(Claim, 'CLM-001'))
        self.db.commit()
        self.assertEqual(self.client.get(self.url + '/similar').status_code, 404)
        self.embedding_mock.assert_not_called()

    def test_only_current_claim_does_not_call_provider(self):
        self.assertEqual(self.matches(), [])
        self.embedding_mock.assert_not_called()

    def test_reasons_match_actual_signals(self):
        self.candidate(incident_location='Other place', collision_type=None,
                       incident_date=date(2026, 1, 4), total_claim_amount=104)
        reasons = self.matches()[0]['reasons']
        self.assertIn('Same customer', reasons)
        self.assertIn('Same policy', reasons)
        self.assertIn('Incident dates are 3 days apart', reasons)
        self.assertIn('Claim amounts differ by 4%', reasons)
        self.assertNotIn('Same incident location', reasons)
        self.assertNotIn('Same collision type', reasons)

    def test_cosine_bounds_and_zero_vectors(self):
        self.assertEqual(_cosine([1, 0], [1, 0]), 1)
        self.assertEqual(_cosine([1, 0], [-1, 0]), 0)
        self.assertEqual(_cosine([0, 0], [1, 0]), 0)

    def test_provider_failure_is_clear_and_does_not_change_claim(self):
        self.candidate()
        self.embedding_mock.return_value.embed_documents.side_effect = RuntimeError('private provider error')
        response = self.client.get(self.url + '/similar')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private', response.text)
        self.assertEqual(self.db.get(Claim, 'CLM-001').status, 'submitted')

    def test_blank_descriptions_do_not_receive_semantic_credit(self):
        self.candidate(claim_description='  ')
        self.assertEqual(self.matches(), [])

    def test_invalid_limit(self):
        for limit in (0, 21):
            self.assertEqual(self.client.get(self.url + f'/similar?limit={limit}').status_code, 422)
