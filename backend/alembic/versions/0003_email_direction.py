"""Add direction to emails (inbound/outbound)

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "inb_pilot_emails",
        sa.Column("direction", sa.String(), nullable=False, server_default="inbound"),
    )
    op.create_index("ix_inb_pilot_emails_direction", "inb_pilot_emails", ["direction"])


def downgrade() -> None:
    op.drop_index("ix_inb_pilot_emails_direction", table_name="inb_pilot_emails")
    op.drop_column("inb_pilot_emails", "direction")
