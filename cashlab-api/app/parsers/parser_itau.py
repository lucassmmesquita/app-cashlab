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

# Seção por cartão: "Cartão final 8001 - LUCAS" ou "Cartão final 8001" ou "Cartão 5122.XXXX.XXXX.8001"
RE_CARD_SECTION = re.compile(
    r"[Cc]art[aã]o\s+(?:final\s+)?(\d{4})(?:\s*[-–]\s*(\w+))?", re.IGNORECASE
)
RE_CARD_MASKED = re.compile(r"[Cc]art[aã]o\s+\d{4}\.\w+\.\w+\.(\d{4})")

# Total da fatura (handles no-space: "Totaldestafatura 10.962,06" or "Total desta fatura 10.962,06")
RE_TOTAL = re.compile(r"Total\s*(?:de\s*)?(?:sta|desta|da)?\s*fatura\s*([\d.]+,\d{2})", re.IGNORECASE)

# Vencimento (handles no-space: "Vencimento:09/04/2026" or "vencimento em 09/04/2026")
RE_DUE_DATE = re.compile(r"[Vv]encimento[:\s]*(?:em\s*)?(\d{2}/\d{2}/\d{4})")

# Mês de referência: "ABR/2026", "Abril 2026", "Fechamento:02/05/2026"
RE_REF_MONTH = re.compile(
    r"(?:Janeiro|Fevereiro|Mar[cç]o|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro"
    r"|JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)"
    r"\s*/?\.?\s*(\d{4})",
    re.IGNORECASE,
)
# Fallback: extract ref month from "Fechamento:DD/MM/YYYY"
RE_FECHAMENTO = re.compile(r"[Ff]echamento[:\s]*(\d{2})/(\d{2})/(\d{4})")

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
    re.compile(r"Total\s*(de\s*)?(sta|desta|da)?\s*fatura", re.IGNORECASE),
    re.compile(r"(Pagamento\s*m[ií]nimo|Limite|Cr[eé]dito|Encargos)", re.IGNORECASE),
    re.compile(r"(SAC|Central\s*de\s*Atendimento|Ouvidoria)", re.IGNORECASE),
    re.compile(r"(P[aá]gina\s*\d)", re.IGNORECASE),
    re.compile(r"(Data\s+Descri|DATA\s+DESCRI)", re.IGNORECASE),
    re.compile(r"(Produtos?\s*e\s*Servi|produtoseservi)", re.IGNORECASE),
    re.compile(r"(Resumo|Parcelas\s*futuras|Comprasparceladas)", re.IGNORECASE),
    re.compile(r"(Para\s*sua\s*seguran|Dicas\s*de\s*seguran)", re.IGNORECASE),
    re.compile(r"(www\.|itau\.com|Resumodafatura|Totaldafatura|Saldofinanciado)", re.IGNORECASE),
    re.compile(r"(Lan[cç]amentos\s*:?\s*compras|Lan[cç]amentos\s*:?\s*produtos)", re.IGNORECASE),
    re.compile(r"(Totaldeoutros|Totaldoslança|Fiqueatentoaos|Novotetodejuros)", re.IGNORECASE),
    re.compile(r"(SimulaçãodeCompras|SimulaçãoSaque|Próximafatura|Demaisfaturas)", re.IGNORECASE),
    re.compile(r"(ALIMENTAÇÃO|VEÍCULOS|DIVERSOS|SAÚDE|MORADIA|EDUCAÇÃO|VESTUÁRIO|TURISMO|HOBBY)", re.IGNORECASE),
    re.compile(r"(Lan[cç]amentos\s*no\s*cart|Lan[cç]amentos\s*internacionais)", re.IGNORECASE),
    re.compile(r"(Valorcompra|ValordoIOF|Valortotalfinanciado|Valorjuros|Valordaparcela)", re.IGNORECASE),
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

        # 3. Extrair transações (using dual-column aware parser)
        transactions = self._extract_transactions(all_text, ref_month)

        # 4. If total is 0, compute from transactions
        if not total_amount or total_amount == Decimal("0"):
            total_amount = sum(t.amount for t in transactions if t.amount > 0)

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
            month_text = re.split(r"[/\s.]", full_match)[0].strip().lower()
            month_num = MONTH_MAP.get(month_text)
            if month_num and year:
                return f"{year}-{month_num}"

        # Fallback: use due_date (Vencimento:09/04/2026 → 2026-04)
        due = RE_DUE_DATE.search(text)
        if due:
            parts = due.group(1).split('/')
            return f"{parts[2]}-{parts[1]}"

        # Fallback: use Fechamento date
        fech = RE_FECHAMENTO.search(text)
        if fech:
            return f"{fech.group(3)}-{fech.group(2)}"

        return None

    def _extract_total(self, text: str) -> Optional[Decimal]:
        """Extrair total da fatura"""
        match = RE_TOTAL.search(text)
        if match:
            return self._parse_brl_amount(match.group(1))
        # Fallback: "Totaldoslançamentosatuais 10.962,06"
        fallback = re.search(r"Totaldoslan[cç]amentos\w*\s+([\d.]+,\d{2})", text)
        if fallback:
            return self._parse_brl_amount(fallback.group(1))
        return None

    def _extract_main_card(self, text: str) -> Optional[str]:
        """Extrair últimos 4 dígitos do cartão principal"""
        # Try masked format first: "Cartão 5122.XXXX.XXXX.8001"
        masked = RE_CARD_MASKED.search(text)
        if masked:
            return masked.group(1)
        # Try "Cartão final 8001"
        match = RE_CARD_SECTION.search(text)
        if match:
            return match.group(1)
        return None

    # ── Transações ─────────────────────────────────────────────────

    def _extract_transactions(
        self, text: str, ref_month: Optional[str]
    ) -> List[ParsedTransaction]:
        """
        Parsing for Itaú PDFs with dual-column layout.

        The PDF has 2 columns of transactions side by side. pdfplumber merges them
        into one line like:
          "07/03 NOELIARIOMAR 7,90 14/03 POSTOVPL3 200,00"

        Strategy: find ALL DD/MM + description + amount patterns in each line.
        """
        transactions = []
        current_card = None
        is_international_section = False
        lines = text.split("\n")

        if ref_month:
            ref_year = int(ref_month.split("-")[0])
            ref_month_num = int(ref_month.split("-")[1])
        else:
            ref_year = datetime.now().year
            ref_month_num = datetime.now().month

        # Regex for a single transaction chunk: DD/MM description amount
        # Handles optional installment XX/YY between description and amount
        RE_TX_CHUNK = re.compile(
            r"(\d{2}/\d{2})\s+"            # date DD/MM
            r"(.+?)\s+"                     # description (non-greedy)
            r"(-?[\d.]+,\d{2})"             # amount
        )

        for line in lines:
            line = line.strip()

            # STOP parsing when hitting future installments section (check BEFORE skip)
            if re.search(r"(Comprasparceladas|parcelas.*pr[oó]ximas|Totalparapr[oó]ximas|Simula[cç][aã]o)", line, re.IGNORECASE):
                logger.info(f"Itaú: parando parse na seção de parcelas futuras")
                break

            if self._should_skip_line(line):
                continue

            # Detect card section
            card_masked = RE_CARD_MASKED.search(line)
            if card_masked:
                current_card = card_masked.group(1)
                continue
            card_match = RE_CARD_SECTION.search(line)
            if card_match:
                current_card = card_match.group(1)
                continue

            # Detect international section
            if re.search(r"internacionais", line, re.IGNORECASE):
                is_international_section = True
                continue

            # Find all transaction chunks in the line
            matches = list(RE_TX_CHUNK.finditer(line))
            for m in matches:
                date_str = m.group(1)
                raw_desc = m.group(2).strip()
                amount_str = m.group(3)

                if not raw_desc or len(raw_desc) < 3:
                    continue

                # Parse date
                try:
                    tx_day = int(date_str.split("/")[0])
                    tx_month = int(date_str.split("/")[1])
                    tx_year = self._infer_year(tx_month, ref_month_num, ref_year)
                    tx_date = date(tx_year, tx_month, tx_day)
                except (ValueError, IndexError):
                    continue

                # Parse amount
                amount = self._parse_brl_amount(amount_str)
                if amount is None:
                    continue

                # Extract installments from description
                installment_num = None
                installment_total = None
                desc_clean = raw_desc
                inst_match = RE_INSTALLMENT.search(raw_desc)
                if inst_match:
                    num = int(inst_match.group(1))
                    total = int(inst_match.group(2))
                    if 1 <= num <= total <= 99 and total > 1:
                        installment_num = num
                        installment_total = total
                        desc_clean = RE_INSTALLMENT.sub("", raw_desc).strip()

                # Detect estorno
                if RE_ESTORNO.search(raw_desc):
                    amount = -abs(amount)

                transactions.append(ParsedTransaction(
                    date=tx_date,
                    description=desc_clean,
                    raw_description=raw_desc,
                    amount=amount,
                    installment_num=installment_num,
                    installment_total=installment_total,
                    is_international=is_international_section,
                    card_last_digits=current_card,
                ))

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
