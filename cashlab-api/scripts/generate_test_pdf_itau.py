"""CashLab — Gerador de PDF de fatura Itaú para testes

Gera um PDF que simula o formato real das faturas do Itaú:
- Logo/header com "Itaú"
- Seções por cartão com nome do titular
- Datas DD/MM (sem ano)
- Parcelas 03/10
- Seção de internacionais com IOF
- Resumo com total

Uso:
    python scripts/generate_test_pdf_itau.py
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from pathlib import Path

OUTPUT = Path(__file__).parent.parent / "tests" / "fixtures" / "fatura_itau_test.pdf"


def generate():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=A4)
    width, height = A4

    # ── Metadados (para detecção) ──────────────────────────────────
    c.setTitle("Fatura Itaú")
    c.setAuthor("Itaú Unibanco S.A.")

    y = height - 30 * mm

    # ── Header ─────────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 18)
    c.drawString(30 * mm, y, "Itaú Unibanco")
    y -= 10 * mm

    c.setFont("Helvetica", 11)
    c.drawString(30 * mm, y, "Fatura do Cartão de Crédito")
    y -= 8 * mm
    c.drawString(30 * mm, y, "LUCAS MESQUITA")
    y -= 8 * mm
    c.drawString(30 * mm, y, "Vencimento: 10/04/2026")
    y -= 6 * mm
    c.drawString(30 * mm, y, "Referência: Abril/2026")
    y -= 6 * mm
    c.drawString(30 * mm, y, "Total da fatura: R$ 10.962,06")
    y -= 12 * mm

    # ── Seção Cartão 8001 - LUCAS ──────────────────────────────────
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30 * mm, y, "Cartão final 8001 - LUCAS")
    y -= 8 * mm

    c.setFont("Helvetica", 9)
    c.drawString(30 * mm, y, "Data      Descrição                                    Valor (R$)")
    y -= 2 * mm
    c.line(30 * mm, y, width - 30 * mm, y)
    y -= 6 * mm

    # Transações nacionais — Cartão 8001
    transactions_8001 = [
        ("15/03", "MERCADO LIVRE 03/10", "450,00"),
        ("15/03", "UBER *TRIP", "28,90"),
        ("16/03", "PADARIA TRIGO BOM", "15,40"),
        ("17/03", "SMART FIT MENSALIDADE", "99,90"),
        ("18/03", "AMAZON.COM.BR", "234,50"),
        ("19/03", "POSTO SHELL PAULISTA", "180,00"),
        ("20/03", "DROGASIL FARMA", "67,80"),
        ("21/03", "NETFLIX.COM", "55,90"),
        ("22/03", "SUPERMERCADO EXTRA", "312,45"),
        ("23/03", "IFOOD *PIZZARIA BELA", "45,90"),
        ("24/03", "ESTORNO COMPRA DUPLICADA", "-89,00"),
        ("25/03", "RENNER SHOPPING", "189,90"),
        ("26/03", "99 TAXI", "22,50"),
        ("27/03", "APPLE.COM/BILL", "37,90"),
        ("28/03", "SHOPEE BR", "78,50"),
    ]

    c.setFont("Helvetica", 10)
    for dt, desc, val in transactions_8001:
        c.drawString(30 * mm, y, dt)
        c.drawString(50 * mm, y, desc)
        c.drawString(145 * mm, y, val)
        y -= 5 * mm

    y -= 8 * mm

    # ── Seção Cartão 5282 - JOICE ──────────────────────────────────
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30 * mm, y, "Cartão final 5282 - JOICE")
    y -= 8 * mm

    c.setFont("Helvetica", 9)
    c.drawString(30 * mm, y, "Data      Descrição                                    Valor (R$)")
    y -= 2 * mm
    c.line(30 * mm, y, width - 30 * mm, y)
    y -= 6 * mm

    transactions_5282 = [
        ("16/03", "ZARA SHOPPING IGUATEMI", "320,00"),
        ("17/03", "SEPHORA COSMETICOS", "189,90"),
        ("18/03", "C&A MODA", "145,50"),
        ("20/03", "LIVRARIA CULTURA", "78,90"),
        ("22/03", "RIACHUELO SHOPPING", "210,00"),
    ]

    c.setFont("Helvetica", 10)
    for dt, desc, val in transactions_5282:
        c.drawString(30 * mm, y, dt)
        c.drawString(50 * mm, y, desc)
        c.drawString(145 * mm, y, val)
        y -= 5 * mm

    y -= 8 * mm

    # ── Página 2: Internacionais ───────────────────────────────────
    c.showPage()
    y = height - 30 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(30 * mm, y, "Lançamentos Internacionais")
    y -= 8 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(30 * mm, y, "Cartão final 8001 - LUCAS")
    y -= 8 * mm

    c.setFont("Helvetica", 9)
    c.drawString(30 * mm, y, "Data      Descrição                                    Valor (R$)")
    y -= 2 * mm
    c.line(30 * mm, y, width - 30 * mm, y)
    y -= 6 * mm

    intl_transactions = [
        ("19/03", "GOOGLE *YOUTUBE PREMIUM", "45,90"),
        ("20/03", "CHATGPT PLUS", "109,90"),
        ("21/03", "STEAM GAMES", "89,90"),
    ]

    c.setFont("Helvetica", 10)
    for dt, desc, val in intl_transactions:
        c.drawString(30 * mm, y, dt)
        c.drawString(50 * mm, y, desc)
        c.drawString(145 * mm, y, val)
        y -= 5 * mm

    # IOF
    y -= 3 * mm
    c.setFont("Helvetica", 9)
    c.drawString(50 * mm, y, "IOF sobre transações internacionais")
    c.drawString(145 * mm, y, "16,08")
    y -= 8 * mm

    # ── Resumo ─────────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30 * mm, y, "Resumo")
    y -= 8 * mm

    c.setFont("Helvetica", 10)
    c.drawString(30 * mm, y, "Pagamento mínimo: R$ 986,58")
    y -= 6 * mm
    c.drawString(30 * mm, y, "www.itau.com.br")

    c.save()
    print(f"✅ PDF Itaú gerado: {OUTPUT}")
    print(f"   Cartão 8001 (LUCAS): {len(transactions_8001)} transações nacionais")
    print(f"   Cartão 5282 (JOICE): {len(transactions_5282)} transações nacionais")
    print(f"   Internacionais: {len(intl_transactions)} transações + IOF")


if __name__ == "__main__":
    generate()
