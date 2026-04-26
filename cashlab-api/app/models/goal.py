
"""CashLab — SpendingGoal model (metas de redução de gastos com cartão)"""
from typing import Optional

from datetime import date
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .base import TimestampMixin, SoftDeleteMixin


class SpendingGoal(Base, TimestampMixin, SoftDeleteMixin):
    """
    Meta de redução de gastos.

    O usuário define um percentual de redução sobre um mês base (baseline).
    O sistema calcula o valor alvo e acompanha o progresso.
    """
    __tablename__ = "spending_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    family_group_id: Mapped[int] = mapped_column(ForeignKey("family_groups.id"), nullable=False, index=True)

    # Cartão específico (None = meta geral, todos os cartões)
    card_id: Mapped[Optional[int]] = mapped_column(ForeignKey("credit_cards.id"), default=None, index=True)

    # Meta
    target_reduction_pct: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..100
    baseline_month: Mapped[str] = mapped_column(String(7), nullable=False)  # "2026-04" — mês base
    baseline_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)  # valor total do baseline
    target_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)  # baseline * (1 - pct/100)
    target_month: Mapped[str] = mapped_column(String(7), nullable=False)  # "2026-05" — mês alvo

    # Status: active, achieved, missed, cancelled
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    # Descrição/nome da meta (opcional)
    name: Mapped[Optional[str]] = mapped_column(String(100), default=None)

    # Relationships
    card = relationship("CreditCard")
    snapshots = relationship("GoalSnapshot", back_populates="goal", order_by="GoalSnapshot.snapshot_date.desc()")
