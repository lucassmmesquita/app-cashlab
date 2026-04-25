# CashLab API

Backend do aplicativo CashLab — controle financeiro familiar com importação automática de faturas de cartão de crédito em PDF.

## Stack

- **Python 3.12+** com **FastAPI**
- **SQLAlchemy 2.0** (async) + **SQLite** (dev) / **PostgreSQL** (prod)
- **Pydantic v2** para validação
- **JWT** para autenticação
- **pdfplumber** para parsing de PDFs

## Setup Rápido

```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env

# 4. Rodar o servidor
uvicorn app.main:app --reload --port 8000
```

O servidor estará disponível em `http://localhost:8000`.

- **Swagger UI:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

## Estrutura do Projeto

```
cashlab-api/
├── app/
│   ├── main.py          # FastAPI app + CORS + lifespan
│   ├── core/            # Config, database, security
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── api/v1/          # Routers (endpoints)
│   ├── services/        # Lógica de negócio
│   ├── parsers/         # Parsers de PDF (BV, Itaú, Nubank)
│   └── tasks/           # Tasks assíncronas (Celery)
├── scripts/             # Seeds e utilitários
├── tests/               # Testes
├── uploads/             # PDFs temporários
├── requirements.txt
└── .env.example
```

## Bancos Suportados

| Banco | Parser | Status |
|-------|--------|--------|
| BV | `parser_bv.py` | 🔜 A implementar |
| Itaú | `parser_itau.py` | 🔜 A implementar |
| Nubank | `parser_nubank.py` | 🔜 A implementar |
