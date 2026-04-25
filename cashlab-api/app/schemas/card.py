from __future__ import annotations
"""CashLab — Card schemas"""
from typing import Optional

from decimal import Decimal
from pydantic import BaseModel


class CardCreate(BaseModel):
    member_id: int
    bank: str
    last_digits: str
    brand: Optional[str] = None
    limit_total: Optional[Decimal] = None
    due_day: Optional[int] = None


class CardUpdate(BaseModel):
    bank: Optional[str] = None
    last_digits: Optional[str] = None
    brand: Optional[str] = None
    limit_total: Optional[Decimal] = None
    due_day: Optional[int] = None
    is_active: Optional[bool] = None


class CardResponse(BaseModel):
    id: int
    member_id: int
    bank: str
    last_digits: str
    brand: Optional[str]
    limit_total: Optional[Decimal]
    due_day: Optional[int]
    is_active: bool

    model_config = {"from_attributes": True}
