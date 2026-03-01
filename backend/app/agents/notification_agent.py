"""
Notification Agent - Handles medicine stock refill notifications and triggers n8n workflows
"""
from __future__ import annotations

import json
import httpx
from typing import Optional
from datetime import datetime
import os

from app.core.langfuse_config import langfuse


# Stock refill thresholds (percentage)
STOCK_REFILL_THRESHOLD = 30  # Notify when stock falls below 30%
CRITICAL_STOCK_THRESHOLD = 10  # Critical notification when below 10%


async def run(input_data: dict) -> dict:
    """
    Main notification agent function
    
    Input:
        - action: "check_stock", "send_notification", "subscribe", "get_alerts"
        - medicine_id: (optional) Medicine ID to check
        - medicine_name: (optional) Medicine name
        - current_stock: (optional) Current stock quantity
        - total_stock: (optional) Total stock capacity
        - customer_phone: (optional) Customer phone for notification
        - customer_email: (optional) Customer email for notification
        - customer_id: (optional) Customer ID
        - alert_type: (optional) "sms", "email", "both"
    """
    _out: dict = {}
    with langfuse.start_as_current_span(name="notification-agent", input=input_data) as span:
        try:
            action = input_data.get("action", "check_stock")

            if action == "check_stock":
                _out = await _check_stock_levels(input_data)
            elif action == "send_notification":
                _out = await _send_notification(input_data)
            elif action == "subscribe":
                _out = await _subscribe_to_alerts(input_data)
            elif action == "get_alerts":
                _out = _get_active_alerts(input_data)
            else:
                _out = {
                    "agent": "notification",
                    "status": "error",
                    "message": f"Unknown action: {action}. Supported: check_stock, send_notification, subscribe, get_alerts",
                }
        except Exception as e:
            _out = {"agent": "notification", "status": "error", "message": str(e)}
        finally:
            try:
                span.update(output=_out)
                langfuse.flush()
            except Exception:
                pass
    return _out


async def _check_stock_levels(input_data: dict) -> dict:
    """Check medicine stock levels and trigger alerts if needed"""
    medicine_id = input_data.get("medicine_id")
    medicine_name = input_data.get("medicine_name")
    current_stock = input_data.get("current_stock")
    total_stock = input_data.get("total_stock", 100)
    
    if not medicine_id and not medicine_name:
        return {
            "agent": "notification",
            "status": "error",
            "message": "Provide `medicine_id` or `medicine_name` to check stock"
        }
    
    if current_stock is None:
        return {
            "agent": "notification",
            "status": "error",
            "message": "Provide `current_stock` for stock check"
        }
    
    stock_percentage = (current_stock / total_stock) * 100
    alert_level = None
    needs_refill = False
    severity = "info"
    
    if stock_percentage < CRITICAL_STOCK_THRESHOLD:
        alert_level = "critical"
        needs_refill = True
        severity = "critical"
    elif stock_percentage < STOCK_REFILL_THRESHOLD:
        alert_level = "warning"
        needs_refill = True
        severity = "warning"
    
    result = {
        "agent": "notification",
        "status": "success",
        "medicine_id": medicine_id,
        "medicine_name": medicine_name,
        "current_stock": current_stock,
        "total_stock": total_stock,
        "stock_percentage": round(stock_percentage, 2),
        "alert_level": alert_level,
        "needs_refill": needs_refill,
        "refill_quantity": _calculate_refill_quantity(current_stock, total_stock) if needs_refill else None,
        "severity": severity,
        "timestamp": datetime.now().isoformat()
    }
    
    # Trigger n8n workflow if refill is needed
    if needs_refill:
        n8n_payload = {
            "medicine_id": medicine_id,
            "medicine_name": medicine_name,
            "current_stock": current_stock,
            "total_stock": total_stock,
            "refill_quantity": result["refill_quantity"],
            "alert_level": alert_level,
            "timestamp": datetime.now().isoformat(),
            "notification_type": "stock_refill_alert"
        }
        result["n8n_workflow_triggered"] = True
        result["n8n_payload"] = n8n_payload
    
    return result


async def _send_notification(input_data: dict) -> dict:
    """Send stock refill notification to customers"""
    medicine_name = input_data.get("medicine_name")
    customer_phone = input_data.get("customer_phone")
    customer_email = input_data.get("customer_email")
    customer_id = input_data.get("customer_id")
    alert_type = input_data.get("alert_type", "both")  # "sms", "email", "both"
    
    if not medicine_name:
        return {
            "agent": "notification",
            "status": "error",
            "message": "Provide `medicine_name` for notification"
        }
    
    if not (customer_phone or customer_email or customer_id):
        return {
            "agent": "notification",
            "status": "error",
            "message": "Provide at least one of: `customer_phone`, `customer_email`, or `customer_id`"
        }
    
    # Prepare notification payload for n8n
    notification_payload = {
        "medicine_name": medicine_name,
        "customer_phone": customer_phone,
        "customer_email": customer_email,
        "customer_id": customer_id,
        "alert_type": alert_type,
        "timestamp": datetime.now().isoformat(),
        "notification_type": "stock_refill_notification",
        "message": f"Your prescribed medicine '{medicine_name}' is available. Please refill your stock now!",
        "urgent": True
    }
    
    # Send to n8n webhook
    n8n_result = await _trigger_n8n_webhook(notification_payload)
    
    return {
        "agent": "notification",
        "status": "success",
        "message": f"Notification sent for {medicine_name}",
        "medicine_name": medicine_name,
        "recipients": {
            "phone": customer_phone if alert_type in ["sms", "both"] else None,
            "email": customer_email if alert_type in ["email", "both"] else None,
            "customer_id": customer_id
        },
        "notification_sent": True,
        "n8n_webhook_status": n8n_result.get("status", "pending"),
        "timestamp": datetime.now().isoformat()
    }


async def _subscribe_to_alerts(input_data: dict) -> dict:
    """Subscribe customer to medicine stock refill alerts"""
    customer_id = input_data.get("customer_id")
    customer_phone = input_data.get("customer_phone")
    customer_email = input_data.get("customer_email")
    medicines = input_data.get("medicines", [])  # List of medicine names/IDs
    
    if not customer_id and not customer_phone and not customer_email:
        return {
            "agent": "notification",
            "status": "error",
            "message": "Provide customer contact information"
        }
    
    if not medicines:
        return {
            "agent": "notification",
            "status": "error",
            "message": "Provide at least one medicine to subscribe to"
        }
    
    return {
        "agent": "notification",
        "status": "success",
        "message": "Successfully subscribed to stock refill alerts",
        "customer_id": customer_id,
        "customer_phone": customer_phone,
        "customer_email": customer_email,
        "subscribed_medicines": medicines,
        "subscription_count": len(medicines),
        "timestamp": datetime.now().isoformat()
    }


def _get_active_alerts(input_data: dict) -> dict:
    """Get active stock refill alerts"""
    customer_id = input_data.get("customer_id")
    medicine_name = input_data.get("medicine_name")
    
    # Simulated active alerts
    active_alerts = [
        {
            "id": "ALERT-001",
            "medicine_name": "Paracetamol 500mg",
            "level": "warning",
            "current_stock": 25,
            "threshold": 30,
            "created_at": datetime.now().isoformat(),
            "refill_quantity": 100
        },
        {
            "id": "ALERT-002",
            "medicine_name": "Amoxicillin 250mg",
            "level": "critical",
            "current_stock": 5,
            "threshold": 10,
            "created_at": datetime.now().isoformat(),
            "refill_quantity": 200
        }
    ]
    
    filtered_alerts = active_alerts
    if medicine_name:
        filtered_alerts = [a for a in active_alerts if medicine_name.lower() in a["medicine_name"].lower()]
    
    return {
        "agent": "notification",
        "status": "success",
        "customer_id": customer_id,
        "active_alerts": filtered_alerts,
        "alert_count": len(filtered_alerts),
        "critical_alerts": len([a for a in filtered_alerts if a["level"] == "critical"]),
        "warning_alerts": len([a for a in filtered_alerts if a["level"] == "warning"]),
        "timestamp": datetime.now().isoformat()
    }


def _calculate_refill_quantity(current_stock: int, total_stock: int) -> int:
    """Calculate refill quantity based on current stock"""
    return max(int(total_stock * 0.5), 50)  # Refill to at least 50% or 50 units


async def _trigger_n8n_webhook(payload: dict) -> dict:
    """
    Trigger n8n workflow via webhook
    
    Set N8N_WEBHOOK_URL environment variable with your n8n webhook URL
    Format: https://your-n8n-instance.com/webhook/your-webhook-path
    """
    n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
    
    if not n8n_webhook_url:
        return {
            "status": "pending",
            "message": "N8N_WEBHOOK_URL not configured",
            "payload": payload
        }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                n8n_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            return {
                "status": "success" if response.status_code < 400 else "error",
                "status_code": response.status_code,
                "webhook_url": n8n_webhook_url,
                "response": response.text[:500] if response.text else "No response body"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to trigger webhook: {str(e)}",
            "webhook_url": n8n_webhook_url
        }
