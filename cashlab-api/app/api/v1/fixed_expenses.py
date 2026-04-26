"""CashLab — Fixed Expenses endpoints (Despesas Fixas Mensais)

Despesas fixas são recorrentes: uma despesa ativa aparece em todos os meses
dentro da sua vigência (effective_from → effective_until).
O filtro por mês (competência) é essencial para o fluxo de caixa.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.models import FixedExpense

router = APIRouter(prefix="/fixed-expenses", tags=["Despesas Fixas"])


# ── Schemas ────────────────────────────────────────────────────────

class FixedExpenseCreate(BaseModel):
    description: str
    category: str
    amount: float
    note: Optional[str] = None
    effective_from: Optional[str] = None  # "2026-03"
    effective_until: Optional[str] = None
    family_group_id: int = 1


class FixedExpenseUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    note: Optional[str] = None
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None


class FixedExpenseResponse(BaseModel):
    id: int
    description: str
    category: str
    amount: float
    note: Optional[str] = None
    is_active: bool
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Helpers ────────────────────────────────────────────────────────

def _vigencia_filter(model, month: str):
    """
    Retorna filtro SQLAlchemy para vigência por competência.

    Uma despesa fixa está vigente no mês se:
    - effective_from IS NULL ou effective_from <= month
    - effective_until IS NULL ou effective_until >= month
    """
    return and_(
        or_(model.effective_from == None, model.effective_from <= month),
        or_(model.effective_until == None, model.effective_until >= month),
    )


def _serialize_expense(exp: FixedExpense) -> dict:
    return {
        "id": exp.id,
        "description": exp.description,
        "category": exp.recurrence or "",
        "amount": float(exp.amount),
        "note": "",
        "is_active": exp.is_active,
        "effective_from": exp.effective_from,
        "effective_until": exp.effective_until,
    }


# ── Routes ─────────────────────────────────────────────────────────

@router.get("")
async def list_fixed_expenses(
    month: Optional[str] = Query(None, description="Filtro por competência (2026-04)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Listar despesas fixas ativas.

    Se `month` informado, filtra apenas despesas vigentes naquele mês.
    Despesas recorrentes aparecem em todos os meses da sua vigência.
    """
    query = select(FixedExpense).where(FixedExpense.is_active == True)

    if month:
        query = query.where(_vigencia_filter(FixedExpense, month))

    query = query.order_by(FixedExpense.id)
    result = await db.execute(query)
    expenses = result.scalars().all()

    return {"data": [_serialize_expense(exp) for exp in expenses]}


@router.post("", status_code=201)
async def create_fixed_expense(payload: FixedExpenseCreate, db: AsyncSession = Depends(get_db)):
    expense = FixedExpense(
        family_group_id=payload.family_group_id,
        description=payload.description,
        amount=payload.amount,
        recurrence=payload.category,
        effective_from=payload.effective_from,
        effective_until=payload.effective_until,
        is_active=True,
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return {"data": _serialize_expense(expense)}


@router.put("/{expense_id}")
async def update_fixed_expense(expense_id: int, payload: FixedExpenseUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FixedExpense).where(FixedExpense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")

    if payload.description is not None:
        expense.description = payload.description
    if payload.category is not None:
        expense.recurrence = payload.category
    if payload.amount is not None:
        expense.amount = payload.amount
    if payload.effective_from is not None:
        expense.effective_from = payload.effective_from
    if payload.effective_until is not None:
        expense.effective_until = payload.effective_until

    await db.commit()
    await db.refresh(expense)
    return {"data": _serialize_expense(expense)}


@router.delete("/{expense_id}")
async def delete_fixed_expense(expense_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FixedExpense).where(FixedExpense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")

    expense.is_active = False
    await db.commit()
    return {"message": "Despesa removida com sucesso"}
