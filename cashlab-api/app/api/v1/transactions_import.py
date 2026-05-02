"""CashLab — Screenshot import for weekly transactions (OpenAI Vision)

Endpoint: POST /transactions/import-screenshot
Receives an image, uses OpenAI Vision to extract transactions,
returns preview for user confirmation.
"""
import uuid
import json
import logging
import base64
from pathlib import Path
from datetime import datetime, date

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db, settings
from app.models import Transaction, CreditCard, Member, Invoice

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["Transações - Import"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR)

# In-memory store for pending screenshot imports (simple approach)
_pending_imports: dict = {}


class ScreenshotTransaction(BaseModel):
    date: str
    description: str
    amount: float
    card_last_digits: Optional[str] = None


EXTRACTION_PROMPT = """Analise esta imagem de uma tela de transações de cartão de crédito.
Extraia TODAS as transações visíveis na imagem.

Para cada transação, extraia:
- date: data no formato YYYY-MM-DD
- description: nome/descrição do estabelecimento
- amount: valor em reais (número positivo, sem R$)
- card_last_digits: últimos 4 dígitos do cartão se visível

IMPORTANTE:
- Se o ano não estiver visível, use 2026
- Valores devem ser números (ex: 45.90, não "R$ 45,90")
- Converta vírgula para ponto nos valores

Retorne APENAS um JSON array, sem markdown, sem explicação:
[{"date": "2026-04-10", "description": "NOME DO ESTABELECIMENTO", "amount": 45.90, "card_last_digits": "6740"}]
"""


@router.post("/import-screenshot")
async def import_screenshot(
    files: List[UploadFile] = File(...),
):
    """Upload de 1-10 screenshots de transações → OCR via OpenAI Vision → preview."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY não configurada. Adicione no .env para usar esta funcionalidade."
        )

    if len(files) > 10:
        raise HTTPException(400, "Máximo de 10 imagens por importação")

    if len(files) == 0:
        raise HTTPException(400, "Envie ao menos uma imagem")

    all_parsed = []
    total = 0.0
    file_id = str(uuid.uuid4())

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    for idx, file in enumerate(files):
        # Validate image
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(400, f"Arquivo {idx+1} não é uma imagem válida (PNG, JPG)")

        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(400, f"Imagem {idx+1} excede 10MB")

        # Save file
        ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "png"
        file_path = UPLOAD_DIR / f"{file_id}_{idx}.{ext}"
        file_path.write_bytes(content)

        logger.info(f"Screenshot {idx+1}/{len(files)} salva: {file_path} ({len(content)} bytes)")

        try:
            # Call OpenAI Vision
            import httpx

            b64_image = base64.b64encode(content).decode("utf-8")
            mime_type = file.content_type or "image/png"

            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": EXTRACTION_PROMPT},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{mime_type};base64,{b64_image}",
                                            "detail": "high",
                                        },
                                    },
                                ],
                            }
                        ],
                        "max_tokens": 4096,
                        "temperature": 0,
                    },
                )

            if resp.status_code != 200:
                error_detail = resp.text
                logger.error(f"OpenAI API error for image {idx+1}: {resp.status_code} - {error_detail}")
                raise HTTPException(500, f"Erro na API OpenAI (imagem {idx+1}): {resp.status_code}")

            result = resp.json()
            raw_text = result["choices"][0]["message"]["content"].strip()

            # Clean markdown fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3].strip()

            transactions = json.loads(raw_text)

            # Validate and normalize
            for tx in transactions:
                amount = float(tx.get("amount", 0))
                total += amount
                all_parsed.append({
                    "date": tx.get("date", ""),
                    "description": tx.get("description", ""),
                    "amount": amount,
                    "card_last_digits": tx.get("card_last_digits"),
                })

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response for image {idx+1}: {e}")
            raise HTTPException(500, f"Não foi possível interpretar as transações da imagem {idx+1}")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Erro ao processar screenshot {idx+1}: {e}")
            raise HTTPException(500, f"Erro ao processar imagem {idx+1}: {str(e)}")

    # Store for confirmation
    _pending_imports[file_id] = {
        "transactions": all_parsed,
        "file_path": str(UPLOAD_DIR / f"{file_id}_0.png"),
        "created_at": datetime.utcnow().isoformat(),
    }

    return {
        "data": {
            "file_id": file_id,
            "transaction_count": len(all_parsed),
            "total_amount": round(total, 2),
            "transactions": all_parsed,
        }
    }


@router.post("/manual")
async def create_manual_transaction(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Criar uma transação manual."""
    from app.models import Invoice as InvoiceModel
    from app.services.categorization_service import get_categorization_engine

    description = data.get("description", "").strip()
    amount = float(data.get("amount", 0))
    tx_date_str = data.get("date", "")
    who = data.get("who", "LUCAS")
    category_name = data.get("category", "")
    billing_month = data.get("billing_month", "")
    bank_slug = data.get("bank_slug", "")

    if not description:
        raise HTTPException(400, "Descrição é obrigatória")
    if amount <= 0:
        raise HTTPException(400, "Valor deve ser positivo")

    try:
        tx_date = date.fromisoformat(tx_date_str)
    except (ValueError, KeyError):
        tx_date = date.today()

    if not billing_month:
        billing_month = tx_date.strftime("%Y-%m")

    # Get member
    member_result = await db.execute(select(Member).where(Member.name == who))
    member = member_result.scalar_one_or_none()
    if not member:
        member_result = await db.execute(select(Member).limit(1))
        member = member_result.scalar_one_or_none()

    # Get card
    card = None
    if bank_slug:
        card_result = await db.execute(
            select(CreditCard).where(CreditCard.bank == bank_slug).limit(1)
        )
        card = card_result.scalar_one_or_none()

    if not card:
        card_result = await db.execute(select(CreditCard).limit(1))
        card = card_result.scalar_one_or_none()

    if not card:
        card = CreditCard(
            member_id=member.id if member else 1,
            bank=bank_slug or "manual",
            last_digits="0000",
            is_active=True,
        )
        db.add(card)
        await db.flush()

    # Find or create a manual invoice for this month
    inv_result = await db.execute(
        select(InvoiceModel).where(
            InvoiceModel.card_id == card.id,
            InvoiceModel.reference_month == billing_month,
            InvoiceModel.source_type == "MANUAL",
        )
    )
    invoice = inv_result.scalar_one_or_none()
    if not invoice:
        invoice = InvoiceModel(
            card_id=card.id,
            reference_month=billing_month,
            total_amount=0,
            status="confirmed",
            source_type="MANUAL",
            parsed_at=datetime.utcnow(),
        )
        db.add(invoice)
        await db.flush()

    # Categorize
    cat_engine = await get_categorization_engine(db)
    category_id, subcategory = cat_engine.categorize(description)

    transaction = Transaction(
        invoice_id=invoice.id,
        card_id=card.id,
        member_id=member.id if member else None,
        category_id=category_id,
        transaction_date=tx_date,
        description=description,
        raw_description=description,
        amount=amount,
        who=who,
        billing_month=billing_month,
        source_type="MANUAL",
        subcategory=subcategory,
    )
    db.add(transaction)

    # Update invoice total
    invoice.total_amount = float(invoice.total_amount or 0) + amount

    await db.commit()

    logger.info(f"✅ Manual transaction created: {description} R${amount}")

    return {
        "data": {
            "id": transaction.id,
            "date": transaction.transaction_date.isoformat(),
            "description": transaction.description,
            "amount": str(transaction.amount),
            "who": transaction.who,
            "billing_month": transaction.billing_month,
        }
    }



@router.post("/import-screenshot/{file_id}/confirm")
async def confirm_screenshot_import(
    file_id: str,
    reference_month: Optional[str] = None,
    bank_slug: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Confirmar importação de transações extraídas do screenshot."""
    pending = _pending_imports.get(file_id)
    if not pending:
        raise HTTPException(404, "Importação não encontrada. Faça upload novamente.")

    try:
        # Get default member and card
        member_result = await db.execute(select(Member).where(Member.name == "LUCAS"))
        member = member_result.scalar_one_or_none()
        if not member:
            member_result = await db.execute(select(Member).limit(1))
            member = member_result.scalar_one()

        # Get or create a "manual" invoice for screenshot imports
        from app.models import Invoice as InvoiceModel

        # Find card by bank_slug if provided, otherwise first card
        card = None
        if bank_slug:
            card_result = await db.execute(
                select(CreditCard).where(CreditCard.bank == bank_slug).limit(1)
            )
            card = card_result.scalar_one_or_none()

        if not card:
            card_result = await db.execute(select(CreditCard).limit(1))
            card = card_result.scalar_one_or_none()

        if not card:
            card = CreditCard(
                member_id=member.id,
                bank=bank_slug or "manual",
                last_digits="0000",
                is_active=True,
            )
            db.add(card)
            await db.flush()

        # Create a pseudo-invoice for these transactions
        # Priority: user param > pending store > current month
        ref_month = reference_month or pending.get("reference_month") or datetime.utcnow().strftime("%Y-%m")
        invoice = InvoiceModel(
            card_id=card.id,
            reference_month=ref_month,
            total_amount=sum(tx["amount"] for tx in pending["transactions"]),
            status="confirmed",
            source_type="PROJECAO_FATURA",
            parsed_at=datetime.utcnow(),
            pdf_file_path=pending["file_path"],
            pdf_hash=file_id,
        )
        db.add(invoice)
        await db.flush()

        # Create transactions
        from app.services.categorization_service import get_categorization_engine
        cat_engine = await get_categorization_engine(db)

        tx_count = 0
        for tx_data in pending["transactions"]:
            # Detect card by last digits if available
            tx_card = card
            tx_member = member
            if tx_data.get("card_last_digits"):
                digits = tx_data["card_last_digits"]
                card_r = await db.execute(
                    select(CreditCard).where(CreditCard.last_digits == digits)
                )
                found_card = card_r.scalar_one_or_none()
                if found_card:
                    tx_card = found_card

            # Categorize
            category_id, subcategory = cat_engine.categorize(tx_data["description"])

            # Parse date
            try:
                tx_date = date.fromisoformat(tx_data["date"])
            except (ValueError, KeyError):
                tx_date = date.today()

            transaction = Transaction(
                invoice_id=invoice.id,
                card_id=tx_card.id,
                member_id=tx_member.id,
                category_id=category_id,
                transaction_date=tx_date,
                description=tx_data["description"],
                raw_description=tx_data["description"],
                amount=tx_data["amount"],
                who=tx_member.name,
                billing_month=ref_month,
                source_type="PROJECAO_FATURA",
            )
            db.add(transaction)
            tx_count += 1

        await db.commit()

        # Cleanup
        del _pending_imports[file_id]

        logger.info(f"✅ Screenshot import confirmed: {tx_count} transactions saved")

        return {
            "data": {
                "status": "confirmed",
                "file_id": file_id,
                "transaction_count": tx_count,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Erro ao confirmar screenshot import: {e}")
        raise HTTPException(500, f"Erro ao salvar: {str(e)}")
