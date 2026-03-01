from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from app.db.database import connect_db, disconnect_db, get_db
from app.routes.admin import router as admin_router
from app.routes.orders import router as orders_router


app = FastAPI(title="Low Stock Notification Agent", version="1.0.0")
app.include_router(orders_router)
app.include_router(admin_router)


@app.on_event("startup")
async def startup() -> None:
    await connect_db()


@app.on_event("shutdown")
async def shutdown() -> None:
    await disconnect_db()


@app.post("/admin/run-migrations", tags=["Admin"])
async def run_migrations() -> dict:
    db = await get_db()
    migration_path = (
        Path(__file__).resolve().parent / "db" / "migrations" / "001_low_stock_notifications.sql"
    )
    sql = migration_path.read_text(encoding="utf-8")

    for statement in [chunk.strip() for chunk in sql.split(";") if chunk.strip()]:
        await db.execute(statement)

    return {"message": "Migrations executed"}

