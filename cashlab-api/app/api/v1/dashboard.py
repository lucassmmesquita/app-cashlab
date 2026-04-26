"""CashLab — Dashboard endpoint (dados reais do banco)

Retorna visão consolidada do mês:
- Total de receitas, despesas fixas e gastos com cartão
- Breakdown por categoria e por membro
- Breakdown por cartão/banco
- Insights financeiros (tendência, alertas, % comprometida)
"""
import logging
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.models import (
    Transaction, Invoice, CreditCard, Category, Member,
    Income, FixedExpense,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _decimal_to_str(val) -> str:
    """Convert Decimal/float/None to string with 2 decimal places."""
    if val is None:
        return "0.00"
    return f"{float(val):.2f}"


def _safe_pct(part, total) -> float:
    """Calculate percentage safely."""
    if not total or float(total) == 0:
        return 0.0
    return round(float(part) / float(total) * 100, 1)


@router.get("/{month}")
async def get_dashboard(month: str, db: AsyncSession = Depends(get_db)):
    """
    Dados consolidados do dashboard para um mês específico.

    - **month**: formato "2026-04"

    Retorna receitas, despesas, breakdowns e insights.
    """
    # ── 1. Total de Receitas (ativas + vigentes no mês) ─────────────
    income_result = await db.execute(
        select(func.coalesce(func.sum(Income.amount), 0))
        .where(
            Income.is_active == True,
            # Vigência: effective_from IS NULL ou <= month
            case(
                (Income.effective_from != None, Income.effective_from <= month),
                else_=True,
            ),
            # Vigência: effective_until IS NULL ou >= month
            case(
                (Income.effective_until != None, Income.effective_until >= month),
                else_=True,
            ),
        )
    )
    total_income = income_result.scalar() or Decimal("0")

    # ── 2. Total de Despesas Fixas (ativas + vigentes no mês) ──────
    fixed_result = await db.execute(
        select(func.coalesce(func.sum(FixedExpense.amount), 0))
        .where(
            FixedExpense.is_active == True,
            case(
                (FixedExpense.effective_from != None, FixedExpense.effective_from <= month),
                else_=True,
            ),
            case(
                (FixedExpense.effective_until != None, FixedExpense.effective_until >= month),
                else_=True,
            ),
        )
    )
    total_fixed_expenses = fixed_result.scalar() or Decimal("0")

    # ── 3. Total de Gastos com Cartão (transações do mês) ──────────
    card_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.billing_month == month,
            Transaction.deleted_at == None,
            Transaction.source_type == "FATURA",  # Apenas dados oficiais
        )
    )
    total_card_expenses = card_result.scalar() or Decimal("0")

    # Total gasto semanal (indicador)
    weekly_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.billing_month == month,
            Transaction.deleted_at == None,
            Transaction.source_type == "GASTO_SEMANAL",
        )
    )
    total_weekly_expenses = weekly_result.scalar() or Decimal("0")

    total_expenses = float(total_fixed_expenses) + float(total_card_expenses)
    balance = float(total_income) - total_expenses

    # ── 4. Breakdown por Categoria ─────────────────────────────────
    cat_result = await db.execute(
        select(
            Category.name,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
            func.count(Transaction.id).label("tx_count"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.billing_month == month,
            Transaction.deleted_at == None,
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    )
    categories_raw = cat_result.all()

    total_for_pct = float(total_card_expenses) + float(total_weekly_expenses) if (float(total_card_expenses) + float(total_weekly_expenses)) > 0 else 1

    by_category = []
    for cat_name, total, tx_count in categories_raw:
        by_category.append({
            "category_name": cat_name or "Outros",
            "total_amount": _decimal_to_str(total),
            "percentage": _safe_pct(total, total_for_pct),
            "transaction_count": tx_count,
        })

    # ── 5. Breakdown por Membro ────────────────────────────────────
    member_result = await db.execute(
        select(
            Member.name,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .outerjoin(Member, Transaction.member_id == Member.id)
        .where(
            Transaction.billing_month == month,
            Transaction.deleted_at == None,
        )
        .group_by(Member.name)
        .order_by(func.sum(Transaction.amount).desc())
    )
    members_raw = member_result.all()

    by_member = []
    for member_name, total in members_raw:
        by_member.append({
            "member_name": member_name or "Não atribuído",
            "total_amount": _decimal_to_str(total),
            "percentage": _safe_pct(total, total_for_pct),
        })

    # ── 6. Breakdown por Cartão/Banco ──────────────────────────────
    card_breakdown_result = await db.execute(
        select(
            CreditCard.bank,
            CreditCard.last_digits,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
            func.count(Transaction.id).label("tx_count"),
        )
        .outerjoin(CreditCard, Transaction.card_id == CreditCard.id)
        .where(
            Transaction.billing_month == month,
            Transaction.deleted_at == None,
        )
        .group_by(CreditCard.bank, CreditCard.last_digits)
        .order_by(func.sum(Transaction.amount).desc())
    )
    cards_raw = card_breakdown_result.all()

    by_card = []
    for bank, last_digits, total, tx_count in cards_raw:
        by_card.append({
            "bank": (bank or "").upper(),
            "last_digits": last_digits or "",
            "total_amount": _decimal_to_str(total),
            "transaction_count": tx_count,
            "percentage": _safe_pct(total, total_for_pct),
        })

    # ── 7. Insights Financeiros ────────────────────────────────────
    insights = []

    # 7a. Total gasto no cartão
    insights.append({
        "type": "info",
        "title": "Gasto total no cartão",
        "message": f"Total de gastos oficiais (faturas PDF) no mês: R$ {float(total_card_expenses):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    })

    # 7b. Impacto do cartão na receita
    if float(total_income) > 0:
        pct_income = _safe_pct(total_card_expenses, total_income)
        insights.append({
            "type": "warning" if pct_income > 70 else "info",
            "title": "Impacto na renda",
            "message": f"Cartões comprometem {pct_income}% da receita mensal",
        })

    # 7c. Alerta de limite saudável
    if float(total_income) > 0:
        pct_total = _safe_pct(total_expenses, total_income)
        if pct_total > 100:
            insights.append({
                "type": "critical",
                "title": "Déficit mensal",
                "message": f"Despesas ({pct_total}%) superam a receita. Balanço: R$ {balance:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            })
        elif pct_total > 85:
            insights.append({
                "type": "warning",
                "title": "Atenção com gastos",
                "message": f"Despesas representam {pct_total}% da receita. Margem de segurança baixa.",
            })

    # 7d. Tendência — comparar com mês anterior
    prev_month = _previous_month(month)
    prev_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.billing_month == prev_month,
            Transaction.deleted_at == None,
            Transaction.source_type == "FATURA",
        )
    )
    prev_total = float(prev_result.scalar() or 0)

    if prev_total > 0:
        variation = ((float(total_card_expenses) - prev_total) / prev_total) * 100
        trend = "subindo" if variation > 0 else "descendo"
        insights.append({
            "type": "warning" if variation > 10 else ("info" if variation > 0 else "info"),
            "title": f"Tendência de gasto: {trend}",
            "message": f"Variação de {abs(variation):.1f}% em relação ao mês anterior ({prev_month})",
        })

    # 7e. Gastos semanais como indicador antecipado
    if float(total_weekly_expenses) > 0:
        insights.append({
            "type": "info",
            "title": "Gastos semanais (prints)",
            "message": f"R$ {float(total_weekly_expenses):,.2f} registrados via prints (indicador parcial)".replace(",", "X").replace(".", ",").replace("X", "."),
        })

    # ── 8. Alertas ─────────────────────────────────────────────────
    alerts = []
    for insight in insights:
        alerts.append({
            "type": insight["type"],
            "message": f"{insight['title']}: {insight['message']}",
        })

    return {
        "data": {
            "month": month,
            "total_income": _decimal_to_str(total_income),
            "total_fixed_expenses": _decimal_to_str(total_fixed_expenses),
            "total_card_expenses": _decimal_to_str(total_card_expenses),
            "total_weekly_expenses": _decimal_to_str(total_weekly_expenses),
            "total_expenses": _decimal_to_str(total_expenses),
            "balance": _decimal_to_str(balance),
            "by_category": by_category,
            "by_member": by_member,
            "by_card": by_card,
            "insights": insights,
            "alerts": alerts,
        }
    }


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
