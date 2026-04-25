"""CashLab — Parser Itaú

Extrai transações de faturas do Itaú em PDF usando pdfplumber.

Estrutura do PDF Itaú:
- Cabeçalho: Logo Itaú + nome titular + cartão parcial + vencimento + mês ref
- Seções por cartão: "Cartão final 8001 - LUCAS"
- Colunas: Data | Descrição | Valor (R$)
- Datas no formato DD/MM (sem ano — inferido do mês de referência)
- Parcelas: XX/YY dentro da descrição
- Seção separada "Lançamentos Internacionais" com USD + IOF
- Seção "Produtos e Serviços" (seguros, acelerador de pontos)

Referência: docs/APP_FINANCAS_ESPECIFICACOES.md → §4.2.2
"""
import re
import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, List, Tuple

import pdfplumber

from .base import BaseParser, ParsedInvoice, ParsedTransaction

logger = logging.getLogger(__name__)


# ── Regex patterns Itaú ──────────────────────────────────────────

# Data no formato Itaú: DD/MM (sem ano)
RE_DATE_SHORT = re.compile(r"(\d{2}/\d{2})")

# Data completa: DD/MM/YYYY
RE_DATE_FULL = re.compile(r"(\d{2}/\d{2}/\d{4})")

# Valor monetário: "1.234,56" ou "123,45"
RE_AMOUNT = re.compile(r"R?\$?\s*([\d.]+,\d{2})")

# Parcela no Itaú: XX/YY (duas dígitos/duas dígitos)
RE_INSTALLMENT = re.compile(r"(\d{2})/(\d{2})")

# Seção por cartão: "Cartão final 8001 - LUCAS" ou "Cartão final 8001"
RE_CARD_SECTION = re.compile(
    r"[Cc]art[aã]o\s+final\s+(\d{4})(?:\s*[-–]\s*(\w+))?", re.IGNORECASE
)

# Total da fatura
RE_TOTAL = re.compile(r"Total\s+(?:da\s+)?fatura.*?([\d.]+,\d{2})", re.IGNORECASE)

# Vencimento
RE_DUE_DATE = re.compile(r"Vencimento.*?(\d{2}/\d{2}/\d{4})", re.IGNORECASE)

# Mês de referência: "ABR/2026", "Abril 2026", "ABR 2026"
RE_REF_MONTH = re.compile(
    r"(?:Janeiro|Fevereiro|Mar[cç]o|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro"
    r"|JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)"
    r"\s*/?\.?\s*(\d{4})",
    re.IGNORECASE,
)

# Internacional: USD/EUR/GBP
RE_INTL_CURRENCY = re.compile(r"(USD|EUR|GBP)\s+([\d.]+,\d{2})", re.IGNORECASE)

# IOF
RE_IOF = re.compile(r"IOF.*?([\d.]+,\d{2})", re.IGNORECASE)

# Estorno
RE_ESTORNO = re.compile(r"(?:ESTORNO|CANCELAMENTO|CRÉDITO|CREDITO)", re.IGNORECASE)

MONTH_MAP = {
    "janeiro": "01", "fevereiro": "02", "março": "03", "marco": "03",
    "abril": "04", "maio": "05", "junho": "06",
    "julho": "07", "agosto": "08", "setembro": "09",
    "outubro": "10", "novembro": "11", "dezembro": "12",
    "jan": "01", "fev": "02", "mar": "03", "abr": "04",
    "mai": "05", "jun": "06", "jul": "07", "ago": "08",
    "set": "09", "out": "10", "nov": "11", "dez": "12",
}

# Linhas a ignorar
SKIP_PATTERNS = [
    re.compile(r"^\s*$"),
    re.compile(r"^(TOTAL|Total\s+(da\s+)?fatura|Pagamento\s+m[ií]nimo)", re.IGNORECASE),
    re.compile(r"^(Limite|Cr[eé]dito\s+dispon[ií]vel|Encargos)", re.IGNORECASE),
    re.compile(r"^(SAC|Central\s+de\s+Atendimento|Ouvidoria)", re.IGNORECASE),
    re.compile(r"^(P[aá]gina\s+\d)", re.IGNORECASE),
    re.compile(r"^(Data\s+Descri)", re.IGNORECASE),
    re.compile(r"^(Produtos?\s+e\s+Servi)", re.IGNORECASE),
    re.compile(r"^(Resumo|Parcelas\s+futuras)", re.IGNORECASE),
    re.compile(r"^(Para\s+sua\s+seguran|Dicas\s+de\s+seguran)", re.IGNORECASE),
    re.compile(r"^(www\.|itau\.com)", re.IGNORECASE),
]


class ParserItau(BaseParser):
    """
    Parser para faturas do Itaú.

    Diferenças vs BV:
    - Datas DD/MM (sem ano) — inferido do mês de referência
    - Seções por cartão incluem nome do titular: "Cartão final 8001 - LUCAS"
    - Seção separada para internacionais com USD + IOF
    - Parcelas com 2 dígitos: 03/10 (não 3/10)
    """

    def detect(self, file_path: str) -> bool:
        """Verificar se o PDF é do Itaú"""
        try:
            with pdfplumber.open(file_path) as pdf:
                # Checar metadados
                metadata = pdf.metadata or {}
                for key in ["Title", "Author", "Producer", "Creator"]:
                    val = str(metadata.get(key, "")).lower()
                    if "itau" in val or "itaú" in val:
                        return True

                # Checar texto da primeira página
                if pdf.pages:
                    text = pdf.pages[0].extract_text() or ""
                    text_lower = text.lower()
                    if "itaú" in text_lower or "itau" in text_lower:
                        return True
                    if "itaucard" in text_lower:
                        return True

            return False
        except Exception:
            return False

    def parse(self, file_path: str) -> ParsedInvoice:
        """Extrair dados completos do PDF Itaú"""
        logger.info(f"Iniciando parsing Itaú: {file_path}")

        # 1. Extrair texto
        all_text, page_texts = self._extract_text(file_path)

        # 2. Extrair metadados
        due_date = self._extract_due_date(all_text)
        ref_month = self._extract_reference_month(all_text)
        total_amount = self._extract_total(all_text)
        card_digits = self._extract_main_card(all_text)

        # 3. Extrair transações
        transactions = self._extract_transactions(all_text, ref_month)

        logger.info(
            f"Itaú parsed: {len(transactions)} transações, "
            f"total={total_amount}, ref={ref_month}, card={card_digits}"
        )

        return ParsedInvoice(
            bank="itau",
            reference_month=ref_month or "",
            due_date=due_date,
            total_amount=total_amount or Decimal("0"),
            card_last_digits=card_digits or "",
            transactions=transactions,
        )

    # ── Extração de texto ──────────────────────────────────────────

    def _extract_text(self, file_path: str) -> Tuple[str, List[str]]:
        """Extrai texto de todas as páginas"""
        page_texts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                page_texts.append(text)

        all_text = "\n".join(page_texts)
        return all_text, page_texts

    # ── Metadados ──────────────────────────────────────────────────

    def _extract_due_date(self, text: str) -> Optional[date]:
        """Extrair data de vencimento"""
        match = RE_DUE_DATE.search(text)
        if match:
            try:
                return datetime.strptime(match.group(1), "%d/%m/%Y").date()
            except ValueError:
                pass
        return None

    def _extract_reference_month(self, text: str) -> Optional[str]:
        """Extrair mês de referência: '2026-04'"""
        match = RE_REF_MONTH.search(text)
        if match:
            full_match = match.group(0)
            year = match.group(1)

            # Extrair nome do mês
            month_text = re.split(r"[/\s.]", full_match)[0].strip().lower()
            month_num = MONTH_MAP.get(month_text)

            if month_num and year:
                return f"{year}-{month_num}"

        return None

    def _extract_total(self, text: str) -> Optional[Decimal]:
        """Extrair total da fatura"""
        match = RE_TOTAL.search(text)
        if match:
            return self._parse_brl_amount(match.group(1))
        return None

    def _extract_main_card(self, text: str) -> Optional[str]:
        """Extrair últimos 4 dígitos do cartão principal (primeiro encontrado)"""
        match = RE_CARD_SECTION.search(text)
        if match:
            return match.group(1)
        return None

    # ── Transações ─────────────────────────────────────────────────

    def _extract_transactions(
        self, text: str, ref_month: Optional[str]
    ) -> List[ParsedTransaction]:
        """
        Parsing linha-a-linha das transações Itaú.

        Estratégia:
        1. Detectar seções por cartão ("Cartão final XXXX - NOME")
        2. Para cada linha, tentar extrair: data (DD/MM) + descrição + valor
        3. Inferir ano da data pelo mês de referência
        4. Detectar seção de internacionais para marcar is_international
        """
        transactions = []
        current_card = None
        current_member_name = None
        is_international_section = False
        lines = text.split("\n")

        # Inferir ano e mês do mês de referência
        if ref_month:
            ref_year = int(ref_month.split("-")[0])
            ref_month_num = int(ref_month.split("-")[1])
        else:
            ref_year = datetime.now().year
            ref_month_num = datetime.now().month

        for line in lines:
            line = line.strip()

            # Pular linhas inúteis
            if self._should_skip_line(line):
                continue

            # Detectar seção de internacionais
            if re.search(r"Lan[cç]amentos\s+Internacionais", line, re.IGNORECASE):
                is_international_section = True
                continue

            if re.search(r"Lan[cç]amentos\s+Nacionais", line, re.IGNORECASE):
                is_international_section = False
                continue

            # Detectar seção de cartão com nome do titular
            card_match = RE_CARD_SECTION.search(line)
            if card_match:
                current_card = card_match.group(1)
                current_member_name = card_match.group(2)  # pode ser None
                continue

            # IOF isolado — pular (IOF já é tratado na transação internacional)
            if re.match(r"^\s*IOF\s", line, re.IGNORECASE):
                # Extrair IOF e aplicar à última transação internacional
                if transactions and transactions[-1].is_international:
                    iof_match = RE_IOF.search(line)
                    if iof_match:
                        iof_amount = self._parse_brl_amount(iof_match.group(1))
                        if iof_amount:
                            transactions[-1] = ParsedTransaction(
                                date=transactions[-1].date,
                                description=transactions[-1].description,
                                raw_description=transactions[-1].raw_description,
                                amount=transactions[-1].amount,
                                installment_num=transactions[-1].installment_num,
                                installment_total=transactions[-1].installment_total,
                                is_international=True,
                                iof_amount=iof_amount,
                                card_last_digits=transactions[-1].card_last_digits,
                            )
                continue

            # Tentar parsear como transação
            transaction = self._parse_transaction_line(
                line, current_card, ref_year, ref_month_num, is_international_section
            )
            if transaction:
                transactions.append(transaction)

        return transactions

    def _parse_transaction_line(
        self,
        line: str,
        current_card: Optional[str],
        ref_year: int,
        ref_month_num: int,
        is_international: bool,
    ) -> Optional[ParsedTransaction]:
        """
        Parsear uma linha como transação Itaú.

        Formato: "DD/MM  DESCRIÇÃO  1.234,56"
        - Data DD/MM (sem ano) — inferir pelo mês de referência
        - Parcelas: "DESCRIÇÃO 03/10" (2 dígitos / 2 dígitos)
        """
        # Precisa começar com uma data DD/MM
        date_match = re.match(r"(\d{2}/\d{2})\s+", line)
        if not date_match:
            return None

        date_str = date_match.group(1)

        # Precisa ter um valor no final da linha
        amount_matches = list(RE_AMOUNT.finditer(line))
        if not amount_matches:
            return None

        last_amount_match = amount_matches[-1]

        # Extrair a data (inferir ano)
        try:
            tx_day = int(date_str.split("/")[0])
            tx_month = int(date_str.split("/")[1])
            tx_year = self._infer_year(tx_month, ref_month_num, ref_year)
            tx_date = date(tx_year, tx_month, tx_day)
        except (ValueError, IndexError):
            return None

        # Extrair o valor
        amount = self._parse_brl_amount(last_amount_match.group(1))
        if amount is None:
            return None

        # Extrair a descrição (entre a data e o valor)
        desc_start = date_match.end()
        desc_end = last_amount_match.start()
        raw_description = line[desc_start:desc_end].strip()

        if not raw_description:
            return None

        # Limpar descrição
        description = re.sub(r"\s+", " ", raw_description).strip()

        # Extrair parcelas (formato Itaú: 03/10)
        installment_num = None
        installment_total = None

        # Procurar parcela no final da descrição (antes do valor)
        inst_match = RE_INSTALLMENT.search(description)
        if inst_match:
            num = int(inst_match.group(1))
            total = int(inst_match.group(2))
            # Validar que parece parcela (não uma data)
            if 1 <= num <= total <= 99 and total > 1:
                installment_num = num
                installment_total = total
                description_clean = RE_INSTALLMENT.sub("", description).strip()
            else:
                description_clean = description
        else:
            description_clean = description

        # Verificar estorno (valor negativo)
        is_estorno = bool(RE_ESTORNO.search(description))
        if is_estorno:
            amount = -abs(amount)

        return ParsedTransaction(
            date=tx_date,
            description=description_clean,
            raw_description=raw_description,
            amount=amount,
            installment_num=installment_num,
            installment_total=installment_total,
            is_international=is_international,
            card_last_digits=current_card,
        )

    # ── Helpers ────────────────────────────────────────────────────

    def _should_skip_line(self, line: str) -> bool:
        """Verificar se a linha deve ser ignorada"""
        for pattern in SKIP_PATTERNS:
            if pattern.search(line):
                return True
        return False

    @staticmethod
    def _infer_year(tx_month: int, ref_month: int, ref_year: int) -> int:
        """
        Inferir o ano de uma transação pelo mês de referência.

        Transações da fatura de Abril/2026 com datas em Março → mesmo ano.
        Transações com meses muito posteriores ao ref_month → ano anterior.
        Ex: Fatura Jan/2026 com transação em Dez → Dez/2025.
        """
        if tx_month > ref_month + 2:
            return ref_year - 1
        return ref_year

    @staticmethod
    def _parse_brl_amount(value_str: str) -> Optional[Decimal]:
        """'1.234,56' → Decimal('1234.56')"""
        try:
            cleaned = value_str.replace(".", "").replace(",", ".")
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None
