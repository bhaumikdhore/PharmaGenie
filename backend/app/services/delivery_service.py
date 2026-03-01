"""
Delivery Service - Business logic for delivery tracking
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.delivery import Delivery, DeliveryHistory, DeliveryNotification


class DeliveryService:
    """Service for managing deliveries"""
    
    @staticmethod
    def create_delivery(
        db: Session,
        order_id: str,
        tracking_number: str,
        customer_id: str,
        customer_phone: Optional[str] = None,
        customer_address: Optional[str] = None,
        stage: str = "pending"
    ) -> Delivery:
        """Create a new delivery record"""
        delivery = Delivery(
            order_id=order_id,
            tracking_number=tracking_number,
            customer_id=customer_id,
            customer_phone=customer_phone,
            customer_address=customer_address,
            current_stage=stage
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        return delivery
    
    @staticmethod
    def get_delivery_by_order(db: Session, order_id: str) -> Optional[Delivery]:
        """Get delivery record by order ID"""
        return db.query(Delivery).filter(Delivery.order_id == order_id).first()
    
    @staticmethod
    def get_delivery_by_tracking(db: Session, tracking_number: str) -> Optional[Delivery]:
        """Get delivery record by tracking number"""
        return db.query(Delivery).filter(Delivery.tracking_number == tracking_number).first()
    
    @staticmethod
    def get_deliveries_by_customer(db: Session, customer_id: str) -> List[Delivery]:
        """Get all deliveries for a customer"""
        return db.query(Delivery).filter(Delivery.customer_id == customer_id).all()
    
    @staticmethod
    def update_delivery_stage(
        db: Session,
        delivery_id: int,
        new_stage: str,
        location: Optional[dict] = None,
        notes: Optional[str] = None
    ) -> Delivery:
        """Update delivery stage and create history record"""
        delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
        if not delivery:
            raise ValueError(f"Delivery not found: {delivery_id}")
        
        old_stage = delivery.current_stage
        delivery.current_stage = new_stage
        delivery.updated_at = datetime.utcnow()
        
        # Update location if provided
        if location:
            delivery.latitude = location.get("latitude")
            delivery.longitude = location.get("longitude")
            delivery.current_location = location.get("address")
        
        # Mark as delivered if final stage
        if new_stage == "delivered":
            delivery.is_delivered = True
            delivery.delivered_at = datetime.utcnow()
        
        if new_stage == "failed":
            delivery.delivery_attempts += 1
        
        db.add(delivery)
        db.commit()
        
        # Create history record
        DeliveryService.create_history_record(
            db=db,
            delivery_id=delivery_id,
            old_stage=old_stage,
            new_stage=new_stage,
            location=location,
            notes=notes
        )
        
        db.refresh(delivery)
        return delivery
    
    @staticmethod
    def create_history_record(
        db: Session,
        delivery_id: int,
        old_stage: str,
        new_stage: str,
        location: Optional[dict] = None,
        notes: Optional[str] = None
    ) -> DeliveryHistory:
        """Create a delivery history record"""
        history = DeliveryHistory(
            delivery_id=delivery_id,
            old_stage=old_stage,
            new_stage=new_stage,
            latitude=location.get("latitude") if location else None,
            longitude=location.get("longitude") if location else None,
            location_description=location.get("address") if location else None,
            description=notes,
            timestamp=datetime.utcnow()
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        return history
    
    @staticmethod
    def get_delivery_history(db: Session, delivery_id: int) -> List[DeliveryHistory]:
        """Get all history records for a delivery"""
        return db.query(DeliveryHistory)\
            .filter(DeliveryHistory.delivery_id == delivery_id)\
            .order_by(desc(DeliveryHistory.timestamp))\
            .all()
    
    @staticmethod
    def create_notification(
        db: Session,
        delivery_id: int,
        notification_type: str,
        message: str,
        customer_id: str,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        notification_method: str = "sms"
    ) -> DeliveryNotification:
        """Create a delivery notification"""
        notification = DeliveryNotification(
            delivery_id=delivery_id,
            notification_type=notification_type,
            message=message,
            customer_id=customer_id,
            phone_number=phone_number,
            email=email,
            notification_method=notification_method
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    @staticmethod
    def mark_notification_sent(
        db: Session,
        notification_id: int,
        n8n_workflow_id: Optional[str] = None,
        n8n_execution_id: Optional[str] = None
    ) -> DeliveryNotification:
        """Mark notification as sent"""
        notification = db.query(DeliveryNotification)\
            .filter(DeliveryNotification.id == notification_id)\
            .first()
        
        if not notification:
            raise ValueError(f"Notification not found: {notification_id}")
        
        notification.is_sent = True
        notification.sent_at = datetime.utcnow()
        if n8n_workflow_id:
            notification.n8n_workflow_id = n8n_workflow_id
        if n8n_execution_id:
            notification.n8n_execution_id = n8n_execution_id
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    @staticmethod
    def get_pending_notifications(db: Session) -> List[DeliveryNotification]:
        """Get all pending notifications"""
        return db.query(DeliveryNotification)\
            .filter(DeliveryNotification.is_sent == False)\
            .order_by(DeliveryNotification.created_at)\
            .all()
    
    @staticmethod
    def get_failed_deliveries(db: Session, max_attempts: int = 3) -> List[Delivery]:
        """Get deliveries that have failed"""
        return db.query(Delivery)\
            .filter(and_(
                Delivery.is_delivered == False,
                Delivery.delivery_attempts >= max_attempts
            ))\
            .all()
