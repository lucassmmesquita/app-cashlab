
"""CashLab — Invoice model (fatura importada por PDF)"""
from typing import Optional

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .base import TimestampMixin, SoftDeleteMixin


class Invoice(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("credit_cards.id"), nullable=False, index=True)
    reference_month: Mapped[str] = mapped_column(String(7), nullable=False)  # "2026-04"
    due_date: Mapped[Optional[date]] = mapped_column(Date, default=None)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    pdf_file_path: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    pdf_hash: Mapped[Optional[str]] = mapped_column(String(64), default=None, index=True)  # MD5 or UUID
    file_size: Mapped[Optional[int]] = mapped_column(Integer, default=None)  # bytes
    status: Mapped[str] = mapped_column(String(20), default="imported")  # imported, confirmed, rejected
    parsed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)

    # Relationships
    card = relationship("CreditCard", back_populates="invoices")
    transactions = relationship("Transaction", back_populates="invoice")
