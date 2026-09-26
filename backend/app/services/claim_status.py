"""Validate claim status changes and persist their audit trail atomically."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Claim, ClaimHistory


ALLOWED_TRANSITIONS = {
    "submitted": {"under_review"},
    "under_review": {"approved", "rejected"},
    "approved": {"closed"},
    "rejected": {"closed"},
    "closed": set(),
}


def update_claim_status(
    db: Session,
    claim_id: str,
    new_status: str,
    note: str | None = None,
    actor_type: str = "reviewer",
    actor_id: str | None = None,
    *,
    claim_updates: dict | None = None,
) -> dict:
    """Also persist validated generic PATCH fields in the same transaction."""
    try:
        # Serialize concurrent transitions and read the latest persisted status.
        claim = db.scalar(
            select(Claim)
            .where(Claim.claim_id == claim_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if claim is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Claim not found")

        old_status = claim.status
        if new_status not in ALLOWED_TRANSITIONS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, f"Invalid status value: {new_status}"
            )
        if new_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Invalid status transition: {old_status} -> {new_status}",
            )

        for field, value in (claim_updates or {}).items():
            if field != "status":
                setattr(claim, field, value)
        claim.status = new_status
        history = ClaimHistory(
            claim_id=claim.claim_id,
            action="status_change",
            old_status=old_status,
            new_status=new_status,
            note=note,
            actor_type=actor_type,
            actor_id=actor_id,
        )
        db.add(history)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(history)
    return {
        "claim_id": history.claim_id,
        "old_status": history.old_status,
        "new_status": history.new_status,
        "history_id": history.history_id,
    }


def get_claim_history(db: Session, claim_id: str):
    if db.get(Claim, claim_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Claim not found")
    return db.scalars(
        select(ClaimHistory)
        .where(ClaimHistory.claim_id == claim_id)
        .order_by(ClaimHistory.created_at, ClaimHistory.history_id)
    ).all()
