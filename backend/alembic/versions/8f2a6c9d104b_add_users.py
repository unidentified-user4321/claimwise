"""Add Clerk identity mappings for application authorization.

Revision ID: 8f2a6c9d104b
Revises: 31abd1a6ab4c
"""
from alembic import op
import sqlalchemy as sa

revision = "8f2a6c9d104b"
down_revision = "31abd1a6ab4c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(50), primary_key=True),
        sa.Column("clerk_user_id", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("customer_id", sa.String(50), sa.ForeignKey("customers.customer_id"), nullable=True),
        sa.UniqueConstraint("clerk_user_id", name="uq_users_clerk_user_id"),
        sa.CheckConstraint(
            "(role = 'client' AND customer_id IS NOT NULL) OR "
            "(role = 'employee' AND customer_id IS NULL)", name="ck_users_role_customer",
        ),
    )


def downgrade() -> None:
    op.drop_table("users")
