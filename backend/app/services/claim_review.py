"""Record reviewer actions in the existing claim audit trail."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Claim, ClaimHistory
from app.services.claim_status import ALLOWED_TRANSITIONS


STATUS_ACTIONS = {
    "start_review": "under_review",
    "approve": "approved",
    "reject": "rejected",
    "close": "closed",
}
REVIEW_ONLY_ACTIONS = {"request_information", "investigate"}
NOTE_REQUIRED_ACTIONS = {"reject", "request_information", "investigate"}


def perform_review_action(
    db: Session,
    claim_id: str,
    action: str,
    note: str | None = None,
    actor_type: str = "reviewer",
    actor_id: str | None = None,
) -> dict:
    try:
        claim = db.scalar(
            select(Claim)
            .where(Claim.claim_id == claim_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if claim is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Claim not found")

        old_status = claim.status
        if action in STATUS_ACTIONS:
            new_status = STATUS_ACTIONS[action]
            allowed = new_status in ALLOWED_TRANSITIONS.get(old_status, set())
        elif action in REVIEW_ONLY_ACTIONS:
            new_status = old_status
            allowed = old_status == "under_review"
        else:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, f"Invalid review action: {action}"
            )

        if not allowed:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Action '{action}' is not allowed while claim is '{old_status}'",
            )
        if action in NOTE_REQUIRED_ACTIONS and (note is None or not note.strip()):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"A non-blank note is required for action '{action}'",
            )

        if new_status != old_status:
            claim.status = new_status
        history = ClaimHistory(
            claim_id=claim.claim_id,
            action=action,
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
        "action": history.action,
        "old_status": history.old_status,
        "new_status": history.new_status,
        "history_id": history.history_id,
    }
