from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class CustomerHistory(Base):
    __tablename__ = "customer_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(String)
    medicine_name: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)