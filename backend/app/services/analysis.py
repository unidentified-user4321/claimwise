"""Orchestrate claim inference, policy analysis, and persistence."""

import uuid

from sqlalchemy.orm import Session

from app.services.claim_context import load_claim_context
from app.feature_builder import build_fraud_features
from app.ml import predict_fraud, classify_claim_description
from app.policy_checks import run_policy_checks
from app.rag.policy_rag import analyze_policy_with_llm
from app.db.models import ClaimAnalysis


def analyze_claim(
    claim_id: str,
    db: Session,
):
    # =========================================================
    # 1. Load claim context from PostgreSQL
    # =========================================================

    context = load_claim_context(claim_id, db)

    claim = context["claim"]


    # =========================================================
    # 2. Structured fraud ML
    # =========================================================

    features = build_fraud_features(
        claim=claim,
        customer=context["customer"],
        policy=context["policy"],
        vehicle=context["vehicle"],
        derived=context["derived"],
    )

    fraud_result = predict_fraud(features)

    fraud_analysis = {
        "probability": fraud_result["fraud_probability"],
        "prediction": fraud_result["fraud_prediction"],
    }


    # =========================================================
# 3. NLP claim-description classification
# =========================================================

    nlp_result = classify_claim_description(
     claim.claim_description
    )

    submitted_type = claim.incident_type
    predicted_type = nlp_result["predicted_incident_type"]


# Normalize frontend/submitted labels to model labels
    INCIDENT_TYPE_MAP = {
     "vehicle theft": "theft",
     "theft": "theft",

     "single vehicle collision": "collision",
     "multi vehicle collision": "collision",
     "collision": "collision",

     "vehicle fire": "fire",
     "fire": "fire",
 
     "weather damage": "weather_damage",
     "weather_damage": "weather_damage",
 
     "vandalism": "vandalism",
     "other": "other",
    } 


    def normalize_incident_type(value: str) -> str:
        value = value.strip().lower()

        return INCIDENT_TYPE_MAP.get(
        value,
        value,
    )


    submitted_normalized = normalize_incident_type(
     submitted_type
    )

    predicted_normalized = normalize_incident_type(
      predicted_type
    )

    incident_type_match = (
      submitted_normalized
       == predicted_normalized
    )


    nlp_analysis = {
    "submitted_incident_type": submitted_type,
    "predicted_incident_type": predicted_type,
    "confidence": nlp_result["confidence"],
    "incident_type_match": incident_type_match,
    }

    # =========================================================
    # 4. Deterministic policy checks
    # =========================================================

    policy_checks = run_policy_checks(context)


    # =========================================================
    # 5. RAG + Gemini policy analysis
    # =========================================================

    policy_analysis = analyze_policy_with_llm(
        context=context,
        policy_checks=policy_checks,
        fraud_analysis=fraud_analysis,
        nlp_analysis=nlp_analysis,
    )


    # =========================================================
    # 6. Build final analysis
    # =========================================================

    result = {
        "claim_id": claim_id,
        "fraud_analysis": fraud_analysis,
        "nlp_analysis": nlp_analysis,
        "policy_checks": policy_checks,
        "policy_analysis": policy_analysis,
    }


    # =========================================================
    # 7. Save analysis to PostgreSQL
    # =========================================================

    analysis_record = ClaimAnalysis(
        analysis_id=f"ANL-{uuid.uuid4().hex[:16]}",
        claim_id=claim_id,
        fraud_analysis=fraud_analysis,
        nlp_analysis=nlp_analysis,
        policy_checks=policy_checks,
        policy_analysis=policy_analysis,
    )

    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)


    # =========================================================
    # 8. Return analysis
    # =========================================================

    return result

