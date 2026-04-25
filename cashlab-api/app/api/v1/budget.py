"""CashLab — Budget endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db

router = APIRouter(prefix="/budget", tags=["Orçamento"])


@router.get("/{month}")
async def get_budget(month: str, db: AsyncSession = Depends(get_db)):
    """Orçamento do mês"""
    return {"data": {}}


@router.put("/{month}")
async def update_budget(month: str, db: AsyncSession = Depends(get_db)):
    """Definir/atualizar planejado"""
    return {"data": {}}


@router.get("/{month}/vs-actual")
async def get_budget_vs_actual(month: str, db: AsyncSession = Depends(get_db)):
    """Planejado vs realizado"""
    return {"data": {}}
