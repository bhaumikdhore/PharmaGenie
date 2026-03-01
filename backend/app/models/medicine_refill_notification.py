"""
Medicine Refill Notification Model
Tracks medicine refill reminders and notifications for customers
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class MedicineRefillNotification(Base):
    """Medicine refill reminder notifications"""
    __tablename__ = "medicine_refill_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(100), ForeignKey("customers.id"), nullable=False)
    medicine_name = Column(String(255), nullable=False)
    dosage = Column(String(100))
    quantity = Column(Integer, default=0)
    refill_date = Column(DateTime, nullable=False)
    notification_sent = Column(Boolean, default=False)
    notification_sent_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<MedicineRefillNotification medicine={self.medicine_name}, customer={self.customer_id}, refill_date={self.refill_date}>"
