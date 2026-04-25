"""CashLab — Parser Nubank"""
from .base import BaseParser, ParsedInvoice


class ParserNubank(BaseParser):
    """
    Parser para faturas do Nubank.
    
    Formato do PDF Nubank:
    - Datas: DD MMM (ex: "15 Mar")
    - Formato simples sem separação por cartão
    - Parcelas: X/Y
    """

    def parse(self, file_path: str) -> ParsedInvoice:
        """Extrair dados do PDF Nubank"""
        # TODO: Implementar parsing com pdfplumber
        raise NotImplementedError("Parser Nubank ainda não implementado")

    def detect(self, file_path: str) -> bool:
        """Verificar se o PDF é do Nubank"""
        # TODO: Implementar detecção
        return False
