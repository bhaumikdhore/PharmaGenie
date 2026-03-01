"""
Prescription Storage Model
Stores prescription photos and details for repetitive orders
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class PrescriptionStorage(Base):
    """
    Stores prescription photos and metadata for repetitive orders
    Allows customers to upload once and reuse for similar medicines
    """
    __tablename__ = "prescription_storage"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    medicine_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    doctor_name: Mapped[str] = mapped_column(String, nullable=True)
    prescription_photo_path: Mapped[str] = mapped_column(String, nullable=False)
    prescription_photo_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    dosage: Mapped[str] = mapped_column(String, nullable=True)
    frequency: Mapped[str] = mapped_column(String, nullable=True)  # e.g., "Once daily", "Twice daily"
    duration_days: Mapped[int] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    upload_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expiry_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)  # Track how many times used
    last_used: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<PrescriptionStorage(id={self.id}, medicine={self.medicine_name}, customer={self.customer_id})>"
