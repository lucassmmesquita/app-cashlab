"""CashLab — Categories endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db

router = APIRouter(prefix="/categories", tags=["Categorias"])


@router.get("")
async def list_categories(db: AsyncSession = Depends(get_db)):
    return {"data": []}


@router.post("", status_code=201)
async def create_category(db: AsyncSession = Depends(get_db)):
    return {"data": {}}
