"""CashLab — Dashboard endpoint"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/{month}")
async def get_dashboard(month: str, db: AsyncSession = Depends(get_db)):
    """Dados consolidados do dashboard"""
    return {"data": {}}
