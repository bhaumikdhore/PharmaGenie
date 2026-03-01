"""
Delivery Agent - Tracks delivery location and shipping process stage by order
"""
from __future__ import annotations

import json
from typing import Optional
from datetime import datetime, timedelta
import random

from app.core.langfuse_config import langfuse


# Simulated delivery tracking data
DELIVERY_STAGES = {
    "pending": {"label": "Order Pending", "description": "Order placed, awaiting dispatch"},
    "confirmed": {"label": "Order Confirmed", "description": "Order confirmed by pharmacy"},
    "packed": {"label": "Packed", "description": "Order packed and ready for dispatch"},
    "dispatched": {"label": "Dispatched", "description": "Order dispatched from warehouse"},
    "in_transit": {"label": "In Transit", "description": "Order on the way to delivery location"},
    "out_for_delivery": {"label": "Out for Delivery", "description": "Order out for delivery today"},
    "delivered": {"label": "Delivered", "description": "Order successfully delivered"},
    "failed": {"label": "Failed", "description": "Delivery failed, will retry"},
    "cancelled": {"label": "Cancelled", "description": "Order cancelled"},
}


def _generate_tracking_number(order_id: str) -> str:
    """Generate a unique tracking number"""
    return f"TRK-{order_id}-{int(datetime.now().timestamp())}"


def _simulate_location_data(current_stage: str) -> dict:
    """Generate simulated location data based on stage"""
    locations = {
        "pending": {"lat": 0, "lng": 0, "address": "Processing at warehouse"},
        "confirmed": {"lat": 19.0760, "lng": 72.8777, "address": "Mumbai Pharmacy Center"},
        "packed": {"lat": 19.0760, "lng": 72.8777, "address": "Mumbai Pharmacy Center"},
        "dispatched": {"lat": 19.0760, "lng": 72.8777, "address": "Distribution Center, Mumbai"},
        "in_transit": {"lat": 19.1136 + random.uniform(-0.05, 0.05), "lng": 72.8697 + random.uniform(-0.05, 0.05), "address": "In Transit"},
        "out_for_delivery": {"lat": 19.0645 + random.uniform(-0.02, 0.02), "lng": 72.8424 + random.uniform(-0.02, 0.02), "address": "Out for Delivery"},
        "delivered": {"lat": 19.0645, "lng": 72.8424, "address": "Delivered at Customer Location"},
    }
    return locations.get(current_stage, {"lat": 0, "lng": 0, "address": "Unknown"})


def _estimate_delivery_time(current_stage: str) -> Optional[str]:
    """Estimate delivery time based on current stage"""
    if current_stage in ["delivered", "cancelled"]:
        return None
    
    hours_remaining = {
        "pending": 72,
        "confirmed": 60,
        "packed": 48,
        "dispatched": 24,
        "in_transit": 12,
        "out_for_delivery": 2,
        "failed": 48,
    }
    
    hours = hours_remaining.get(current_stage, 72)
    estimated_time = datetime.now() + timedelta(hours=hours)
    return estimated_time.isoformat()


async def run(input_data: dict) -> dict:
    """
    Main delivery agent function
    
    Input:
        - order_id: ID of the order to track
        - action: "track" (default), "update_status", "get_history"
        - new_stage: (optional) New delivery stage for update_status
        - customer_phone: (optional) Customer phone for update notifications
    """
    _out: dict = {}
    with langfuse.start_as_current_span(name="delivery-agent", input=input_data) as span:
        try:
            action = input_data.get("action", "track")
            order_id = input_data.get("order_id")

            if not order_id:
                _out = {
                    "agent": "delivery",
                    "status": "error",
                    "message": "Provide `order_id` to track delivery",
                }
            elif action == "track":
                _out = _track_delivery(order_id, input_data)
            elif action == "update_status":
                _out = _update_delivery_status(order_id, input_data)
            elif action == "get_history":
                _out = _get_delivery_history(order_id)
            else:
                _out = {
                    "agent": "delivery",
                    "status": "error",
                    "message": f"Unknown action: {action}. Supported: track, update_status, get_history",
                }
        except Exception as e:
            _out = {"agent": "delivery", "status": "error", "message": str(e)}
        finally:
            try:
                span.update(output=_out)
                langfuse.flush()
            except Exception:
                pass
    return _out


def _track_delivery(order_id: str, input_data: dict) -> dict:
    """Track current delivery status of an order"""
    # Simulate current stage based on order_id hash
    stage_list = list(DELIVERY_STAGES.keys())[:-1]  # Exclude cancelled
    current_stage = stage_list[hash(order_id) % len(stage_list)]
    
    tracking_number = _generate_tracking_number(order_id)
    location_data = _simulate_location_data(current_stage)
    estimated_delivery = _estimate_delivery_time(current_stage)
    
    return {
        "agent": "delivery",
        "status": "success",
        "order_id": order_id,
        "tracking_number": tracking_number,
        "current_stage": current_stage,
        "stage_info": DELIVERY_STAGES[current_stage],
        "location": location_data,
        "estimated_delivery": estimated_delivery,
        "timestamp": datetime.now().isoformat(),
        "last_update": f"{current_stage} - {datetime.now().isoformat()}"
    }


def _update_delivery_status(order_id: str, input_data: dict) -> dict:
    """Update delivery status to next stage"""
    new_stage = input_data.get("new_stage")
    customer_phone = input_data.get("customer_phone")
    
    if not new_stage:
        return {
            "agent": "delivery",
            "status": "error",
            "message": "Provide `new_stage` for status update"
        }
    
    if new_stage not in DELIVERY_STAGES:
        return {
            "agent": "delivery",
            "status": "error",
            "message": f"Invalid stage: {new_stage}. Valid stages: {list(DELIVERY_STAGES.keys())}"
        }
    
    # Prepare notification payload for n8n webhook
    notification_payload = {
        "order_id": order_id,
        "new_stage": new_stage,
        "stage_info": DELIVERY_STAGES[new_stage],
        "customer_phone": customer_phone,
        "timestamp": datetime.now().isoformat(),
        "notification_type": "delivery_status_update"
    }
    
    return {
        "agent": "delivery",
        "status": "success",
        "order_id": order_id,
        "new_stage": new_stage,
        "stage_info": DELIVERY_STAGES[new_stage],
        "message": f"Delivery status updated to {new_stage}",
        "notification_triggered": True,
        "notification_payload": notification_payload,
        "timestamp": datetime.now().isoformat()
    }


def _get_delivery_history(order_id: str) -> dict:
    """Get delivery history for an order"""
    # Simulate delivery history
    history = [
        {
            "stage": "pending",
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
            "description": "Order placed"
        },
        {
            "stage": "confirmed",
            "timestamp": (datetime.now() - timedelta(days=2, hours=1)).isoformat(),
            "description": "Order confirmed by pharmacy"
        },
        {
            "stage": "packed",
            "timestamp": (datetime.now() - timedelta(days=1, hours=20)).isoformat(),
            "description": "Order packed and ready"
        },
        {
            "stage": "dispatched",
            "timestamp": (datetime.now() - timedelta(days=1, hours=12)).isoformat(),
            "description": "Order dispatched"
        },
        {
            "stage": "in_transit",
            "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(),
            "description": "Order in transit"
        },
    ]
    
    return {
        "agent": "delivery",
        "status": "success",
        "order_id": order_id,
        "history": history,
        "total_events": len(history),
        "timestamp": datetime.now().isoformat()
    }
