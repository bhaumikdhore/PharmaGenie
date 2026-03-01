from __future__ import annotations

from fastapi import APIRouter

from app.agents.stock_notification_agent import check_stock_and_notify
from app.db.database import get_db


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/check-all-stock")
async def check_all_stock() -> dict:
    db = await get_db()
    medicines = await db.fetch_all("SELECT id FROM medicines")

    for medicine in medicines:
        await check_stock_and_notify(int(medicine["id"]))

    return {"message": "Stock check completed", "checked_count": len(medicines)}


@router.get("/stock-alerts")
async def get_stock_alerts() -> list[dict]:
    db = await get_db()
    alerts = await db.fetch_all(
        """
        SELECT
            sa.id,
            sa.medicine_id,
            m.name AS medicine_name,
            sa.alert_type,
            sa.current_stock,
            sa.created_at,
            sa.resolved
        FROM stock_alerts sa
        JOIN medicines m ON sa.medicine_id = m.id
        ORDER BY sa.created_at DESC
        """
    )

    return [dict(row) for row in alerts]

