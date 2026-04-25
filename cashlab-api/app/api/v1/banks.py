"""CashLab — Banks API (CRUD de bancos emissores)"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.models import Bank

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/banks", tags=["Bancos"])

# Default banks with native parsers
DEFAULT_BANKS = [
    {"name": "Banco BV", "slug": "bv", "color": "#F5A623", "has_native_parser": True, "status": "ready"},
    {"name": "Itaú", "slug": "itau", "color": "#FF6B00", "has_native_parser": True, "status": "ready"},
    {"name": "Nubank", "slug": "nubank", "color": "#8A05BE", "has_native_parser": False, "status": "pending"},
]


class BankCreate(BaseModel):
    name: str
    color: str = "#007AFF"


class BankUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


async def ensure_default_banks(db: AsyncSession):
    """Seed default banks if table is empty."""
    result = await db.execute(select(Bank).limit(1))
    if result.scalar_one_or_none() is None:
        for bank_data in DEFAULT_BANKS:
            bank = Bank(**bank_data)
            db.add(bank)
        await db.commit()
        logger.info("Default banks seeded")


@router.get("")
async def list_banks(db: AsyncSession = Depends(get_db)):
    """Listar todos os bancos cadastrados."""
    await ensure_default_banks(db)

    result = await db.execute(
        select(Bank)
        .where(Bank.deleted_at == None)
        .order_by(Bank.name)
    )
    banks = result.scalars().all()

    return {
        "data": [
            {
                "id": b.id,
                "name": b.name,
                "slug": b.slug,
                "color": b.color,
                "status": b.status,
                "has_native_parser": b.has_native_parser,
            }
            for b in banks
        ]
    }


@router.post("")
async def create_bank(payload: BankCreate, db: AsyncSession = Depends(get_db)):
    """Criar um novo banco."""
    slug = payload.name.lower().replace(" ", "_").replace("-", "_")

    # Check unique slug
    existing = await db.execute(select(Bank).where(Bank.slug == slug, Bank.deleted_at == None))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Banco '{payload.name}' já existe.")

    bank = Bank(
        name=payload.name,
        slug=slug,
        color=payload.color,
        status="pending",
        has_native_parser=False,
    )
    db.add(bank)
    await db.commit()
    await db.refresh(bank)

    logger.info(f"Banco criado: {bank.name} ({bank.slug})")

    return {
        "data": {
            "id": bank.id,
            "name": bank.name,
            "slug": bank.slug,
            "color": bank.color,
            "status": bank.status,
        }
    }


@router.delete("/{bank_id}")
async def delete_bank(bank_id: int, db: AsyncSession = Depends(get_db)):
    """Excluir banco (soft delete)."""
    result = await db.execute(select(Bank).where(Bank.id == bank_id, Bank.deleted_at == None))
    bank = result.scalar_one_or_none()
    if not bank:
        raise HTTPException(404, "Banco não encontrado")

    if bank.has_native_parser:
        raise HTTPException(400, "Não é possível excluir um banco com parser nativo.")

    bank.deleted_at = datetime.utcnow()
    await db.commit()

    return {"status": "deleted", "bank_id": bank_id}
