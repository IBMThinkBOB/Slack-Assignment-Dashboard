"""slack_event: add created_at and is_system_msg

Revision ID: d2e4f6a8b123
Revises: c1f3d2e4a567
Create Date: 2026-07-02 14:00:00.000000
"""
from typing import Sequence, Union
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa

revision: str = "d2e4f6a8b123"
down_revision: Union[str, None] = "c1f3d2e4a567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "slack_events",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.add_column(
        "slack_events",
        sa.Column("is_system_msg", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("slack_events", "is_system_msg")
    op.drop_column("slack_events", "created_at")
