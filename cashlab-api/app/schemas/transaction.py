from __future__ import annotations
"""CashLab — Transaction schemas"""
from typing import Optional

from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class TransactionResponse(BaseModel):
    id: int
    invoice_id: int
    card_id: int
    member_id: Optional[int]
    category_id: Optional[int]
    date: date
    description: str
    amount: Decimal
    installment_num: Optional[int]
    installment_total: Optional[int]
    subcategory: Optional[str]
    who: str
    is_international: bool
    iof_amount: Optional[Decimal]
    notes: Optional[str]

    model_config = {"from_attributes": True}


class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    subcategory: Optional[str] = None
    member_id: Optional[int] = None
    who: Optional[str] = None
    notes: Optional[str] = None


class TransactionListResponse(BaseModel):
    data: list[TransactionResponse]
    meta: dict
