from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.agents.stock_notification_agent import check_stock_and_notify
from app.db.database import get_db


router = APIRouter(prefix="/orders", tags=["Orders"])


class OrderCreateRequest(BaseModel):
    medicine_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


@router.post("")
async def create_order(payload: OrderCreateRequest) -> dict:
    db = await get_db()

    transaction = await db.transaction()
    try:
        medicine = await db.fetch_one(
            """
            SELECT id, name, stock, threshold
            FROM medicines
            WHERE id = :id
            FOR UPDATE
            """,
            {"id": payload.medicine_id},
        )

        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found"
            )

        if medicine["stock"] < payload.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock"
            )

        await db.execute(
            """
            INSERT INTO orders (medicine_id, quantity)
            VALUES (:medicine_id, :quantity)
            """,
            {"medicine_id": payload.medicine_id, "quantity": payload.quantity},
        )

        updated_stock = medicine["stock"] - payload.quantity
        await db.execute(
            """
            UPDATE medicines
            SET stock = :stock
            WHERE id = :id
            """,
            {"stock": updated_stock, "id": payload.medicine_id},
        )

        await transaction.commit()
    except Exception:
        await transaction.rollback()
        raise

    await check_stock_and_notify(payload.medicine_id)

    return {
        "message": "Order created",
        "medicine_id": payload.medicine_id,
        "remaining_stock": updated_stock,
    }

