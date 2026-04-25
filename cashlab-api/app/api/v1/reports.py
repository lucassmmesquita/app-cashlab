"""CashLab — Reports endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db

router = APIRouter(prefix="/reports", tags=["Relatórios"])


@router.get("/by-category")
async def report_by_category(month: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Gastos por categoria"""
    return {"data": []}


@router.get("/by-member")
async def report_by_member(month: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Gastos por membro"""
    return {"data": []}


@router.get("/installments")
async def report_installments(db: AsyncSession = Depends(get_db)):
    """Parcelamentos ativos"""
    return {"data": []}


@router.get("/subscriptions")
async def report_subscriptions(db: AsyncSession = Depends(get_db)):
    """Assinaturas recorrentes"""
    return {"data": []}


@router.get("/projection")
async def report_projection(db: AsyncSession = Depends(get_db)):
    """Projeção 12 meses"""
    return {"data": []}


@router.get("/trend")
async def report_trend(db: AsyncSession = Depends(get_db)):
    """Evolução mensal"""
    return {"data": []}
