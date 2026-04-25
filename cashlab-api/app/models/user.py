
"""CashLab — User model (autenticação)"""
from typing import Optional

from sqlalchemy import String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .base import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Nullable para social login
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    family_group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("family_groups.id"), default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Social login
    auth_provider: Mapped[str] = mapped_column(String(20), default="email")  # "email", "google", "apple"
    provider_id: Mapped[Optional[str]] = mapped_column(String(255), default=None, index=True)  # Google/Apple sub
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), default=None)

    # Relationships
    family_group = relationship("FamilyGroup", back_populates="users")
