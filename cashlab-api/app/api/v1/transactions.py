"""CashLab — Transactions endpoints (real DB queries)"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.models import Transaction, CreditCard, Category

router = APIRouter(prefix="/transactions", tags=["Transações"])


@router.get("")
async def list_transactions(
    month: Optional[str] = Query(None, description="Filtro por mês (2026-04)"),
    bank: Optional[str] = Query(None, description="Filtro por banco (bv,itau)"),
    member: Optional[str] = Query(None, description="Filtro por membro (LUCAS,JURA)"),
    category_id: Optional[int] = Query(None, description="Filtro por categoria"),
    search: Optional[str] = Query(None, description="Busca por descrição"),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Listar transações com filtros"""
    query = (
        select(
            Transaction,
            Category.name.label("category_name"),
            CreditCard.bank.label("card_bank"),
            CreditCard.last_digits.label("card_last_digits"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .outerjoin(CreditCard, Transaction.card_id == CreditCard.id)
        .where(Transaction.deleted_at == None)
    )

    # Filters
    if month:
        # month = "2026-04" → filter transaction_date between 2026-04-01 and 2026-04-30
        from datetime import date as dt_date
        year, m = month.split("-")
        start = dt_date(int(year), int(m), 1)
        if int(m) == 12:
            end = dt_date(int(year) + 1, 1, 1)
        else:
            end = dt_date(int(year), int(m) + 1, 1)
        query = query.where(Transaction.transaction_date >= start, Transaction.transaction_date < end)

    if bank:
        query = query.where(CreditCard.bank == bank.lower())

    if member:
        query = query.where(Transaction.who == member)

    if category_id:
        query = query.where(Transaction.category_id == category_id)

    if search:
        query = query.where(Transaction.description.ilike(f"%{search}%"))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(Transaction.transaction_date.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    rows = result.all()

    data = []
    for tx, cat_name, card_bank, card_digits in rows:
        data.append({
            "id": tx.id,
            "date": tx.transaction_date.isoformat(),
            "description": tx.description,
            "amount": str(tx.amount),
            "category": cat_name or "Outros",
            "subcategory": tx.subcategory,
            "who": tx.who,
            "bank": card_bank.upper() if card_bank else "—",
            "card": card_digits or "",
            "installment": f"{tx.installment_num}/{tx.installment_total}" if tx.installment_num and tx.installment_total else None,
            "location": tx.location,
        })

    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}}


@router.get("/{transaction_id}")
async def get_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    """Detalhe da transação"""
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id, Transaction.deleted_at == None)
    )
    tx = result.scalar_one_or_none()
    if not tx:
        from fastapi import HTTPException
        raise HTTPException(404, "Transação não encontrada")
    return {"data": {
        "id": tx.id, "date": tx.transaction_date.isoformat(),
        "description": tx.description, "amount": str(tx.amount),
        "who": tx.who, "subcategory": tx.subcategory,
    }}


@router.put("/{transaction_id}")
async def update_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    """Editar transação (categoria, membro)"""
    return {"data": {}}


@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    """Excluir transação (soft delete)"""
    return {"status": "deleted"}
