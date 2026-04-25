"""CashLab — Incomes endpoints (Receitas Mensais)"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.models import Income

router = APIRouter(prefix="/incomes", tags=["Receitas"])


# ── Schemas ────────────────────────────────────────────────────────

class IncomeCreate(BaseModel):
    source: str
    type: str
    amount: float
    note: Optional[str] = None
    family_group_id: int = 1


class IncomeUpdate(BaseModel):
    source: Optional[str] = None
    type: Optional[str] = None
    amount: Optional[float] = None
    note: Optional[str] = None


class IncomeResponse(BaseModel):
    id: int
    source: str
    type: str
    amount: float
    note: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


# ── Routes ─────────────────────────────────────────────────────────

@router.get("")
async def list_incomes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Income).where(Income.is_active == True).order_by(Income.id)
    )
    incomes = result.scalars().all()
    return {
        "data": [
            {
                "id": inc.id,
                "source": inc.source,
                "type": inc.type,
                "amount": float(inc.amount),
                "note": inc.earmarked_for or "",
                "is_active": inc.is_active,
            }
            for inc in incomes
        ]
    }


@router.post("", status_code=201)
async def create_income(payload: IncomeCreate, db: AsyncSession = Depends(get_db)):
    income = Income(
        family_group_id=payload.family_group_id,
        source=payload.source,
        type=payload.type,
        amount=payload.amount,
        earmarked_for=payload.note,
        is_active=True,
    )
    db.add(income)
    await db.commit()
    await db.refresh(income)
    return {
        "data": {
            "id": income.id,
            "source": income.source,
            "type": income.type,
            "amount": float(income.amount),
            "note": income.earmarked_for or "",
            "is_active": income.is_active,
        }
    }


@router.put("/{income_id}")
async def update_income(income_id: int, payload: IncomeUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Income).where(Income.id == income_id))
    income = result.scalar_one_or_none()
    if not income:
        raise HTTPException(status_code=404, detail="Receita não encontrada")

    if payload.source is not None:
        income.source = payload.source
    if payload.type is not None:
        income.type = payload.type
    if payload.amount is not None:
        income.amount = payload.amount
    if payload.note is not None:
        income.earmarked_for = payload.note

    await db.commit()
    await db.refresh(income)
    return {
        "data": {
            "id": income.id,
            "source": income.source,
            "type": income.type,
            "amount": float(income.amount),
            "note": income.earmarked_for or "",
            "is_active": income.is_active,
        }
    }


@router.delete("/{income_id}")
async def delete_income(income_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Income).where(Income.id == income_id))
    income = result.scalar_one_or_none()
    if not income:
        raise HTTPException(status_code=404, detail="Receita não encontrada")

    income.is_active = False
    await db.commit()
    return {"message": "Receita removida com sucesso"}
