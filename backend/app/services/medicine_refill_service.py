"""
Medicine Refill Notification Service
Manages creation, retrieval, and status updates for refill notifications
"""

from datetime import datetime, timedelta
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.models.medicine_refill_notification import MedicineRefillNotification
from typing import Optional, List


class MedicineRefillService:
    """Service for managing medicine refill notifications"""
    
    @staticmethod
    def create_refill_notification(
        db: Session,
        customer_id: str,
        medicine_name: str,
        dosage: Optional[str] = None,
        quantity: int = 0,
        refill_days: int = 7
    ) -> MedicineRefillNotification:
        """Create a new refill notification"""
        refill_date = datetime.utcnow() + timedelta(days=refill_days)
        
        notification = MedicineRefillNotification(
            customer_id=customer_id,
            medicine_name=medicine_name,
            dosage=dosage,
            quantity=quantity,
            refill_date=refill_date
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    @staticmethod
    def get_pending_notifications(
        db: Session,
        customer_id: str
    ) -> List[MedicineRefillNotification]:
        """Get pending notifications for a customer"""
        return db.query(MedicineRefillNotification).filter(
            MedicineRefillNotification.customer_id == customer_id,
            MedicineRefillNotification.is_active == True,
            MedicineRefillNotification.notification_sent == False,
            MedicineRefillNotification.refill_date <= datetime.utcnow()
        ).order_by(desc(MedicineRefillNotification.refill_date)).all()
    
    @staticmethod
    def get_upcoming_notifications(
        db: Session,
        customer_id: str,
        days_ahead: int = 7
    ) -> List[MedicineRefillNotification]:
        """Get upcoming refill notifications (within days_ahead)"""
        future_date = datetime.utcnow() + timedelta(days=days_ahead)
        return db.query(MedicineRefillNotification).filter(
            MedicineRefillNotification.customer_id == customer_id,
            MedicineRefillNotification.is_active == True,
            MedicineRefillNotification.refill_date <= future_date,
            MedicineRefillNotification.refill_date >= datetime.utcnow()
        ).order_by(MedicineRefillNotification.refill_date).all()
    
    @staticmethod
    def mark_notification_sent(
        db: Session,
        notification_id: int
    ) -> MedicineRefillNotification:
        """Mark notification as sent"""
        notification = db.query(MedicineRefillNotification).filter(
            MedicineRefillNotification.id == notification_id
        ).first()
        
        if notification:
            notification.notification_sent = True
            notification.notification_sent_date = datetime.utcnow()
            db.commit()
            db.refresh(notification)
        
        return notification
    
    @staticmethod
    def deactivate_notification(
        db: Session,
        notification_id: int
    ) -> MedicineRefillNotification:
        """Deactivate a refill notification"""
        notification = db.query(MedicineRefillNotification).filter(
            MedicineRefillNotification.id == notification_id
        ).first()
        
        if notification:
            notification.is_active = False
            db.commit()
            db.refresh(notification)
        
        return notification
    
    @staticmethod
    def get_all_notifications(
        db: Session,
        customer_id: str
    ) -> List[MedicineRefillNotification]:
        """Get all notifications for customer"""
        return db.query(MedicineRefillNotification).filter(
            MedicineRefillNotification.customer_id == customer_id
        ).order_by(desc(MedicineRefillNotification.created_at)).all()
