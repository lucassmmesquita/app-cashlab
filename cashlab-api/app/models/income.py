
"""CashLab — Income model (receitas mensais)"""
from typing import Optional

from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from .base import TimestampMixin


class Income(Base, TimestampMixin):
    __tablename__ = "incomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    family_group_id: Mapped[int] = mapped_column(ForeignKey("family_groups.id"), nullable=False, index=True)
    member_id: Mapped[Optional[int]] = mapped_column(ForeignKey("members.id"), default=None, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)  # "IRede CLT", "IRede PJ", etc.
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # CLT, PJ, Benefício
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    earmarked_for: Mapped[Optional[str]] = mapped_column(String(100), default=None)  # Verba carimbada (ex: "Lazer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Vigência: competência de início e fim (formato "YYYY-MM")
    # Receita recorrente aparece em todos os meses entre effective_from e effective_until
    effective_from: Mapped[Optional[str]] = mapped_column(String(7), default=None, index=True)  # "2026-03"
    effective_until: Mapped[Optional[str]] = mapped_column(String(7), default=None, index=True)  # NULL = sem fim
