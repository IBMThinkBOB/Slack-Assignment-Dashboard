from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class SlackEvent(Base):
    __tablename__ = "slack_events"

    event_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    channel = Column(String, nullable=True)
    slack_user_id = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    ts = Column(String, nullable=True)  # Slack timestamp string e.g. "1716400000.123456"
    processed = Column(Boolean, nullable=False, default=False)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="SET NULL"), nullable=True)

    # Simulator-specific fields
    # Name extracted from @mention in the message (e.g. "Adam" from "Hey @Adam, ...")
    mentioned_name = Column(String, nullable=True)
    # resource_id of whoever claimed or was auto-assigned via @mention
    claimed_by_resource_id = Column(String, ForeignKey("resources.resource_id", ondelete="SET NULL"), nullable=True)
    # Wall-clock time message was stored — used for guaranteed chronological ordering
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: datetime.now(timezone.utc))
    # True for auto-generated system messages (e.g. "✅ Aman claimed …")
    is_system_msg = Column(Boolean, nullable=False, default=False)

    project = relationship("Project", back_populates="slack_events")
    claimed_by = relationship("Resource", foreign_keys=[claimed_by_resource_id])
