
"""CashLab — Category model (18 categorias de gastos)"""
from typing import Optional

from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from .base import TimestampMixin


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    color: Mapped[Optional[str]] = mapped_column(String(7), default=None)  # Hex
    type: Mapped[str] = mapped_column(String(20), default="variavel")  # fixa, variavel
    is_system: Mapped[bool] = mapped_column(Boolean, default=True)
