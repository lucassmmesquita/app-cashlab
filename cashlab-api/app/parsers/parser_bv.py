"""CashLab — Parser BV (Banco BV)

Extrai transações de faturas do Banco BV em PDF usando pdfplumber.

Estrutura do PDF BV (novo formato 2026):
- Cabeçalho: "Esta é a sua fatura de {Mês}" + "no valor de R$ X.XXX,XX"
- "Cartão BV Platinum - Master: 5213 **** **** 3776"
- Seção "Lançamentos nacionais": Data | Descrição | Localização | Valor em R$
- Datas no formato DD/MM (sem ano!) — ano inferido do vencimento
- Parcelas: "DESCRIÇÃO XX/YY" (sem parênteses)
- Separador: "NOME DO TITULAR" seguido de "Cartão 5213 **** **** XXXX"

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


# ── Regex patterns ────────────────────────────────────────────────

# Data curta: DD/MM (sem ano) — formato real do BV
RE_DATE_SHORT = re.compile(r"^(\d{2}/\d{2})\b")

# Data longa: DD/MM/YYYY (para vencimento)
RE_DATE_LONG = re.compile(r"(\d{2}/\d{2}/\d{4})")

# Valor monetário: "R$ 36,89" ou "36,89" ou "1.234,56"
RE_AMOUNT = re.compile(r"R?\$?\s*([\d.]+,\d{2})\s*$")

# Parcela: "03/05" ou "05/10" no meio da descrição (entre espaços)
# NB: Cuidado para não confundir com datas DD/MM
RE_INSTALLMENT = re.compile(r"\b(\d{2})/(\d{2})\s*$")

# Cartão completo: "Cartão BV ... : 5213 **** **** 3776" ou "Cartão 5213 **** **** 9348"
RE_CARD_FULL = re.compile(r"Cart[aã]o.*?(\d{4})\s*$", re.IGNORECASE)

# Cartão na seção de titular: "Cartão 5213 **** **** XXXX"
RE_CARD_SECTION = re.compile(r"Cart[aã]o\s+\d{4}\s+\*{4}\s+\*{4}\s+(\d{4})", re.IGNORECASE)

# Total da fatura: "no valor de R$ 13.705,53" ou "Total desta fatura R$ 13.705,53"
RE_TOTAL = re.compile(r"(?:no\s+valor\s+de|Total\s+desta\s+fatura)\s+R\$\s*([\d.]+,\d{2})", re.IGNORECASE)

# Vencimento: "Vencimento: 22/04/2026" ou "Data de Vencimento 22/04/2026"
RE_DUE_DATE = re.compile(r"[Vv]encimento[:\s]+(\d{2}/\d{2}/\d{4})")

# Mês de referência: "fatura de Abril" ou "fatura de março"
RE_REF_MONTH = re.compile(
    r"fatura\s+de\s+(Janeiro|Fevereiro|Mar[cç]o|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)",
    re.IGNORECASE,
)

# Mapeamento de mês textual → número
MONTH_MAP = {
    "janeiro": "01", "fevereiro": "02", "março": "03", "marco": "03",
    "abril": "04", "maio": "05", "junho": "06",
    "julho": "07", "agosto": "08", "setembro": "09",
    "outubro": "10", "novembro": "11", "dezembro": "12",
}

# Total de lançamentos nacionais (para ignorar como transação)
RE_TOTAL_SECTION = re.compile(r"^Total\s+l", re.IGNORECASE)

# Linhas a ignorar
SKIP_PATTERNS = [
    re.compile(r"^\s*$"),
    re.compile(r"^Total\s+l", re.IGNORECASE),  # "Total lançamentos nacionais"
    re.compile(r"^Total\s+d", re.IGNORECASE),  # "Total desta fatura"
    re.compile(r"^Pagamento\s+(efetuado|m[ií]nimo)", re.IGNORECASE),
    re.compile(r"^Data\s+Descri", re.IGNORECASE),  # Header da tabela
    re.compile(r"^(Limite|Cr[eé]dito|Encargos|SAC|Ouvidoria|Central)", re.IGNORECASE),
    re.compile(r"^\d+/\d+\s+\d+\s+\d+$"),  # Numeração de página "4/9 001 00001"
    re.compile(r"^(Pagamentos|Ajustes)$", re.IGNORECASE),
    re.compile(r"^Op[cç][oõ]es\s+de\s+pagamento", re.IGNORECASE),
    re.compile(r"^Pagamento\s+(total|parcelado)", re.IGNORECASE),
    re.compile(r"^(Sempre|Pague\s+o\s+Valor|Valores\s+n|N[aã]o\s+consegue)", re.IGNORECASE),
    re.compile(r"^(Parcele\s+em|Entrada\s+R|Parcelas\s+\d|Total\s+a\s+pagar)", re.IGNORECASE),
    re.compile(r"^Informa[cç][oõ]es", re.IGNORECASE),
    re.compile(r"^(Taxas|Produtos|Parcelamento|Rotativo|Empréstimo|Crediário|Pagamento\s+de\s+contas)", re.IGNORECASE),
    re.compile(r"^(IOF|Multa|Retirada|CET)", re.IGNORECASE),
    re.compile(r"^(As\s+taxas|Essa\s+fatura)", re.IGNORECASE),
    re.compile(r"^(Resumo\s+das\s+Transa|Saldo\s+anterior)", re.IGNORECASE),
    re.compile(r"^(Total\s+da\s+fatura\s+anterior|Compras,\s+retirada)", re.IGNORECASE),
    re.compile(r"^(Detalhamento|Cartão\s+BV\s+Platinum)", re.IGNORECASE),
]


class ParserBV(BaseParser):
    """
    Parser para faturas do Banco BV (formato 2026).

    Fluxo:
    1. Extrai todo o texto das páginas com pdfplumber
    2. Identifica metadados (vencimento, mês ref, total)
    3. Identifica seções por cartão ("Cartão 5213 **** **** XXXX")
    4. Faz parsing linha-a-linha das transações
    5. Extrai parcelas (XX/YY) das descrições
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
                    if "cartão bv" in text_lower:
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
        ref_month = self._extract_reference_month(all_text, due_date)
        total_amount = self._extract_total(all_text)
        card_digits = self._extract_main_card(all_text)

        # Armazenar para uso na inferência de ano
        self._ref_month = ref_month

        # Inferir ano de referência
        if ref_month:
            ref_year = int(ref_month.split("-")[0])
        elif due_date:
            ref_year = due_date.year
        else:
            ref_year = datetime.now().year

        # 3. Extrair transações
        transactions = self._extract_transactions(all_text, ref_year)

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

    def _extract_reference_month(self, text: str, due_date: Optional[date] = None) -> Optional[str]:
        """
        Extrair mês de referência no formato '2026-04'.
        
        O BV usa "Esta é a sua fatura de Abril" sem indicar o ano.
        O ano é inferido da data de vencimento.
        """
        match = RE_REF_MONTH.search(text)
        if match:
            month_name = match.group(1).lower()
            month_num = MONTH_MAP.get(month_name)
            
            if month_num:
                # Inferir ano da data de vencimento
                if due_date:
                    year = due_date.year
                else:
                    year = datetime.now().year
                return f"{year}-{month_num}"

        # Fallback: usar mês do vencimento
        if due_date:
            return f"{due_date.year}-{due_date.month:02d}"

        return None

    def _extract_total(self, text: str) -> Optional[Decimal]:
        """Extrair total da fatura"""
        match = RE_TOTAL.search(text)
        if match:
            return self._parse_brl_amount(match.group(1))
        return None

    def _extract_main_card(self, text: str) -> Optional[str]:
        """
        Extrair últimos 4 dígitos do cartão principal.
        Formato BV: "Cartão BV Platinum - Master: 5213 **** **** 3776"
        """
        match = RE_CARD_SECTION.search(text)
        if match:
            return match.group(1)
        return None

    # ── Transações ─────────────────────────────────────────────────

    def _extract_transactions(
        self, text: str, ref_year: int
    ) -> List[ParsedTransaction]:
        """
        Parsing linha-a-linha das transações.

        Formato real do BV:
        "22/03 IFD*LOVE YOU BURGUER L FORTALEZA R$ 36,89"
        "06/12 SHEIN *SHEIN.COM 05/05 Vila Olimpia R$ 12,25"
        
        Estratégia:
        1. Linhas que iniciam com DD/MM são candidatas a transações
        2. O último R$ X.XXX,XX da linha é o valor
        3. A descrição é o que sobra entre a data e o valor
        4. Parcelas aparecem como XX/YY no meio (ex: "05/05")
        5. Detectar seção do cartão para atribuir card_last_digits
        """
        transactions = []
        current_card = None
        lines = text.split("\n")

        in_transactions_section = False

        for line in lines:
            line = line.strip()

            # Pular linhas vazias e headers
            if self._should_skip_line(line):
                continue

            # Detectar início da seção de lançamentos
            if re.search(r"Lan[cç]amentos\s+nacionais", line, re.IGNORECASE):
                in_transactions_section = True
                continue

            # Detectar seção de pagamentos (ignorar)
            if re.search(r"^Pagamentos$", line, re.IGNORECASE):
                in_transactions_section = False
                continue

            # Detectar seção de cartão: "Cartão 5213 **** **** 9348"
            card_match = RE_CARD_SECTION.search(line)
            if card_match:
                current_card = card_match.group(1)
                in_transactions_section = False  # Reset — espera "Lançamentos" novamente
                continue

            # Se não estamos na seção de transações, pular
            if not in_transactions_section:
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
        Parsear uma linha de transação do BV.

        Formato: "22/03 IFD*LOVE YOU BURGUER L FORTALEZA R$ 36,89"
        Com parcela: "06/12 SHEIN *SHEIN.COM 05/05 Vila Olimpia R$ 12,25"
        Pagamento: "23/03 PAGAMENTO EFETUADO (-) R$ 10.429,92"
        """
        # Precisa iniciar com DD/MM
        date_match = RE_DATE_SHORT.match(line)
        if not date_match:
            return None

        # Precisa ter um valor no final: R$ XX,XX
        amount_match = RE_AMOUNT.search(line)
        if not amount_match:
            return None

        # Ignorar linhas de pagamento
        if "PAGAMENTO EFETUADO" in line.upper():
            return None

        # Extrair data
        date_str = date_match.group(1)
        try:
            day, month = date_str.split("/")
            tx_month = int(month)
            tx_day = int(day)
            
            # Inferir o ano: o BV não inclui o ano na data da transação.
            # Regra: se o mês da transação é muito posterior ao mês de referência
            # da fatura, provavelmente é do ano anterior (parcela antiga).
            # Ex: fatura abril/2026, transação em 28/06 → junho/2025 (parcela 10/10)
            # Ex: fatura abril/2026, transação em 06/12 → dezembro/2025 (parcela 5/5)
            # Ex: fatura abril/2026, transação em 22/03 → março/2026 (compra recente)
            tx_year = ref_year
            
            # Extrair mês de referência da fatura para comparação
            ref_month_num = 4  # fallback
            try:
                ref_month_num = int(self._ref_month.split("-")[1]) if hasattr(self, '_ref_month') and self._ref_month else ref_month_num
            except (ValueError, IndexError):
                pass
            
            # Se o mês da transação é > mês de referência da fatura + 1,
            # significa que é do ano anterior
            # (transação em junho para fatura de abril → ano anterior)
            if tx_month > ref_month_num + 1:
                tx_year = ref_year - 1

            tx_date = date(tx_year, tx_month, tx_day)
        except (ValueError, IndexError):
            return None

        # Extrair valor
        amount = self._parse_brl_amount(amount_match.group(1))
        if amount is None or amount <= 0:
            return None

        # Verificar se é crédito/ajuste (contém (-) antes do valor)
        if "(-)" in line:
            return None  # Ignorar ajustes/créditos

        # Extrair descrição (entre data e valor)
        desc_start = date_match.end()
        desc_end = amount_match.start()
        raw_description = line[desc_start:desc_end].strip()

        if not raw_description:
            return None

        # Limpar descrição
        description = re.sub(r"\s+", " ", raw_description).strip()

        # Extrair parcelas do BV: "DESCRIÇÃO XX/YY LOCALIZAÇÃO"
        # Parcelas aparecem como "05/05" no meio da descrição
        installment_num = None
        installment_total = None

        # Procurar padrão de parcela na descrição
        inst_match = re.search(r"\b(\d{2})/(\d{2})\b", description)
        if inst_match:
            num = int(inst_match.group(1))
            total = int(inst_match.group(2))
            # Distinguir parcela de data: parcelas têm total > 1 e num <= total
            if total > 1 and num <= total and total <= 36:
                installment_num = num
                installment_total = total
                # Remover parcela da descrição
                description = description[:inst_match.start()].strip()
                # Remover localização após a parcela
                location_after = raw_description[inst_match.end():].strip()
                # A localização é o que sobra após a parcela e antes do R$

        # Remover "R$" solto no final da descrição
        description = re.sub(r"\s*R\$\s*$", "", description).strip()

        return ParsedTransaction(
            date=tx_date,
            description=description,
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
