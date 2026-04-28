"""CashLab — Spending Goals API (Metas de Redução de Gastos)

CRUD de metas + cálculo de progresso + projeção.
Integrado ao módulo de Fluxo de Caixa.
"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.models import (
    SpendingGoal, GoalSnapshot, Transaction, CreditCard,
    FamilyGroup, Invoice,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/goals", tags=["Metas de Gastos"])


# ── Schemas ────────────────────────────────────────────────────────

class GoalCreate(BaseModel):
    card_id: Optional[int] = None
    target_reduction_pct: int = Field(..., ge=1, le=100)
    baseline_month: str  # "2026-04"
    target_month: str    # "2026-05"
    name: Optional[str] = None


class GoalUpdate(BaseModel):
    target_reduction_pct: Optional[int] = Field(None, ge=1, le=100)
    target_month: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None  # active, achieved, missed, cancelled


# ── Helpers ────────────────────────────────────────────────────────

async def _get_family_group_id(db: AsyncSession) -> int:
    """Get the first family group (single-family mode)."""
    result = await db.execute(select(FamilyGroup).limit(1))
    fg = result.scalar_one_or_none()
    return fg.id if fg else 1


async def _calc_baseline_amount(
    db: AsyncSession, baseline_month: str, card_id: Optional[int]
) -> Decimal:
    """Calculate total spending for a given month (FATURA only)."""
    query = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.billing_month == baseline_month,
        Transaction.deleted_at == None,
        Transaction.source_type == "FATURA",
    )
    if card_id:
        query = query.where(Transaction.card_id == card_id)

    result = await db.execute(query)
    return result.scalar() or Decimal("0")


async def _calc_current_spending(
    db: AsyncSession, target_month: str, card_id: Optional[int],
    source_type: Optional[str] = None,
) -> Decimal:
    """Calculate current spending for the target month."""
    query = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.billing_month == target_month,
        Transaction.deleted_at == None,
    )
    if card_id:
        query = query.where(Transaction.card_id == card_id)
    if source_type:
        query = query.where(Transaction.source_type == source_type)

    result = await db.execute(query)
    return result.scalar() or Decimal("0")


def _project_month_end(current_amount: float, days_elapsed: int, days_in_month: int) -> float:
    """Project end-of-month spending based on daily average."""
    if days_elapsed <= 0:
        return current_amount
    daily_avg = current_amount / days_elapsed
    return daily_avg * days_in_month


def _month_info(month_str: str):
    """Extract year, month number and days in month."""
    import calendar
    year, m = month_str.split("-")
    y, mo = int(year), int(m)
    days = calendar.monthrange(y, mo)[1]
    return y, mo, days


def _next_month(month: str, offset: int = 1) -> str:
    """Get month string offset months ahead."""
    y, m = month.split("-")
    year, mo = int(y), int(m)
    for _ in range(offset):
        mo += 1
        if mo > 12:
            mo = 1
            year += 1
    return f"{year}-{mo:02d}"


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("")
async def create_goal(payload: GoalCreate, db: AsyncSession = Depends(get_db)):
    """
    Criar meta de redução de gastos.

    Calcula automaticamente o baseline_amount a partir das transações
    do mês base e define o target_amount.
    """
    fg_id = await _get_family_group_id(db)

    # Calcular valor base do mês de referência
    baseline_amount = await _calc_baseline_amount(
        db, payload.baseline_month, payload.card_id
    )

    if float(baseline_amount) == 0:
        raise HTTPException(
            400,
            f"Nenhuma transação encontrada no mês {payload.baseline_month}. "
            "Importe faturas antes de criar uma meta."
        )

    # Calcular valor alvo
    target_amount = baseline_amount * (Decimal(100 - payload.target_reduction_pct) / Decimal(100))

    goal = SpendingGoal(
        family_group_id=fg_id,
        card_id=payload.card_id,
        target_reduction_pct=payload.target_reduction_pct,
        baseline_month=payload.baseline_month,
        baseline_amount=baseline_amount,
        target_amount=target_amount,
        target_month=payload.target_month,
        name=payload.name or f"Reduzir {payload.target_reduction_pct}% em {payload.target_month}",
        status="active",
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)

    logger.info(
        f"✅ Meta criada: id={goal.id}, redução={payload.target_reduction_pct}%, "
        f"baseline={baseline_amount}, target={target_amount}"
    )

    return {"data": _serialize_goal(goal)}


@router.get("")
async def list_goals(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Listar metas com status calculado."""
    query = select(SpendingGoal).where(SpendingGoal.deleted_at == None)
    if status:
        query = query.where(SpendingGoal.status == status)
    query = query.order_by(SpendingGoal.created_at.desc())

    result = await db.execute(query)
    goals = result.scalars().all()

    data = []
    for goal in goals:
        # Calcular progresso rápido
        current = await _calc_current_spending(db, goal.target_month, goal.card_id)
        data.append({
            **_serialize_goal(goal),
            "current_amount": f"{float(current):.2f}",
            "progress_pct": _calc_progress_pct(goal, current),
        })

    return {"data": data}


@router.get("/{goal_id}")
async def get_goal(goal_id: int, db: AsyncSession = Depends(get_db)):
    """Detalhe da meta com progresso e projeção completa."""
    result = await db.execute(
        select(SpendingGoal).where(
            SpendingGoal.id == goal_id, SpendingGoal.deleted_at == None
        )
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(404, "Meta não encontrada")

    # Progresso completo
    progress = await _calc_full_progress(db, goal)

    return {"data": {**_serialize_goal(goal), **progress}}


@router.get("/{goal_id}/progress")
async def get_goal_progress(goal_id: int, db: AsyncSession = Depends(get_db)):
    """
    Calcular progresso detalhado da meta.

    Inclui:
    - % atingida
    - Gasto atual vs meta
    - Projeção de valor final (mês corrente + 3 e 6 meses)
    - Categorias que mais impactam
    - Status: "dentro" | "risco" | "fora"
    """
    result = await db.execute(
        select(SpendingGoal).where(
            SpendingGoal.id == goal_id, SpendingGoal.deleted_at == None
        )
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(404, "Meta não encontrada")

    progress = await _calc_full_progress(db, goal)
    return {"data": progress}


@router.put("/{goal_id}")
async def update_goal(
    goal_id: int, payload: GoalUpdate, db: AsyncSession = Depends(get_db)
):
    """Atualizar meta."""
    result = await db.execute(
        select(SpendingGoal).where(
            SpendingGoal.id == goal_id, SpendingGoal.deleted_at == None
        )
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(404, "Meta não encontrada")

    if payload.target_reduction_pct is not None:
        goal.target_reduction_pct = payload.target_reduction_pct
        goal.target_amount = goal.baseline_amount * (
            Decimal(100 - payload.target_reduction_pct) / Decimal(100)
        )
    if payload.target_month is not None:
        goal.target_month = payload.target_month
    if payload.name is not None:
        goal.name = payload.name
    if payload.status is not None:
        goal.status = payload.status

    await db.commit()
    await db.refresh(goal)

    return {"data": _serialize_goal(goal)}


@router.delete("/{goal_id}")
async def delete_goal(goal_id: int, db: AsyncSession = Depends(get_db)):
    """Cancelar/excluir meta (soft delete)."""
    result = await db.execute(
        select(SpendingGoal).where(
            SpendingGoal.id == goal_id, SpendingGoal.deleted_at == None
        )
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(404, "Meta não encontrada")

    goal.deleted_at = datetime.utcnow()
    goal.status = "cancelled"
    await db.commit()

    return {"status": "deleted", "goal_id": goal_id}


# ── Serialization ──────────────────────────────────────────────────

def _serialize_goal(goal: SpendingGoal) -> dict:
    return {
        "id": goal.id,
        "name": goal.name,
        "card_id": goal.card_id,
        "target_reduction_pct": goal.target_reduction_pct,
        "baseline_month": goal.baseline_month,
        "baseline_amount": f"{float(goal.baseline_amount):.2f}",
        "target_amount": f"{float(goal.target_amount):.2f}",
        "target_month": goal.target_month,
        "status": goal.status,
        "created_at": goal.created_at.isoformat() if goal.created_at else None,
    }


def _calc_progress_pct(goal: SpendingGoal, current_amount) -> float:
    """Calculate simple progress percentage."""
    target = float(goal.target_amount)
    baseline = float(goal.baseline_amount)
    current = float(current_amount)

    if baseline == 0:
        return 0.0

    # Reduction achieved: how much of the target reduction has been accomplished
    reduction_needed = baseline - target
    if reduction_needed == 0:
        return 100.0

    actual_reduction = baseline - current
    pct = (actual_reduction / reduction_needed) * 100
    return round(min(max(pct, 0), 200), 1)  # Cap at 200% (overachieved)


async def _calc_full_progress(db: AsyncSession, goal: SpendingGoal) -> dict:
    """Calculate full progress with projections."""
    target_month = goal.target_month
    baseline = float(goal.baseline_amount)
    target = float(goal.target_amount)

    # Current spending (FATURA — official)
    current_fatura = await _calc_current_spending(db, target_month, goal.card_id, "FATURA")
    # Current spending (PROJECAO_FATURA — indicador)
    current_weekly = await _calc_current_spending(db, target_month, goal.card_id, "PROJECAO_FATURA")
    current_total = float(current_fatura) + float(current_weekly)

    # Days elapsed
    today = date.today()
    year, mo, days_in_month = _month_info(target_month)
    target_start = date(year, mo, 1)
    days_elapsed = max((today - target_start).days, 0)
    if days_elapsed > days_in_month:
        days_elapsed = days_in_month

    # Projection: end of current month
    projected_current = _project_month_end(current_total, days_elapsed, days_in_month)

    # Status
    if current_total > baseline:
        goal_status = "fora"
    elif projected_current > target * 1.1:
        goal_status = "risco"
    else:
        goal_status = "dentro"

    # Progress percentage
    progress_pct = _calc_progress_pct(goal, current_total)

    # Top categories (most spending)
    cat_result = await db.execute(
        select(
            func.coalesce(func.min(Transaction.category_id), 0).label("cat_id"),
            func.count(Transaction.id).label("tx_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .where(
            Transaction.billing_month == target_month,
            Transaction.deleted_at == None,
        )
        .group_by(Transaction.category_id)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
    )
    top_categories_raw = cat_result.all()

    from app.models import Category
    top_categories = []
    for cat_id, tx_count, total in top_categories_raw:
        cat_name = "Outros"
        if cat_id:
            cat_r = await db.execute(select(Category.name).where(Category.id == cat_id))
            name = cat_r.scalar_one_or_none()
            if name:
                cat_name = name
        top_categories.append({
            "category": cat_name,
            "amount": f"{float(total):.2f}",
            "transaction_count": tx_count,
        })

    # Snapshots (weekly history)
    snap_result = await db.execute(
        select(GoalSnapshot)
        .where(GoalSnapshot.goal_id == goal.id)
        .order_by(GoalSnapshot.snapshot_date.desc())
    )
    snapshots = [
        {
            "id": s.id,
            "date": s.snapshot_date.isoformat(),
            "amount": f"{float(s.current_amount):.2f}",
            "source": s.source,
            "notes": s.notes,
        }
        for s in snap_result.scalars().all()
    ]

    # Projection for 3 and 6 months
    projections = []
    if days_elapsed > 0 and current_total > 0:
        daily_avg = current_total / days_elapsed
        for offset_label, offset_months in [("3_meses", 3), ("6_meses", 6)]:
            # Simple projection: assume same daily average
            future_month = _next_month(target_month, offset_months)
            fy, fm, future_days = _month_info(future_month)
            # Apply a trend reduction based on goal commitment (optimistic model)
            trend_factor = max(1 - (goal.target_reduction_pct / 100) * 0.5, 0.3)
            projected_future = daily_avg * future_days * (trend_factor ** (offset_months / 3))
            projections.append({
                "month": future_month,
                "label": offset_label,
                "projected_amount": f"{projected_future:.2f}",
                "target_amount": f"{target:.2f}",
                "within_target": projected_future <= target,
            })

    # Estimated time to reach goal
    estimated_months = None
    if current_total > target and days_elapsed > 0:
        # Already over target — not reachable this month
        estimated_months = None
    elif baseline > 0 and current_total < target:
        estimated_months = 0  # Already within target

    return {
        "current_amount_fatura": f"{float(current_fatura):.2f}",
        "current_amount_weekly": f"{float(current_weekly):.2f}",
        "current_amount_total": f"{current_total:.2f}",
        "baseline_amount": f"{baseline:.2f}",
        "target_amount": f"{target:.2f}",
        "projected_month_end": f"{projected_current:.2f}",
        "progress_pct": progress_pct,
        "goal_status": goal_status,
        "days_elapsed": days_elapsed,
        "days_in_month": days_in_month,
        "top_categories": top_categories,
        "snapshots": snapshots,
        "projections": projections,
        "estimated_months_to_goal": estimated_months,
        "feedback": _generate_feedback(goal_status, progress_pct, projected_current, target),
    }


def _generate_feedback(status: str, progress_pct: float, projected: float, target: float) -> dict:
    """Generate user-facing feedback based on goal progress."""
    if status == "dentro":
        if progress_pct >= 100:
            return {
                "emoji": "🎉",
                "title": "Meta atingida!",
                "message": "Parabéns! Você está dentro da meta de redução.",
                "type": "success",
            }
        return {
            "emoji": "✅",
            "title": "No caminho certo",
            "message": f"Progresso de {progress_pct}% — continue assim!",
            "type": "success",
        }
    elif status == "risco":
        diff = projected - target
        return {
            "emoji": "⚠️",
            "title": "Atenção: risco de ultrapassar",
            "message": f"Projeção indica R$ {diff:,.2f} acima da meta. Reduza gastos nas categorias principais.".replace(",", "X").replace(".", ",").replace("X", "."),
            "type": "warning",
        }
    else:  # fora
        return {
            "emoji": "🚨",
            "title": "Fora da meta",
            "message": "Gastos já ultrapassaram o valor base. Revise gastos urgentemente.",
            "type": "critical",
        }
