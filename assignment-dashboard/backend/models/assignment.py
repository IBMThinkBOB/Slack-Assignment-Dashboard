from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship

from database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    assignment_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(String, ForeignKey("resources.resource_id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=True)
    status = Column(
        Enum("Assigned", "In Progress", "Completed", "Removed", name="assignment_status"),
        nullable=False,
        default="Assigned",
    )
    progress_percent = Column(Integer, nullable=True, default=0)

    project = relationship("Project", back_populates="assignments")
    resource = relationship("Resource", back_populates="assignments")
