import razorpay
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.core.config import settings
from app.services.local_order_fallback import get_fallback_order

router = APIRouter(prefix="/payment", tags=["Payment"])

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

@router.post("/create/{order_id}")
async def create_payment(order_id: int, db: AsyncSession = Depends(get_db)):
    order_total_amount = None
    try:
        result = await db.execute(
            text("SELECT total_amount FROM orders WHERE id = :order_id"),
            {"order_id": order_id}
        )
        order = result.fetchone()
        if order:
            order_total_amount = float(order.total_amount) if order.total_amount is not None else None
    except Exception:
        order_total_amount = None

    if order_total_amount is None:
        fallback = get_fallback_order(order_id)
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
            "receipt": f"order_{order_id}"
        })
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Razorpay order creation failed: {exc}") from exc

    return {
        "razorpay_order_id": razorpay_order["id"],
        "amount": razorpay_order["amount"],
        "currency": "INR"
    }

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

    order_result = await db.execute(
        text("SELECT id, medicine_id, quantity FROM orders WHERE id = :order_id"),
        {"order_id": data["order_id"]},
    )
    order = order_result.fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    await db.execute(
        text("UPDATE orders SET status='paid' WHERE id=:order_id"),
        {"order_id": data["order_id"]}
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

    return {"status": "payment_verified", "stock_deducted": True}
