"""
Notification Service - Business logic for stock refill notifications
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.notification import (
    StockAlert, 
    NotificationSubscription, 
    NotificationLog,
    NotificationTemplate
)


class NotificationService:
    """Service for managing notifications"""
    
    @staticmethod
    def create_stock_alert(
        db: Session,
        medicine_id: int,
        medicine_name: str,
        current_stock: int,
        total_stock: int,
        alert_level: str,
        refill_quantity: Optional[int] = None
    ) -> StockAlert:
        """Create a stock alert"""
        stock_percentage = (current_stock / total_stock) * 100
        
        alert = StockAlert(
            medicine_id=medicine_id,
            medicine_name=medicine_name,
            current_stock=current_stock,
            total_stock=total_stock,
            stock_percentage=stock_percentage,
            alert_level=alert_level,
            severity="critical" if alert_level == "critical" else "warning",
            needs_refill=True,
            refill_quantity=refill_quantity or int(total_stock * 0.5)
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
    
    @staticmethod
    def get_active_alerts(db: Session) -> List[StockAlert]:
        """Get all active stock alerts"""
        return db.query(StockAlert)\
            .filter(and_(
                StockAlert.is_active == True,
                StockAlert.is_resolved == False
            ))\
            .order_by(desc(StockAlert.created_at))\
            .all()
    
    @staticmethod
    def get_alerts_by_medicine(db: Session, medicine_id: int) -> List[StockAlert]:
        """Get alerts for a specific medicine"""
        return db.query(StockAlert)\
            .filter(StockAlert.medicine_id == medicine_id)\
            .order_by(desc(StockAlert.created_at))\
            .all()
    
    @staticmethod
    def resolve_alert(db: Session, alert_id: int) -> StockAlert:
        """Resolve a stock alert"""
        alert = db.query(StockAlert).filter(StockAlert.id == alert_id).first()
        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")
        
        alert.is_resolved = True
        alert.is_active = False
        alert.resolved_at = datetime.utcnow()
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
    
    @staticmethod
    def subscribe_to_alerts(
        db: Session,
        customer_id: str,
        medicine_id: int,
        medicine_name: str,
        customer_phone: Optional[str] = None,
        customer_email: Optional[str] = None,
        alert_type: str = "both"
    ) -> NotificationSubscription:
        """Subscribe customer to medicine stock alerts"""
        
        # Check if subscription already exists
        existing = db.query(NotificationSubscription).filter(and_(
            NotificationSubscription.customer_id == customer_id,
            NotificationSubscription.medicine_id == medicine_id
        )).first()
        
        if existing:
            # Update existing subscription
            existing.alert_type = alert_type
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing
        
        subscription = NotificationSubscription(
            customer_id=customer_id,
            medicine_id=medicine_id,
            medicine_name=medicine_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            alert_type=alert_type
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription
    
    @staticmethod
    def get_subscriptions_by_customer(db: Session, customer_id: str) -> List[NotificationSubscription]:
        """Get all subscriptions for a customer"""
        return db.query(NotificationSubscription)\
            .filter(and_(
                NotificationSubscription.customer_id == customer_id,
                NotificationSubscription.is_active == True
            ))\
            .all()
    
    @staticmethod
    def get_subscriptions_by_medicine(db: Session, medicine_id: int) -> List[NotificationSubscription]:
        """Get all subscriptions for a medicine"""
        return db.query(NotificationSubscription)\
            .filter(and_(
                NotificationSubscription.medicine_id == medicine_id,
                NotificationSubscription.is_active == True
            ))\
            .all()
    
    @staticmethod
    def unsubscribe(db: Session, subscription_id: int) -> NotificationSubscription:
        """Unsubscribe from alerts"""
        subscription = db.query(NotificationSubscription)\
            .filter(NotificationSubscription.id == subscription_id)\
            .first()
        
        if not subscription:
            raise ValueError(f"Subscription not found: {subscription_id}")
        
        subscription.is_active = False
        subscription.updated_at = datetime.utcnow()
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription
    
    @staticmethod
    def create_notification_log(
        db: Session,
        customer_id: str,
        medicine_id: int,
        medicine_name: str,
        notification_type: str,
        message: str,
        notification_method: str,
        customer_phone: Optional[str] = None,
        customer_email: Optional[str] = None,
        stock_alert_id: Optional[int] = None
    ) -> NotificationLog:
        """Create a notification log entry"""
        log = NotificationLog(
            stock_alert_id=stock_alert_id,
            customer_id=customer_id,
            medicine_id=medicine_id,
            medicine_name=medicine_name,
            notification_type=notification_type,
            message=message,
            notification_method=notification_method,
            customer_phone=customer_phone,
            customer_email=customer_email,
            delivery_status="pending"
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def mark_notification_sent(
        db: Session,
        notification_id: int,
        n8n_workflow_id: Optional[str] = None,
        n8n_execution_id: Optional[str] = None,
        n8n_status: str = "success"
    ) -> NotificationLog:
        """Mark notification as sent"""
        notification = db.query(NotificationLog)\
            .filter(NotificationLog.id == notification_id)\
            .first()
        
        if not notification:
            raise ValueError(f"Notification not found: {notification_id}")
        
        notification.is_sent = True
        notification.sent_at = datetime.utcnow()
        notification.delivery_status = "sent" if n8n_status == "success" else "failed"
        if n8n_workflow_id:
            notification.n8n_workflow_id = n8n_workflow_id
        if n8n_execution_id:
            notification.n8n_execution_id = n8n_execution_id
        if n8n_status:
            notification.n8n_status = n8n_status
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    @staticmethod
    def get_pending_notifications(db: Session) -> List[NotificationLog]:
        """Get all pending notifications"""
        return db.query(NotificationLog)\
            .filter(NotificationLog.is_sent == False)\
            .order_by(NotificationLog.created_at)\
            .all()
    
    @staticmethod
    def get_notification_history(
        db: Session,
        customer_id: Optional[str] = None,
        medicine_id: Optional[int] = None,
        limit: int = 50
    ) -> List[NotificationLog]:
        """Get notification history"""
        query = db.query(NotificationLog)
        
        if customer_id:
            query = query.filter(NotificationLog.customer_id == customer_id)
        if medicine_id:
            query = query.filter(NotificationLog.medicine_id == medicine_id)
        
        return query.order_by(desc(NotificationLog.created_at)).limit(limit).all()
    
    @staticmethod
    def get_or_create_template(
        db: Session,
        name: str,
        notification_type: str,
        sms_template: Optional[str] = None,
        email_subject: Optional[str] = None,
        email_template: Optional[str] = None
    ) -> NotificationTemplate:
        """Get or create a notification template"""
        template = db.query(NotificationTemplate)\
            .filter(NotificationTemplate.name == name)\
            .first()
        
        if template:
            return template
        
        template = NotificationTemplate(
            name=name,
            notification_type=notification_type,
            sms_template=sms_template,
            email_subject=email_subject,
            email_template=email_template
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template
    
    @staticmethod
    def get_template_by_name(db: Session, name: str) -> Optional[NotificationTemplate]:
        """Get a notification template by name"""
        return db.query(NotificationTemplate)\
            .filter(NotificationTemplate.name == name)\
            .first()


# Default notification templates
DEFAULT_TEMPLATES = {
    "stock_refill_alert": {
        "name": "stock_refill_alert",
        "notification_type": "stock_alert",
        "sms_template": "Hi! Your medicine {medicine_name} stock is running low. Please refill now to avoid missing your doses. Reply STOP to unsubscribe.",
        "email_subject": "Refill Your Medicine: {medicine_name}",
        "email_template": """<h2>Medicine Stock Alert</h2>
<p>Your prescribed medicine <strong>{medicine_name}</strong> is running low.</p>
<p>Current stock: {current_stock} units</p>
<p><a href="{refill_link}">Click here to refill</a></p>"""
    },
    "critical_stock_alert": {
        "name": "critical_stock_alert",
        "notification_type": "stock_alert",
        "sms_template": "URGENT: Your medicine {medicine_name} stock is critically low! Refill immediately to avoid missing your medication.",
        "email_subject": "URGENT: Refill Your Medicine NOW - {medicine_name}",
        "email_template": """<h2 style="color: red;">URGENT: Medicine Stock Critical</h2>
<p>Your prescribed medicine <strong>{medicine_name}</strong> is almost out of stock!</p>
<p>Current stock: {current_stock} units (Critical Level)</p>
<p><a href="{refill_link}" style="background: red; color: white; padding: 10px;">Refill Now</a></p>"""
    },
    "refill_reminder": {
        "name": "refill_reminder",
        "notification_type": "reminder",
        "sms_template": "Reminder: Don't forget to refill your medicine {medicine_name}. Visit our pharmacy or order online.",
        "email_subject": "Reminder: Refill Your Medicine {medicine_name}",
        "email_template": """<h2>Refill Reminder</h2>
<p>This is a friendly reminder to refill your medicine <strong>{medicine_name}</strong>.</p>
<p><a href="{refill_link}">Refill now</a></p>"""
    }
}
