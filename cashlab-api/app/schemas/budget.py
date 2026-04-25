from __future__ import annotations
"""CashLab — Budget schemas"""
from typing import Optional

from decimal import Decimal
from pydantic import BaseModel


class BudgetResponse(BaseModel):
    id: int
    category_id: int
    month: str
    planned_amount: Decimal
    actual_amount: Decimal

    model_config = {"from_attributes": True}


class BudgetUpdate(BaseModel):
    planned_amount: Decimal
    notes: Optional[str] = None
