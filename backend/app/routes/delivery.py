"""
Delivery routes - API endpoints for delivery tracking
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.agents import delivery_agent
from app.db.session import get_db
from app.services.delivery_service import DeliveryService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/delivery", tags=["Delivery"])


# Pydantic models for request/response
class DeliveryTrackRequest(BaseModel):
    action: str = "track"  # track, update_status, get_history
    order_id: Optional[str] = None
    new_stage: Optional[str] = None
    customer_phone: Optional[str] = None
    tracking_number: Optional[str] = None


class LocationData(BaseModel):
    latitude: float
    longitude: float
    address: str


class DeliveryResponse(BaseModel):
    agent: str
    status: str
    order_id: Optional[str] = None
    tracking_number: Optional[str] = None
    current_stage: Optional[str] = None
    stage_info: Optional[dict] = None
    estimated_delivery: Optional[str] = None
    message: Optional[str] = None


class DeliveryHistoryItem(BaseModel):
    stage: str
    timestamp: str
    description: str


class DeliveryHistoryResponse(BaseModel):
    agent: str
    status: str
    order_id: str
    history: List[DeliveryHistoryItem]
    total_events: int


# get_db is imported from app.db.session


@router.post("/track", response_model=DeliveryResponse)
async def track_delivery(request: DeliveryTrackRequest):
    """
    Track delivery status of an order
    
    - **order_id**: The order ID to track
    - **tracking_number**: (optional) The tracking number
    """
    if not request.order_id and not request.tracking_number:
        raise HTTPException(status_code=400, detail="Provide order_id or tracking_number")
    
    input_data = {
        "action": "track",
        "order_id": request.order_id or request.tracking_number,
    }
    
    result = await delivery_agent.run(input_data)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result


@router.post("/update-status", response_model=DeliveryResponse)
async def update_delivery_status(request: DeliveryTrackRequest):
    """
    Update delivery status to next stage
    
    - **order_id**: The order ID
    - **new_stage**: New delivery stage (confirmed, packed, dispatched, in_transit, out_for_delivery, delivered, failed)
    - **customer_phone**: (optional) Phone number for notification
    """
    if not request.order_id:
        raise HTTPException(status_code=400, detail="Provide order_id")
    
    if not request.new_stage:
        raise HTTPException(status_code=400, detail="Provide new_stage")
    
    input_data = {
        "action": "update_status",
        "order_id": request.order_id,
        "new_stage": request.new_stage,
        "customer_phone": request.customer_phone
    }
    
    result = await delivery_agent.run(input_data)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result


@router.post("/history", response_model=DeliveryHistoryResponse)
async def get_delivery_history(request: DeliveryTrackRequest):
    """
    Get delivery history for an order
    
    - **order_id**: The order ID
    """
    if not request.order_id:
        raise HTTPException(status_code=400, detail="Provide order_id")
    
    input_data = {
        "action": "get_history",
        "order_id": request.order_id
    }
    
    result = await delivery_agent.run(input_data)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result


@router.get("/stages")
async def get_delivery_stages():
    """Get available delivery stages"""
    stages = {
        "pending": "Order placed, awaiting dispatch",
        "confirmed": "Order confirmed by pharmacy",
        "packed": "Order packed and ready for dispatch",
        "dispatched": "Order dispatched from warehouse",
        "in_transit": "Order on the way to delivery location",
        "out_for_delivery": "Order out for delivery today",
        "delivered": "Order successfully delivered",
        "failed": "Delivery failed, will retry"
    }
    return {"stages": stages}


@router.post("/webhook/from-n8n")
async def receive_n8n_delivery_update(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    Receive delivery updates from n8n workflow
    
    This webhook is called by n8n to update delivery status
    Payload should contain:
    - order_id: Order ID
    - new_stage: New delivery stage
    - location: {latitude, longitude, address}
    - notes: Additional notes
    """
    try:
        order_id = payload.get("order_id")
        new_stage = payload.get("new_stage")
        location = payload.get("location")
        notes = payload.get("notes")
        
        if not order_id or not new_stage:
            return {
                "status": "error",
                "message": "Provide order_id and new_stage"
            }
        
        # Get delivery from database
        delivery = DeliveryService.get_delivery_by_order(db, order_id)
        if not delivery:
            # Create new delivery record if doesn't exist
            delivery = DeliveryService.create_delivery(
                db=db,
                order_id=order_id,
                tracking_number=f"TRK-{order_id}",
                customer_id=payload.get("customer_id", order_id),
                stage=new_stage
            )
        else:
            # Update existing delivery
            DeliveryService.update_delivery_stage(
                db=db,
                delivery_id=delivery.id,
                new_stage=new_stage,
                location=location,
                notes=notes
            )
        
        return {
            "status": "success",
            "message": f"Delivery updated to {new_stage}",
            "order_id": order_id,
            "delivery_id": delivery.id
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/health")
async def delivery_health():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "delivery", "timestamp": datetime.now().isoformat()}
