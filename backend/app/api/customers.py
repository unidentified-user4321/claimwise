"""Customer identity lookup route."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Customer


router = APIRouter(prefix="/customers")


@router.get("/{customer_id}", response_model=dict[str, str])
def get_customer_identity(customer_id: str, db: Session = Depends(get_db)):
    """Read-only identity check for the local workspace; not authentication."""
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer ID not found. Please check the ID and try again.")
    return {"customer_id": customer.customer_id}

