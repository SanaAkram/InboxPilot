"""Job applications tracker

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inb_pilot_job_applications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("inb_pilot_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email_id", UUID(as_uuid=True), sa.ForeignKey("inb_pilot_emails.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("company_domain", sa.String(), nullable=True),
        sa.Column("role_title", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default="applied"),
        sa.Column("source", sa.String(), server_default="manual"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_contact_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("ix_inb_pilot_job_applications_user_id", "inb_pilot_job_applications", ["user_id"])
    op.create_index("ix_inb_pilot_job_applications_status", "inb_pilot_job_applications", ["status"])
    op.create_index("ix_inb_pilot_job_applications_company_domain", "inb_pilot_job_applications", ["company_domain"])


def downgrade() -> None:
    op.drop_table("inb_pilot_job_applications")
