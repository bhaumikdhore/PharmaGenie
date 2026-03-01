from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String, default="customer")
    password: Mapped[str] = mapped_column(String, nullable=True)  # Stored as plain text for demo, use hashing in production