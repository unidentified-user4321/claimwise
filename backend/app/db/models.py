"""SQLAlchemy mappings for the existing insurance_claims tables."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import CheckConstraint, UniqueConstraint, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.db.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String)
    date_of_birth: Mapped[date] = mapped_column(Date)
    sex: Mapped[str] = mapped_column(String)
    education_level: Mapped[str] = mapped_column(String)
    occupation: Mapped[str] = mapped_column(String)
    hobbies: Mapped[str] = mapped_column(String)
    relationship: Mapped[str] = mapped_column(String)
    zip_code: Mapped[str] = mapped_column(String)

    policies: Mapped[list["Policy"]] = orm_relationship(back_populates="customer")
    vehicles: Mapped[list["Vehicle"]] = orm_relationship(back_populates="customer")
    previous_claims: Mapped[list["PreviousClaim"]] = orm_relationship(back_populates="customer")
    claims: Mapped[list["Claim"]] = orm_relationship(back_populates="customer")


class Policy(Base):
    __tablename__ = "policies"

    policy_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    policy_number: Mapped[str] = mapped_column(String)
    policy_bind_date: Mapped[date] = mapped_column(Date)
    policy_state: Mapped[str] = mapped_column(String)
    policy_csl: Mapped[str] = mapped_column(String)
    deductible: Mapped[Decimal] = mapped_column(Numeric)
    annual_premium: Mapped[Decimal] = mapped_column(Numeric)
    umbrella_limit: Mapped[Decimal] = mapped_column(Numeric)

    customer: Mapped[Customer] = orm_relationship(back_populates="policies")
    vehicles: Mapped[list["Vehicle"]] = orm_relationship(back_populates="policy")
    previous_claims: Mapped[list["PreviousClaim"]] = orm_relationship(back_populates="policy")
    claims: Mapped[list["Claim"]] = orm_relationship(back_populates="policy")

    policy_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    policy_status: Mapped[str] = mapped_column(
       String(20),
       default="active"
    )

    product_code: Mapped[str | None] = mapped_column(
       String(50),
       nullable=True
    )

    coverage_limit: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    policy_id: Mapped[str] = mapped_column(ForeignKey("policies.policy_id"), index=True)
    make: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)

    customer: Mapped[Customer] = orm_relationship(back_populates="vehicles")
    policy: Mapped[Policy] = orm_relationship(back_populates="vehicles")


class PreviousClaim(Base):
    __tablename__ = "previous_claims"

    previous_claim_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    policy_id: Mapped[str] = mapped_column(ForeignKey("policies.policy_id"), index=True)
    claim_date: Mapped[date] = mapped_column(Date)
    claim_amount: Mapped[Decimal] = mapped_column(Numeric)
    incident_type: Mapped[str] = mapped_column(String)
    incident_severity: Mapped[str] = mapped_column(String)

    customer: Mapped[Customer] = orm_relationship(back_populates="previous_claims")
    policy: Mapped[Policy] = orm_relationship(back_populates="previous_claims")


class Claim(Base):
    __tablename__ = "claims"

    claim_id: Mapped[str] = mapped_column(
        String(20), primary_key=True, default=lambda: f"CLM-{uuid4().hex[:16]}"
    )
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"), index=True)
    policy_id: Mapped[str] = mapped_column(ForeignKey("policies.policy_id"), index=True)
    incident_date: Mapped[date] = mapped_column(Date)
    incident_type: Mapped[str] = mapped_column(String)
    collision_type: Mapped[str | None] = mapped_column(String, nullable=True)

    incident_severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    authorities_contacted: Mapped[str | None] = mapped_column(String(50), nullable=True)
    incident_state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    incident_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    incident_hour_of_the_day: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    
    incident_location: Mapped[str] = mapped_column(String)
    number_of_vehicles_involved: Mapped[int] = mapped_column(Integer)
    property_damage: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    bodily_injuries: Mapped[int] = mapped_column(Integer)
    witnesses: Mapped[int] = mapped_column(Integer)
    police_report_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    total_claim_amount: Mapped[Decimal] = mapped_column(Numeric)
    claim_description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="submitted")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    customer: Mapped[Customer] = orm_relationship(back_populates="claims")
    policy: Mapped[Policy] = orm_relationship(back_populates="claims")




from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime


class ClaimAnalysis(Base):
    __tablename__ = "claim_analyses"

    analysis_id = Column(String(50), primary_key=True)
    claim_id = Column(String(50), nullable=False, index=True)

    fraud_analysis = Column(JSONB, nullable=False)
    nlp_analysis = Column(JSONB, nullable=False)
    policy_checks = Column(JSONB, nullable=False)
    policy_analysis = Column(JSONB, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )



class ClaimHistory(Base):
    __tablename__ = "claim_history"

    history_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    claim_id: Mapped[str] = mapped_column(
        ForeignKey("claims.claim_id", ondelete="CASCADE"),
        index=True,
    )

    action: Mapped[str] = mapped_column(String(50))

    old_status: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )

    new_status: Mapped[str] = mapped_column(String(30))

    note: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    actor_type: Mapped[str] = mapped_column(String(30))

    actor_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        server_default=func.now(),
    )

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("clerk_user_id", name="uq_users_clerk_user_id"),
        CheckConstraint(
            "(role = 'client' AND customer_id IS NOT NULL) OR "
            "(role = 'employee' AND customer_id IS NULL)", name="ck_users_role_customer",
        ),
    )

    user_id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: uuid4().hex)
    clerk_user_id: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.customer_id"), nullable=True)
