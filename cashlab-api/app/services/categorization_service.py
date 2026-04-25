"""CashLab — Serviço de categorização automática de transações

Usa regras regex (tabela categorization_rules) para classificar transações
com base na descrição. Regras do usuário (is_user_rule=True) têm prioridade.

Fluxo:
1. Carrega todas as regras (ordenadas por prioridade DESC)
2. Para cada transação, testa a descrição contra os patterns
3. Primeiro match → atribui category_id e subcategory
4. Sem match → categoria "Outros"
"""
import re
import logging
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CategorizationRule, Category

logger = logging.getLogger(__name__)


class CategorizationEngine:
    """Engine de categorização por regex — carrega regras do DB uma vez e aplica em batch."""

    def __init__(self):
        self._rules: list[dict] = []
        self._fallback_category_id: Optional[int] = None
        self._loaded = False

    async def load_rules(self, db: AsyncSession):
        """Carrega regras do banco, ordenadas por prioridade (user rules primeiro)."""
        result = await db.execute(
            select(CategorizationRule).order_by(
                CategorizationRule.is_user_rule.desc(),
                CategorizationRule.priority.desc(),
            )
        )
        rules = result.scalars().all()

        self._rules = []
        for rule in rules:
            try:
                compiled = re.compile(rule.pattern, re.IGNORECASE)
                self._rules.append({
                    "id": rule.id,
                    "pattern": compiled,
                    "category_id": rule.category_id,
                    "subcategory": rule.subcategory,
                    "is_user_rule": rule.is_user_rule,
                })
            except re.error as e:
                logger.warning(f"Regex inválida na regra {rule.id}: {rule.pattern} → {e}")

        # Fallback: categoria "Outros"
        cat_result = await db.execute(
            select(Category).where(Category.name == "Outros")
        )
        outros = cat_result.scalar_one_or_none()
        self._fallback_category_id = outros.id if outros else None

        self._loaded = True
        logger.info(f"Categorização: {len(self._rules)} regras carregadas")

    def categorize(self, description: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Categoriza uma descrição de transação.

        Returns:
            (category_id, subcategory) ou (fallback_id, None) se sem match
        """
        if not self._loaded:
            return self._fallback_category_id, None

        desc_upper = description.upper().strip()

        for rule in self._rules:
            if rule["pattern"].search(desc_upper):
                return rule["category_id"], rule["subcategory"]

        return self._fallback_category_id, None

    def categorize_batch(
        self, descriptions: list[str]
    ) -> list[Tuple[Optional[int], Optional[str]]]:
        """Categoriza uma lista de descrições em batch."""
        return [self.categorize(desc) for desc in descriptions]


# Singleton global — carregado uma vez por request
_engine: Optional[CategorizationEngine] = None


async def get_categorization_engine(db: AsyncSession) -> CategorizationEngine:
    """Retorna o engine de categorização (carrega regras na primeira chamada)."""
    global _engine
    if _engine is None or not _engine._loaded:
        _engine = CategorizationEngine()
        await _engine.load_rules(db)
    return _engine


def invalidate_cache():
    """Invalida o cache do engine (chamar quando regras mudam)."""
    global _engine
    _engine = None
