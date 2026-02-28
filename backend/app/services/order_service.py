from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.order import Order


class OrderService:

    @staticmethod
    async def create_order(session: AsyncSession, order_data: dict):
        order = Order(**order_data)
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order

    @staticmethod
    async def update_order_status(session: AsyncSession, order_id: int, status: str):
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()

        if not order:
            return None

        order.status = status
        await session.commit()
        await session.refresh(order)
        return order

    @staticmethod
    async def get_order(session: AsyncSession, order_id: int):
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()