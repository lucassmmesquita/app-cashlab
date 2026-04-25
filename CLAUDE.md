# CLAUDE.md — Contexto do Projeto FinançasPro

## O que é este projeto

Aplicativo mobile de controle financeiro familiar. A funcionalidade principal é **importar faturas de cartão de crédito em PDF** (BV, Itaú e Nubank), extrair as transações automaticamente, categorizar os gastos e identificar qual membro da família é responsável por cada transação.

O projeto substitui um controle manual feito via planilhas Excel que consome ~4h/mês e apresenta erros frequentes (itens esquecidos, valores divergentes).

## Stack

- **Frontend:** React Native (Expo) com TypeScript
- **Backend:** Python com FastAPI
- **Banco de dados:** PostgreSQL
- **Fila de processamento:** Redis + Celery
- **Infraestrutura:** Docker

## Quem usa

A família tem 3 membros que compartilham cartões de crédito. Cada transação precisa ser atribuída ao responsável (campo chamado "QUEM"):

| Membro | Papel | Cartões |
|--------|-------|---------|
| LUCAS | Titular | BV 6740, Itaú 8001, Itaú 9825 |
| JURA | Cônjuge | BV 6740 (compartilhado com Lucas) |
| JOICE | Familiar | Itaú 5282 (adicional) |

## Situação financeira real (base para o app)

Os dados abaixo foram extraídos da análise real das faturas de Abril/2026 e servem como referência para testes, seeds e validação.

**Receitas mensais: R$ 27.200,00**
- IRede CLT: R$ 6.700 | IRede PJ: R$ 17.500 | Totalis: R$ 2.000
- Auxílio Alimentação: R$ 1.000 (verba carimbada para Lazer — não entra no cálculo de sobra livre)

**Despesas fixas mensais: R$ 8.095,92**
- Moradia (aluguel + condomínio + água + gás): R$ 4.645,50
- Financiamento carro (parcela 6/36): R$ 1.650,42
- Energia (média): R$ 800
- Ajuda pais Joice: R$ 500 | Ajuda pais Lucas: R$ 500

**Faturas de cartão (Abril/2026): R$ 22.933,73**
- BV: R$ 11.971,67 (96 transações) → LUCAS R$ 6.106,73 + JURA R$ 5.864,94
- Itaú: R$ 10.962,06 (166 transações) → LUCAS R$ 10.536,47 + JOICE R$ 30,32
- Nubank: a importar (ainda sem dados)

**Resultado do mês: – R$ 3.829,65 (déficit)**
**Limite agregado: R$ 57.800 — utilizado 99,88%**

## Problema central que o app resolve

O fluxo que o app automatiza:

1. Usuário recebe PDF da fatura por e-mail ou app do banco
2. Abre o FinançasPro e seleciona o PDF
3. O backend detecta qual banco (BV/Itaú/Nubank), extrai todas as transações, categoriza e atribui o QUEM
4. Usuário revisa, ajusta se necessário, confirma
5. Dashboard atualiza com visão consolidada

Hoje esse processo é feito à mão, transação por transação, numa planilha Excel.

## Bancos suportados e diferenças nos PDFs

Cada banco tem um formato diferente de PDF que precisa de um parser específico:

- **BV:** datas DD/MM/YYYY, parcelas como "(X/Y)", seções por cartão com "Cartão final XXXX"
- **Itaú:** datas DD/MM (sem ano), seções por cartão com nome do titular, seção separada para internacionais com IOF
- **Nubank:** datas "DD MMM" (ex: "15 Mar"), formato mais simples sem separação por cartão

## Categorias de gastos (18 categorias)

Alimentação, Assinaturas e Serviços Digitais, Automotivo, Combustível, Compras Online, Educação, Estacionamento e Transporte, Farmácia e Saúde, Lazer e Entretenimento, Moradia, Pets, Seguros, Serviços Pessoais (Estética), Supermercado, Transferências Pessoais, Vestuário, Tarifas Bancárias, Outros.

A categorização é feita por regex sobre a descrição da transação (ex: "CASA PORTUGUESA" → Alimentação > Restaurante, "J PESSOA" → Serviços Pessoais > Estética).

## Regras de atribuição QUEM

- Por cartão: 5282 → JOICE, 8001/9825 → LUCAS
- Por descrição: J PESSOA → JURA, PAGUE MENOS → JURA, EXTRA FARMA → JURA
- Anuidades e tarifas → sem membro ("-")
- Sem regra aplicável → "PENDENTE" para revisão manual
- Regras do usuário prevalecem sobre as do sistema

## Conceitos de negócio importantes

- **QUEM:** campo obrigatório em toda transação que identifica o membro responsável (LUCAS, JURA, JOICE ou "-")
- **Verba carimbada:** receita destinada a uso específico (ex: Auxílio Alimentação reservado para Lazer) que não deve ser considerada na sobra livre
- **Divisão de transação:** uma transação pode ser dividida entre membros (ex: J PESSOA 22/12: R$ 400 JURA + R$ 100 LUCAS = R$ 500 total)
- **Duplicata:** detectada por hash MD5 do PDF ou por combinação cartão + mês de referência
- **Projeção de parcelas:** ao importar parcela X/Y, o sistema projeta as parcelas futuras nos meses seguintes

## Problemas reais já identificados (insights do app)

Estes são exemplos de alertas que o app deve gerar automaticamente:

- Apple.com/Bill cobrado nos 2 cartões: R$ 407/mês (duplicidade)
- 3 seguros de cartão simultâneos: R$ 29,22/mês (desperdício)
- ~R$ 6.200 em alimentação fragmentada em 25+ estabelecimentos (difícil controlar)
- R$ 4.270 em estética (J PESSOA) numa única fatura (concentração)
- R$ 275,70/mês em programas de pontos (Livelo + Latam Pass) com ROI questionável

## Módulo de Metas de Redução de Gastos

Funcionalidade que complementa a importação de faturas PDF. Permite ao usuário definir metas de redução com base em faturas anteriores e acompanhar o progresso semanalmente.

**Fluxo principal:**
1. Usuário seleciona uma fatura anterior importada como baseline (ex: Abril/2026 = R$ 22.933)
2. Define meta de redução percentual (ex: 30% → valor alvo = R$ 16.053)
3. Durante o mês, importa prints (screenshots) do app bancário com gastos parciais
4. Sistema extrai transações via OCR, categoriza e calcula progresso
5. Dashboard de metas mostra: % atingida, projeção de fechamento, categorias críticas

**Metas e acompanhamento:**
- Meta vinculada a cartão específico (BV, Itaú, Nubank), com múltiplas metas simultâneas
- Status automático: "Dentro da meta" / "Risco de ultrapassar" / "Fora da meta"
- Projeção do valor final da fatura baseada em média semanal e padrão de consumo

**Importação por imagem (OCR):**
- Upload de múltiplas imagens (prints de apps bancários)
- Extração automática de: data, valor, descrição, categoria
- Edição e exclusão manual dos dados extraídos para correção

**Análise inteligente:**
- Comparação por categoria com mês anterior (variação percentual)
- Identificação automática de "categorias vilãs" que mais impactam o estouro da meta
- Recomendações personalizadas (ex: "Reduza alimentação em X%" ou "Evite compras na categoria Y")

**Alertas:**
- Categoria ultrapassou limite esperado
- Projeção indica que a meta não será atingida
- Usuário próximo de atingir a meta (reforço positivo)

**Visualização:**
- Painel de progresso: % da meta, gasto vs alvo, projeção
- Gráfico de evolução semanal
- Distribuição por categoria
- Linha do tempo dos uploads e evolução

**Critérios de sucesso:**
- Definir meta em menos de 1 minuto
- Análise inicial de imagem em menos de 3 segundos
- Projeção com margem de erro aceitável
- Insights acionáveis a cada importação semanal

## Skills disponíveis

Ative com `/nome-da-skill` no chat. Os arquivos ficam em `.claude/commands/`.

| Comando | Skill | Quando usar |
|---------|-------|-------------|
| `/uxui` | ARIA — Especialista UX/UI | Protótipos, fluxos, componentes visuais |
| `/db` | FORGE — Especialista em Banco de Dados | Modelagem, DDL, migrations Alembic, índices, seeds |
| `/devbackend` | APEX — Engenheiro Backend Python | Endpoints FastAPI, parsers PDF, tasks Celery, APIs mobile-grade |
| `/devmobile` | NOVA — Especialista Mobile React Native | Telas, componentes, animações, integração com API |

Para adicionar nova skill: crie um arquivo `.md` em `.claude/commands/` com a definição da persona. O nome do arquivo vira o comando (ex: `backend.md` → `/backend`).

## Documentos de referência

- `docs/CASHLAB_DESIGN_SYSTEM_v2.html` — **Design system visual do app** (referência primária para UI/UX e desenvolvimento mobile)
- `docs/PRD_FinancasPro.docx` — Requisitos de Produto com critérios de aceite, priorização MoSCoW, riscos e métricas
- `docs/APP_FINANCAS_ESPECIFICACOES.md` — Especificações técnicas (modelo de dados, APIs, wireframes, parsers, estrutura de pastas)
- `docs/requisitos_funcionais_app_financeiro.md` — Requisitos funcionais do módulo de Metas de Redução de Gastos (26 RFs detalhados)

## Roadmap resumido

1. **MVP (12 semanas):** Parsers BV + Itaú, importação, dashboard, transações com filtros
2. **Fase 2 (6 semanas):** Parser Nubank, orçamento, relatórios, alertas
3. **Fase 3 (4 semanas):** Regras editáveis, exportação Excel, notificações, dark mode
4. **Fase 4 (6 semanas):** Módulo de Metas de Redução de Gastos (OCR de prints, projeção, recomendações)
5. **Futuro:** Open Finance, assistente IA, multi-família, versão web
