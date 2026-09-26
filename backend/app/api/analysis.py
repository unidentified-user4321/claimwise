"""Routes for insurance claim analysis."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.analysis import analyze_claim as run_claim_analysis
from app.db.models import ClaimAnalysis


router = APIRouter(prefix="/claims", tags=["analysis"])


@router.post("/{claim_id}/analyze")
def analyze_claim(
    claim_id: str,
    db: Session = Depends(get_db),
):
    return run_claim_analysis(claim_id, db)


@router.get("/{claim_id}/analysis")
def get_claim_analysis(
    claim_id: str,
    db: Session = Depends(get_db),
):
    analysis = (
        db.query(ClaimAnalysis)
        .filter(ClaimAnalysis.claim_id == claim_id)
        .order_by(ClaimAnalysis.created_at.desc())
        .first()
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="No analysis found for this claim",
        )

    return {
        "analysis_id": analysis.analysis_id,
        "claim_id": analysis.claim_id,

        "fraud_analysis": analysis.fraud_analysis,

        "nlp_analysis": analysis.nlp_analysis,

        "policy_checks": analysis.policy_checks,

        "policy_analysis": analysis.policy_analysis,

        "created_at": analysis.created_at,
    }

