from app.db.base import Base
from app.db.session import engine

# Ensure all model tables are registered on metadata before create_all.
from app.models import customer_history, medicine, order, user, delivery, notification, prescription_storage, medicine_refill_notification  # noqa: F401


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
