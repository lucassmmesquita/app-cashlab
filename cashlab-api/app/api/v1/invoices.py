"""CashLab — Invoices endpoints (upload + processamento + persistência)

Fluxo:
1. POST /upload → recebe PDF → detecta banco → parseia → retorna preview
2. POST /upload/{file_id}/confirm → usa dados em memória → cria CreditCard/Invoice/Transactions no DB
"""
import hashlib
import uuid
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db, settings
from app.models import CreditCard, Invoice, Transaction, Member
from app.parsers.detector import detect_bank, get_parser
from app.services.categorization_service import get_categorization_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invoices", tags=["Faturas"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
MAX_SIZE = settings.MAX_PDF_SIZE_MB * 1024 * 1024  # bytes

# In-memory store for pending PDF imports (avoids re-parsing from disk)
_pending_pdf_imports: dict = {}


def _previous_month(month: str) -> str:
    """Get previous month string from 'YYYY-MM' format."""
    try:
        year, m = month.split("-")
        y, mo = int(year), int(m)
        if mo == 1:
            return f"{y - 1}-12"
        return f"{y}-{mo - 1:02d}"
    except (ValueError, IndexError):
        return month


# ── Helpers ────────────────────────────────────────────────────────

async def get_or_create_card(
    db: AsyncSession, bank: str, last_digits: str, member_id: int
) -> CreditCard:
    """Busca cartão existente ou cria um novo."""
    result = await db.execute(
        select(CreditCard).where(
            CreditCard.bank == bank,
            CreditCard.last_digits == last_digits,
        )
    )
    card = result.scalar_one_or_none()

    if not card:
        card = CreditCard(
            member_id=member_id,
            bank=bank,
            last_digits=last_digits,
            is_active=True,
        )
        db.add(card)
        await db.flush()  # Gera o ID
        logger.info(f"Cartão criado: {bank} final {last_digits}")

    return card


async def detect_member_for_card(
    db: AsyncSession, card_last_digits: str
) -> Member:
    """
    Detecta o membro dono do cartão pelos últimos dígitos.
    Regra BV (spec): 6740 = LUCAS, outros = JURA/JOICE.
    Fallback: primeiro membro.
    """
    # Mapear por dígitos conhecidos (hardcoded da spec, pode virar tabela depois)
    CARD_MEMBER_MAP = {
        "6740": "LUCAS",
        "8001": "JURA",
        "9825": "JOICE",
    }

    member_name = CARD_MEMBER_MAP.get(card_last_digits)

    if member_name:
        result = await db.execute(
            select(Member).where(Member.name == member_name)
        )
        member = result.scalar_one_or_none()
        if member:
            return member

    # Fallback: primeiro membro
    result = await db.execute(select(Member).limit(1))
    return result.scalar_one()


async def check_duplicate_invoice(
    db: AsyncSession, pdf_hash: str, card_id: int, reference_month: str
) -> bool:
    """Verifica se já existe uma fatura com o mesmo hash ou mês/cartão."""
    result = await db.execute(
        select(Invoice).where(
            Invoice.card_id == card_id,
            Invoice.reference_month == reference_month,
            Invoice.deleted_at == None,
        )
    )
    existing = result.scalar_one_or_none()
    return existing is not None


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    bank: str = "auto",
    reference_month: str = "",
):
    """
    Upload de PDF da fatura → detecta banco → parseia → retorna preview.

    - **file**: arquivo PDF (multipart/form-data)
    - **bank**: 'auto' (detecção automática), 'bv', 'itau', 'nubank'

    Retorna preview com transações extraídas para revisão antes de confirmar.
    """
    # 1. Validar tipo
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos")

    # 2. Ler conteúdo e validar tamanho
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo excede o limite de {settings.MAX_PDF_SIZE_MB}MB",
        )

    # 3. Salvar em disco (temporary)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.pdf"
    file_path.write_bytes(content)

    logger.info(f"PDF salvo: {file_path} ({len(content)} bytes)")

    try:
        # 4. Detectar banco
        if bank == "auto":
            detected_bank = detect_bank(str(file_path))
        else:
            detected_bank = bank

        if detected_bank == "unknown":
            raise HTTPException(
                status_code=422,
                detail="Não foi possível identificar o banco emissor do PDF. "
                       "Bancos suportados: BV, Itaú, Nubank.",
            )

        # 5. Parsear
        parser = get_parser(detected_bank)
        result = parser.parse(str(file_path))

        logger.info(
            f"Parsing OK: banco={detected_bank}, "
            f"mês={result.reference_month}, "
            f"total={result.total_amount}, "
            f"transações={len(result.transactions)}"
        )

        # 6. Compute hash
        pdf_hash = hashlib.md5(content).hexdigest()

        # 7. Serialize transactions for storage
        transactions_data = []
        for tx in result.transactions:
            transactions_data.append({
                "date": tx.date.isoformat() if tx.date else None,
                "description": tx.description,
                "raw_description": tx.raw_description,
                "amount": str(tx.amount),
                "installment_num": tx.installment_num,
                "installment_total": tx.installment_total,
                "is_international": tx.is_international,
                "card_last_digits": tx.card_last_digits,
                "iof_amount": str(tx.iof_amount) if tx.iof_amount else None,
            })

        # 8. Store parsed result in memory for confirm step
        # reference_month do usuário = mês de PAGAMENTO da fatura
        final_ref_month = reference_month if reference_month else result.reference_month
        payment_month = final_ref_month
        competence_month = _previous_month(payment_month)

        _pending_pdf_imports[file_id] = {
            "bank": detected_bank,
            "reference_month": final_ref_month,
            "payment_month": payment_month,
            "competence_month": competence_month,
            "due_date": result.due_date.isoformat() if result.due_date else None,
            "total_amount": str(result.total_amount),
            "card_last_digits": result.card_last_digits,
            "pdf_hash": pdf_hash,
            "file_size": len(content),
            "transactions": transactions_data,
            "created_at": datetime.utcnow().isoformat(),
        }

        return {
            "data": {
                "file_id": file_id,
                "bank": detected_bank,
                "reference_month": result.reference_month,
                "payment_month": payment_month,
                "competence_month": competence_month,
                "due_date": result.due_date.isoformat() if result.due_date else None,
                "total_amount": str(result.total_amount),
                "card_last_digits": result.card_last_digits,
                "transaction_count": len(transactions_data),
                "transactions": transactions_data,
            }
        }

    except HTTPException:
        raise
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.exception(f"Erro ao processar PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar o PDF: {str(e)}",
        )


@router.post("/upload/{file_id}/confirm")
async def confirm_import(file_id: str, db: AsyncSession = Depends(get_db)):
    """
    Confirmar importação: usa dados em memória e persiste no DB.

    Cria: CreditCard (se não existe) → Invoice → Transaction[].
    Detecta membro pelo cartão. Verifica duplicidade.
    """
    # 1. Buscar dados do parse em memória
    pending = _pending_pdf_imports.get(file_id)
    if not pending:
        raise HTTPException(
            status_code=404,
            detail="Importação não encontrada. O servidor pode ter reiniciado. Faça upload novamente."
        )

    try:
        detected_bank = pending["bank"]
        reference_month = pending["reference_month"]
        payment_month = pending.get("payment_month", reference_month)
        competence_month = pending.get("competence_month", _previous_month(payment_month))
        due_date_str = pending.get("due_date")
        total_amount = Decimal(pending["total_amount"])
        card_last_digits = pending["card_last_digits"]
        pdf_hash = pending["pdf_hash"]
        transactions_data = pending["transactions"]

        # 2. Parse due_date
        from datetime import date
        due_date = date.fromisoformat(due_date_str) if due_date_str else None

        # 3. Detectar membro e criar/buscar cartão
        member = await detect_member_for_card(db, card_last_digits)
        card = await get_or_create_card(db, detected_bank, card_last_digits, member.id)

        # 4. Verificar duplicidade
        is_duplicate = await check_duplicate_invoice(db, pdf_hash, card.id, reference_month)
        if is_duplicate:
            raise HTTPException(
                status_code=409,
                detail=f"Fatura de {reference_month} para cartão final {card_last_digits} "
                       f"já foi importada anteriormente.",
            )

        # 5. Criar Invoice
        invoice = Invoice(
            card_id=card.id,
            reference_month=reference_month,
            payment_month=payment_month,
            competence_month=competence_month,
            due_date=due_date,
            total_amount=total_amount,
            pdf_file_path=f"uploads/{file_id}.pdf",
            pdf_hash=pdf_hash,
            file_size=pending.get("file_size"),
            status="confirmed",
            source_type="PDF",
            parsed_at=datetime.utcnow(),
        )
        db.add(invoice)
        await db.flush()  # Gera invoice.id

        # 6. Carregar engine de categorização
        cat_engine = await get_categorization_engine(db)
        categorized_count = 0

        # 7. Criar Transactions
        tx_count = 0
        for tx in transactions_data:
            # Detectar membro por cartão individual da transação
            tx_card_digits = tx.get("card_last_digits") or card_last_digits
            tx_member = await detect_member_for_card(db, tx_card_digits)
            tx_card = await get_or_create_card(db, detected_bank, tx_card_digits, tx_member.id)

            # Categorização automática por descrição
            category_id, subcategory = cat_engine.categorize(tx["description"])
            if category_id and subcategory != cat_engine._fallback_category_id:
                categorized_count += 1

            # Parse date
            try:
                tx_date = date.fromisoformat(tx["date"]) if tx.get("date") else date.today()
            except (ValueError, KeyError):
                tx_date = date.today()

            # Parse amount
            amount = Decimal(tx["amount"])

            # Parse IOF
            iof_amount = Decimal(tx["iof_amount"]) if tx.get("iof_amount") else None

            transaction = Transaction(
                invoice_id=invoice.id,
                card_id=tx_card.id,
                member_id=tx_member.id,
                category_id=category_id,
                transaction_date=tx_date,
                description=tx["description"],
                raw_description=tx.get("raw_description", tx["description"]),
                amount=amount,
                installment_num=tx.get("installment_num"),
                installment_total=tx.get("installment_total"),
                subcategory=subcategory,
                who=None,
                is_international=tx.get("is_international", False),
                iof_amount=iof_amount,
                billing_month=competence_month,
                source_type="FATURA",
            )
            db.add(transaction)
            tx_count += 1

        # 8. Commit
        await db.commit()

        # 9. Cleanup
        del _pending_pdf_imports[file_id]

        logger.info(
            f"✅ Importação confirmada: invoice_id={invoice.id}, "
            f"cartão={card.bank} {card.last_digits}, "
            f"mês={reference_month}, "
            f"{tx_count} transações salvas, "
            f"{categorized_count} categorizadas automaticamente"
        )

        return {
            "data": {
                "status": "confirmed",
                "file_id": file_id,
                "invoice_id": invoice.id,
                "card": f"{card.bank} final {card.last_digits}",
                "reference_month": reference_month,
                "total_amount": str(total_amount),
                "transaction_count": tx_count,
                "categorized_count": categorized_count,
                "member": member.name,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Erro ao confirmar importação: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao salvar transações: {str(e)}",
        )


@router.get("")
async def list_invoices(
    month: str = None,
    db: AsyncSession = Depends(get_db),
):
    """Listar faturas importadas com informações enriquecidas"""
    from sqlalchemy import func

    query = (
        select(
            Invoice,
            CreditCard.bank.label("bank_name"),
            CreditCard.last_digits.label("card_last_digits"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .outerjoin(CreditCard, Invoice.card_id == CreditCard.id)
        .outerjoin(
            Transaction,
            (Transaction.invoice_id == Invoice.id) & (Transaction.deleted_at == None),
        )
        .where(Invoice.deleted_at == None)
    )

    if month:
        query = query.where(Invoice.reference_month == month)

    query = (
        query
        .group_by(Invoice.id, CreditCard.bank, CreditCard.last_digits)
        .order_by(Invoice.created_at.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    data = []
    for inv, bank_name, card_last_digits, tx_count in rows:
        data.append({
            "id": inv.id,
            "reference_month": inv.reference_month,
            "payment_month": inv.payment_month,
            "competence_month": inv.competence_month,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "total_amount": str(inv.total_amount),
            "status": inv.status,
            "card_id": inv.card_id,
            "bank_name": bank_name,
            "card_last_digits": card_last_digits,
            "transaction_count": tx_count,
            "file_size": inv.file_size,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        })

    return {"data": data}


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    """Detalhe da fatura com transações"""
    result = await db.execute(
        select(Invoice, CreditCard.bank.label("bank_name"), CreditCard.last_digits.label("card_last_digits"))
        .outerjoin(CreditCard, Invoice.card_id == CreditCard.id)
        .where(Invoice.id == invoice_id, Invoice.deleted_at == None)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")

    inv, bank_name, card_last_digits = row

    # Buscar transações
    from app.models import Category
    tx_result = await db.execute(
        select(Transaction, Category.name.label("category_name"))
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(Transaction.invoice_id == invoice_id, Transaction.deleted_at == None)
        .order_by(Transaction.transaction_date)
    )
    rows = tx_result.all()

    return {
        "data": {
            "id": inv.id,
            "reference_month": inv.reference_month,
            "payment_month": inv.payment_month,
            "competence_month": inv.competence_month,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "total_amount": str(inv.total_amount),
            "status": inv.status,
            "bank_name": bank_name,
            "card_last_digits": card_last_digits,
            "file_size": inv.file_size,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "transaction_count": len(rows),
            "transactions": [
                {
                    "id": tx.id,
                    "date": tx.transaction_date.isoformat(),
                    "description": tx.description,
                    "amount": str(tx.amount),
                    "who": tx.who,
                    "category_id": tx.category_id,
                    "category": cat_name,
                    "subcategory": tx.subcategory,
                    "installment_num": tx.installment_num,
                    "installment_total": tx.installment_total,
                    "is_international": tx.is_international,
                }
                for tx, cat_name in rows
            ],
        }
    }


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    """Excluir fatura e suas transações (soft delete)"""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.deleted_at == None)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")

    # Soft delete invoice
    inv.deleted_at = datetime.utcnow()

    # Soft delete associated transactions
    tx_result = await db.execute(
        select(Transaction).where(
            Transaction.invoice_id == invoice_id,
            Transaction.deleted_at == None,
        )
    )
    for tx in tx_result.scalars().all():
        tx.deleted_at = datetime.utcnow()

    await db.commit()

    return {"status": "deleted", "invoice_id": invoice_id}

