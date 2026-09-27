"""Resolve Clerk identities and link public users to demo customers."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_clerk_user_id, get_current_user
from app.db.database import get_db
from app.db.models import Customer, User
from app.schemas import LinkCustomerRequest, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/link", response_model=UserRead, status_code=201)
def link_customer(
    payload: LinkCustomerRequest,
    clerk_user_id: str = Depends(get_clerk_user_id),
    db: Session = Depends(get_db),
):
    if db.scalar(select(User).where(User.clerk_user_id == clerk_user_id)) is not None:
        raise HTTPException(409, "Account is already linked")
    if db.get(Customer, payload.customer_id) is None:
        raise HTTPException(400, "Customer ID does not exist")
    user = User(clerk_user_id=clerk_user_id, role="client", customer_id=payload.customer_id)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Account already linked or customer no longer exists") from None
    db.refresh(user)
    return user


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user
