from __future__ import annotations
"""CashLab — Invoice schemas"""
from typing import Optional

from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


class InvoiceResponse(BaseModel):
    id: int
    card_id: int
    reference_month: str
    due_date: Optional[date]
    total_amount: Decimal
    status: str
    parsed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class InvoiceUploadResponse(BaseModel):
    task_id: str
    status: str
    estimated_seconds: int


class InvoicePreview(BaseModel):
    """Preview das transações extraídas do PDF antes da confirmação"""
    task_id: str
    status: str
    detected_bank: str
    reference_month: str
    due_date: Optional[str]
    total_amount: Decimal
    card_last_digits: str
    is_duplicate: bool
    transactions: list["TransactionPreviewItem"]
    summary: dict


class TransactionPreviewItem(BaseModel):
    temp_id: int
    date: str
    raw_description: str
    description: str
    amount: Decimal
    installment_num: Optional[int]
    installment_total: Optional[int]
    suggested_category: Optional[str]
    suggested_subcategory: Optional[str]
    suggested_member: Optional[str]
    confidence: float
    is_international: bool


class InvoiceConfirmRequest(BaseModel):
    """Confirmação com ajustes do usuário"""
    transactions: list["TransactionConfirmItem"]


class TransactionConfirmItem(BaseModel):
    temp_id: int
    category_id: Optional[int] = None
    subcategory: Optional[str] = None
    member_id: Optional[int] = None
    notes: Optional[str] = None
