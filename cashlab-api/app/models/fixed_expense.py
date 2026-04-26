
"""CashLab — FixedExpense model (despesas fixas mensais)"""
from typing import Optional

from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from .base import TimestampMixin


class FixedExpense(Base, TimestampMixin):
    __tablename__ = "fixed_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    family_group_id: Mapped[int] = mapped_column(ForeignKey("family_groups.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), default=None, index=True)
    recurrence: Mapped[str] = mapped_column(String(20), default="mensal")  # mensal, anual
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Vigência: competência de início e fim (formato "YYYY-MM")
    # Despesa recorrente aparece em todos os meses entre effective_from e effective_until
    effective_from: Mapped[Optional[str]] = mapped_column(String(7), default=None, index=True)  # "2026-03"
    effective_until: Mapped[Optional[str]] = mapped_column(String(7), default=None, index=True)  # NULL = sem fim
