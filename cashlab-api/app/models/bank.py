"""CashLab — Bank model (bancos emissores de faturas)"""
from typing import Optional

from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from .base import TimestampMixin, SoftDeleteMixin


class Bank(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "banks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    slug: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#007AFF")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    has_native_parser: Mapped[bool] = mapped_column(Boolean, default=False)
    closing_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # dia fechamento
    due_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)      # dia vencimento

