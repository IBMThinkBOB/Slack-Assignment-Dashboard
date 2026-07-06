"""slack_event: add mentioned_name and claimed_by_resource_id

Revision ID: c1f3d2e4a567
Revises: ab02b8a47a49
Create Date: 2026-07-02 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c1f3d2e4a567"
down_revision: Union[str, None] = "ab02b8a47a49"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("slack_events", sa.Column("mentioned_name", sa.String(), nullable=True))
    op.add_column(
        "slack_events",
        sa.Column(
            "claimed_by_resource_id",
            sa.String(),
            sa.ForeignKey("resources.resource_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("slack_events", "claimed_by_resource_id")
    op.drop_column("slack_events", "mentioned_name")
