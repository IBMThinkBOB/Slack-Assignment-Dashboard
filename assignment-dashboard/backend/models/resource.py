from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Float, Enum
from sqlalchemy.orm import relationship

from database import Base


class Resource(Base):
    __tablename__ = "resources"

    resource_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=True, unique=True)
    availability = Column(
        Enum("Available", "Busy", "On Leave", name="resource_availability"),
        nullable=False,
        default="Available",
    )
    utilization = Column(Float, nullable=True, default=0.0)  # 0.0–100.0 percent

    assignments = relationship("Assignment", back_populates="resource")
