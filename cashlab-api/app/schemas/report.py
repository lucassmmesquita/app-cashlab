"""CashLab — Report schemas"""
from decimal import Decimal
from pydantic import BaseModel


class DashboardResponse(BaseModel):
    """Dados consolidados do dashboard mensal"""
    month: str
    total_income: Decimal
    total_fixed_expenses: Decimal
    total_card_expenses: Decimal
    balance: Decimal
    by_category: list[dict]
    by_member: list[dict]
    alerts: list[dict]


class CategoryReportItem(BaseModel):
    category_name: str
    total_amount: Decimal
    percentage: float
    transaction_count: int


class MemberReportItem(BaseModel):
    member_name: str
    total_amount: Decimal
    percentage: float
