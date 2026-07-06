from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Column, String, Integer, Date, JSON, Text, Enum
from sqlalchemy.orm import relationship

from database import Base


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    customer = Column(String, nullable=False)
    status = Column(
        Enum("Active", "In Progress", "On Hold", "Completed", "Cancelled", name="project_status"),
        nullable=False,
        default="Active",
    )
    type = Column(
        Enum("Paid", "Presales", "Internal", "Support", name="project_type"),
        nullable=True,
    )
    priority = Column(
        Enum("High", "Medium", "Low", name="project_priority"),
        nullable=True,
    )
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    progress_percent = Column(Integer, nullable=True, default=0)
    description = Column(Text, nullable=True)
    source = Column(
        Enum("slack", "excel", "manual", name="project_source"),
        nullable=False,
        default="manual",
    )
    required_skills = Column(JSON, nullable=True)  # list of strings
    manager = Column(String, nullable=True)
    practice = Column(String, nullable=True)

    assignments = relationship("Assignment", back_populates="project", cascade="all, delete-orphan")
    slack_events = relationship("SlackEvent", back_populates="project")
