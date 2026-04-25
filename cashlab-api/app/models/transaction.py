
"""CashLab — Transaction model"""
from typing import Optional

from datetime import date
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, Boolean, Date, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .base import TimestampMixin, SoftDeleteMixin


class Transaction(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "who IN ('LUCAS', 'JURA', 'JOICE', '-', 'PENDENTE')",
            name="chk_transaction_who",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("credit_cards.id"), nullable=False, index=True)
    member_id: Mapped[Optional[int]] = mapped_column(ForeignKey("members.id"), default=None, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), default=None, index=True)

    # Data da transação
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Descrição
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_description: Mapped[Optional[str]] = mapped_column(String(500), default=None)

    # Valor — sempre NUMERIC, nunca float
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Parcelas
    installment_num: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    installment_total: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    # Categorização
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    who: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDENTE")

    # Internacional
    is_international: Mapped[bool] = mapped_column(Boolean, default=False)
    iof_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), default=None)

    # Metadados
    location: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    notes: Mapped[Optional[str]] = mapped_column(Text, default=None)

    # Relationships
    invoice = relationship("Invoice", back_populates="transactions")
    card = relationship("CreditCard")
    member = relationship("Member", back_populates="transactions")
    category = relationship("Category")
