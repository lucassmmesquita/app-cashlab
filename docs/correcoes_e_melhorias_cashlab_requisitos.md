# 📌 Requisitos – Correções e Melhorias (CashLab)

## 1. 🐞 Correção de Bug – Importação de Fatura (Tela Cartões)

### Problema
Ao importar uma fatura na tela **Cartões**:
- O usuário seleciona:
  - Mês
  - Ano
  - Banco
- Ao clicar em **processar**, o sistema retorna erro de falha na importação.

### Causa provável
- O frontend está recebendo erro antes da conclusão do processamento do backend.
- Possível delay na inserção dos dados no banco de dados.

### Requisitos de Correção
- Implementar controle assíncrono adequado entre frontend e backend:
  - O frontend deve aguardar a finalização do processamento antes de retornar erro/sucesso.
- Adicionar:
  - Estado de loading durante processamento
  - Retry automático ou tratamento de timeout
- Garantir que:
  - A resposta do backend só seja enviada após persistência completa dos dados
- Melhorar logging de erro para rastreabilidade

---

## 2. 📊 Nova Implementação – Tela “Início” (Summary)

### Situação atual
- Tela possui dados mockados

### Requisitos
- Substituir todos os dados mockados por dados reais vindos do:
  - Backend
  - Banco de dados

### Componentes existentes (manter)
- Categorias
- Gastos por categoria
- Total de despesas
- Resultado do mês
- Receita
- Cartões

### Nova funcionalidade (principal)

#### 💡 Insights financeiros
Implementar geração de insights como:

- Total gasto no cartão no mês
- Impacto do cartão na receita mensal (percentual da renda comprometida)
- Alertas:
  - Quando gasto no cartão ultrapassar limite saudável
- Tendência de gasto (subindo/descendo)

---

## 3. 🔄 Ajuste de Regra – Tela de Transações

### Problema
Atualmente, ao importar uma imagem:
- O sistema pode tratar como fatura de cartão, o que é incorreto

### Regra correta

#### 1. Fatura (PDF)
- Origem: Importação de PDF
- Representa:
  - Fatura fechada do cartão
- Deve:
  - Ser categorizada como fatura oficial

#### 2. Gastos semanais (Imagem/Print)
- Origem: Imagem enviada pelo usuário
- Representa:
  - Controle parcial de gastos (semana)
- Não deve:
  - Ser considerada fatura

### Requisitos
- Criar distinção clara no banco e no frontend:
  - Tipo da transação:
    - FATURA
    - GASTO_SEMANAL
- Ajustar exibição na tela de transações:
  - Identificação visual dos dois tipos
- Garantir que:
  - Apenas PDFs alimentam os dados oficiais de fatura

---

## 4. 🎯 Nova Funcionalidade – Metas de Redução de Gastos com Cartão

### Objetivo
Permitir ao usuário definir metas de redução de gastos

### Exemplo
- Reduzir gastos no cartão em 30%

### Requisitos

#### Cadastro de Meta
- Usuário define:
  - Percentual de redução (ex: 30%)

#### Cálculo e acompanhamento
- Sistema deve calcular:
  - Gasto atual médio
  - Meta de gasto ideal
- Comparar:
  - Gastos reais vs meta

#### Monitoramento contínuo
- Utilizar dados de:
  - Faturas (oficial)
  - Gastos semanais (prints)

#### Indicadores
- Percentual atingido da meta
- Evolução ao longo do tempo
- Estimativa:
  - Quanto tempo para atingir a meta

#### Feedback ao usuário
- Exibir:
  - Se está dentro ou fora da meta
  - Alertas de desvio
  - Progresso semanal

---

## 5. 📈 Integração entre Funcionalidades

### Regras importantes
- Os gastos semanais (prints):
  - Servem como indicador antecipado
  - Não substituem a fatura
- As faturas (PDF):
  - São a base oficial de cálculo financeiro
- Os insights e metas devem considerar:
  - Ambos os dados, com pesos e contextos diferentes
