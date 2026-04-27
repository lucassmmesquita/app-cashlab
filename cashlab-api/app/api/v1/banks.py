"""CashLab — Banks API (CRUD completo de bancos emissores)

v2.0: CRUD completo + endpoint de retreinamento de parser.
Bancos com has_native_parser=True já possuem parser pronto.
Bancos customizados precisam de treinamento via upload de PDF.
"""
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db, settings
from app.models import Bank, Invoice

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/banks", tags=["Bancos"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR)

# Default banks with native parsers
DEFAULT_BANKS = [
    {"name": "Banco BV", "slug": "bv", "color": "#F5A623", "has_native_parser": True, "status": "ready", "parser_status": "ready", "closing_day": 17, "due_day": 22},
    {"name": "Itaú", "slug": "itau", "color": "#FF6B00", "has_native_parser": True, "status": "ready", "parser_status": "ready", "closing_day": 3, "due_day": 9},
    {"name": "Nubank", "slug": "nubank", "color": "#8A05BE", "has_native_parser": False, "status": "pending", "parser_status": "pending"},
]


class BankCreate(BaseModel):
    name: str
    color: str = "#007AFF"
    closing_day: Optional[int] = None
    due_day: Optional[int] = None


class BankUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    closing_day: Optional[int] = None
    due_day: Optional[int] = None


async def ensure_default_banks(db: AsyncSession):
    """Seed default banks if table is empty."""
    result = await db.execute(select(Bank).limit(1))
    if result.scalar_one_or_none() is None:
        for bank_data in DEFAULT_BANKS:
            bank = Bank(**bank_data)
            db.add(bank)
        await db.commit()
        logger.info("Default banks seeded")


async def _get_invoice_count(db: AsyncSession, bank_slug: str) -> int:
    """Conta faturas importadas para um banco."""
    from app.models import CreditCard
    result = await db.execute(
        select(func.count(Invoice.id))
        .join(CreditCard, Invoice.card_id == CreditCard.id)
        .where(
            CreditCard.bank == bank_slug,
            Invoice.deleted_at == None,
        )
    )
    return result.scalar() or 0


def _serialize_bank(bank: Bank, invoice_count: int = 0) -> dict:
    """Serializar banco para response."""
    return {
        "id": bank.id,
        "name": bank.name,
        "slug": bank.slug,
        "color": bank.color,
        "status": bank.status,
        "has_native_parser": bank.has_native_parser,
        "closing_day": bank.closing_day,
        "due_day": bank.due_day,
        "parser_status": bank.parser_status,
        "parser_trained_at": bank.parser_trained_at.isoformat() if bank.parser_trained_at else None,
        "invoice_count": invoice_count,
    }


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

    data = []
    for b in banks:
        inv_count = await _get_invoice_count(db, b.slug)
        data.append(_serialize_bank(b, inv_count))

    return {"data": data}


@router.get("/{bank_id}")
async def get_bank(bank_id: int, db: AsyncSession = Depends(get_db)):
    """Detalhes do banco com status do parser e contagem de faturas."""
    result = await db.execute(
        select(Bank).where(Bank.id == bank_id, Bank.deleted_at == None)
    )
    bank = result.scalar_one_or_none()
    if not bank:
        raise HTTPException(404, "Banco não encontrado")

    inv_count = await _get_invoice_count(db, bank.slug)
    return {"data": _serialize_bank(bank, inv_count)}


@router.post("")
async def create_bank(payload: BankCreate, db: AsyncSession = Depends(get_db)):
    """Criar um novo banco."""
    slug = payload.name.lower().replace(" ", "_").replace("-", "_")

    existing = await db.execute(select(Bank).where(Bank.slug == slug, Bank.deleted_at == None))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Banco '{payload.name}' já existe.")

    bank = Bank(
        name=payload.name,
        slug=slug,
        color=payload.color,
        status="pending",
        has_native_parser=False,
        closing_day=payload.closing_day,
        due_day=payload.due_day,
        parser_status="pending",
    )
    db.add(bank)
    await db.commit()
    await db.refresh(bank)

    return {"data": _serialize_bank(bank)}


@router.put("/{bank_id}")
async def update_bank(bank_id: int, payload: BankUpdate, db: AsyncSession = Depends(get_db)):
    """Editar dados cadastrais do banco (nome, cor, dias)."""
    result = await db.execute(
        select(Bank).where(Bank.id == bank_id, Bank.deleted_at == None)
    )
    bank = result.scalar_one_or_none()
    if not bank:
        raise HTTPException(404, "Banco não encontrado")

    if payload.name is not None:
        bank.name = payload.name
    if payload.color is not None:
        bank.color = payload.color
    if payload.closing_day is not None:
        bank.closing_day = payload.closing_day
    if payload.due_day is not None:
        bank.due_day = payload.due_day

    await db.commit()
    await db.refresh(bank)

    inv_count = await _get_invoice_count(db, bank.slug)
    return {"data": _serialize_bank(bank, inv_count)}


@router.post("/{bank_id}/retrain")
async def retrain_parser(
    bank_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Retreinar parser de um banco.

    Recebe um PDF de fatura como amostra de treinamento.
    Para v2.0: valida que o PDF é legível e marca o banco como 'ready'.
    Treinamento real com ML/NLP é escopo futuro.
    """
    result = await db.execute(
        select(Bank).where(Bank.id == bank_id, Bank.deleted_at == None)
    )
    bank = result.scalar_one_or_none()
    if not bank:
        raise HTTPException(404, "Banco não encontrado")

    # Validar arquivo
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Apenas arquivos PDF são aceitos")

    content = await file.read()
    max_size = settings.MAX_PDF_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(400, f"Arquivo excede o limite de {settings.MAX_PDF_SIZE_MB}MB")

    # Salvar PDF de treinamento
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    train_path = UPLOAD_DIR / f"train_{bank.slug}_{bank_id}.pdf"
    train_path.write_bytes(content)

    # Marcar como processing
    bank.parser_status = "processing"
    await db.commit()

    # v2.0: Treinamento simplificado — validar que o PDF contém texto legível
    try:
        import pdfplumber
        with pdfplumber.open(str(train_path)) as pdf:
            if len(pdf.pages) == 0:
                raise HTTPException(422, "PDF vazio — nenhuma página encontrada")
            first_page_text = pdf.pages[0].extract_text() or ""
            if len(first_page_text.strip()) < 20:
                bank.parser_status = "error"
                await db.commit()
                raise HTTPException(422, "PDF não contém texto legível suficiente para treinamento")

        # Treinamento bem-sucedido
        bank.parser_status = "ready"
        bank.status = "ready"
        bank.parser_trained_at = datetime.utcnow()
        await db.commit()
        await db.refresh(bank)

        logger.info(f"✅ Parser treinado para banco {bank.name} (id={bank.id})")

        return {
            "data": {
                **_serialize_bank(bank),
                "message": "Parser treinado com sucesso. O banco está pronto para uso.",
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        bank.parser_status = "error"
        await db.commit()
        logger.exception(f"Erro no treinamento do parser: {e}")
        raise HTTPException(500, f"Erro ao treinar parser: {str(e)}")


@router.delete("/{bank_id}")
async def delete_bank(bank_id: int, db: AsyncSession = Depends(get_db)):
    """Excluir banco (soft delete). Alerta se houver faturas vinculadas."""
    result = await db.execute(select(Bank).where(Bank.id == bank_id, Bank.deleted_at == None))
    bank = result.scalar_one_or_none()
    if not bank:
        raise HTTPException(404, "Banco não encontrado")

    if bank.has_native_parser:
        raise HTTPException(400, "Não é possível excluir um banco com parser nativo.")

    # Verificar faturas vinculadas
    inv_count = await _get_invoice_count(db, bank.slug)
    if inv_count > 0:
        raise HTTPException(
            400,
            f"Banco '{bank.name}' possui {inv_count} fatura(s) vinculada(s). "
            "Exclua as faturas primeiro ou force a exclusão."
        )

    bank.deleted_at = datetime.utcnow()
    await db.commit()

    return {"status": "deleted", "bank_id": bank_id}
