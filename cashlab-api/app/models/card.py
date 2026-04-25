
"""CashLab — CreditCard model"""
from typing import Optional

from sqlalchemy import String, Integer, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.core.database import Base
from .base import TimestampMixin


class CreditCard(Base, TimestampMixin):
    __tablename__ = "credit_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False, index=True)
    bank: Mapped[str] = mapped_column(String(20), nullable=False)  # bv, itau, nubank
    last_digits: Mapped[str] = mapped_column(String(4), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(20), default=None)  # visa, mastercard
    limit_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), default=None)
    due_day: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    member = relationship("Member", back_populates="cards")
    invoices = relationship("Invoice", back_populates="card")
