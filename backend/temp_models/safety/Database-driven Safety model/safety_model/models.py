from __future__ import annotations

from sqlalchemy import Boolean, Column, Integer, String

from .db import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    # Database-driven safety flags
    requires_prescription = Column(Boolean, nullable=False, default=False)
    controlled_level = Column(Integer, nullable=False, default=0)
    max_daily_dosage = Column(Integer, nullable=True)  # in mg

