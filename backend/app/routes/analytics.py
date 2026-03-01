from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/revenue")
async def get_revenue_analytics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text(
            """
            SELECT
                COALESCE(SUM(
                    CASE
                        WHEN DATE(o.created_at) = CURRENT_DATE THEN COALESCE(o.total_amount, 0)
                        ELSE 0
                    END
                ), 0) AS daily_revenue,
                COALESCE(SUM(
                    CASE
                        WHEN o.created_at >= DATE_TRUNC('month', CURRENT_DATE) THEN COALESCE(o.total_amount, 0)
                        ELSE 0
                    END
                ), 0) AS monthly_revenue,
                COUNT(*) AS total_orders
            FROM public.orders o
            """
        )
    )
    row = result.mappings().first() or {}
    return {
        "daily_revenue": float(row.get("daily_revenue") or 0),
        "monthly_revenue": float(row.get("monthly_revenue") or 0),
        "total_orders": int(row.get("total_orders") or 0),
    }


@router.get("/demand-forecast")
async def get_demand_forecast(
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text(
            """
            SELECT
                m.name AS medicine_name,
                COALESCE(SUM(
                    CASE
                        WHEN o.created_at >= NOW() - INTERVAL '7 days' THEN COALESCE(o.quantity, 0)
                        ELSE 0
                    END
                ), 0) AS weekly_orders,
                COALESCE(SUM(
                    CASE
                        WHEN o.created_at >= NOW() - INTERVAL '14 days'
                         AND o.created_at < NOW() - INTERVAL '7 days' THEN COALESCE(o.quantity, 0)
                        ELSE 0
                    END
                ), 0) AS previous_week_orders
            FROM public.orders o
            JOIN public.medicines m ON m.id = o.medicine_id
            GROUP BY m.name
            ORDER BY weekly_orders DESC, m.name ASC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    )
    rows = result.mappings().all()

    payload = []
    for row in rows:
        weekly_orders = int(row.get("weekly_orders") or 0)
        previous_week_orders = int(row.get("previous_week_orders") or 0)

        if weekly_orders > previous_week_orders:
            trend = "up"
        elif weekly_orders < previous_week_orders:
            trend = "down"
        else:
            trend = "stable"

        delta = weekly_orders - previous_week_orders
        forecast_next_week = max(0, int(round(weekly_orders + (delta * 0.5))))

        payload.append(
            {
                "medicine_name": row.get("medicine_name"),
                "weekly_orders": weekly_orders,
                "trend": trend,
                "forecast_next_week": forecast_next_week,
            }
        )

    return payload
