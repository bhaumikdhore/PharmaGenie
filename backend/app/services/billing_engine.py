import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order
from app.models.medicine import Medicine

TAX_RATE = 0.05
DISCOUNT_RATE = 0.0

async def generate_invoice_number():
    now = datetime.utcnow()
    return f"PG-{now.year}-{str(uuid.uuid4())[:8]}"

async def create_invoice(order_id: int, db: AsyncSession):
    # Fetch order
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise ValueError("Order not found")

    # Fetch medicine price
    result = await db.execute(select(Medicine).where(Medicine.id == order.medicine_id))
    medicine = result.scalar_one_or_none()

    if not medicine:
        raise ValueError("Medicine not found")

    subtotal = medicine.price * order.quantity
    tax_amount = subtotal * TAX_RATE
    discount_amount = subtotal * DISCOUNT_RATE
    total_amount = subtotal + tax_amount - discount_amount

    invoice_number = await generate_invoice_number()
    invoice = {
        "invoice_number": invoice_number,
        "order_id": order.id,
        "customer_id": order.user_id,
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "discount_amount": discount_amount,
        "total_amount": total_amount,
        "payment_status": "pending",
        "created_at": datetime.utcnow(),
    }
    return invoice, order, medicine
