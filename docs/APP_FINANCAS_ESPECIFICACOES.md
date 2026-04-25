# 📱 FinançasPro — Especificações Técnicas do Aplicativo

**Versão:** 1.0  
**Data:** 24/04/2026  
**Stack:** React Native (Frontend) + Python/FastAPI (Backend)  
**Plataformas:** Android e iOS

---

## 1. VISÃO GERAL DO PRODUTO

### 1.1 Objetivo

Aplicativo mobile de controle financeiro familiar com foco em **importação automática de faturas de cartão de crédito em PDF** (BV, Itaú e Nubank), categorização de gastos, controle por membro da família e visão consolidada de orçamento.

### 1.2 Problema que Resolve

O usuário hoje controla finanças manualmente via planilhas Excel e anotações manuscritas, o que gera divergências de valores, itens esquecidos e falta de visibilidade em tempo real. O app automatiza a extração de dados das faturas PDF e entrega dashboards prontos.

### 1.3 Usuários

| Membro | Papel | Cartões |
|--------|-------|---------|
| Lucas | Titular principal | BV 6740, Itaú 8001, Itaú 9825 |
| Jura | Dependente/Cônjuge | BV 6740 (compartilhado) |
| Joice | Familiar | Itaú 5282 (adicional) |

### 1.4 Dados de Referência (já mapeados)

| Banco | Total fatura Abril/2026 | Transações | Formato PDF |
|-------|------------------------|------------|-------------|
| BV | R$ 11.971,67 | 96 | PDF com tabela estruturada |
| Itaú | R$ 10.962,06 | 166 | PDF com tabela estruturada |
| Nubank | A importar | - | PDF com tabela estruturada |
| **Consolidado** | **R$ 22.933,73** | **262** | - |

---

## 2. ARQUITETURA DO SISTEMA

### 2.1 Visão Macro

```
┌──────────────────────────┐     ┌──────────────────────────────┐
│   REACT NATIVE APP       │     │   BACKEND PYTHON (FastAPI)   │
│                          │     │                              │
│  • Telas e navegação     │◄───►│  • API REST                  │
│  • Upload de PDF         │HTTP │  • Parser de PDF por banco   │
│  • Dashboards            │JSON │  • Categorização automática  │
│  • Gestão de orçamento   │     │  • Regras de negócio         │
│  • Notificações locais   │     │  • Autenticação              │
│                          │     │                              │
│  AsyncStorage / SQLite   │     │  PostgreSQL + Redis          │
│  (cache offline)         │     │  (persistência + cache)      │
└──────────────────────────┘     └──────────────────────────────┘
```

### 2.2 Stack Tecnológico

#### Frontend — React Native

| Componente | Tecnologia | Justificativa |
|------------|------------|---------------|
| Framework | React Native 0.76+ com Expo SDK 52+ | Multiplataforma, comunidade ativa |
| Navegação | React Navigation 7 | Padrão de mercado para RN |
| Estado global | Zustand | Leve, sem boilerplate, boa DX |
| Requisições HTTP | Axios + React Query (TanStack Query) | Cache, retry, offline support |
| Gráficos | react-native-chart-kit ou Victory Native | Gráficos responsivos nativos |
| Upload de arquivo | react-native-document-picker + expo-file-system | Seleção de PDF do dispositivo |
| Armazenamento local | expo-sqlite ou WatermelonDB | Cache offline de transações |
| Estilização | NativeWind (Tailwind CSS para RN) | Produtividade, design system |
| Ícones | @expo/vector-icons (MaterialCommunityIcons) | Set completo e leve |
| Autenticação | expo-secure-store (tokens) | Armazenamento seguro |

#### Backend — Python

| Componente | Tecnologia | Justificativa |
|------------|------------|---------------|
| Framework web | FastAPI 0.110+ | Async, validação automática, OpenAPI |
| ORM | SQLAlchemy 2.0 + Alembic | Migrações robustas, tipagem |
| Banco de dados | PostgreSQL 16 | JSONB para metadados flexíveis |
| Cache | Redis 7 | Sessões, rate limiting |
| Parser PDF | pdfplumber + tabula-py + camelot | Extração de tabelas de PDF |
| OCR (fallback) | pytesseract + Pillow | PDFs escaneados/imagem |
| Autenticação | python-jose (JWT) + bcrypt | Token-based, stateless |
| Validação | Pydantic v2 | Schemas tipados |
| Task queue | Celery + Redis | Processamento assíncrono de PDFs |
| Testes | pytest + httpx | Cobertura de API e parsers |
| Deploy | Docker + Docker Compose | Reprodutibilidade |

---

## 3. MODELO DE DADOS

### 3.1 Diagrama ER (PostgreSQL)

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│   users      │────►│  family_     │◄────│   members        │
│              │     │  groups      │     │                  │
│ id (PK)      │     │              │     │ id (PK)          │
│ email        │     │ id (PK)      │     │ family_group_id  │
│ password_hash│     │ name         │     │ name             │
│ family_group │     │ created_at   │     │ color (hex)      │
│ created_at   │     └──────────────┘     │ avatar_url       │
└─────────────┘                           └──────────────────┘
                                                   │
      ┌────────────────┐     ┌─────────────────────┤
      │  credit_cards   │     │                     │
      │                 │     │              ┌──────▼──────────┐
      │ id (PK)         │     │              │  transactions   │
      │ member_id (FK)  │     │              │                 │
      │ bank            │◄────┘              │ id (PK)         │
      │ last_digits     │                    │ card_id (FK)    │
      │ brand           │───────────────────►│ member_id (FK)  │
      │ limit_total     │                    │ invoice_id (FK) │
      │ due_day         │                    │ date            │
      │ active          │                    │ description     │
      └────────────────┘                    │ raw_description │
                                            │ amount          │
      ┌────────────────┐                    │ installment_num │
      │   invoices      │                    │ installment_tot │
      │                 │───────────────────►│ category_id(FK) │
      │ id (PK)         │                    │ subcategory     │
      │ card_id (FK)    │                    │ location        │
      │ reference_month │                    │ is_international│
      │ due_date        │                    │ iof_amount      │
      │ total_amount    │                    │ notes           │
      │ pdf_file_path   │                    │ created_at      │
      │ pdf_hash (MD5)  │                    └─────────────────┘
      │ parsed_at       │
      │ status          │     ┌─────────────────────┐
      └────────────────┘     │   categories         │
                              │                     │
      ┌────────────────┐     │ id (PK)              │
      │   budgets       │     │ name                 │
      │                 │     │ icon                 │
      │ id (PK)         │     │ color                │
      │ family_group_id │     │ type (fixa/variável) │
      │ category_id(FK) │     │ is_system            │
      │ month           │     └─────────────────────┘
      │ planned_amount  │
      │ actual_amount   │     ┌─────────────────────┐
      │ notes           │     │  fixed_expenses      │
      └────────────────┘     │                     │
                              │ id (PK)              │
                              │ family_group_id      │
                              │ description          │
                              │ amount               │
                              │ category_id (FK)     │
                              │ recurrence (mensal)  │
                              │ active               │
                              └─────────────────────┘

      ┌────────────────┐
      │   incomes       │
      │                 │
      │ id (PK)         │
      │ family_group_id │
      │ member_id (FK)  │
      │ source          │
      │ type (CLT/PJ/   │
      │   Benefício)    │
      │ amount          │
      │ earmarked_for   │
      │ active          │
      └────────────────┘
```

### 3.2 Categorias Pré-cadastradas (baseadas na análise real)

| ID | Categoria | Ícone sugerido | Tipo |
|----|-----------|----------------|------|
| 1 | Alimentação | 🍽️ food | Variável |
| 2 | Assinaturas e Serviços Digitais | 📱 subscription | Fixa |
| 3 | Automotivo | 🚗 car | Variável |
| 4 | Combustível | ⛽ fuel | Variável |
| 5 | Compras Online | 🛒 shopping-cart | Variável |
| 6 | Educação | 📚 book | Variável |
| 7 | Estacionamento e Transporte | 🅿️ parking | Variável |
| 8 | Farmácia e Saúde | 💊 medical | Variável |
| 9 | Lazer e Entretenimento | 🎮 gamepad | Variável |
| 10 | Moradia | 🏠 home | Fixa |
| 11 | Pets | 🐾 paw | Variável |
| 12 | Seguros | 🛡️ shield | Fixa |
| 13 | Serviços Pessoais (Estética) | ✂️ scissors | Variável |
| 14 | Supermercado | 🛒 cart | Variável |
| 15 | Transferências Pessoais | 💸 transfer | Variável |
| 16 | Vestuário | 👕 shirt | Variável |
| 17 | Tarifas Bancárias | 🏦 bank | Fixa |
| 18 | Outros | ❓ help-circle | Variável |

### 3.3 Subcategorias (exemplos do mapeamento real)

| Categoria | Subcategorias |
|-----------|---------------|
| Alimentação | Restaurante, Cafeteria, Delivery, Açaí/Sorvete, Padaria |
| Automotivo | Peças, Manutenção, Acessórios, Lavagem |
| Assinaturas | Apple (iCloud, Music, TV+, Arcade), Netflix, Canva, Uber One |
| Farmácia e Saúde | Farmácia, Drogaria, Ótica |
| Supermercado | Supermercado, Atacado (Sam's Club), Mercadinho, Distribuidora |

---

## 4. FUNCIONALIDADE PRINCIPAL — IMPORTAÇÃO DE PDF

### 4.1 Fluxo de Importação

```
Usuário seleciona PDF
        │
        ▼
Upload para o backend (multipart/form-data)
        │
        ▼
Backend detecta banco (BV / Itaú / Nubank)
  ├── Por metadados do PDF (título, emissor)
  ├── Por padrões de texto (regex no cabeçalho)
  └── Por seleção manual do usuário (fallback)
        │
        ▼
Parser específico do banco é acionado
  ├── parser_bv.py
  ├── parser_itau.py
  └── parser_nubank.py
        │
        ▼
Extração de dados:
  ├── Mês de referência e vencimento
  ├── Dados do cartão (últimos dígitos, titular)
  ├── Lista de transações (data, desc, valor, parcela)
  ├── Totais por seção (nacional, internacional, IOF)
  └── Resumo de parcelas futuras
        │
        ▼
Categorização automática (rules engine + ML futuro)
        │
        ▼
Detecção de duplicatas (hash do PDF + mês/cartão)
        │
        ▼
Atribuição de QUEM (membro responsável):
  ├── Por cartão (ex: 5282 = JOICE)
  ├── Por regra do usuário (ex: J PESSOA = JURA)
  └── Pendente de revisão manual
        │
        ▼
Retorna JSON com transações para revisão no app
        │
        ▼
Usuário confirma / edita / salva
```

### 4.2 Especificação dos Parsers por Banco

#### 4.2.1 Parser BV (`parser_bv.py`)

**Estrutura do PDF BV identificada:**

```
CABEÇALHO:
  - "Fatura do Cartão" + últimos dígitos
  - Mês de referência
  - Vencimento
  - Limite total / Limite disponível

SEÇÃO "Lançamentos Nacionais":
  Colunas: Data | Descrição | Valor (R$)
  - Parcelas aparecem como "DESCRIÇÃO (X/Y)"
  - Lançamentos agrupados por cartão adicional
  - Separadores de seção: "Cartão final XXXX"

SEÇÃO "Resumo":
  - Total da fatura
  - Pagamento mínimo
  - Encargos
  - Parcelas futuras (12 meses)

RODAPÉ:
  - Informações de contato e SAC
```

**Regras de extração BV:**

```python
# Padrões regex para o BV
PATTERNS_BV = {
    "data": r"(\d{2}/\d{2}/\d{4})",           # DD/MM/YYYY
    "valor": r"R?\$?\s*([\d.]+,\d{2})",         # 1.234,56 ou 123,45
    "parcela": r"\((\d+)/(\d+)\)",              # (X/Y)
    "cartao_secao": r"Cart[aã]o\s+final\s+(\d{4})",
    "total_fatura": r"Total\s+da\s+fatura.*?([\d.]+,\d{2})",
    "limite": r"Limite\s+total.*?([\d.]+,\d{2})",
    "vencimento": r"Vencimento.*?(\d{2}/\d{2}/\d{4})",
}

# Mapeamento cartão → membro (configurável pelo usuário)
CARD_MEMBER_MAP_BV = {
    "6740": "LUCAS",  # titular
}

# Descrições que indicam membro específico (regras do usuário)
MEMBER_RULES_BV = {
    "J PESSOA": "JURA",
    "PAGUE MENOS": "JURA",   # farmácia da Jura
    "EXTRA FARMA": "JURA",
    "BM SERVIÇOS": "JURA",
    "COMETA": "JURA",
}
```

#### 4.2.2 Parser Itaú (`parser_itau.py`)

**Estrutura do PDF Itaú identificada:**

```
CABEÇALHO:
  - Logo Itaú
  - Nome do titular
  - Número do cartão (parcial)
  - Vencimento e mês de referência

SEÇÕES POR CARTÃO:
  "Cartão final 8001 - LUCAS" (titular)
  "Cartão final 9825 - LUCAS" (adicional)
  "Cartão final 5282 - JOICE" (adicional)

  Colunas: Data | Descrição | Valor (R$)
  - Internacional em seção separada com IOF

SEÇÃO "Lançamentos Internacionais":
  - Valor em USD + cotação + valor em BRL
  - IOF calculado por transação

SEÇÃO "Produtos e Serviços":
  - Seguros, acelerador de pontos, etc.

RESUMO:
  - Total por cartão
  - Total geral
  - Pagamento mínimo
  - Parcelas futuras
```

**Regras de extração Itaú:**

```python
PATTERNS_ITAU = {
    "data": r"(\d{2}/\d{2})",                    # DD/MM (sem ano)
    "valor": r"([\d.]+,\d{2})",
    "parcela": r"(\d{2})/(\d{2})",               # XX/YY dentro da descrição
    "cartao_secao": r"[Cc]art[aã]o\s+final\s+(\d{4})\s*[-–]\s*(\w+)",
    "internacional": r"(USD|EUR|GBP)\s+([\d.]+,\d{2})",
    "iof": r"IOF.*?([\d.]+,\d{2})",
    "estorno": r"(?:ESTORNO|CANCELAMENTO|CRÉDITO)",
}

CARD_MEMBER_MAP_ITAU = {
    "8001": "LUCAS",
    "9825": "LUCAS",
    "5282": "JOICE",
}
```

#### 4.2.3 Parser Nubank (`parser_nubank.py`)

**Estrutura esperada do PDF Nubank (a ser refinada após importação):**

```
CABEÇALHO:
  - Logo Nubank
  - Nome do titular
  - Vencimento
  - Total da fatura

TRANSAÇÕES:
  Formato simplificado:
  Data | Descrição | Valor
  - Parcelas: "DESCRIÇÃO X/Y"
  - Sem separação por cartão adicional (Nubank é individual)

RESUMO:
  - Total
  - Pagamento mínimo
  - Crédito rotativo
```

**Regras de extração Nubank:**

```python
PATTERNS_NUBANK = {
    "data": r"(\d{2}\s+\w{3})",                  # DD MMM (ex: "15 Mar")
    "valor": r"([\d.]+,\d{2})",
    "parcela": r"(\d+)/(\d+)",
    "total": r"Total.*?([\d.]+,\d{2})",
    "vencimento": r"Vencimento.*?(\d{2}/\d{2}/\d{4})",
}

# Mapeamento de meses abreviados PT-BR
MESES_NUBANK = {
    "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4,
    "MAI": 5, "JUN": 6, "JUL": 7, "AGO": 8,
    "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12
}
```

### 4.3 Motor de Categorização Automática

```python
# Dicionário de regras baseado nos dados reais já mapeados
CATEGORIZATION_RULES = {
    # Alimentação
    r"CASA PORTUGUESA|BUTCHER|ALDEOTA RUA|CHURRASCARIA|PIZZA|ERIVALDO": 
        ("Alimentação", "Restaurante"),
    r"MERCADINHO|SAM'?S CLUB|ENTRE AMIGOS|SUPERMERCADO|MERCADO": 
        ("Supermercado", "Supermercado"),
    r"A[CÇ]A[IÍ]|PITANGA|SORVETE": 
        ("Alimentação", "Açaí/Sorvete"),
    r"CONVENI[EÊ]NCIA|ANCORA|DISTRIBUIDORA": 
        ("Supermercado", "Distribuidora"),
    
    # Automotivo
    r"STONE\s*C[AE]R|RL\s*AUTO|TOP\s*CAR|CR[\.\s]*PE[CÇ]AS|BM[\.\s]*AUTOS": 
        ("Automotivo", "Peças e Manutenção"),
    r"PETRO\s*CAR|POSTO|SHELL|BR\s*DISTRIBUI|COMBUST[IÍ]VEL|IPIRANGA": 
        ("Combustível", "Combustível"),
    r"ZUL|ESTACIONAMENTO|ZONA\s*AZUL|ESTAPAR": 
        ("Estacionamento e Transporte", "Estacionamento"),
    
    # Digital / Assinaturas
    r"APPLE\.COM|APPLE\s*BILL": 
        ("Assinaturas e Serviços Digitais", "Apple"),
    r"NETFLIX": 
        ("Assinaturas e Serviços Digitais", "Netflix"),
    r"CANVA": 
        ("Assinaturas e Serviços Digitais", "Canva"),
    r"UBER\s*ONE|UBER\s*TRIP|UBER\s*EATS": 
        ("Assinaturas e Serviços Digitais", "Uber"),
    r"SPOTIFY": 
        ("Assinaturas e Serviços Digitais", "Spotify"),
    r"AMAZON\s*PRIME|AMZN": 
        ("Assinaturas e Serviços Digitais", "Amazon"),
    
    # Farmácia
    r"PAGUE\s*MENOS|EXTRA\s*FARMA|DROGASIL|DROGARIA|FARM[AÁ]CIA": 
        ("Farmácia e Saúde", "Farmácia"),
    
    # Serviços Pessoais
    r"J\s*PESSOA|EST[EÉ]TICA|SAL[AÃ]O|BELEZA|BARBEARIA": 
        ("Serviços Pessoais (Estética)", "Estética"),
    
    # Vestuário
    r"ZARA|LUPO|RENNER|C&A|RIACHUELO|HERING": 
        ("Vestuário", "Vestuário"),
    r"SEPHORA|BRAVE\s*PRATAS|JOALHERIA": 
        ("Vestuário", "Acessórios"),
    
    # Seguros
    r"CHUBB|SEGURO|PROTEÇÃO": 
        ("Seguros", "Seguro Cartão"),
    
    # Tarifas
    r"ANUIDADE|TARIFA|MENSALIDADE\s*CART": 
        ("Tarifas Bancárias", "Tarifa"),
    
    # Transporte
    r"UBER(?!\s*ONE|\s*EATS)": 
        ("Estacionamento e Transporte", "Uber Viagem"),
    r"99|CABIFY": 
        ("Estacionamento e Transporte", "App de transporte"),
    
    # Educação
    r"BRASIL\s*PARALELO|UDEMY|COURSERA|HOTMART": 
        ("Educação", "Curso Online"),
    
    # Transferências
    r"PICPAY|PIX\s*ENV|TRANSFER": 
        ("Transferências Pessoais", "PicPay/Pix"),
}
```

### 4.4 Detecção de Duplicatas

```python
def check_duplicate(invoice_hash: str, card_id: int, reference_month: str) -> bool:
    """
    Verifica duplicidade por:
    1. Hash MD5 do arquivo PDF (mesmo arquivo)
    2. Combinação cartão + mês de referência (mesma fatura re-importada)
    """
    existing = db.query(Invoice).filter(
        or_(
            Invoice.pdf_hash == invoice_hash,
            and_(
                Invoice.card_id == card_id,
                Invoice.reference_month == reference_month
            )
        )
    ).first()
    return existing is not None
```

---

## 5. TELAS DO APLICATIVO

### 5.1 Mapa de Navegação

```
Tab Navigator (Bottom)
├── 🏠 Home (Dashboard)
│   ├── Resumo do mês (receita - despesas - saldo)
│   ├── Gráfico de gastos por categoria (donut)
│   ├── Alertas e insights
│   └── Atalho para importar PDF
│
├── 💳 Cartões
│   ├── Lista de cartões cadastrados
│   │   └── Detalhe do cartão
│   │       ├── Fatura atual
│   │       ├── Histórico de faturas
│   │       └── Limite e utilização
│   ├── Importar fatura (PDF)
│   │   ├── Selecionar arquivo
│   │   ├── Detecção automática do banco
│   │   ├── Preview das transações extraídas
│   │   ├── Revisão: categorias e QUEM
│   │   └── Confirmar importação
│   └── Consolidado de faturas
│
├── 📊 Orçamento
│   ├── Visão mensal (planejado vs realizado)
│   ├── Por categoria (barra de progresso)
│   ├── Por membro (LUCAS / JURA / JOICE)
│   ├── Despesas fixas
│   └── Receitas
│
├── 📈 Relatórios
│   ├── Evolução mensal (linha temporal)
│   ├── Comparativo mês a mês
│   ├── Top gastos do mês
│   ├── Parcelamentos ativos e projeção
│   ├── Assinaturas recorrentes
│   └── Análise por membro (QUEM)
│
└── ⚙️ Configurações
    ├── Perfil e membros da família
    ├── Gerenciar cartões
    ├── Categorias personalizadas
    ├── Regras de categorização
    ├── Regras de atribuição (QUEM)
    ├── Notificações
    ├── Exportar dados (Excel/CSV)
    └── Backup e segurança
```

### 5.2 Detalhamento das Telas Principais

#### 5.2.1 Tela — Dashboard (Home)

**Layout:**

```
┌─────────────────────────────────────┐
│  Abril 2026           ◄  ►   👤    │
├─────────────────────────────────────┤
│                                     │
│  Receita Total        R$ 27.200,00  │
│  Despesas Fixas      -R$  8.095,92  │
│  Cartões             -R$ 22.933,73  │
│  ─────────────────────────────────  │
│  Saldo do Mês        -R$  3.829,65  │
│  (barra vermelha █████████░░░░░░)   │
│                                     │
├─────────────────────────────────────┤
│         [Gráfico Donut]             │
│    Alimentação  27%  ████           │
│    Serv.Pessoais 19% ███            │
│    Automotivo   17%  ██             │
│    Assinaturas   8%  █              │
│    Outros       29%  ████           │
│                                     │
├─────────────────────────────────────┤
│  ⚠️ Alertas                         │
│  • Limite BV: 99,88% utilizado      │
│  • 9 cobranças Apple: R$ 407/mês    │
│  • 3 seguros de cartão simultâneos  │
│                                     │
├─────────────────────────────────────┤
│  [📄 Importar Fatura]  botão CTA    │
└─────────────────────────────────────┘
```

**Componentes React Native:**

```jsx
// HomeScreen.tsx - estrutura
<ScrollView>
  <MonthSelector month={selectedMonth} />
  <BalanceSummaryCard 
    income={27200} 
    fixedExpenses={8095.92}
    cardExpenses={22933.73} 
  />
  <CategoryDonutChart data={categoryData} />
  <AlertsSection alerts={monthAlerts} />
  <ImportCTA onPress={navigateToImport} />
</ScrollView>
```

#### 5.2.2 Tela — Importação de PDF

**Fluxo de telas (wizard em 4 steps):**

**Step 1 — Selecionar PDF:**
```
┌─────────────────────────────────────┐
│  ← Importar Fatura         Step 1/4│
├─────────────────────────────────────┤
│                                     │
│      ┌───────────────────────┐      │
│      │                       │      │
│      │    📄 Toque para      │      │
│      │    selecionar o PDF   │      │
│      │    da sua fatura      │      │
│      │                       │      │
│      └───────────────────────┘      │
│                                     │
│  Bancos suportados:                 │
│  🟢 BV    🟢 Itaú    🟢 Nubank    │
│                                     │
│  Últimas importações:               │
│  • BV - Abril/2026 ✅               │
│  • Itaú - Abril/2026 ✅             │
│                                     │
└─────────────────────────────────────┘
```

**Step 2 — Processamento + Detecção:**
```
┌─────────────────────────────────────┐
│  ← Importar Fatura         Step 2/4│
├─────────────────────────────────────┤
│                                     │
│        ⏳ Processando PDF...        │
│        ████████░░░░░  65%           │
│                                     │
│  ✅ Banco detectado: BV             │
│  ✅ Mês: Abril/2026                 │
│  ✅ 96 transações encontradas       │
│  ✅ Total: R$ 11.971,67             │
│                                     │
│  ⚠️ Essa fatura já foi importada.   │
│     Deseja substituir?              │
│                                     │
│  [Substituir]   [Cancelar]          │
│                                     │
└─────────────────────────────────────┘
```

**Step 3 — Revisão de Transações:**
```
┌─────────────────────────────────────┐
│  ← Revisar Transações      Step 3/4│
├─────────────────────────────────────┤
│  Filtrar: [Todos▼] [Cat.▼] [Quem▼] │
├─────────────────────────────────────┤
│                                     │
│  22/12/2025                         │
│  J PESSOA (4/5)                     │
│  R$ 500,00   Cat: Estética  JURA ▼ │
│  ──────────────────────────────     │
│  22/01/2026                         │
│  MERCADINHO SÃO LUIZ               │
│  R$ 297,00   Cat: Supermercado LUCAS│
│  ──────────────────────────────     │
│  22/01/2026                         │
│  APPLE.COM/BILL                     │
│  R$ 37,90    Cat: Assinaturas LUCAS │
│  ──────────────────────────────     │
│  [... scroll ...]                   │
│                                     │
├─────────────────────────────────────┤
│  96 transações | R$ 11.971,67       │
│  [Confirmar Importação]             │
└─────────────────────────────────────┘
```

**Step 4 — Confirmação:**
```
┌─────────────────────────────────────┐
│  ← Importação Concluída    Step 4/4│
├─────────────────────────────────────┤
│                                     │
│              ✅                      │
│     Fatura importada com sucesso!   │
│                                     │
│  BV - Abril/2026                    │
│  96 transações                      │
│  R$ 11.971,67                       │
│                                     │
│  Resumo rápido:                     │
│  LUCAS: R$ 6.106,73  (51%)         │
│  JURA:  R$ 5.864,94  (49%)         │
│                                     │
│  [Ver Dashboard]  [Importar Outra]  │
│                                     │
└─────────────────────────────────────┘
```

#### 5.2.3 Tela — Transações (lista com filtros)

```
┌─────────────────────────────────────┐
│  Transações          🔍  🔽 Filtros │
├─────────────────────────────────────┤
│  Chips: [BV] [Itaú] [Nubank]       │
│         [LUCAS] [JURA] [JOICE]     │
│         [Abril/2026 ▼]             │
├─────────────────────────────────────┤
│                                     │
│  HOJE                               │
│  ┌─ 🍽️ Casa Portuguesa             │
│  │  R$ 89,90     LUCAS    BV       │
│  │  Alimentação > Restaurante       │
│  │                                  │
│  ┌─ ⛽ PETROCAR COMBUSTÍVEIS       │
│  │  R$ 200,00    LUCAS    Itaú     │
│  │  Combustível                     │
│                                     │
│  ONTEM                              │
│  ┌─ ✂️ J PESSOA (3/8)               │
│  │  R$ 325,00    JURA     BV       │
│  │  Serviços Pessoais               │
│  │                                  │
│  [... FlatList com lazy loading]    │
│                                     │
├─────────────────────────────────────┤
│  262 transações | Total: R$22.933   │
└─────────────────────────────────────┘
```

#### 5.2.4 Tela — Parcelamentos Ativos

```
┌─────────────────────────────────────┐
│  Parcelamentos Ativos        📊    │
├─────────────────────────────────────┤
│                                     │
│  Comprometimento futuro:            │
│  R$ 24.052,03 em parcelas a vencer  │
│  ████████████████████░  (gráfico)   │
│                                     │
├── Ordenar: [Valor ▼] [Restantes]───┤
│                                     │
│  🚗 STONE CAR CENTER (1/10)        │
│  R$ 390,00/mês × 10 = R$ 3.900,00  │
│  Restam: 9 parcelas     LUCAS  BV  │
│  ████░░░░░░░░░░  10%               │
│                                     │
│  🚗 RL AUTO PECAS (1/10)           │
│  R$ 317,20/mês × 10 = R$ 3.172,00  │
│  Restam: 9 parcelas     LUCAS  BV  │
│  ████░░░░░░░░░░  10%               │
│                                     │
│  ✂️ J PESSOA (1/8)                  │
│  R$ 325,00/mês × 8 = R$ 2.600,00   │
│  Restam: 7 parcelas     JURA   BV  │
│  █████░░░░░░░░░  12.5%             │
│                                     │
│  [... scroll ...]                   │
│                                     │
└─────────────────────────────────────┘
```

---

## 6. API — ENDPOINTS

### 6.1 Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/auth/register` | Cadastro de usuário |
| POST | `/api/v1/auth/login` | Login (retorna JWT) |
| POST | `/api/v1/auth/refresh` | Renovar token |
| POST | `/api/v1/auth/logout` | Invalidar token |

### 6.2 Família e Membros

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/family` | Dados do grupo familiar |
| POST | `/api/v1/family/members` | Adicionar membro |
| PUT | `/api/v1/family/members/{id}` | Editar membro |
| DELETE | `/api/v1/family/members/{id}` | Remover membro |

### 6.3 Cartões

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/cards` | Listar cartões |
| POST | `/api/v1/cards` | Cadastrar cartão |
| PUT | `/api/v1/cards/{id}` | Editar cartão |
| DELETE | `/api/v1/cards/{id}` | Desativar cartão |

### 6.4 Faturas e Importação (core)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/invoices/upload` | Upload do PDF (multipart) |
| GET | `/api/v1/invoices/upload/{task_id}/status` | Status do processamento |
| GET | `/api/v1/invoices/upload/{task_id}/preview` | Preview das transações extraídas |
| POST | `/api/v1/invoices/upload/{task_id}/confirm` | Confirmar importação |
| GET | `/api/v1/invoices` | Listar faturas importadas |
| GET | `/api/v1/invoices/{id}` | Detalhe da fatura |
| DELETE | `/api/v1/invoices/{id}` | Excluir fatura |

**Payload do upload:**
```json
// POST /api/v1/invoices/upload
// Content-Type: multipart/form-data
{
  "file": "<arquivo PDF>",
  "bank": "bv|itau|nubank|auto",    // "auto" = detecção automática
  "card_id": 1                       // opcional, associa ao cartão
}

// Response 202 Accepted
{
  "task_id": "uuid-do-processamento",
  "status": "processing",
  "estimated_seconds": 5
}
```

**Payload do preview:**
```json
// GET /api/v1/invoices/upload/{task_id}/preview
{
  "task_id": "uuid",
  "status": "completed",
  "detected_bank": "bv",
  "reference_month": "2026-04",
  "due_date": "2026-04-15",
  "total_amount": 11971.67,
  "card_last_digits": "6740",
  "is_duplicate": false,
  "transactions": [
    {
      "temp_id": 1,
      "date": "2025-12-22",
      "raw_description": "J PESSOA",
      "description": "J PESSOA",
      "amount": 500.00,
      "installment_num": 4,
      "installment_total": 5,
      "suggested_category": "Serviços Pessoais (Estética)",
      "suggested_subcategory": "Estética",
      "suggested_member": "JURA",
      "confidence": 0.95,
      "is_international": false,
      "location": null
    }
  ],
  "summary": {
    "total_transactions": 96,
    "by_member": { "LUCAS": 6106.73, "JURA": 5864.94 },
    "by_category": { "Alimentação": 2700.00, "Automotivo": 3900.00 }
  }
}
```

**Payload de confirmação:**
```json
// POST /api/v1/invoices/upload/{task_id}/confirm
{
  "transactions": [
    {
      "temp_id": 1,
      "category_id": 13,
      "subcategory": "Estética",
      "member_id": 2,
      "notes": "J Pessoa - parcela final em agosto"
    }
  ]
}
```

### 6.5 Transações

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/transactions` | Listar (com filtros) |
| GET | `/api/v1/transactions/{id}` | Detalhe |
| PUT | `/api/v1/transactions/{id}` | Editar (categoria, membro) |
| DELETE | `/api/v1/transactions/{id}` | Excluir |

**Query params de filtro:**
```
?month=2026-04
&bank=bv,itau
&member=LUCAS,JURA
&category_id=1,2,3
&min_amount=100
&max_amount=500
&search=apple
&has_installment=true
&sort=date_desc
&page=1
&per_page=50
```

### 6.6 Orçamento

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/budget/{month}` | Orçamento do mês |
| PUT | `/api/v1/budget/{month}` | Definir/atualizar planejado |
| GET | `/api/v1/budget/{month}/vs-actual` | Planejado vs realizado |

### 6.7 Dashboard e Relatórios

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/dashboard/{month}` | Dados consolidados do dashboard |
| GET | `/api/v1/reports/by-category` | Gastos por categoria |
| GET | `/api/v1/reports/by-member` | Gastos por membro |
| GET | `/api/v1/reports/installments` | Parcelamentos ativos |
| GET | `/api/v1/reports/subscriptions` | Assinaturas recorrentes |
| GET | `/api/v1/reports/projection` | Projeção 12 meses |
| GET | `/api/v1/reports/trend` | Evolução mensal |

### 6.8 Receitas e Despesas Fixas

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/incomes` | Listar receitas |
| POST | `/api/v1/incomes` | Cadastrar receita |
| PUT | `/api/v1/incomes/{id}` | Editar receita |
| GET | `/api/v1/fixed-expenses` | Listar despesas fixas |
| POST | `/api/v1/fixed-expenses` | Cadastrar despesa fixa |
| PUT | `/api/v1/fixed-expenses/{id}` | Editar despesa fixa |

### 6.9 Categorias e Regras

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/categories` | Listar categorias |
| POST | `/api/v1/categories` | Criar categoria custom |
| GET | `/api/v1/rules/categorization` | Regras de categorização |
| POST | `/api/v1/rules/categorization` | Criar regra |
| GET | `/api/v1/rules/member-assignment` | Regras de atribuição QUEM |
| POST | `/api/v1/rules/member-assignment` | Criar regra QUEM |

### 6.10 Exportação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/export/excel?month=2026-04` | Exportar como Excel |
| GET | `/api/v1/export/csv?month=2026-04` | Exportar como CSV |

---

## 7. ESTRUTURA DE PASTAS DO PROJETO

### 7.1 Frontend (React Native)

```
financas-pro-app/
├── app.json
├── package.json
├── tsconfig.json
├── babel.config.js
├── tailwind.config.js          # NativeWind
├── App.tsx
├── src/
│   ├── navigation/
│   │   ├── TabNavigator.tsx
│   │   ├── StackNavigator.tsx
│   │   └── types.ts
│   ├── screens/
│   │   ├── home/
│   │   │   └── HomeScreen.tsx
│   │   ├── cards/
│   │   │   ├── CardsListScreen.tsx
│   │   │   ├── CardDetailScreen.tsx
│   │   │   └── ImportInvoiceScreen.tsx
│   │   ├── budget/
│   │   │   ├── BudgetScreen.tsx
│   │   │   └── FixedExpensesScreen.tsx
│   │   ├── reports/
│   │   │   ├── ReportsScreen.tsx
│   │   │   ├── InstallmentsScreen.tsx
│   │   │   └── SubscriptionsScreen.tsx
│   │   └── settings/
│   │       ├── SettingsScreen.tsx
│   │       ├── MembersScreen.tsx
│   │       ├── CategoriesScreen.tsx
│   │       └── RulesScreen.tsx
│   ├── components/
│   │   ├── common/
│   │   │   ├── Card.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── MonthSelector.tsx
│   │   │   ├── AmountText.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   └── EmptyState.tsx
│   │   ├── dashboard/
│   │   │   ├── BalanceSummaryCard.tsx
│   │   │   ├── CategoryDonutChart.tsx
│   │   │   └── AlertsSection.tsx
│   │   ├── transactions/
│   │   │   ├── TransactionItem.tsx
│   │   │   ├── TransactionList.tsx
│   │   │   ├── FilterChips.tsx
│   │   │   └── CategoryPicker.tsx
│   │   ├── import/
│   │   │   ├── PdfUploader.tsx
│   │   │   ├── ProcessingStatus.tsx
│   │   │   ├── TransactionPreview.tsx
│   │   │   └── ImportConfirmation.tsx
│   │   └── charts/
│   │       ├── DonutChart.tsx
│   │       ├── BarChart.tsx
│   │       ├── LineChart.tsx
│   │       └── StackedBar.tsx
│   ├── services/
│   │   ├── api.ts              # Axios instance + interceptors
│   │   ├── authService.ts
│   │   ├── invoiceService.ts
│   │   ├── transactionService.ts
│   │   ├── budgetService.ts
│   │   └── reportService.ts
│   ├── store/
│   │   ├── useAuthStore.ts     # Zustand
│   │   ├── useTransactionStore.ts
│   │   ├── useBudgetStore.ts
│   │   └── useSettingsStore.ts
│   ├── hooks/
│   │   ├── useInvoiceUpload.ts
│   │   ├── useDashboard.ts
│   │   ├── useTransactions.ts
│   │   └── useMonthNavigation.ts
│   ├── utils/
│   │   ├── formatters.ts       # moeda, data, percentual
│   │   ├── colors.ts           # paleta por categoria e membro
│   │   └── constants.ts
│   └── types/
│       ├── transaction.ts
│       ├── invoice.ts
│       ├── category.ts
│       ├── member.ts
│       └── budget.ts
└── assets/
    ├── icons/
    └── images/
```

### 7.2 Backend (Python/FastAPI)

```
financas-pro-api/
├── pyproject.toml              # Dependências (Poetry ou uv)
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app + CORS + lifespan
│   ├── config.py               # Settings via pydantic-settings
│   ├── database.py             # SQLAlchemy engine + session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── family.py
│   │   ├── member.py
│   │   ├── card.py
│   │   ├── invoice.py
│   │   ├── transaction.py
│   │   ├── category.py
│   │   ├── budget.py
│   │   ├── income.py
│   │   ├── fixed_expense.py
│   │   └── rule.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── card.py
│   │   ├── invoice.py
│   │   ├── transaction.py
│   │   ├── budget.py
│   │   └── report.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Dependências (get_db, get_current_user)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # Agrega todos os routers
│   │       ├── auth.py
│   │       ├── cards.py
│   │       ├── invoices.py     # Upload + processamento
│   │       ├── transactions.py
│   │       ├── budget.py
│   │       ├── reports.py
│   │       ├── incomes.py
│   │       ├── fixed_expenses.py
│   │       ├── categories.py
│   │       └── export.py
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py             # Classe abstrata BaseParser
│   │   ├── detector.py         # Detecta banco do PDF
│   │   ├── parser_bv.py
│   │   ├── parser_itau.py
│   │   ├── parser_nubank.py
│   │   └── categorizer.py      # Motor de categorização
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── invoice_service.py
│   │   ├── transaction_service.py
│   │   ├── budget_service.py
│   │   ├── report_service.py
│   │   └── export_service.py
│   └── tasks/
│       ├── __init__.py
│       └── pdf_processing.py   # Celery task para processar PDF
├── migrations/
│   └── versions/               # Alembic migrations
├── tests/
│   ├── conftest.py
│   ├── test_parsers/
│   │   ├── test_parser_bv.py
│   │   ├── test_parser_itau.py
│   │   ├── test_parser_nubank.py
│   │   └── fixtures/           # PDFs de teste
│   ├── test_api/
│   │   ├── test_auth.py
│   │   ├── test_invoices.py
│   │   └── test_transactions.py
│   └── test_services/
│       └── test_categorizer.py
└── scripts/
    ├── seed_categories.py      # Popular categorias iniciais
    └── import_existing.py      # Migrar dados das planilhas Excel
```

---

## 8. REGRAS DE NEGÓCIO

### 8.1 Importação

| # | Regra | Descrição |
|---|-------|-----------|
| RN-01 | Duplicata por hash | Se o MD5 do PDF já existe, avisa e oferece substituir |
| RN-02 | Duplicata por mês | Se já existe fatura do mesmo cartão+mês, avisa |
| RN-03 | Validação de total | Total extraído deve bater com total declarado no PDF (tolerância ±R$ 0,05) |
| RN-04 | Parcelas futuras | Ao importar parcela X/Y, criar projeção das parcelas X+1 a Y nos meses seguintes |
| RN-05 | Estornos | Valores negativos ou com flag "ESTORNO" devem subtrair do total |
| RN-06 | IOF | Transações internacionais: separar valor + IOF como campos distintos |
| RN-07 | Anuidade | Categorizar automaticamente como "Tarifas Bancárias", sem membro (QUEM = "-") |

### 8.2 Categorização

| # | Regra | Descrição |
|---|-------|-----------|
| RN-08 | Regra do usuário prevalece | Se o usuário criou uma regra manual, ela tem prioridade sobre a automática |
| RN-09 | Aprendizado por edição | Se o usuário recategoriza uma transação, criar sugestão de regra |
| RN-10 | Confiança | Mostrar nível de confiança da categorização (alta >80%, média 50-80%, baixa <50%) |
| RN-11 | Sem categoria | Transações não categorizadas vão para "Outros" e geram alerta |

### 8.3 Atribuição de Membro (QUEM)

| # | Regra | Descrição |
|---|-------|-----------|
| RN-12 | Por cartão | Cartão adicional tem membro fixo (ex: 5282 = JOICE) |
| RN-13 | Por descrição | Regras regex por descrição (ex: J PESSOA = JURA) |
| RN-14 | Divisão de valor | Permitir dividir uma transação entre membros (ex: J PESSOA 22/12: R$ 400 JURA + R$ 100 LUCAS) |
| RN-15 | Pendente | Se nenhuma regra se aplica, marcar como "PENDENTE" para revisão |

### 8.4 Orçamento

| # | Regra | Descrição |
|---|-------|-----------|
| RN-16 | Verba carimbada | Receitas marcadas como "carimbadas" (ex: Auxílio Alimentação → Lazer) não entram no cálculo de sobra livre |
| RN-17 | Alerta de estouro | Notificação quando categoria ultrapassar 80% do planejado |
| RN-18 | Despesa fixa vs variável | Despesas fixas são projetadas automaticamente nos meses futuros |

---

## 9. DADOS PRÉ-CONFIGURADOS (MIGRAÇÃO INICIAL)

### 9.1 Receitas

| Fonte | Valor | Tipo | Observação |
|-------|-------|------|------------|
| IRede CLT | R$ 6.700,00 | CLT | Salário registrado |
| IRede PJ | R$ 17.500,00 | PJ | Pró-labore / nota fiscal |
| Totalis | R$ 2.000,00 | PJ/Extra | Receita adicional |
| Auxílio Alimentação | R$ 1.000,00 | Benefício | Reservado para LAZER (carimbado) |
| **Total** | **R$ 27.200,00** | | |

### 9.2 Despesas Fixas

| Descrição | Valor | Categoria |
|-----------|-------|-----------|
| Aluguel + Condomínio + Água + Gás | R$ 4.645,50 | Moradia |
| Financiamento Carro (6/36) | R$ 1.650,42 | Automotivo |
| Energia (média) | R$ 800,00 | Moradia |
| Pais Joice | R$ 500,00 | Transferências Pessoais |
| Pais Lucas | R$ 500,00 | Transferências Pessoais |
| **Total** | **R$ 8.095,92** | |

### 9.3 Cartões Cadastrados

| Banco | Últimos dígitos | Titular | Limite |
|-------|----------------|---------|--------|
| BV | 6740 | Lucas (+ Jura compartilhado) | R$ 24.000,00 |
| Itaú | 8001 | Lucas | R$ 23.800,00 |
| Itaú | 9825 | Lucas (adicional) | - (compartilha com 8001) |
| Itaú | 5282 | Joice (adicional) | - (compartilha com 8001) |
| Nubank | A definir | A definir | A definir |

---

## 10. INSIGHTS E ALERTAS AUTOMÁTICOS

O sistema deve gerar alertas inteligentes baseados nos padrões já identificados:

| Tipo | Condição | Mensagem exemplo |
|------|----------|------------------|
| 🔴 Crítico | Limite utilizado > 95% | "Limite do BV está 99,88% utilizado. Evite novas compras." |
| 🟡 Atenção | Duplicidade de assinaturas | "Apple.com/Bill cobrado nos 2 cartões: R$ 407/mês. Consolidar?" |
| 🟡 Atenção | Múltiplos seguros | "3 seguros de cartão ativos: R$ 29,22/mês. Manter apenas 1?" |
| 🟢 Info | Parcela finalizando | "J PESSOA (4/5): última parcela em maio. -R$ 500/mês liberado." |
| 🟢 Info | Comparativo mensal | "Alimentação subiu 15% vs mês anterior." |
| 🔴 Crítico | Déficit mensal | "Déficit de R$ 3.829,65 este mês. Receitas < Despesas." |

---

## 11. REQUISITOS NÃO-FUNCIONAIS

| Requisito | Meta | Detalhes |
|-----------|------|---------|
| Performance | PDF processado em < 10s | Parser otimizado + task async |
| Offline | Funcionar sem internet | SQLite local com sync |
| Segurança | Dados criptografados | JWT + HTTPS + bcrypt + SecureStore |
| Privacidade | PDFs não armazenados em cloud | Processados e descartados (ou opt-in para backup) |
| Responsividade | Suportar telas de 5" a 7" | Design responsivo com NativeWind |
| Disponibilidade | API 99.5% uptime | Docker + health checks + monitoramento |
| Backup | Export mensal automático | Excel e JSON para Google Drive |

---

## 12. FASES DE DESENVOLVIMENTO

### Fase 1 — MVP (8-12 semanas)

| Semana | Entrega |
|--------|---------|
| 1-2 | Setup do projeto (RN + FastAPI + DB + Docker) |
| 3-4 | Backend: Modelos, auth, CRUD de cartões/membros/categorias |
| 5-6 | Backend: Parsers BV + Itaú + endpoint de upload |
| 7-8 | Frontend: Navegação, Home, tela de importação |
| 9-10 | Frontend: Lista de transações com filtros + dashboard |
| 11-12 | Integração E2E, testes, polish, deploy |

**Entregável:** App funcional com importação de PDF (BV + Itaú), dashboard e lista de transações.

### Fase 2 — Orçamento e Relatórios (4-6 semanas)

| Entrega |
|---------|
| Parser Nubank |
| Tela de orçamento (planejado vs realizado) |
| Relatórios por categoria, membro e evolução mensal |
| Parcelamentos ativos com projeção |
| Alertas e insights automáticos |

### Fase 3 — Refinamento (4 semanas)

| Entrega |
|---------|
| Sistema de regras editável pelo usuário |
| Divisão de transação entre membros |
| Exportação Excel/CSV |
| Notificações push (vencimento de fatura, estouro de orçamento) |
| Dark mode |
| Migração dos dados das planilhas existentes |

### Fase 4 — Evolução Futura

| Feature | Descrição |
|---------|-----------|
| OCR avançado | Suporte a PDFs escaneados/imagem |
| Integração Open Finance | Importação automática via API dos bancos |
| Meta de economia | Gamificação com desafios (52 semanas, etc.) |
| Assistente IA | Chatbot integrado para dúvidas financeiras |
| Multi-família | Suporte a mais de um grupo familiar |
| Web app | Dashboard completo em versão web |

---

## 13. VARIÁVEIS DE AMBIENTE (.env)

```env
# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/financas_pro
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=sua-chave-secreta-jwt-256-bits
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Upload
MAX_PDF_SIZE_MB=10
UPLOAD_DIR=/tmp/invoices
KEEP_PDF_AFTER_PARSE=false

# Frontend
API_BASE_URL=https://api.financaspro.app/api/v1
```

---

## 14. COMANDOS DE SETUP

### Backend

```bash
# Criar ambiente
cd financas-pro-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Banco de dados
docker compose up -d postgres redis
alembic upgrade head
python scripts/seed_categories.py

# Rodar
uvicorn app.main:app --reload --port 8000

# Worker Celery (em outro terminal)
celery -A app.tasks worker --loglevel=info
```

### Frontend

```bash
# Criar projeto
npx create-expo-app financas-pro-app --template tabs
cd financas-pro-app

# Dependências
npx expo install react-native-chart-kit react-native-svg
npx expo install expo-document-picker expo-file-system
npx expo install expo-secure-store expo-sqlite
npm install @react-navigation/native @react-navigation/bottom-tabs
npm install zustand axios @tanstack/react-query
npm install nativewind tailwindcss

# Rodar
npx expo start
```

---

## 15. CONSIDERAÇÕES DE SEGURANÇA

| Aspecto | Implementação |
|---------|---------------|
| Senhas | Bcrypt com salt rounds = 12 |
| Tokens | JWT com expiração curta (30min access + 7d refresh) |
| Upload | Validar MIME type (application/pdf), limitar tamanho (10MB) |
| SQL Injection | SQLAlchemy com parametrized queries |
| XSS | React Native não é vulnerável (não renderiza HTML) |
| Rate limiting | 100 req/min por IP via Redis |
| CORS | Restrito ao domínio do app |
| PDFs | Não armazenar em produção (processar e descartar) |
| Dados sensíveis | Nunca armazenar número completo do cartão |
| Logs | Nunca logar dados financeiros em produção |

---

*Documento gerado em 24/04/2026 — Baseado na análise real das faturas BV (R$ 11.971,67 / 96 transações) e Itaú (R$ 10.962,06 / 166 transações) do período de Abril/2026.*
