"""CashLab — Detector automático de banco do PDF"""
import logging
from .base import BaseParser

logger = logging.getLogger(__name__)


def detect_bank(file_path: str) -> str:
    """
    Detecta qual banco emitiu o PDF da fatura.
    
    Tenta cada parser na ordem de prioridade.
    Retorna 'bv', 'itau', 'nubank' ou 'unknown'.
    """
    from .parser_bv import ParserBV
    from .parser_itau import ParserItau
    from .parser_nubank import ParserNubank

    parsers = [
        ("bv", ParserBV()),
        ("itau", ParserItau()),
        ("nubank", ParserNubank()),
    ]

    for bank_name, parser in parsers:
        try:
            if parser.detect(file_path):
                logger.info(f"Banco detectado: {bank_name}")
                return bank_name
        except Exception as e:
            logger.warning(f"Erro ao detectar {bank_name}: {e}")
            continue

    logger.warning(f"Banco não identificado para: {file_path}")
    return "unknown"


def get_parser(bank: str) -> BaseParser:
    """
    Factory: retorna o parser correto para o banco identificado.
    
    Args:
        bank: 'bv', 'itau' ou 'nubank'
    
    Returns:
        BaseParser: instância do parser específico
    
    Raises:
        ValueError: se o banco não for suportado
    """
    from .parser_bv import ParserBV
    from .parser_itau import ParserItau
    from .parser_nubank import ParserNubank

    parsers = {
        "bv": ParserBV,
        "itau": ParserItau,
        "nubank": ParserNubank,
    }

    parser_class = parsers.get(bank)
    if not parser_class:
        raise ValueError(f"Banco não suportado: {bank}")

    return parser_class()
