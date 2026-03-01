from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.medicine import Medicine

LOW_STOCK_THRESHOLD = 20


async def warehouse_check(medicine_name: str):
    if not medicine_name:
        return {
            "status": "error",
            "message": "Medicine name not provided."
        }

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Medicine).where(
                Medicine.name.ilike(f"%{medicine_name}%")
            )
        )

        medicine = result.scalars().first()

        if not medicine:
            return {
                "status": "not_found",
                "message": f"{medicine_name} not found in warehouse."
            }

        stock_status = "in_stock"
        alert = None

        if medicine.stock <= 0:
            stock_status = "out_of_stock"
        elif medicine.stock < LOW_STOCK_THRESHOLD:
            stock_status = "low_stock"
            alert = "Reorder recommended."

        return {
            "status": stock_status,
            "medicine_name": medicine.name,
            "stock": medicine.stock,
            "price": float(medicine.price) if medicine.price is not None else 0.0,
            "alert": alert
        }