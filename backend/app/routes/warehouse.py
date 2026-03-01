from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.medicine import Medicine
from app.services.webhook_service import trigger_n8n_webhook

router = APIRouter(prefix="/warehouse", tags=["Warehouse"])

DEFAULT_STOCK_THRESHOLD = 20


class StockUpdateRequest(BaseModel):
    medicine_name: str = Field(min_length=1)
    quantity_change: int


def _status_from_stock(stock: int, threshold: int) -> str:
    if stock <= 0:
        return "critical"
    if stock < threshold:
        return "low"
    return "ok"


@router.get("/medicines")
async def get_medicines(db: AsyncSession = Depends(get_db)):
    """Return full medicine catalogue including price and category for the customer shop."""
    result = await db.execute(select(Medicine).order_by(Medicine.name.asc()))
    medicines = result.scalars().all()

    return [
        {
            "id": medicine.id,
            "name": medicine.name,
            "category": medicine.category or "General",
            "price": float(medicine.price or 0),
            "stock": int(medicine.stock or 0),
            "requires_prescription": False,
        }
        for medicine in medicines
    ]


@router.get("/stock")
async def get_warehouse_stock(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Medicine).order_by(Medicine.name.asc()))
    medicines = result.scalars().all()

    return [
        {
            "medicine_name": medicine.name,
            "stock": int(medicine.stock or 0),
            "threshold": DEFAULT_STOCK_THRESHOLD,
            "status": _status_from_stock(int(medicine.stock or 0), DEFAULT_STOCK_THRESHOLD),
        }
        for medicine in medicines
    ]


@router.post("/update-stock")
async def update_warehouse_stock(payload: StockUpdateRequest, db: AsyncSession = Depends(get_db)):
    medicine_query = await db.execute(
        select(Medicine).where(Medicine.name.ilike(f"%{payload.medicine_name.strip()}%"))
    )
    medicine = medicine_query.scalars().first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")

    previous_stock = int(medicine.stock or 0)
    updated_stock = previous_stock + payload.quantity_change
    if updated_stock < 0:
        updated_stock = 0

    medicine.stock = updated_stock
    await db.commit()
    await db.refresh(medicine)

    webhook_triggered = False
    webhook_error = None
    if updated_stock < DEFAULT_STOCK_THRESHOLD:
        try:
            await trigger_n8n_webhook(
                settings.N8N_ORDER_WEBHOOK,
                {
                    "event": "low_stock_alert",
                    "medicine_id": medicine.id,
                    "medicine_name": medicine.name,
                    "stock": updated_stock,
                    "threshold": DEFAULT_STOCK_THRESHOLD,
                },
            )
            webhook_triggered = True
        except Exception as exc:
            webhook_error = str(exc)

    return {
        "medicine_id": medicine.id,
        "medicine_name": medicine.name,
        "previous_stock": previous_stock,
        "updated_stock": updated_stock,
        "threshold": DEFAULT_STOCK_THRESHOLD,
        "status": _status_from_stock(updated_stock, DEFAULT_STOCK_THRESHOLD),
        "webhook_triggered": webhook_triggered,
        "webhook_error": webhook_error,
    }
