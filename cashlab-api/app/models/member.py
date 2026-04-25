
"""CashLab — Member model (LUCAS, JURA, JOICE)"""
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .base import TimestampMixin


class Member(Base, TimestampMixin):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    family_group_id: Mapped[int] = mapped_column(ForeignKey("family_groups.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # LUCAS, JURA, JOICE
    color: Mapped[Optional[str]] = mapped_column(String(7), default=None)  # Hex color
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), default=None)

    # Relationships
    family_group = relationship("FamilyGroup", back_populates="members")
    cards = relationship("CreditCard", back_populates="member")
    transactions = relationship("Transaction", back_populates="member")
