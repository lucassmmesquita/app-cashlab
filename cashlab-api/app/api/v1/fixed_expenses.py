"""CashLab — Fixed Expenses endpoints (Despesas Fixas Mensais)"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
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
    family_group_id: int = 1


class FixedExpenseUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    note: Optional[str] = None


class FixedExpenseResponse(BaseModel):
    id: int
    description: str
    category: str
    amount: float
    note: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


# ── Routes ─────────────────────────────────────────────────────────

@router.get("")
async def list_fixed_expenses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FixedExpense).where(FixedExpense.is_active == True).order_by(FixedExpense.id)
    )
    expenses = result.scalars().all()
    return {
        "data": [
            {
                "id": exp.id,
                "description": exp.description,
                "category": exp.recurrence or "",
                "amount": float(exp.amount),
                "note": "",
                "is_active": exp.is_active,
            }
            for exp in expenses
        ]
    }


@router.post("", status_code=201)
async def create_fixed_expense(payload: FixedExpenseCreate, db: AsyncSession = Depends(get_db)):
    expense = FixedExpense(
        family_group_id=payload.family_group_id,
        description=payload.description,
        amount=payload.amount,
        recurrence=payload.category,
        is_active=True,
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return {
        "data": {
            "id": expense.id,
            "description": expense.description,
            "category": expense.recurrence or "",
            "amount": float(expense.amount),
            "note": "",
            "is_active": expense.is_active,
        }
    }


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

    await db.commit()
    await db.refresh(expense)
    return {
        "data": {
            "id": expense.id,
            "description": expense.description,
            "category": expense.recurrence or "",
            "amount": float(expense.amount),
            "note": "",
            "is_active": expense.is_active,
        }
    }


@router.delete("/{expense_id}")
async def delete_fixed_expense(expense_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FixedExpense).where(FixedExpense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")

    expense.is_active = False
    await db.commit()
    return {"message": "Despesa removida com sucesso"}
