"""CashLab — Parser BV (Banco BV)

Extrai transações de faturas do Banco BV em PDF usando pdfplumber.

Estrutura do PDF BV:
- Cabeçalho: "Fatura do Cartão" + últimos dígitos + mês referência + vencimento
- Seção "Lançamentos Nacionais": Data | Descrição | Valor (R$)
- Parcelas: "DESCRIÇÃO (X/Y)"
- Separadores de cartão: "Cartão final XXXX"
- Datas no formato DD/MM/YYYY
- Valores no formato 1.234,56

Referência: docs/APP_FINANCAS_ESPECIFICACOES.md → §4.2.1
"""
import re
import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, List, Tuple

import pdfplumber

from .base import BaseParser, ParsedInvoice, ParsedTransaction

logger = logging.getLogger(__name__)


# ── Regex patterns extraídos da especificação ────────────────────────

# Data no formato BV: DD/MM/YYYY
RE_DATE = re.compile(r"(\d{2}/\d{2}/\d{4})")

# Valor monetário: "1.234,56" ou "123,45" (com ou sem R$)
RE_AMOUNT = re.compile(r"R?\$?\s*([\d.]+,\d{2})")

# Parcela: (X/Y)
RE_INSTALLMENT = re.compile(r"\((\d+)/(\d+)\)")

# Seção por cartão: "Cartão final 6740"
RE_CARD_SECTION = re.compile(r"Cart[aã]o\s+final\s+(\d{4})", re.IGNORECASE)

# Total da fatura
RE_TOTAL = re.compile(r"Total\s+da\s+fatura.*?([\d.]+,\d{2})", re.IGNORECASE)

# Vencimento
RE_DUE_DATE = re.compile(r"Vencimento.*?(\d{2}/\d{2}/\d{4})", re.IGNORECASE)

# Mês de referência: "Abril/2026", "MAR/2026", etc.
RE_REF_MONTH = re.compile(
    r"(?:Janeiro|Fevereiro|Mar[cç]o|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro"
    r"|JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)"
    r"\s*/?\s*(\d{4})",
    re.IGNORECASE,
)

# Mapeamento de mês textual → número
MONTH_MAP = {
    "janeiro": "01", "fevereiro": "02", "março": "03", "marco": "03",
    "abril": "04", "maio": "05", "junho": "06",
    "julho": "07", "agosto": "08", "setembro": "09",
    "outubro": "10", "novembro": "11", "dezembro": "12",
    "jan": "01", "fev": "02", "mar": "03", "abr": "04",
    "mai": "05", "jun": "06", "jul": "07", "ago": "08",
    "set": "09", "out": "10", "nov": "11", "dez": "12",
}

# Linhas a ignorar durante parsing de transações
SKIP_PATTERNS = [
    re.compile(r"^\s*$"),
    re.compile(r"^(TOTAL|Total\s+da\s+fatura|Pagamento\s+m[ií]nimo)", re.IGNORECASE),
    re.compile(r"^(Limite|Cr[eé]dito\s+dispon[ií]vel|Encargos)", re.IGNORECASE),
    re.compile(r"^(SAC|Central\s+de\s+Atendimento|Ouvidoria)", re.IGNORECASE),
    re.compile(r"^(P[aá]gina\s+\d)", re.IGNORECASE),
    re.compile(r"^(Lan[cç]amentos\s+Nacionais|Lan[cç]amentos\s+Internacionais)", re.IGNORECASE),
    re.compile(r"^(Data\s+Descri)", re.IGNORECASE),  # header da tabela
]

# Mapeamento cartão → membro (configurável)
CARD_MEMBER_MAP = {
    "6740": "LUCAS",
}

# Regras de membro por descrição
MEMBER_RULES = {
    "J PESSOA": "JURA",
    "PAGUE MENOS": "JURA",
    "EXTRA FARMA": "JURA",
    "BM SERVIÇOS": "JURA",
    "BM SERVICOS": "JURA",
    "COMETA": "JURA",
}


class ParserBV(BaseParser):
    """
    Parser para faturas do Banco BV.

    Fluxo:
    1. Extrai todo o texto das páginas com pdfplumber
    2. Identifica metadados (vencimento, mês ref, total)
    3. Identifica seções por cartão ("Cartão final XXXX")
    4. Faz parsing linha-a-linha das transações
    5. Extrai parcelas (X/Y) das descrições
    """

    def detect(self, file_path: str) -> bool:
        """Verificar se o PDF é do BV"""
        try:
            with pdfplumber.open(file_path) as pdf:
                # Checar metadados primeiro
                metadata = pdf.metadata or {}
                for key in ["Title", "Author", "Producer", "Creator"]:
                    val = str(metadata.get(key, "")).lower()
                    if "bv" in val or "banco bv" in val:
                        return True

                # Checar texto da primeira página
                if pdf.pages:
                    text = pdf.pages[0].extract_text() or ""
                    text_lower = text.lower()
                    if "banco bv" in text_lower or "bancodigital.com.br" in text_lower:
                        return True
                    if "bv financeira" in text_lower:
                        return True

            return False
        except Exception:
            return False

    def parse(self, file_path: str) -> ParsedInvoice:
        """Extrair dados completos do PDF BV"""
        logger.info(f"Iniciando parsing BV: {file_path}")

        # 1. Extrair todo o texto
        all_text, page_texts = self._extract_text(file_path)

        # 2. Extrair metadados do cabeçalho
        due_date = self._extract_due_date(all_text)
        ref_month = self._extract_reference_month(all_text)
        total_amount = self._extract_total(all_text)
        card_digits = self._extract_main_card(all_text)

        # 3. Extrair transações
        transactions = self._extract_transactions(all_text, ref_month)

        logger.info(
            f"BV parsed: {len(transactions)} transações, "
            f"total={total_amount}, ref={ref_month}, card={card_digits}"
        )

        return ParsedInvoice(
            bank="bv",
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
        """Extrair mês de referência no formato '2026-04'"""
        match = RE_REF_MONTH.search(text)
        if match:
            full_match = match.group(0)
            year = match.group(1)

            # Extrair nome do mês do match
            month_text = full_match.split("/")[0].split()[0].strip().lower()
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
        """Extrair últimos 4 dígitos do cartão principal"""
        match = RE_CARD_SECTION.search(text)
        if match:
            return match.group(1)
        return None

    # ── Transações ─────────────────────────────────────────────────

    def _extract_transactions(
        self, text: str, ref_month: Optional[str]
    ) -> List[ParsedTransaction]:
        """
        Parsing linha-a-linha das transações.

        Estratégia:
        1. Identificar a seção de lançamentos
        2. Para cada linha, tentar extrair: data + descrição + valor
        3. Linhas sem data → continuação da descrição anterior
        4. Detectar seção do cartão para atribuir card_last_digits
        """
        transactions = []
        current_card = None
        lines = text.split("\n")

        # Ano padrão do mês de referência
        ref_year = int(ref_month.split("-")[0]) if ref_month else datetime.now().year

        in_transactions_section = False

        for line in lines:
            line = line.strip()

            # Pular linhas vazias e headers
            if self._should_skip_line(line):
                continue

            # Detectar início da seção de lançamentos
            if re.search(r"Lan[cç]amentos\s+(Nacionais|Internacionais)", line, re.IGNORECASE):
                in_transactions_section = True
                continue

            # Detectar fim da seção (Resumo, Pagamento Mínimo, etc.)
            if re.search(r"(Resumo\s+de\s+parcelas|Pagamento\s+m[ií]nimo|Total\s+da\s+fatura)", line, re.IGNORECASE):
                # Não para — pode ter mais transações em outra seção
                pass

            # Detectar seção de cartão
            card_match = RE_CARD_SECTION.search(line)
            if card_match:
                current_card = card_match.group(1)
                continue

            # Tentar parsear como transação
            transaction = self._parse_transaction_line(line, current_card, ref_year)
            if transaction:
                transactions.append(transaction)

        return transactions

    def _parse_transaction_line(
        self, line: str, current_card: Optional[str], ref_year: int
    ) -> Optional[ParsedTransaction]:
        """
        Tentar parsear uma linha como transação.

        Formato esperado: "DD/MM/YYYY  DESCRIÇÃO DO LANÇAMENTO  1.234,56"
        Variações:
        - "DD/MM/YYYY  DESCRIÇÃO (3/10)  1.234,56"
        - "DD/MM/YYYY  DESCRIÇÃO  -1.234,56" (crédito)
        """
        # Precisa ter uma data no início
        date_match = RE_DATE.search(line)
        if not date_match:
            return None

        # Precisa ter um valor no final
        # Pegar o ÚLTIMO valor da linha (o mais à direita)
        amount_matches = list(RE_AMOUNT.finditer(line))
        if not amount_matches:
            return None

        last_amount_match = amount_matches[-1]

        # Extrair a data
        try:
            tx_date = datetime.strptime(date_match.group(1), "%d/%m/%Y").date()
        except ValueError:
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

        # Limpar descrição — remover caracteres estranhos
        description = re.sub(r"\s+", " ", raw_description).strip()

        # Extrair parcelas da descrição
        installment_num = None
        installment_total = None
        inst_match = RE_INSTALLMENT.search(description)
        if inst_match:
            installment_num = int(inst_match.group(1))
            installment_total = int(inst_match.group(2))
            # Limpar parcela da descrição para ter a descrição limpa
            description_clean = RE_INSTALLMENT.sub("", description).strip()
        else:
            description_clean = description

        # Verificar se é crédito (valor negativo)
        if "-" in line[desc_end:last_amount_match.start() + 1]:
            amount = -amount

        return ParsedTransaction(
            date=tx_date,
            description=description_clean,
            raw_description=raw_description,
            amount=amount,
            installment_num=installment_num,
            installment_total=installment_total,
            is_international=False,
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
    def _parse_brl_amount(value_str: str) -> Optional[Decimal]:
        """
        Converte string BRL para Decimal.
        '1.234,56' → Decimal('1234.56')
        '123,45' → Decimal('123.45')
        """
        try:
            # Remove pontos de milhar, troca vírgula decimal por ponto
            cleaned = value_str.replace(".", "").replace(",", ".")
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None
