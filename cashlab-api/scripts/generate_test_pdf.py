"""
Gera um PDF fake no formato de fatura do Banco BV para testes.

Uso:
    python -m scripts.generate_test_pdf

Saída: tests/fixtures/fatura_bv_test.pdf
"""
from pathlib import Path


def generate_bv_test_pdf(output_path: str = None):
    """Gera um PDF de teste no formato BV que o ParserBV.detect() reconhece."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    if output_path is None:
        output_dir = Path(__file__).parent.parent / "tests" / "fixtures"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / "fatura_bv_test.pdf")

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Metadata que o detector usa
    c.setTitle("Fatura do Cartão - Banco BV")
    c.setAuthor("Banco BV S.A.")
    c.setSubject("Fatura Cartão de Crédito")

    y = height - 50

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "Banco BV")
    y -= 30

    c.setFont("Helvetica", 12)
    c.drawString(50, y, "Fatura do Cartão de Crédito")
    y -= 20
    c.drawString(50, y, "Cartão final 6740")
    y -= 20
    c.drawString(50, y, "Vencimento: 15/04/2026")
    y -= 20
    c.drawString(50, y, "Mês de referência: Abril/2026")
    y -= 40

    # Seção de lançamentos
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Lançamentos Nacionais")
    y -= 10
    c.line(50, y, width - 50, y)
    y -= 25

    # Cartão section
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Cartão final 6740")
    y -= 25

    # Transações mock
    transactions = [
        ("15/03/2026", "CASA PORTUGUESA", "89,90"),
        ("15/03/2026", "PAG*JoseDaSilva", "150,00"),
        ("16/03/2026", "PETROCAR COMBUSTIVEIS", "200,00"),
        ("17/03/2026", "SAMS CLUB", "412,35"),
        ("18/03/2026", "DROGARIA SAO PAULO", "87,50"),
        ("19/03/2026", "J PESSOA (3/8)", "325,00"),
        ("20/03/2026", "AMAZON.COM.BR", "189,90"),
        ("21/03/2026", "MERCADO LIVRE (2/5)", "299,00"),
        ("22/03/2026", "APPLE.COM/BILL", "37,90"),
        ("23/03/2026", "UBER *TRIP", "32,50"),
        ("24/03/2026", "IFOOD *RESTAURANTE", "45,80"),
        ("25/03/2026", "EXTRA FARMA", "67,30"),
    ]

    c.setFont("Helvetica", 10)
    for date_str, desc, amount in transactions:
        line = f"{date_str}    {desc}    {amount}"
        c.drawString(60, y, line)
        y -= 18

    y -= 15

    # Total
    c.setFont("Helvetica-Bold", 12)
    total = sum(
        float(a.replace(".", "").replace(",", "."))
        for _, _, a in transactions
    )
    total_str = f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    c.drawString(50, y, f"Total da fatura: {total_str}")
    y -= 30

    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(50, y, "Banco BV S.A. - CNPJ 01.149.953/0001-89")

    c.save()
    print(f"✅ PDF gerado: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_bv_test_pdf()
