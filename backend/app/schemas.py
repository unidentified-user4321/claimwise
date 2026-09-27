"""Pydantic schemas for the existing claims table API."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class ClaimCreate(BaseModel):
    customer_id: str = Field(min_length=1)
    policy_id: str = Field(min_length=1)
    incident_date: date
    incident_type: str = Field(min_length=1)
    collision_type: str | None = None

    incident_severity: str | None = None
    authorities_contacted: str | None = None
    incident_state: str | None = None
    incident_city: str | None = None
    incident_hour_of_the_day: int | None = Field(default=None, ge=0, le=23)


    incident_location: str = Field(min_length=1)
    number_of_vehicles_involved: int = Field(ge=0)
    property_damage: bool | None = None
    bodily_injuries: int = Field(ge=0)
    witnesses: int = Field(ge=0)
    police_report_available: bool | None = None
    total_claim_amount: Decimal = Field(gt=0)
    claim_description: str = Field(min_length=1)


class ClaimPatch(BaseModel):
    customer_id: str | None = Field(default=None, min_length=1)
    policy_id: str | None = Field(default=None, min_length=1)
    incident_date: date | None = None
    incident_type: str | None = Field(default=None, min_length=1)
    collision_type: str | None = None

    incident_severity: str | None = None
    authorities_contacted: str | None = None
    incident_state: str | None = None
    incident_city: str | None = None
    incident_hour_of_the_day: int | None = Field(default=None, ge=0, le=23)

    incident_location: str | None = Field(default=None, min_length=1)
    number_of_vehicles_involved: int | None = Field(default=None, ge=0)
    property_damage: bool | None = None
    bodily_injuries: int | None = Field(default=None, ge=0)
    witnesses: int | None = Field(default=None, ge=0)
    police_report_available: bool | None = None
    total_claim_amount: Decimal | None = Field(default=None, gt=0)
    claim_description: str | None = Field(default=None, min_length=1)
    status: str | None = Field(default=None, min_length=1)


class SimilarClaimRead(BaseModel):
    claim_id: str
    similarity_score: float = Field(ge=0, le=1)
    description_similarity: float = Field(ge=0, le=1)
    reasons: list[str]


class SimilarClaimsResponse(BaseModel):
    claim_id: str
    similar_claims: list[SimilarClaimRead]


class ClaimStatusUpdate(BaseModel):
    status: str
    note: str | None = None


class ClaimStatusUpdateResponse(BaseModel):
    claim_id: str
    old_status: str
    new_status: str
    history_id: int


class ClaimReviewActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    note: str | None = None


class ClaimReviewActionResponse(BaseModel):
    claim_id: str
    action: str
    old_status: str
    new_status: str
    history_id: int


class ClaimHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: int
    claim_id: str
    action: str
    old_status: str | None
    new_status: str
    note: str | None
    actor_type: str
    actor_id: str | None
    created_at: datetime


class ClaimRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_id: str
    customer_id: str
    policy_id: str
    incident_date: date
    incident_type: str
    collision_type: str | None

    incident_severity: str | None
    authorities_contacted: str | None
    incident_state: str | None
    incident_city: str | None
    incident_hour_of_the_day: int | None

    incident_location: str
    number_of_vehicles_involved: int
    property_damage: bool | None
    bodily_injuries: int
    witnesses: int
    police_report_available: bool | None
    total_claim_amount: Decimal
    claim_description: str
    status: str
    created_at: datetime


class CustomerContextRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    name: str
    date_of_birth: date
    sex: str
    education_level: str
    occupation: str
    hobbies: str
    relationship: str
    zip_code: str


# class PolicyContextRead(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     policy_id: str
#     customer_id: str
#     policy_number: str
#     policy_bind_date: date
#     policy_state: str
#     policy_csl: str
#     deductible: Decimal
#     annual_premium: Decimal
#     umbrella_limit: Decimal

class PolicyContextRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    policy_id: str
    customer_id: str
    policy_number: str
    policy_bind_date: date
    policy_end_date: date | None

    policy_status: str
    product_code: str | None

    policy_state: str
    policy_csl: str

    deductible: Decimal
    annual_premium: Decimal
    umbrella_limit: Decimal
    coverage_limit: Decimal | None

class VehicleContextRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vehicle_id: int
    customer_id: str
    policy_id: str
    make: str
    model: str
    year: int


class PreviousClaimContextRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    previous_claim_id: int
    customer_id: str
    policy_id: str
    claim_date: date
    claim_amount: Decimal
    incident_type: str
    incident_severity: str


class ClaimContextDerived(BaseModel):
    age: int
    months_as_customer: int
    previous_claim_count: int
    previous_claim_amount: Decimal
    days_since_previous_claim: int | None


class ClaimContextRead(BaseModel):
    claim: ClaimRead
    customer: CustomerContextRead
    policy: PolicyContextRead
    vehicle: VehicleContextRead
    previous_claims: list[PreviousClaimContextRead]
    derived: ClaimContextDerived


class LinkCustomerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: str = Field(min_length=1, max_length=50)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: str
    clerk_user_id: str
    role: Literal["client", "employee"]
    customer_id: str | None
