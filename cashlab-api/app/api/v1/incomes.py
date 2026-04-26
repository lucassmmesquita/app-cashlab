"""CashLab — Incomes endpoints (Receitas Mensais)

Receitas são recorrentes: uma receita ativa aparece em todos os meses
dentro da sua vigência (effective_from → effective_until).
O filtro por mês (competência) é essencial para o fluxo de caixa.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_, or_
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
    effective_from: Optional[str] = None  # "2026-03"
    effective_until: Optional[str] = None
    family_group_id: int = 1


class IncomeUpdate(BaseModel):
    source: Optional[str] = None
    type: Optional[str] = None
    amount: Optional[float] = None
    note: Optional[str] = None
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None


class IncomeResponse(BaseModel):
    id: int
    source: str
    type: str
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

    Uma receita/despesa está vigente no mês se:
    - effective_from IS NULL ou effective_from <= month
    - effective_until IS NULL ou effective_until >= month
    """
    return and_(
        or_(model.effective_from == None, model.effective_from <= month),
        or_(model.effective_until == None, model.effective_until >= month),
    )


def _serialize_income(inc: Income) -> dict:
    return {
        "id": inc.id,
        "source": inc.source,
        "type": inc.type,
        "amount": float(inc.amount),
        "note": inc.earmarked_for or "",
        "is_active": inc.is_active,
        "effective_from": inc.effective_from,
        "effective_until": inc.effective_until,
    }


# ── Routes ─────────────────────────────────────────────────────────

@router.get("")
async def list_incomes(
    month: Optional[str] = Query(None, description="Filtro por competência (2026-04)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Listar receitas ativas.

    Se `month` informado, filtra apenas receitas vigentes naquele mês.
    Receitas recorrentes aparecem em todos os meses da sua vigência.
    """
    query = select(Income).where(Income.is_active == True)

    if month:
        query = query.where(_vigencia_filter(Income, month))

    query = query.order_by(Income.id)
    result = await db.execute(query)
    incomes = result.scalars().all()

    return {"data": [_serialize_income(inc) for inc in incomes]}


@router.post("", status_code=201)
async def create_income(payload: IncomeCreate, db: AsyncSession = Depends(get_db)):
    income = Income(
        family_group_id=payload.family_group_id,
        source=payload.source,
        type=payload.type,
        amount=payload.amount,
        earmarked_for=payload.note,
        effective_from=payload.effective_from,
        effective_until=payload.effective_until,
        is_active=True,
    )
    db.add(income)
    await db.commit()
    await db.refresh(income)
    return {"data": _serialize_income(income)}


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
    if payload.effective_from is not None:
        income.effective_from = payload.effective_from
    if payload.effective_until is not None:
        income.effective_until = payload.effective_until

    await db.commit()
    await db.refresh(income)
    return {"data": _serialize_income(income)}


@router.delete("/{income_id}")
async def delete_income(income_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Income).where(Income.id == income_id))
    income = result.scalar_one_or_none()
    if not income:
        raise HTTPException(status_code=404, detail="Receita não encontrada")

    income.is_active = False
    await db.commit()
    return {"message": "Receita removida com sucesso"}
