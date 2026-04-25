
"""CashLab — Rule models (categorização e atribuição QUEM)"""
from typing import Optional

from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from .base import TimestampMixin


class CategorizationRule(Base, TimestampMixin):
    """Regras de categorização por descrição da transação (regex)"""
    __tablename__ = "categorization_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pattern: Mapped[str] = mapped_column(Text, nullable=False)  # Regex pattern
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Maior = mais prioridade
    is_user_rule: Mapped[bool] = mapped_column(default=False)  # Regra do usuário prevalece


class MemberAssignmentRule(Base, TimestampMixin):
    """Regras de atribuição de membro (QUEM) por cartão ou descrição"""
    __tablename__ = "member_assignment_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "card" ou "description"
    pattern: Mapped[str] = mapped_column(Text, nullable=False)  # Últimos dígitos ou regex
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_user_rule: Mapped[bool] = mapped_column(default=False)
