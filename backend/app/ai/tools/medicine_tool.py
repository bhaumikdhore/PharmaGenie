from langchain.tools import tool
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.medicine import Medicine

@tool
async def search_medicine(name: str):
    """Search medicine by name in the database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Medicine).where(Medicine.name.ilike(f"%{name}%"))
        )
        medicines = result.scalars().all()

        if not medicines:
            return "No medicine found."

        return [
            {
                "name": m.name,
                "price": m.price,
                "stock": m.stock
            }
            for m in medicines
        ]
