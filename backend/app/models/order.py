from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, func
from app.db.base import Base  # adjust if your Base is imported differently


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    medicine_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String, default="pending")

    total_amount = Column(Numeric, nullable=True)
    requires_prescription = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())