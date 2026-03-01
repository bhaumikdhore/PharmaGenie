from __future__ import annotations

import logging

import httpx

from app.config import get_settings
from app.db.database import get_db


logger = logging.getLogger(__name__)


async def _resolve_open_alerts(medicine_id: int) -> None:
    db = await get_db()
    await db.execute(
        """
        UPDATE stock_alerts
        SET resolved = TRUE
        WHERE medicine_id = :medicine_id
          AND resolved = FALSE
        """,
        {"medicine_id": medicine_id},
    )


async def check_stock_and_notify(medicine_id: int) -> None:
    db = await get_db()
    settings = get_settings()

    medicine = await db.fetch_one(
        """
        SELECT id, name, stock, threshold
        FROM medicines
        WHERE id = :id
        """,
        {"id": medicine_id},
    )

    if not medicine:
        return

    stock = int(medicine["stock"])
    threshold = int(medicine["threshold"] or 10)

    alert_type: str | None = None
    if stock == 0:
        alert_type = "out_of_stock"
    elif 0 < stock <= threshold:
        alert_type = "low_stock"

    if not alert_type:
        await _resolve_open_alerts(medicine_id)
        return

    existing = await db.fetch_one(
        """
        SELECT id
        FROM stock_alerts
        WHERE medicine_id = :medicine_id
          AND alert_type = :alert_type
          AND resolved = FALSE
        LIMIT 1
        """,
        {"medicine_id": medicine_id, "alert_type": alert_type},
    )

    if existing:
        return

    await db.execute(
        """
        INSERT INTO stock_alerts (medicine_id, alert_type, current_stock)
        VALUES (:medicine_id, :alert_type, :current_stock)
        """,
        {
            "medicine_id": medicine_id,
            "alert_type": alert_type,
            "current_stock": stock,
        },
    )

    payload = {
        "event": "stock_alert",
        "medicine_id": medicine_id,
        "medicine_name": medicine["name"],
        "alert_type": alert_type,
        "current_stock": stock,
        "threshold": threshold,
        "message": (
            f"Stock alert for {medicine['name']}: "
            f"{'out of stock' if alert_type == 'out_of_stock' else 'low stock'} "
            f"(current={stock}, threshold={threshold})"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=settings.webhook_timeout_seconds) as client:
            response = await client.post(settings.n8n_low_stock_webhook, json=payload)
            response.raise_for_status()
    except httpx.HTTPError:
        logger.exception(
            "Failed to send low stock webhook for medicine_id=%s", medicine_id
        )
