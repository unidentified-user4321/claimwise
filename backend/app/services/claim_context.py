"""Load claim records and derived context for API and analysis use."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Claim, Customer, Policy, PreviousClaim, Vehicle


def load_claim_context(claim_id: str, db: Session):
    claim = db.get(Claim, claim_id)

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    customer = db.get(Customer, claim.customer_id)

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer referenced by claim was not found",
        )

    policy = db.get(Policy, claim.policy_id)

    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy referenced by claim was not found",
        )

    # -----------------------------------------------------
    # Find vehicle attached to policy + customer
    # -----------------------------------------------------

    vehicles = db.scalars(
        select(Vehicle)
        .where(
            Vehicle.policy_id == claim.policy_id,
            Vehicle.customer_id == claim.customer_id,
        )
        .order_by(Vehicle.vehicle_id)
    ).all()

    if not vehicles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle for the claim policy was not found",
        )

    if len(vehicles) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Multiple vehicles match this policy; "
                "the claim does not identify one vehicle"
            ),
        )

    vehicle = vehicles[0]

    # -----------------------------------------------------
    # Previous claims
    # -----------------------------------------------------

    previous_claims = db.scalars(
        select(PreviousClaim)
        .where(
            PreviousClaim.customer_id == claim.customer_id,
            PreviousClaim.policy_id == claim.policy_id,
        )
        .order_by(
            PreviousClaim.claim_date,
            PreviousClaim.previous_claim_id,
        )
    ).all()

    # -----------------------------------------------------
    # Derived features
    # -----------------------------------------------------

    # Customer age at time of incident
    age = (
        claim.incident_date.year
        - customer.date_of_birth.year
    )

    if (
        claim.incident_date.month,
        claim.incident_date.day,
    ) < (
        customer.date_of_birth.month,
        customer.date_of_birth.day,
    ):
        age -= 1

    # Months as customer
    months_as_customer = (
        (
            claim.incident_date.year
            - policy.policy_bind_date.year
        )
        * 12
        + claim.incident_date.month
        - policy.policy_bind_date.month
    )

    if (
        claim.incident_date.day
        < policy.policy_bind_date.day
    ):
        months_as_customer -= 1

    # Previous claim amount
    previous_claim_amount = sum(
        (
            previous_claim.claim_amount
            for previous_claim in previous_claims
        ),
        start=0,
    )

    # Days since most recent previous claim
    days_since_previous_claim = None

    if previous_claims:
        most_recent_date = max(
            previous_claim.claim_date
            for previous_claim in previous_claims
        )

        days_since_previous_claim = (
            claim.incident_date
            - most_recent_date
        ).days

    derived = {
        "age": age,
        "months_as_customer": months_as_customer,
        "previous_claim_count": len(previous_claims),
        "previous_claim_amount": previous_claim_amount,
        "days_since_previous_claim": days_since_previous_claim,
    }

    return {
        "claim": claim,
        "customer": customer,
        "policy": policy,
        "vehicle": vehicle,
        "previous_claims": previous_claims,
        "derived": derived,
    }

