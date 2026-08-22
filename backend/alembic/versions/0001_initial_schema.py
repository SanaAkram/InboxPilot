"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inb_pilot_users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("google_id", sa.String(), nullable=True, unique=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "inb_pilot_email_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("inb_pilot_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(), nullable=False, server_default="gmail"),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "inb_pilot_emails",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("inb_pilot_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gmail_message_id", sa.String(), nullable=False, unique=True),
        sa.Column("thread_id", sa.String(), nullable=True),
        sa.Column("sender_name", sa.String(), nullable=True),
        sa.Column("sender_email", sa.String(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("category", sa.String(), server_default="other"),
        sa.Column("priority", sa.String(), server_default="medium"),
        sa.Column("status", sa.String(), server_default="new"),
        sa.Column("processed", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "inb_pilot_attachments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email_id", UUID(as_uuid=True), sa.ForeignKey("inb_pilot_emails.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(), nullable=True),
        sa.Column("file_type", sa.String(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("storage_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "inb_pilot_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email_id", UUID(as_uuid=True), sa.ForeignKey("inb_pilot_emails.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("inb_pilot_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("action_type", sa.String(), server_default="other"),
        sa.Column("priority", sa.String(), server_default="medium"),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed", sa.Boolean(), server_default="false"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "inb_pilot_ai_extractions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email_id", UUID(as_uuid=True), sa.ForeignKey("inb_pilot_emails.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_response", JSONB(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("priority", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "inb_pilot_daily_briefings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("inb_pilot_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("briefing", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes for common query patterns
    op.create_index("ix_inb_pilot_emails_user_id", "inb_pilot_emails", ["user_id"])
    op.create_index("ix_inb_pilot_emails_category", "inb_pilot_emails", ["category"])
    op.create_index("ix_inb_pilot_emails_priority", "inb_pilot_emails", ["priority"])
    op.create_index("ix_inb_pilot_emails_received_at", "inb_pilot_emails", ["received_at"])
    op.create_index("ix_inb_pilot_tasks_user_id", "inb_pilot_tasks", ["user_id"])
    op.create_index("ix_inb_pilot_tasks_completed", "inb_pilot_tasks", ["completed"])


def downgrade() -> None:
    op.drop_table("inb_pilot_daily_briefings")
    op.drop_table("inb_pilot_ai_extractions")
    op.drop_table("inb_pilot_tasks")
    op.drop_table("inb_pilot_attachments")
    op.drop_table("inb_pilot_emails")
    op.drop_table("inb_pilot_email_accounts")
    op.drop_table("inb_pilot_users")
