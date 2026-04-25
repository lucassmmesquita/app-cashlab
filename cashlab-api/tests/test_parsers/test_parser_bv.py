"""CashLab — Testes do Parser BV"""
import pytest
from decimal import Decimal
from datetime import date

from app.parsers.parser_bv import ParserBV


@pytest.fixture
def parser():
    return ParserBV()


@pytest.fixture
def fake_invoice_text():
    return """
Fatura do Cartão
Banco BV

Vencimento: 10/05/2026
Abril/2026

Cartão final 6740

Lançamentos Nacionais

Data Descrição Valor
15/03/2026  NETFLIX.COM AMSTERDAM NLD  49,90
18/03/2026  CASA PORTUGUESA FORTALEZA  89,90
20/03/2026  SAM'S CLUB FORTALEZA  325,50
22/03/2026  STONE CAR AUTO PECAS (3/10)  450,00
25/03/2026  PAGUE MENOS FORTALEZA  67,80
01/04/2026  APPLE.COM/BILL  14,90
05/04/2026  SPOTIFY BRAZIL  34,90
10/04/2026  ALDEOTA RUA CANUTO  120,00
12/04/2026  MERCADINHO ENTRE AMIGOS  45,60
15/04/2026  PETRO CAR COMBUSTIVEL  250,00
18/04/2026  EXTRA FARMA FORTALEZA  89,50
20/04/2026  J PESSOA ESTETICA  180,00

Total da fatura 1.718,00
Pagamento mínimo 171,80
"""


# ── Testes de conversão de valores ──────────────────────────────

class TestParseAmount:
    def test_valor_com_milhar(self, parser):
        assert parser._parse_brl_amount("1.234,56") == Decimal("1234.56")

    def test_valor_simples(self, parser):
        assert parser._parse_brl_amount("123,45") == Decimal("123.45")

    def test_valor_grande(self, parser):
        assert parser._parse_brl_amount("11.971,67") == Decimal("11971.67")

    def test_valor_pequeno(self, parser):
        assert parser._parse_brl_amount("89,90") == Decimal("89.90")


# ── Testes de parsing de linha ──────────────────────────────────

class TestParseTransactionLine:
    def test_transacao_simples(self, parser):
        tx = parser._parse_transaction_line(
            "15/04/2026  NETFLIX.COM AMSTERDAM NLD  49,90",
            "6740", 2026,
        )
        assert tx is not None
        assert tx.description == "NETFLIX.COM AMSTERDAM NLD"
        assert tx.amount == Decimal("49.90")
        assert tx.card_last_digits == "6740"
        assert tx.date == date(2026, 4, 15)

    def test_transacao_com_parcela(self, parser):
        tx = parser._parse_transaction_line(
            "10/03/2026  STONE CAR AUTO PECAS (3/10)  325,00",
            "6740", 2026,
        )
        assert tx is not None
        assert tx.installment_num == 3
        assert tx.installment_total == 10
        assert tx.amount == Decimal("325.00")
        assert "STONE CAR AUTO PECAS" in tx.description

    def test_linha_sem_data_retorna_none(self, parser):
        tx = parser._parse_transaction_line(
            "Total da fatura  11.971,67",
            "6740", 2026,
        )
        assert tx is None

    def test_linha_sem_valor_retorna_none(self, parser):
        tx = parser._parse_transaction_line(
            "15/04/2026  DESCRICAO SEM VALOR",
            "6740", 2026,
        )
        assert tx is None


# ── Testes de skip ──────────────────────────────────────────────

class TestShouldSkipLine:
    def test_linha_vazia(self, parser):
        assert parser._should_skip_line("") is True

    def test_total_fatura(self, parser):
        assert parser._should_skip_line("Total da fatura") is True

    def test_limite(self, parser):
        assert parser._should_skip_line("Limite total") is True

    def test_pagina(self, parser):
        assert parser._should_skip_line("Página 1") is True

    def test_transacao_normal(self, parser):
        assert parser._should_skip_line("15/04/2026 Netflix 49,90") is False


# ── Testes de metadados ─────────────────────────────────────────

class TestMetadata:
    def test_extract_due_date(self, parser, fake_invoice_text):
        due = parser._extract_due_date(fake_invoice_text)
        assert due == date(2026, 5, 10)

    def test_extract_reference_month(self, parser, fake_invoice_text):
        ref = parser._extract_reference_month(fake_invoice_text)
        assert ref == "2026-04"

    def test_extract_total(self, parser, fake_invoice_text):
        total = parser._extract_total(fake_invoice_text)
        assert total == Decimal("1718.00")

    def test_extract_main_card(self, parser, fake_invoice_text):
        card = parser._extract_main_card(fake_invoice_text)
        assert card == "6740"


# ── Teste de extração completa ──────────────────────────────────

class TestExtractTransactions:
    def test_extract_all_transactions(self, parser, fake_invoice_text):
        txs = parser._extract_transactions(fake_invoice_text, "2026-04")
        assert len(txs) == 12

    def test_parcela_detectada(self, parser, fake_invoice_text):
        txs = parser._extract_transactions(fake_invoice_text, "2026-04")
        stone = [t for t in txs if "STONE" in t.description]
        assert len(stone) == 1
        assert stone[0].installment_num == 3
        assert stone[0].installment_total == 10

    def test_card_digits_propagated(self, parser, fake_invoice_text):
        txs = parser._extract_transactions(fake_invoice_text, "2026-04")
        for tx in txs:
            assert tx.card_last_digits == "6740"
