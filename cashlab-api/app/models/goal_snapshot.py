
"""CashLab — GoalSnapshot model (capturas de progresso semanal da meta)"""
from typing import Optional

from datetime import date
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .base import TimestampMixin


class GoalSnapshot(Base, TimestampMixin):
    """
    Captura de progresso de uma meta em um ponto no tempo.

    Cada snapshot registra o gasto acumulado até aquela data,
    permitindo acompanhar evolução semanal.
    """
    __tablename__ = "goal_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("spending_goals.id"), nullable=False, index=True)

    # Data do snapshot
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Gasto acumulado até esta data
    current_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Origem dos dados: FATURA (oficial) ou GASTO_SEMANAL (print/OCR)
    source: Mapped[str] = mapped_column(String(20), default="FATURA", nullable=False)

    # Notas opcionais
    notes: Mapped[Optional[str]] = mapped_column(Text, default=None)

    # Relationship
    goal = relationship("SpendingGoal", back_populates="snapshots")
