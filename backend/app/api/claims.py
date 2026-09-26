"""CRUD routes for submitted insurance claims."""

from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Claim
from app.services.claim_context import load_claim_context
from app.services.claim_similarity import find_similar_claims
from app.services.claim_review import perform_review_action
from app.services.claim_status import (
    get_claim_history as load_claim_history,
    update_claim_status as change_claim_status,
)
from app.schemas import (
    ClaimContextRead,
    SimilarClaimsResponse,
    ClaimCreate,
    ClaimPatch,
    ClaimRead,
    ClaimHistoryResponse,
    ClaimStatusUpdate,
    ClaimStatusUpdateResponse,
    ClaimReviewActionRequest,
    ClaimReviewActionResponse,
)


router = APIRouter(prefix="/claims", tags=["claims"])


@router.get("/{claim_id}/similar", response_model=SimilarClaimsResponse)
def get_similar_claims(
    claim_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return find_similar_claims(db, claim_id, limit)



# Create claim


@router.post(
    "",
    response_model=ClaimRead,
    status_code=status.HTTP_201_CREATED,
)
def create_claim(
    payload: ClaimCreate,
    db: Session = Depends(get_db),
):
    claim = Claim(**payload.model_dump())

    db.add(claim)
    db.commit()
    db.refresh(claim)

    return claim


# =========================================================
# List claims
#
# Supports:
#
# GET /claims
# GET /claims?status=submitted
# GET /claims?customer_id=C1001
# GET /claims?customer_id=C1001&status=submitted
# GET /claims?limit=10
# =========================================================

@router.get("", response_model=list[ClaimRead])
def list_claims(
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
    ),
    customer_id: Optional[str] = Query(
        default=None,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    query = select(Claim)

    # Employee dashboard:
    # filter claims by workflow status
    if status_filter:
        query = query.where(
            Claim.status == status_filter
        )

    # Client dashboard:
    # only claims belonging to this customer
    if customer_id:
        query = query.where(
            Claim.customer_id == customer_id
        )

    # Newest claims first
    query = query.order_by(
        Claim.created_at.desc()
    )

    query = query.limit(limit)

    return db.scalars(query).all()


# Get single claim


@router.get(
    "/{claim_id}",
    response_model=ClaimRead,
)
def get_claim(
    claim_id: str,
    db: Session = Depends(get_db),
):
    claim = db.get(Claim, claim_id)

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    return claim



# Get complete claim context


@router.get(
    "/{claim_id}/context",
    response_model=ClaimContextRead,
)
def get_claim_context(
    claim_id: str,
    db: Session = Depends(get_db),
):
    return load_claim_context(
        claim_id,
        db,
    )


# Update claim


@router.patch(
    "/{claim_id}",
    response_model=ClaimRead,
)
def update_claim(
    claim_id: str,
    payload: ClaimPatch,
    db: Session = Depends(get_db),
):
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "status" in updates:
        # TODO: derive actor identity from authentication when available.
        change_claim_status(
            db,
            claim_id,
            updates.pop("status"),
            claim_updates=updates,
        )
        return db.get(Claim, claim_id)

    claim = db.get(Claim, claim_id)

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    for field, value in updates.items():
        setattr(claim, field, value)

    db.commit()
    db.refresh(claim)

    return claim



# Delete claim


@router.delete(
    "/{claim_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_claim(
    claim_id: str,
    db: Session = Depends(get_db),
):
    claim = db.get(Claim, claim_id)

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    db.delete(claim)
    db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )



# Update claim status


@router.patch("/{claim_id}/status", response_model=ClaimStatusUpdateResponse)
def update_claim_status(
    claim_id: str,
    payload: ClaimStatusUpdate,
    db: Session = Depends(get_db),
):
    # TODO: derive actor identity from authentication when available.
    return change_claim_status(db, claim_id, payload.status, note=payload.note)



# Claim history


@router.get("/{claim_id}/history", response_model=list[ClaimHistoryResponse])
def get_claim_history(claim_id: str, db: Session = Depends(get_db)):
    return load_claim_history(db, claim_id)


@router.post("/{claim_id}/review-action", response_model=ClaimReviewActionResponse)
def review_claim(
    claim_id: str,
    payload: ClaimReviewActionRequest,
    db: Session = Depends(get_db),
):
    # TODO: derive actor identity from authentication when available.
    return perform_review_action(db, claim_id, payload.action, note=payload.note)
