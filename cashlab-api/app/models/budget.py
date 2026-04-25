
"""CashLab — Budget model (orçamento mensal por categoria)"""
from typing import Optional

from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from .base import TimestampMixin


class Budget(Base, TimestampMixin):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    family_group_id: Mapped[int] = mapped_column(ForeignKey("family_groups.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    month: Mapped[str] = mapped_column(String(7), nullable=False)  # "2026-04"
    planned_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    actual_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    notes: Mapped[Optional[str]] = mapped_column(Text, default=None)
