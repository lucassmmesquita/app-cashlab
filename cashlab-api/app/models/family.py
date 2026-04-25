"""CashLab — FamilyGroup model"""
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .base import TimestampMixin


class FamilyGroup(Base, TimestampMixin):
    __tablename__ = "family_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    users = relationship("User", back_populates="family_group")
    members = relationship("Member", back_populates="family_group")
