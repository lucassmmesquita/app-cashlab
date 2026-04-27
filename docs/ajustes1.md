# FinançasPro — Refatoração v2.0

**Data:** 27/04/2026  
**Tipo:** Correção de Bugs + Melhorias de Arquitetura  
**Status:** Planejado  
**Impacto:** Alto — altera fluxo de navegação, regras de negócio e UX das telas Cartões, Config e Fluxo

---

## Sumário Executivo

Esta refatoração reorganiza a arquitetura de três telas principais do app (Cartões, Configurações e Fluxo) para corrigir problemas de usabilidade, separar responsabilidades e implementar a regra de competência correta para faturas de cartão de crédito. As mudanças envolvem migração do cadastro de bancos, novo fluxo de treinamento de parser PDF e uma barra de progresso financeiro na tela Fluxo.

---

## 1. Migração do Cadastro de Bancos para Tela de Configurações

### 1.1 Contexto do Problema

Atualmente, o cadastro de bancos está acoplado à tela de Cartões, misturando duas responsabilidades distintas: gerenciamento de bancos (configuração) e operação de faturas (uso diário). Isso gera confusão no fluxo do usuário e dificulta a manutenção.

### 1.2 Mudanças Necessárias

**Migração da tela Cartões → tela Configurações:**

- Mover todo o CRUD de Bancos para a tela de Configurações (`SettingsScreen`).
- Substituir o modal atual por uma navegação via `StackNavigator` (tela dedicada), garantindo mais espaço e melhor experiência, especialmente em dispositivos menores.
- Manter o formulário de cadastro atual (nome do banco, identificação, etc.) sem alteração nos campos.

**Funcionalidade crítica — Treinamento do Parser PDF:**

- Ao cadastrar um novo banco, o sistema deve exigir a importação de um arquivo PDF de fatura como etapa obrigatória de configuração.
- O sistema realizará o parse do PDF para aprender o padrão de layout daquele banco (posição das colunas, formato de data, separadores de cartão, formato de parcelas, etc.).
- O banco só será considerado "ativo" e disponível na tela de Cartões **após a conclusão bem-sucedida do treinamento do parser**.
- Exibir status visual claro: `Pendente de treinamento` → `Processando...` → `Pronto para uso`.

### 1.3 CRUD Completo de Bancos

Implementar as seguintes operações na tela de Configurações:

| Ação | Descrição |
|------|-----------|
| **Criar** | Formulário atual + upload obrigatório do PDF para treinamento |
| **Visualizar** | Tela de detalhes do banco com status do parser, data do último treinamento e quantidade de faturas importadas |
| **Editar** | Permitir alterar dados cadastrais do banco (nome, identificação) |
| **Excluir** | Remover banco com confirmação — exibir alerta caso existam faturas vinculadas |

### 1.4 Retreinamento do Parser

- Incluir botão "Retreinar parser" na tela de detalhes do banco.
- Caso o banco altere o layout do PDF da fatura, o usuário pode enviar um novo arquivo para atualizar o padrão reconhecido.
- O retreinamento não deve afetar faturas já importadas — apenas futuras importações.

### 1.5 Critérios de Aceite

- [ ] Cadastro de bancos removido da tela de Cartões.
- [ ] Cadastro de bancos acessível via tela de Configurações com navegação por `StackNavigator`.
- [ ] Upload de PDF obrigatório no cadastro de novo banco.
- [ ] Parse do PDF executado com sucesso e padrão armazenado.
- [ ] Banco só aparece como opção na importação de faturas após treinamento concluído.
- [ ] Operações de Visualizar, Editar e Excluir funcionando corretamente.
- [ ] Opção de retreinamento do parser disponível e funcional.

---

## 2. Refatoração da Tela de Cartões

### 2.1 Contexto do Problema

Com a migração do cadastro de bancos para Configurações, a tela de Cartões deve focar exclusivamente na operação diária: importar faturas, visualizar histórico e consultar transações por período.

### 2.2 Funcionalidades da Nova Tela de Cartões

**Importar Fatura:**

- Botão principal de ação (CTA) para selecionar o arquivo PDF.
- Ao selecionar o PDF, o usuário deve informar o **Banco** (lista apenas bancos com parser treinado) e o **Mês/Ano de pagamento** da fatura.
- Processamento com feedback visual (barra de progresso, contagem de transações encontradas).
- Pré-visualização das transações antes da confirmação.

**Visualizar Faturas Importadas:**

- Listagem de todas as faturas já importadas.
- Faturas **agrupadas por mês** para facilitar a visualização (ex: "Abril/2026", "Março/2026").
- Dentro de cada grupo mensal, exibir os bancos com resumo (quantidade de transações, valor total).

**Filtros:**

- Filtro por banco.
- Filtro por mês/ano.
- Filtro por membro (QUEM).
- Filtro por status (importada, em revisão, confirmada).

### 2.3 Regra de Negócio Crítica — Competência das Transações

> **REGRA:** O mês/ano informado pelo usuário na importação é o **mês de pagamento da fatura**. As transações contidas nessa fatura devem ser registradas no **mês anterior** para efeito de exibição na tela de Transações e na tela de Fluxo.

**Exemplo prático:**

- O usuário importa a fatura do BV e seleciona **Maio/2026** como mês de pagamento.
- As transações dessa fatura (compras realizadas em abril) serão exibidas em **Abril/2026** nas telas de Transações e Fluxo.
- Na tela de Fluxo de **Maio/2026**, o valor total dessa fatura aparecerá como uma **despesa de cartão** (pois é quando o dinheiro efetivamente sai da conta).

**Impacto nos dados:**

| Tela | Mês afetado | O que exibe |
|------|-------------|-------------|
| **Transações** | Mês anterior (competência) | Detalhamento das compras individuais |
| **Fluxo** | Mês do pagamento | Valor consolidado da fatura como despesa |

### 2.4 Critérios de Aceite

- [ ] Importação de fatura funcional com seleção de banco e mês/ano.
- [ ] Apenas bancos com parser treinado aparecem na lista de seleção.
- [ ] Faturas agrupadas por mês na listagem.
- [ ] Filtros por banco, mês, membro e status funcionando.
- [ ] Regra de competência aplicada corretamente: transações no mês anterior, despesa no mês do pagamento.
- [ ] Importação duplicada detectada com alerta ao usuário (opção de substituir).

---

## 3. Barra de Progresso Financeiro na Tela de Fluxo

### 3.1 Contexto do Problema

Atualmente, o usuário não tem uma visão rápida e intuitiva de quanto ainda pode gastar no cartão de crédito sem comprometer a receita do mês. A informação existe nos números, mas não está representada visualmente de forma que permita uma decisão instantânea.

### 3.2 Componente: Barra de Progresso do Orçamento

Implementar uma barra de progresso horizontal (ou empilhada) no topo da tela de Fluxo que represente visualmente a composição do mês:

```
Receita Total: R$ 27.200,00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
█████████████ Desp. Fixas (R$ 8.095)  ██████████████████████ Cartão (R$ 22.933)  ░░
           30%                                    84%                         ⚠️ -14%
```

**Elementos visuais:**

| Segmento | Cor | Descrição |
|----------|-----|-----------|
| Despesas Fixas | Azul | Valor comprometido com despesas fixas mensais |
| Cartão de Crédito | Amarelo → Vermelho | Valor acumulado das faturas importadas. Muda de amarelo para vermelho ao ultrapassar o limite disponível |
| Saldo Livre | Verde | Diferença positiva entre receita e (fixas + cartão). Desaparece quando não há saldo |
| Excedente | Vermelho (pulsante) | Quando a soma de fixas + cartão ultrapassa a receita total |

**Comportamento dinâmico:**

- A barra atualiza automaticamente à medida que novas faturas são importadas.
- O segmento de cartão cresce progressivamente com cada importação.
- Quando o total (fixas + cartão) ultrapassa a receita, o trecho excedente é destacado em vermelho com indicador visual de alerta.

**Informações complementares abaixo da barra:**

- **Receita Total:** R$ XX.XXX,XX
- **Despesas Fixas:** R$ X.XXX,XX (XX%)
- **Cartão de Crédito:** R$ XX.XXX,XX (XX%)
- **Saldo Disponível:** R$ X.XXX,XX ou **Déficit: -R$ X.XXX,XX**

### 3.3 Exemplo com Dados Reais (Abril/2026)

```
Receita:        R$ 27.200,00  (100%)
Desp. Fixas:    R$  8.095,92  ( 30%)
Cartão:         R$ 22.933,73  ( 84%)
──────────────────────────────────────
TOTAL DESPESAS:  R$ 31.029,65  (114%)  ⚠️
DÉFICIT:        -R$  3.829,65  (-14%)
```

A barra exibirá o segmento de cartão em vermelho com ~14% ultrapassando o limite da receita, sinalizando visualmente que os gastos estão acima da capacidade do mês.

### 3.4 Critérios de Aceite

- [ ] Barra de progresso renderizada no topo da tela de Fluxo.
- [ ] Segmentos representam corretamente: Despesas Fixas, Cartão e Saldo/Déficit.
- [ ] Valores e percentuais atualizados em tempo real ao importar novas faturas.
- [ ] Cores mudam automaticamente conforme a situação (verde → amarelo → vermelho).
- [ ] Indicador visual claro quando há déficit (excedente da receita).
- [ ] Valores detalhados exibidos abaixo da barra com formatação monetária brasileira.

---

## Resumo das Telas Afetadas

| Tela | Alteração | Prioridade |
|------|-----------|------------|
| **Configurações** | Recebe o cadastro de bancos + treinamento de parser PDF | Alta |
| **Cartões** | Foco em importação e visualização de faturas com filtros e agrupamento mensal | Alta |
| **Transações** | Recebe transações no mês de competência (anterior ao pagamento) | Alta |
| **Fluxo** | Nova barra de progresso financeiro + despesa de cartão no mês do pagamento | Alta |

---

## Dependências Técnicas

- Ajuste no modelo de dados: tabela `banks` precisa de campo `parser_status` (enum: `pending`, `processing`, `ready`, `error`).
- Ajuste no modelo de dados: tabela `invoices` precisa de campos `payment_month` e `competence_month`.
- Endpoint de retreinamento do parser: `POST /api/v1/banks/{id}/retrain`.
- Componente React Native de barra de progresso segmentada (pode usar `react-native-svg` ou `Victory Native`).
- Atualização da navegação: novo `StackNavigator` para bancos dentro de Configurações.

---

## Ordem de Implementação Sugerida

1. **Backend:** Migrar modelo de bancos, adicionar campos `parser_status`, `payment_month`, `competence_month`.
2. **Backend:** Endpoint de retreinamento de parser.
3. **Frontend:** Tela de bancos em Configurações (CRUD + treinamento).
4. **Frontend:** Refatorar tela de Cartões (importação + listagem agrupada + filtros).
5. **Frontend:** Aplicar regra de competência nas telas de Transações e Fluxo.
6. **Frontend:** Barra de progresso financeiro na tela de Fluxo.
7. **Testes:** Validar fluxo completo com PDFs reais (BV, Itaú, Nubank).