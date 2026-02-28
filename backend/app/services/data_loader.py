import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
from app.models.medicine import Medicine
from app.models.customer_history import CustomerHistory
from app.db.session import AsyncSessionLocal


def _resolve_csv_path(path: str) -> Path:
    csv_path = Path(path)
    if csv_path.is_absolute():
        return csv_path
    return Path(__file__).resolve().parents[2] / csv_path


async def load_medicines_from_csv(path: str):
    df = pd.read_csv(_resolve_csv_path(path))

    async with AsyncSessionLocal() as session:
        for _, row in df.iterrows():
            medicine = Medicine(
                name=str(row.get("name") or row.get("medicine_name") or ""),
                category=str(row.get("category", "")),
                price=float(row.get("price") or 0),
                stock=int(row.get("stock") or row.get("stock_quantity") or 0),
            )
            session.add(medicine)

        await session.commit()


async def load_customer_history_from_csv(path: str):
    df = pd.read_csv(_resolve_csv_path(path))

    async with AsyncSessionLocal() as session:
        for _, row in df.iterrows():
            history = CustomerHistory(
                customer_id=str(row.get("customer_id", "")),
                medicine_name=str(row.get("medicine_name", "")),
                quantity=int(row.get("quantity") or 0),
            )
            session.add(history)

        await session.commit()
