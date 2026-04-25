from __future__ import annotations
"""CashLab — Base parser (padrão Strategy)"""
from typing import Optional

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class ParsedTransaction:
    """Transação extraída do PDF antes de salvar no banco"""
    date: date
    description: str
    raw_description: str
    amount: Decimal
    installment_num: Optional[int] = None
    installment_total: Optional[int] = None
    is_international: bool = False
    iof_amount: Optional[Decimal] = None
    card_last_digits: Optional[str] = None


@dataclass
class ParsedInvoice:
    """Resultado completo do parsing de uma fatura"""
    bank: str
    reference_month: str
    due_date: Optional[date]
    total_amount: Decimal
    card_last_digits: str
    transactions: list[ParsedTransaction]


class BaseParser(ABC):
    """Classe base para parsers de PDF — cada banco implementa o seu"""

    @abstractmethod
    def parse(self, file_path: str) -> ParsedInvoice:
        """Extrair dados de um PDF de fatura"""
        pass

    @abstractmethod
    def detect(self, file_path: str) -> bool:
        """Verificar se o PDF pertence a este banco"""
        pass
