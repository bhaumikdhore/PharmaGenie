import razorpay
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.core.config import settings
from app.services.local_order_fallback import get_fallback_order, update_fallback_order_status, create_fallback_order
from app.routes.simple_billing import generate_invoice_pdf_file
from app.services.webhook_service import trigger_n8n_webhook
from datetime import datetime

router = APIRouter(prefix="/payment", tags=["Payment"])

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


class PaymentCreateRequest(BaseModel):
    order_id: str


class CheckoutItem(BaseModel):
    name: str
    quantity: int
    price: float


class CheckoutSessionRequest(BaseModel):
    items: List[CheckoutItem]
    user_id: str = "demo_user"


class VerifySessionRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    order_ids: List[int]
    items: List[CheckoutItem]
    customer_email: str = "customer@pharmagenie.ai"
    customer_name: str = "PharmaGenie Customer"


def _normalize_order_id(raw_order_id: str | int) -> int:
    text_order_id = str(raw_order_id).strip()
    if text_order_id.isdigit():
        return int(text_order_id)
    if text_order_id.upper().startswith("ORD-") and text_order_id[4:].isdigit():
        return int(text_order_id[4:])
    raise HTTPException(status_code=400, detail="Invalid order_id format")


async def _create_payment_for_order(order_id: str, db: AsyncSession) -> dict:
    normalized_order_id = _normalize_order_id(order_id)
    order_total_amount = None
    try:
        result = await db.execute(
            text("SELECT total_amount FROM orders WHERE id = :order_id"),
            {"order_id": normalized_order_id}
        )
        order = result.fetchone()
        if order:
            order_total_amount = float(order.total_amount) if order.total_amount is not None else None
    except Exception:
        order_total_amount = None

    if order_total_amount is None:
        fallback = get_fallback_order(normalized_order_id)
        if fallback:
            order_total_amount = float(fallback.get("total_amount") or 0)

    if order_total_amount is None:
        raise HTTPException(status_code=404, detail="Order not found")

    amount_paise = int(round(order_total_amount * 100))
    if amount_paise <= 0:
        raise HTTPException(status_code=400, detail="Order amount must be greater than 0")

    try:
        razorpay_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"order_{normalized_order_id}"
        })
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Razorpay order creation failed: {exc}") from exc

    return {
        "razorpay_order_id": razorpay_order["id"],
        "order_id": normalized_order_id,
        "amount": razorpay_order["amount"],
        "currency": "INR"
    }


@router.post("/create/{order_id}")
async def create_payment(order_id: str, db: AsyncSession = Depends(get_db)):
    return await _create_payment_for_order(order_id, db)


@router.post("/create")
async def create_payment_from_body(payload: PaymentCreateRequest, db: AsyncSession = Depends(get_db)):
    """
    Body-based variant of payment creation to match the API contract.
    """
    return await _create_payment_for_order(payload.order_id, db)

@router.post("/verify")
async def verify_payment(data: dict, db: AsyncSession = Depends(get_db)):
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"]
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payment")

    if "order_id" not in data:
        raise HTTPException(status_code=422, detail="order_id is required")
    normalized_order_id = _normalize_order_id(data["order_id"])

    order = None
    try:
        order_result = await db.execute(
            text("SELECT id, medicine_id, quantity FROM orders WHERE id = :order_id"),
            {"order_id": normalized_order_id},
        )
        order = order_result.fetchone()
    except Exception:
        order = None
    stock_deducted = False
    invoice_pdf_url = f"/billing/{normalized_order_id}/pdf"

    if order:
        try:
            await db.execute(
                text("UPDATE orders SET status='paid' WHERE id=:order_id"),
                {"order_id": normalized_order_id}
            )

            await db.execute(
                text(
                    """
                    UPDATE medicines
                    SET stock = CASE
                        WHEN stock - :quantity < 0 THEN 0
                        ELSE stock - :quantity
                    END
                    WHERE id = :medicine_id
                    """
                ),
                {"medicine_id": order.medicine_id, "quantity": int(order.quantity)},
            )
            await db.commit()
            stock_deducted = True
        except Exception:
            stock_deducted = False
        else:
            try:
                # Eagerly generate invoice after successful payment and stock deduction.
                await generate_invoice_pdf_file(normalized_order_id, db)
            except Exception:
                pass
    else:
        fallback = get_fallback_order(normalized_order_id)
        if not fallback:
            raise HTTPException(status_code=404, detail="Order not found")
        update_fallback_order_status(normalized_order_id, "paid")
        stock_deducted = True

    return {
        "status": "payment_verified",
        "order_status": "paid",
        "stock_deducted": stock_deducted,
        "invoice_pdf_url": invoice_pdf_url,
    }


# ─────────────────────────────────────────────
#  Multi-item cart checkout endpoints
# ─────────────────────────────────────────────

@router.post("/checkout-session")
async def create_checkout_session(payload: CheckoutSessionRequest):
    """
    Create orders for all cart items, then create a single Razorpay order
    for the combined total (including 18% GST).
    Returns Razorpay order details + fallback order IDs.
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    subtotal = sum(item.price * item.quantity for item in payload.items)
    tax = round(subtotal * 0.18, 2)
    grand_total = round(subtotal + tax, 2)
    amount_paise = int(round(grand_total * 100))

    if amount_paise <= 0:
        raise HTTPException(status_code=400, detail="Total must be greater than 0")

    # Create a local fallback order per item so we have record IDs
    order_ids: list[int] = []
    for item in payload.items:
        fallback = create_fallback_order(
            order_data={
                "user_id": payload.user_id,
                "medicine_id": 0,
                "quantity": item.quantity,
                "status": "pending_payment",
                "total_amount": round(item.price * item.quantity * 1.18, 2),
                "requires_prescription": False,
            },
            fallback_reason=f"cart_checkout:{item.name}",
        )
        order_ids.append(fallback["id"])

    # Create Razorpay order for the combined total
    try:
        rzp_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"cart_{payload.user_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        })
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Razorpay order creation failed: {exc}") from exc

    return {
        "razorpay_order_id": rzp_order["id"],
        "order_ids": order_ids,
        "amount": rzp_order["amount"],
        "currency": "INR",
        "key_id": settings.RAZORPAY_KEY_ID,
        "subtotal": subtotal,
        "tax": tax,
        "grand_total": grand_total,
    }


@router.post("/verify-session")
async def verify_checkout_session(data: VerifySessionRequest):
    """
    Verify Razorpay payment signature for multi-item cart checkout.
    Marks all fallback orders as paid and returns structured invoice data.
    """
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": data.razorpay_order_id,
            "razorpay_payment_id": data.razorpay_payment_id,
            "razorpay_signature": data.razorpay_signature,
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # Mark all orders as paid
    for oid in data.order_ids:
        update_fallback_order_status(oid, "paid")

    # Build invoice from cart items
    subtotal = round(sum(item.price * item.quantity for item in data.items), 2)
    tax = round(subtotal * 0.18, 2)
    grand_total = round(subtotal + tax, 2)
    invoice_number = f"INV-{data.razorpay_payment_id[-6:].upper()}"

    invoice_items = [
        {
            "name": item.name,
            "quantity": item.quantity,
            "unit_price": item.price,
            "total": round(item.price * item.quantity, 2),
        }
        for item in data.items
    ]

    # Fire n8n order-created webhook (best-effort — email failure must not block payment)
    try:
        asyncio.create_task(trigger_n8n_webhook(settings.N8N_ORDER_WEBHOOK, {
            "event": "order_created",
            "customer_name": data.customer_name,
            "customer_email": data.customer_email,
            "invoice_number": invoice_number,
            "payment_id": data.razorpay_payment_id,
            "order_ids": data.order_ids,
            "items": invoice_items,
            "subtotal": subtotal,
            "tax": tax,
            "grand_total": grand_total,
            "invoice_date": datetime.utcnow().strftime("%d %b %Y"),
            "currency": "INR",
        }))
    except Exception:
        pass  # Never block the payment response for a notification failure

    return {
        "status": "payment_verified",
        "payment_id": data.razorpay_payment_id,
        "razorpay_order_id": data.razorpay_order_id,
        "order_ids": data.order_ids,
        "invoice_number": invoice_number,
        "invoice_date": datetime.utcnow().strftime("%d %b %Y"),
        "items": invoice_items,
        "subtotal": subtotal,
        "tax": tax,
        "tax_rate": 18,
        "grand_total": grand_total,
        "currency": "INR",
    }

