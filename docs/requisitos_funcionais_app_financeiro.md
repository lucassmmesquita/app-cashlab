# 📱 Requisitos Funcionais — Monitoramento de Meta de Redução de Gastos

## 1. Visão Geral

Esta funcionalidade complementa o aplicativo existente de gestão de faturas de cartão de crédito, que atualmente permite a importação de faturas em PDF (BV, Itaú e Nubank).

O novo módulo permitirá ao usuário:

- Definir metas de redução de gastos com base em faturas anteriores
- Acompanhar semanalmente sua evolução
- Importar dados atualizados via prints (imagens)
- Receber análises, previsões e recomendações inteligentes

---

## 2. Objetivo da Funcionalidade

Permitir que o usuário reduza seus gastos mensais com cartão de crédito através de:

- Monitoramento contínuo (semanal)
- Comparação com fatura anterior
- Previsão de fechamento da fatura atual
- Identificação de categorias críticas
- Alertas e recomendações personalizadas

---

## 3. Definição de Meta

### RF-01: Criação de Meta de Redução
O sistema deve permitir que o usuário:

- Selecione uma fatura anterior importada (baseline)
- Defina uma meta de redução percentual (ex: 30%)
- Visualize automaticamente:
  - Valor total da fatura anterior
  - Valor alvo da nova fatura (ex: 70% da anterior)

### RF-02: Associação por Cartão
- A meta deve ser vinculada a um cartão específico (BV, Itaú, Nubank)
- O usuário pode ter múltiplas metas simultâneas (uma por cartão)

---

## 4. Importação de Dados Semanais

### RF-03: Upload de Imagens (Prints)
O sistema deve permitir:

- Upload de múltiplas imagens (prints das transações)
- Suporte a imagens da tela de apps bancários

### RF-04: Processamento de Imagem (OCR)
- O sistema deve extrair automaticamente:
  - Data da transação
  - Valor
  - Descrição
  - Categoria (quando possível)

### RF-05: Validação de Dados
- Permitir edição manual dos dados extraídos
- Permitir exclusão de transações incorretas

---

## 5. Consolidação e Cálculo

### RF-06: Acumulado Atual
O sistema deve calcular:

- Total gasto até o momento (mês corrente)
- Comparação com:
  - Fatura anterior (baseline)
  - Meta definida

### RF-07: Projeção de Fatura
- O sistema deve estimar o valor final da fatura com base em:
  - Média semanal de gastos
  - Padrão de consumo

### RF-08: Status da Meta
O sistema deve classificar o progresso em:

- Dentro da meta
- Risco de ultrapassar
- Fora da meta

---

## 6. Análise por Categoria

### RF-09: Classificação de Gastos
- O sistema deve agrupar gastos por categoria:
  - Alimentação
  - Transporte
  - Lazer
  - Compras
  - Outros

### RF-10: Comparação com Mês Anterior
- Exibir variação percentual por categoria
- Destacar categorias com aumento de gasto

### RF-11: Identificação de Vilões
- O sistema deve identificar automaticamente:
  - Categorias que mais impactam o estouro da meta

---

## 7. Recomendações Inteligentes

### RF-12: Sugestões de Redução
O sistema deve gerar sugestões como:

- “Reduzir gastos em alimentação em X%”
- “Evitar compras na categoria Y nos próximos dias”

### RF-13: Estratégias Personalizadas
- Baseadas no comportamento do usuário
- Baseadas no histórico de consumo

---

## 8. Alertas e Notificações

### RF-14: Alertas de Categoria
- Notificar quando uma categoria ultrapassar um limite esperado

### RF-15: Alertas de Projeção
- Notificar quando a projeção indicar que a meta não será atingida

### RF-16: Alertas de Proximidade da Meta
- Notificar quando o usuário estiver próximo de atingir a meta

---

## 9. Visualização e Dashboard

### RF-17: Painel de Progresso
Exibir:

- % de meta atingida
- Valor gasto vs valor alvo
- Projeção da fatura

### RF-18: Gráficos
- Evolução semanal de gastos
- Distribuição por categoria

### RF-19: Linha do Tempo
- Histórico semanal de uploads e evolução

---

## 10. Multi-cartão

### RF-20: Gestão de Múltiplos Cartões
- O sistema deve permitir:
  - Alternar entre cartões
  - Visualizar metas separadas

---

## 11. Experiência do Usuário (UX)

### RF-21: Simplicidade de Uso
- Upload rápido de prints
- Feedback imediato após importação

### RF-22: Feedback Visual
- Uso de cores para indicar status da meta
- Indicadores claros de risco

---

## 12. Requisitos Técnicos

### RF-23: Compatibilidade
- Aplicativo desenvolvido em React Native
- Deve rodar de forma fluida em dispositivos iOS

### RF-24: Performance
- Processamento de imagens deve ser otimizado
- Feedback ao usuário em tempo aceitável (< 3s para análise inicial)

### RF-25: Armazenamento
- Armazenar histórico de:
  - Faturas
  - Metas
  - Imports semanais

---

## 13. Segurança

### RF-26: Privacidade dos Dados
- Dados financeiros devem ser armazenados com segurança
- Criptografia de dados sensíveis

---

## 14. Critérios de Sucesso

- Usuário consegue definir meta em menos de 1 minuto
- Upload de prints funcional e confiável
- Projeção com margem de erro aceitável
- Usuário recebe insights acionáveis
