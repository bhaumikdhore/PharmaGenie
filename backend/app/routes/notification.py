"""
Notification routes - API endpoints for stock refill notifications
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.agents import notification_agent
from app.db.session import get_db
from app.services.notification_service import NotificationService, DEFAULT_TEMPLATES
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# Pydantic models for request/response
class StockCheckRequest(BaseModel):
    action: str = "check_stock"
    medicine_id: Optional[int] = None
    medicine_name: Optional[str] = None
    current_stock: Optional[int] = None
    total_stock: int = 100


class SendNotificationRequest(BaseModel):
    action: str = "send_notification"
    medicine_name: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_id: Optional[str] = None
    alert_type: str = "both"  # sms, email, both


class SubscribeToAlertsRequest(BaseModel):
    action: str = "subscribe"
    customer_id: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    medicines: List[str]  # List of medicine names or IDs


class GetAlertsRequest(BaseModel):
    action: str = "get_alerts"
    customer_id: Optional[str] = None
    medicine_name: Optional[str] = None


class NotificationResponse(BaseModel):
    agent: str
    status: str
    message: Optional[str] = None


class StockAlertResponse(BaseModel):
    agent: str
    status: str
    medicine_id: Optional[int] = None
    medicine_name: Optional[str] = None
    current_stock: Optional[int] = None
    stock_percentage: Optional[float] = None
    alert_level: Optional[str] = None
    needs_refill: Optional[bool] = None


class ActiveAlertsResponse(BaseModel):
    agent: str
    status: str
    customer_id: Optional[str] = None
    active_alerts: List[dict]
    alert_count: int
    critical_alerts: int
    warning_alerts: int


# get_db is imported from app.db.session


@router.post("/check-stock", response_model=StockAlertResponse)
async def check_stock_levels(request: StockCheckRequest):
    """
    Check medicine stock levels and trigger alerts if needed
    
    - **medicine_id** or **medicine_name**: Medicine identifier
    - **current_stock**: Current stock quantity
    - **total_stock**: Total stock capacity (default: 100)
    """
    input_data = {
        "action": "check_stock",
        "medicine_id": request.medicine_id,
        "medicine_name": request.medicine_name,
        "current_stock": request.current_stock,
        "total_stock": request.total_stock
    }
    
    result = await notification_agent.run(input_data)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result


@router.post("/send", response_model=NotificationResponse)
async def send_notification(request: SendNotificationRequest):
    """
    Send stock refill notification to customer
    
    - **medicine_name**: Name of the medicine
    - **customer_phone**: (optional) Phone number for SMS
    - **customer_email**: (optional) Email for email notification
    - **customer_id**: (optional) Customer ID
    - **alert_type**: "sms", "email", or "both" (default: "both")
    """
    input_data = {
        "action": "send_notification",
        "medicine_name": request.medicine_name,
        "customer_phone": request.customer_phone,
        "customer_email": request.customer_email,
        "customer_id": request.customer_id,
        "alert_type": request.alert_type
    }
    
    result = await notification_agent.run(input_data)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result


@router.post("/subscribe", response_model=NotificationResponse)
async def subscribe_to_alerts(request: SubscribeToAlertsRequest):
    """
    Subscribe customer to medicine stock refill alerts
    
    - **customer_id**: Customer ID
    - **customer_phone**: (optional) Phone for SMS alerts
    - **customer_email**: (optional) Email for email alerts
    - **medicines**: List of medicine names to subscribe to
    """
    input_data = {
        "action": "subscribe",
        "customer_id": request.customer_id,
        "customer_phone": request.customer_phone,
        "customer_email": request.customer_email,
        "medicines": request.medicines
    }
    
    result = await notification_agent.run(input_data)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result


@router.post("/alerts", response_model=ActiveAlertsResponse)
async def get_active_alerts(request: GetAlertsRequest):
    """
    Get active stock refill alerts
    
    - **customer_id**: (optional) Filter by customer
    - **medicine_name**: (optional) Filter by medicine
    """
    input_data = {
        "action": "get_alerts",
        "customer_id": request.customer_id,
        "medicine_name": request.medicine_name
    }
    
    result = await notification_agent.run(input_data)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result


@router.post("/webhook/from-n8n")
async def receive_n8n_notification(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    Receive notification acknowledgments from n8n workflow
    
    Payload should contain:
    - notification_id: ID of the notification
    - status: Success or failure status
    - n8n_workflow_id: ID of the n8n workflow
    - n8n_execution_id: ID of the n8n execution
    """
    try:
        notification_id = payload.get("notification_id")
        status = payload.get("status", "success")
        
        if notification_id:
            # Mark notification as sent in database
            NotificationService.mark_notification_sent(
                db=db,
                notification_id=notification_id,
                n8n_workflow_id=payload.get("n8n_workflow_id"),
                n8n_execution_id=payload.get("n8n_execution_id"),
                n8n_status=status
            )
        
        return {
            "status": "success",
            "message": "Notification webhook received",
            "action": status
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/templates")
async def get_notification_templates():
    """Get available notification templates"""
    return {
        "templates": {name: {
            "name": template.get("name"),
            "notification_type": template.get("notification_type"),
            "description": f"Template for {template.get('notification_type')}"
        } for name, template in DEFAULT_TEMPLATES.items()}
    }


@router.get("/statistics")
async def get_notification_statistics(db: AsyncSession = Depends(get_db)):
    """Get notification statistics"""
    pending = len(NotificationService.get_pending_notifications(db))
    active_alerts = len(NotificationService.get_active_alerts(db))
    
    return {
        "status": "success",
        "pending_notifications": pending,
        "active_stock_alerts": active_alerts,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def notification_health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "notification",
        "timestamp": datetime.now().isoformat()
    }
