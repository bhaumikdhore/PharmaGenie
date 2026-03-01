"""
Delivery tracking model for database
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, nullable=False, index=True)
    tracking_number = Column(String, unique=True, nullable=False, index=True)
    
    # Current status/stage
    current_stage = Column(String, default="pending", nullable=False)
    
    # Location tracking
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    current_location = Column(String, nullable=True)
    
    # Delivery partner info
    delivery_partner_id = Column(String, nullable=True)
    delivery_partner_name = Column(String, nullable=True)
    delivery_partner_phone = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    estimated_delivery_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Customer info for delivery
    customer_id = Column(String, nullable=False)
    customer_phone = Column(String, nullable=True)
    customer_address = Column(Text, nullable=True)
    
    # Delivery details
    is_delivered = Column(Boolean, default=False, index=True)
    delivery_attempts = Column(Integer, default=0)
    notes = Column(Text, nullable=True)


class DeliveryHistory(Base):
    __tablename__ = "delivery_history"
    
    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"), nullable=False)
    
    # Stage transition
    old_stage = Column(String, nullable=True)
    new_stage = Column(String, nullable=False, index=True)
    stage_label = Column(String, nullable=True)
    
    # Location at transition
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_description = Column(String, nullable=True)
    
    # Event details
    description = Column(Text, nullable=True)
    extra_data = Column(String, nullable=True)  # JSON string for additional data
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DeliveryNotification(Base):
    __tablename__ = "delivery_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"), nullable=False)
    
    # Notification details
    notification_type = Column(String, nullable=False)  # "status_update", "delay", "failed_attempt"
    message = Column(Text, nullable=False)
    
    # Recipient info
    customer_id = Column(String, nullable=False, index=True)
    phone_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    # Delivery method
    notification_method = Column(String, nullable=False)  # "sms", "email", "push", "webhook"
    
    # Status tracking
    is_sent = Column(Boolean, default=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0)
    
    # n8n workflow tracking
    n8n_workflow_id = Column(String, nullable=True)
    n8n_execution_id = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
