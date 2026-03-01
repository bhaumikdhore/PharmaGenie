"""
Medicine Refill Notifications Routes
Endpoints for managing medicine refill reminders
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import httpx

from app.db.session import get_db
from app.models.medicine_refill_notification import MedicineRefillNotification
from app.services.medicine_refill_service import MedicineRefillService


router = APIRouter(prefix="/api/refill-notifications", tags=["refill-notifications"])


class RefillTriggerRequest(BaseModel):
    medicine_name: str
    dosage: Optional[str] = None
    customer_id: Optional[str] = "guest"
    rx_id: Optional[str] = None


@router.post("/trigger")
async def trigger_refill_n8n(body: RefillTriggerRequest):
    """Directly trigger n8n refill webhook — no DB required."""
    # Try env var first, fall back to known URL
    webhook_url = os.getenv("N8N_ORDER_WEBHOOK", "").strip()
    if not webhook_url:
        # Load .env explicitly as a fallback
        try:
            from dotenv import load_dotenv as _ld
            import pathlib
            _ld(pathlib.Path(__file__).parent.parent.parent / ".env")
            webhook_url = os.getenv("N8N_ORDER_WEBHOOK", "").strip()
        except Exception:
            pass
    if not webhook_url:
        webhook_url = "https://shiftry.app.n8n.cloud/webhook/order-created"

    payload = {
        "event": "refill_alert",
        "rx_id": body.rx_id or "unknown",
        "medicine_name": body.medicine_name,
        "dosage": body.dosage or "",
        "customer_id": body.customer_id or "guest",
        "triggered_at": datetime.utcnow().isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
        return {
            "status": "success",
            "message": f"Refill alert sent for {body.medicine_name}",
            "webhook_status": resp.status_code,
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"n8n returned {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RefillCreateRequest(BaseModel):
    customer_id: Optional[str] = "guest"
    medicine_name: str
    dosage: Optional[str] = None
    quantity: int = 0
    refill_days: int = 7


@router.post("/create")
async def create_refill_notification(
    body: RefillCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new medicine refill notification"""
    customer_id = body.customer_id
    medicine_name = body.medicine_name
    dosage = body.dosage
    quantity = body.quantity
    refill_days = body.refill_days
    try:
        notification = MedicineRefillService.create_refill_notification(
            db=db,
            customer_id=customer_id,
            medicine_name=medicine_name,
            dosage=dosage,
            quantity=quantity,
            refill_days=refill_days
        )
        
        return {
            "status": "success",
            "notification_id": notification.id,
            "medicine_name": notification.medicine_name,
            "refill_date": notification.refill_date.isoformat(),
            "message": f"Refill reminder created for {medicine_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending")
async def get_pending_notifications(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """Get pending refill notifications for customer"""
    try:
        notifications = MedicineRefillService.get_pending_notifications(
            db=db,
            customer_id=customer_id
        )
        
        return {
            "status": "success",
            "count": len(notifications),
            "notifications": [
                {
                    "id": n.id,
                    "medicine_name": n.medicine_name,
                    "dosage": n.dosage,
                    "quantity": n.quantity,
                    "refill_date": n.refill_date.isoformat(),
                    "message": f"Time to refill {n.medicine_name}"
                }
                for n in notifications
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming")
async def get_upcoming_notifications(
    customer_id: str,
    days_ahead: int = Query(7),
    db: Session = Depends(get_db)
):
    """Get upcoming refill notifications within specified days"""
    try:
        notifications = MedicineRefillService.get_upcoming_notifications(
            db=db,
            customer_id=customer_id,
            days_ahead=days_ahead
        )
        
        return {
            "status": "success",
            "count": len(notifications),
            "notifications": [
                {
                    "id": n.id,
                    "medicine_name": n.medicine_name,
                    "dosage": n.dosage,
                    "refill_date": n.refill_date.isoformat(),
                    "days_until_refill": (n.refill_date - datetime.utcnow()).days,
                    "message": f"Refill {n.medicine_name} in {(n.refill_date - datetime.utcnow()).days} days"
                }
                for n in notifications
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{notification_id}/mark-sent")
async def mark_notification_sent(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Mark notification as sent"""
    try:
        notification = MedicineRefillService.mark_notification_sent(
            db=db,
            notification_id=notification_id
        )
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {
            "status": "success",
            "notification_id": notification.id,
            "message": "Notification marked as sent"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}")
async def deactivate_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate a refill notification"""
    try:
        notification = MedicineRefillService.deactivate_notification(
            db=db,
            notification_id=notification_id
        )
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {
            "status": "success",
            "notification_id": notification.id,
            "message": "Refill notification deactivated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_notifications(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """Get all refill notifications for customer"""
    try:
        notifications = MedicineRefillService.get_all_notifications(
            db=db,
            customer_id=customer_id
        )
        
        return {
            "status": "success",
            "count": len(notifications),
            "notifications": [
                {
                    "id": n.id,
                    "medicine_name": n.medicine_name,
                    "dosage": n.dosage,
                    "refill_date": n.refill_date.isoformat(),
                    "notification_sent": n.notification_sent,
                    "is_active": n.is_active
                }
                for n in notifications
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/trigger-n8n")
async def trigger_n8n_refill_webhook(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Trigger the N8N refill workflow webhook for a specific notification (for testing)"""
    try:
        notification = db.query(MedicineRefillNotification).filter(
            MedicineRefillNotification.id == notification_id
        ).first()
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        webhook_url = os.getenv("N8N_ORDER_WEBHOOK", "")
        if not webhook_url:
            raise HTTPException(status_code=500, detail="N8N_ORDER_WEBHOOK is not configured")

        payload = {
            "event": "refill_reminder_test",
            "notification_id": notification.id,
            "medicine_name": notification.medicine_name,
            "dosage": notification.dosage,
            "quantity": notification.quantity,
            "refill_date": notification.refill_date.isoformat(),
            "customer_id": notification.customer_id,
            "triggered_at": datetime.utcnow().isoformat(),
        }

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()

        return {
            "status": "success",
            "message": f"N8N webhook triggered for {notification.medicine_name}",
            "webhook_status": resp.status_code,
        }
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"N8N webhook returned {e.response.status_code}: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
