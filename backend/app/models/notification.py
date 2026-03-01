"""
Notification models for medicine stock refill alerts
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, func, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class StockAlert(Base):
    __tablename__ = "stock_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Medicine info
    medicine_id = Column(Integer, nullable=False, index=True)
    medicine_name = Column(String, nullable=False)
    
    # Stock levels
    current_stock = Column(Integer, nullable=False)
    total_stock = Column(Integer, nullable=False)
    stock_percentage = Column(Float, nullable=False)
    
    # Alert level
    alert_level = Column(String, nullable=False)  # "warning", "critical"
    severity = Column(String, default="info")  # "info", "warning", "critical"
    
    # Refill info
    needs_refill = Column(Boolean, default=True, index=True)
    refill_quantity = Column(Integer, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # n8n workflow tracking
    n8n_workflow_triggered = Column(Boolean, default=False)
    n8n_workflow_id = Column(String, nullable=True)
    n8n_execution_id = Column(String, nullable=True)


class NotificationSubscription(Base):
    __tablename__ = "notification_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Customer info
    customer_id = Column(String, nullable=False, index=True)
    customer_phone = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    
    # Medicine info
    medicine_id = Column(Integer, nullable=False)
    medicine_name = Column(String, nullable=False)
    
    # Subscription preferences
    alert_type = Column(String, default="both")  # "sms", "email", "both"
    notification_threshold = Column(Integer, default=30)  # Alert when stock % falls below this
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_notified_at = Column(DateTime(timezone=True), nullable=True)


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Alert info
    stock_alert_id = Column(Integer, ForeignKey("stock_alerts.id"), nullable=True)
    
    # Recipient
    customer_id = Column(String, nullable=False, index=True)
    customer_phone = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    
    # Medicine
    medicine_id = Column(Integer, nullable=False)
    medicine_name = Column(String, nullable=False)
    
    # Notification details
    notification_type = Column(String, nullable=False)  # "stock_alert", "reminder", "urgent"
    message = Column(Text, nullable=False)
    
    # Delivery method
    notification_method = Column(String, nullable=False)  # "sms", "email", "push"
    
    # Status tracking
    is_sent = Column(Boolean, default=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivery_status = Column(String, nullable=True)  # "pending", "sent", "failed", "bounced"
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # n8n workflow tracking
    n8n_workflow_id = Column(String, nullable=True)
    n8n_execution_id = Column(String, nullable=True)
    n8n_status = Column(String, nullable=True)
    
    # Additional info
    extra_data = Column(Text, nullable=True)  # JSON string for additional data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Template info
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    notification_type = Column(String, nullable=False)  # "stock_alert", "reminder", "urgent"
    
    # Templates for different channels
    sms_template = Column(Text, nullable=True)
    email_subject = Column(String, nullable=True)
    email_template = Column(Text, nullable=True)
    push_title = Column(String, nullable=True)
    push_body = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
