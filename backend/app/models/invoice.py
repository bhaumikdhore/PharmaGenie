import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String, unique=True, nullable=False)

    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), nullable=False)

    subtotal = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)

    payment_status = Column(String, default="pending")
    pdf_path = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())