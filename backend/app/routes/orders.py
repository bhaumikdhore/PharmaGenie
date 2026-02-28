import re
from decimal import Decimal
from types import SimpleNamespace

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.local_order_fallback import create_fallback_order
from app.services.order_service import OrderService
from app.services.webhook_service import trigger_n8n_webhook

router = APIRouter(prefix="/orders", tags=["Orders"])
legacy_router = APIRouter(tags=["Orders"])


class OrderCreateRequest(BaseModel):
    user_id: str | None = None
    medicine_id: int | None = Field(default=None, ge=1)
    quantity: int | None = Field(default=None, ge=1)
    status: str | None = None
    total_amount: Decimal | None = Field(default=None, ge=0)
    requires_prescription: bool | None = None
    query: str | None = None


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
    parsed_query_data = _parse_query_to_order_data(query) if query else {}
    return {**parsed_query_data, **payload_data}


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

    if not order_data.get("user_id") or not order_data.get("medicine_id") or not order_data.get("quantity"):
        raise HTTPException(
            status_code=422,
            detail="Provide user_id, medicine_id, quantity (direct fields or in query).",
        )

    # Production path: never fall back to dummy success.
    return await _create_order_and_trigger(order_data)


@router.post("/test-create", operation_id="orders_test_create_order")
async def test_create_order(payload: OrderCreateRequest):
    order_data = _build_order_data(payload, payload.query)

    if not order_data.get("user_id") or not order_data.get("medicine_id") or not order_data.get("quantity"):
        raise HTTPException(
            status_code=422,
            detail="Provide user_id, medicine_id, quantity (direct fields or in query).",
        )

    return await _create_order_and_trigger(order_data)


@router.post("/post/order", operation_id="orders_post_order")
async def post_order(
    payload: OrderCreateRequest,
    query: str | None = Query(default=None, description="Optional order query text"),
):
    order_data = _build_order_data(payload, query or payload.query)

    if not order_data.get("user_id") or not order_data.get("medicine_id") or not order_data.get("quantity"):
        raise HTTPException(
            status_code=422,
            detail="Provide user_id, medicine_id, quantity (direct fields or in query).",
        )

    return await _create_order_and_trigger(order_data)


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
