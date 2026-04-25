"""CashLab — Cards endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db

router = APIRouter(prefix="/cards", tags=["Cartões"])


@router.get("")
async def list_cards(db: AsyncSession = Depends(get_db)):
    """Listar cartões cadastrados"""
    return {"data": []}


@router.post("", status_code=201)
async def create_card(db: AsyncSession = Depends(get_db)):
    """Cadastrar cartão"""
    return {"data": {}}


@router.put("/{card_id}")
async def update_card(card_id: int, db: AsyncSession = Depends(get_db)):
    """Editar cartão"""
    return {"data": {}}


@router.delete("/{card_id}")
async def deactivate_card(card_id: int, db: AsyncSession = Depends(get_db)):
    """Desativar cartão"""
    return {"status": "deactivated"}
