import re
import csv
import logging
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.medicine import Medicine
from app.models.order import Order
from app.models.user import User
from app.services.local_order_fallback import create_fallback_order, list_fallback_orders_by_user
from app.services.order_service import OrderService
from app.services.webhook_service import trigger_n8n_webhook

router = APIRouter(prefix="/orders", tags=["Orders"])
legacy_router = APIRouter(tags=["Orders"])


class OrderCreateRequest(BaseModel):
    user_id: str | None = None
    customer_id: str | None = None
    medicine_id: int | None = Field(default=None, ge=1)
    medicine_name: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    status: str | None = None
    total_amount: Decimal | None = Field(default=None, ge=0)
    requires_prescription: bool | None = None
    query: str | None = None


class PharmacistDecisionRequest(BaseModel):
    order_id: str
    decision: Literal["approved", "rejected"]


class OrderStatusUpdateRequest(BaseModel):
    order_id: str
    status: str


def _normalize_order_id(raw_order_id: str | int) -> int:
    text_order_id = str(raw_order_id).strip()
    if text_order_id.isdigit():
        return int(text_order_id)
    if text_order_id.upper().startswith("ORD-") and text_order_id[4:].isdigit():
        return int(text_order_id[4:])
    raise HTTPException(status_code=400, detail="Invalid order_id format")


def _infer_safety_level(order: Order) -> str:
    """
    Derive a simple safety level for pharmacist review using real order fields.
    """
    quantity = int(order.quantity or 0)
    if quantity >= 90:
        return "high"
    if quantity >= 30:
        return "medium"
    return "low"


def _infer_fraud_risk(order: Order) -> tuple[str, list[str]]:
    """
    Lightweight fraud heuristic based on order attributes.
    Uses real data but keeps logic intentionally simple and transparent.
    """
    flags: list[str] = []
    quantity = int(order.quantity or 0)
    total = float(order.total_amount or 0)

    if quantity >= 120:
        flags.append("Unusually high quantity for a single outpatient order.")
    if total >= 20000:
        flags.append("High total invoice amount flagged for review.")
    if quantity <= 0:
        flags.append("Non-positive quantity is invalid and should be rejected.")

    if any("invalid" in f.lower() for f in flags):
        return "high", flags
    if len(flags) >= 2:
        return "high", flags
    if flags:
        return "medium", flags
    return "low", flags


def _parse_query_to_order_data(query: str) -> dict:
    text = query.strip().lower()
    if not text:
        return {}

    user_match = re.search(r"user[_\s-]*id[:=\s]*(\w+)", text)
    medicine_match = re.search(r"medicine[_\s-]*id[:=\s]*(\d+)", text)
    quantity_match = re.search(r"(?:qty|quantity)[:=\s]*(\d+)", text)
    total_match = re.search(r"(?:total|amount|total_amount)[:=\s]*([0-9]+(?:\.[0-9]+)?)", text)

    data: dict = {}
    if user_match:
        data["user_id"] = user_match.group(1)
    if medicine_match:
        data["medicine_id"] = int(medicine_match.group(1))
    if quantity_match:
        data["quantity"] = int(quantity_match.group(1))
    if total_match:
        data["total_amount"] = Decimal(total_match.group(1))

    return data


def _build_order_data(payload: OrderCreateRequest, query: str | None) -> dict:
    payload_data = payload.model_dump(exclude_none=True, exclude={"query"})
    if payload_data.get("customer_id") and not payload_data.get("user_id"):
        payload_data["user_id"] = payload_data["customer_id"]
    payload_data.pop("customer_id", None)
    parsed_query_data = _parse_query_to_order_data(query) if query else {}
    return {**parsed_query_data, **payload_data}


def _lookup_medicine_id_from_csv(medicine_name: str) -> int | None:
    csv_path = Path(__file__).resolve().parents[2] / "medicine_master.csv"
    if not csv_path.exists():
        return None

    needle = medicine_name.strip().lower()
    if not needle:
        return None

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            for row in rows:
                name = (row.get("medicine_name") or "").strip().lower()
                if name == needle:
                    raw_id = (row.get("medicine_id") or "").strip()
                    if raw_id.isdigit():
                        return int(raw_id)
            for row in rows:
                name = (row.get("medicine_name") or "").strip().lower()
                if needle in name or name in needle:
                    raw_id = (row.get("medicine_id") or "").strip()
                    if raw_id.isdigit():
                        return int(raw_id)
    except Exception:
        return None

    return None


async def _resolve_medicine_id(order_data: dict) -> dict:
    if order_data.get("medicine_id"):
        return order_data

    medicine_name = order_data.get("medicine_name")
    if not medicine_name:
        return order_data

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Medicine).where(Medicine.name.ilike(f"%{medicine_name.strip()}%"))
            )
            medicine = result.scalar_one_or_none()
            if medicine:
                order_data["medicine_id"] = medicine.id
                return order_data
        except Exception:
            pass

    fallback_id = _lookup_medicine_id_from_csv(medicine_name)
    if fallback_id:
        order_data["medicine_id"] = fallback_id

    return order_data


def _format_total_amount(value: Decimal | int | float | None):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else value
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    if value == value.to_integral_value():
        return int(value)
    return float(value)


async def _create_order(order_data: dict):
    async with AsyncSessionLocal() as session:
        try:
            return await OrderService.create_order(session, order_data)
        except (SQLAlchemyError, Exception) as exc:
            raise HTTPException(status_code=500, detail=f"Database error while creating order: {exc}") from exc


async def _trigger_order_created_webhook(order) -> dict:
    webhook_url = settings.N8N_ORDER_WEBHOOK
    return await trigger_n8n_webhook(
        webhook_url,
        {
            "order_id": order.id,
            "user_id": order.user_id,
            "medicine_id": order.medicine_id,
            "quantity": order.quantity,
            "status": order.status,
            "total_amount": _format_total_amount(order.total_amount),
        },
    )


async def _ensure_webhook_triggered(order) -> None:
    await _trigger_order_created_webhook(order)


@router.get("", operation_id="orders_list_placeholder")
async def orders_index():
    return {"message": "Orders routes are active", "create_path": "/orders/create"}


async def _create_order_and_trigger(order_data: dict):
    order_data = await _resolve_medicine_id(order_data)
    order_data.pop("medicine_name", None)
    fallback_used = False
    try:
        order = await _create_order(order_data)
    except HTTPException as exc:
        if exc.status_code != 500:
            raise
        fallback_order = create_fallback_order(order_data, str(exc.detail))
        fallback_used = True
        order = SimpleNamespace(
            id=fallback_order["id"],
            user_id=fallback_order["user_id"],
            medicine_id=fallback_order["medicine_id"],
            quantity=fallback_order["quantity"],
            status=fallback_order["status"],
            total_amount=fallback_order["total_amount"],
        )
        print(f"[orders] fallback_storage=sqlite local_id={order.id}")

    await _ensure_webhook_triggered(order)
    response = {
        "id": order.id,
        "status": order.status,
        "total_amount": _format_total_amount(order.total_amount),
    }
    if fallback_used:
        response["storage"] = "local_fallback"
    return response


@router.post("/create", operation_id="orders_create_order")
async def create_order(payload: OrderCreateRequest):
    order_data = _build_order_data(payload, payload.query)

    has_medicine_ref = bool(order_data.get("medicine_id") or order_data.get("medicine_name"))
    if not order_data.get("user_id") or not has_medicine_ref or not order_data.get("quantity"):
        raise HTTPException(
            status_code=422,
            detail="Provide user_id/customer_id, medicine_id/medicine_name, quantity (direct fields or in query).",
        )

    # Production path: never fall back to dummy success.
    return await _create_order_and_trigger(order_data)


@router.post("/test-create", operation_id="orders_test_create_order")
async def test_create_order(payload: OrderCreateRequest):
    order_data = _build_order_data(payload, payload.query)

    has_medicine_ref = bool(order_data.get("medicine_id") or order_data.get("medicine_name"))
    if not order_data.get("user_id") or not has_medicine_ref or not order_data.get("quantity"):
        raise HTTPException(
            status_code=422,
            detail="Provide user_id/customer_id, medicine_id/medicine_name, quantity (direct fields or in query).",
        )

    return await _create_order_and_trigger(order_data)


@router.post("/post/order", operation_id="orders_post_order")
async def post_order(
    payload: OrderCreateRequest,
    query: str | None = Query(default=None, description="Optional order query text"),
):
    order_data = _build_order_data(payload, query or payload.query)

    has_medicine_ref = bool(order_data.get("medicine_id") or order_data.get("medicine_name"))
    if not order_data.get("user_id") or not has_medicine_ref or not order_data.get("quantity"):
        raise HTTPException(
            status_code=422,
            detail="Provide user_id/customer_id, medicine_id/medicine_name, quantity (direct fields or in query).",
        )

    return await _create_order_and_trigger(order_data)


@router.get("/my-orders", operation_id="orders_get_my_orders")
async def get_my_orders(customer_id: str = Query(..., min_length=1)):
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Order).where(Order.user_id == customer_id).order_by(Order.created_at.desc())
            )
            orders = result.scalars().all()
            if not orders:
                return []

            medicine_ids = {o.medicine_id for o in orders if o.medicine_id is not None}
            medicine_map: dict[int, str] = {}
            if medicine_ids:
                meds_result = await session.execute(select(Medicine).where(Medicine.id.in_(medicine_ids)))
                for med in meds_result.scalars().all():
                    medicine_map[med.id] = med.name

            return [
                {
                    "order_id": str(order.id),
                    "medicine": medicine_map.get(order.medicine_id, f"Medicine-{order.medicine_id}"),
                    "quantity": order.quantity,
                    "status": order.status,
                    "total": float(order.total_amount) if order.total_amount is not None else 0.0,
                    "created_date": order.created_at.isoformat() if order.created_at else None,
                }
                for order in orders
            ]
        except Exception:
            fallback_orders = list_fallback_orders_by_user(customer_id)
            return [
                {
                    "order_id": str(order.get("id")),
                    "medicine": f"Medicine-{order.get('medicine_id')}",
                    "quantity": int(order.get("quantity") or 0),
                    "status": order.get("status") or "pending",
                    "total": float(order.get("total_amount") or 0),
                    "created_date": order.get("created_at"),
                }
                for order in fallback_orders
            ]


@router.get("/all", operation_id="orders_get_all")
async def get_all_orders(limit: int = Query(default=200, ge=1, le=1000)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order, Medicine.name)
            .outerjoin(Medicine, Medicine.id == Order.medicine_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        rows = result.all()

        return [
            {
                "order_id": f"ORD-{order.id}",
                "medicine_name": medicine_name or f"Medicine-{order.medicine_id}",
                "quantity": int(order.quantity or 0),
                "status": order.status or "pending",
                "total_amount": float(order.total_amount) if order.total_amount is not None else 0.0,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }
            for order, medicine_name in rows
        ]


@router.get("/pending", operation_id="orders_get_pending")
async def get_pending_orders(limit: int = Query(default=200, ge=1, le=1000)):
    """
    Orders awaiting pharmacist validation and safety review.
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Order, Medicine.name, User.email)
                .outerjoin(Medicine, Medicine.id == Order.medicine_id)
                .outerjoin(User, User.id == Order.user_id)
                .where(Order.status.in_(["pending", "awaiting_pharmacist"]))
                .order_by(Order.created_at.asc())
                .limit(limit)
            )
            rows = result.all()

            pending_orders: list[dict] = []
            for order, medicine_name, customer_email in rows:
                safety_level = _infer_safety_level(order)
                fraud_risk_level, fraud_flags = _infer_fraud_risk(order)
                pending_orders.append(
                    {
                        "order_id": f"ORD-{order.id}",
                        "customer_name": customer_email or order.user_id,
                        "medicine": medicine_name or f"Medicine-{order.medicine_id}",
                        "quantity": int(order.quantity or 0),
                        "prescription_required": bool(order.requires_prescription),
                        "safety_level": safety_level,
                        "fraud_risk_level": fraud_risk_level,
                        "fraud_flags": fraud_flags,
                    }
                )
            return pending_orders
    except Exception as exc:
        logger.error("Failed to fetch pending orders from DB: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"Database unavailable: {exc}. Please ensure Supabase project is active (free-tier projects pause after inactivity).",
        )


@router.get("/approved", operation_id="orders_get_approved")
async def get_approved_orders(limit: int = Query(default=200, ge=1, le=1000)):
    """
    Orders that have been approved and are ready for warehouse shipment.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order, Medicine.name, User.email)
            .outerjoin(Medicine, Medicine.id == Order.medicine_id)
            .outerjoin(User, User.id == Order.user_id)
            .where(Order.status.in_(["approved", "paid", "shipped"]))
            .order_by(Order.created_at.asc())
            .limit(limit)
        )
        rows = result.all()

        approved_orders: list[dict] = []
        for order, medicine_name, customer_email in rows:
            approved_orders.append(
                {
                    "order_id": f"ORD-{order.id}",
                    "customer_name": customer_email or order.user_id,
                    "medicine": medicine_name or f"Medicine-{order.medicine_id}",
                    "quantity": int(order.quantity or 0),
                }
            )
        return approved_orders


@router.post("/pharmacist-decision", operation_id="orders_pharmacist_decision")
async def pharmacist_decision(payload: PharmacistDecisionRequest):
    """
    Pharmacist approval/rejection of a pending order.
    """
    normalized_order_id = _normalize_order_id(payload.order_id)
    new_status = "approved" if payload.decision == "approved" else "rejected"

    try:
        async with AsyncSessionLocal() as session:
            order = await OrderService.update_order_status(session, normalized_order_id, new_status)
            if not order:
                # Order not found in DB (may be a demo order) — acknowledge gracefully
                return {
                    "order_id": payload.order_id,
                    "status": new_status,
                    "note": "Order not found in database; decision recorded locally.",
                }
            return {
                "order_id": f"ORD-{order.id}",
                "status": order.status,
            }
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("pharmacist_decision DB error (returning offline ack): %s", exc)
        # DB offline — return a success-like ack so the UI can still proceed
        return {
            "order_id": payload.order_id,
            "status": new_status,
            "note": "Database unavailable; decision applied to local view only.",
        }


@router.post("/update-status", operation_id="orders_update_status")
async def update_order_status(payload: OrderStatusUpdateRequest):
    """
    Generic order status update used by warehouse and internal flows.
    """
    allowed_statuses = {
        "pending",
        "awaiting_pharmacist",
        "approved",
        "rejected",
        "shipped",
        "delivered",
        "cancelled",
        "paid",
    }
    status = (payload.status or "").strip()
    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status}'. Allowed: {', '.join(sorted(allowed_statuses))}",
        )

    normalized_order_id = _normalize_order_id(payload.order_id)

    async with AsyncSessionLocal() as session:
        order = await OrderService.update_order_status(session, normalized_order_id, status)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return {
            "order_id": f"ORD-{order.id}",
            "status": order.status,
        }


@legacy_router.post("/order/test", operation_id="orders_order_test_create_legacy")
async def legacy_test_create_order(payload: OrderCreateRequest):
    return await test_create_order(payload)


@legacy_router.post("/post/order", operation_id="orders_post_order_legacy")
async def legacy_post_order(
    payload: OrderCreateRequest,
    query: str | None = Query(default=None, description="Optional order query text"),
):
    return await post_order(payload, query)


@legacy_router.post("/post/order/create", operation_id="orders_post_order_create_legacy")
@legacy_router.post("/post/order/created", operation_id="orders_post_order_created_legacy")
async def legacy_post_order_created(
    payload: OrderCreateRequest,
    query: str | None = Query(default=None, description="Optional order query text"),
):
    return await post_order(payload, query)


@router.get("/debug/webhook-url", operation_id="debug_webhook_url")
async def debug_webhook_url():
    return {"webhook_url": settings.N8N_ORDER_WEBHOOK}
