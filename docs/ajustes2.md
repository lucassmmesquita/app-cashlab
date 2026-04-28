# 📌 Requisitos de Correção de Bugs e Melhorias  
## Módulo: Cartões (antigo Bancos)

---

## 1. 🔄 Alteração de Nomenclatura e Estrutura

### 1.1 Mudança de nomenclatura
Substituir o termo **“Bancos”** por **“Cartões”** em:
- Menus
- Telas
- Mensagens do sistema

### 1.2 Migração de funcionalidades
Migrar todas as funcionalidades atualmente associadas a **“Bancos”** para a tela de **“Cartões”**

Garantir:
- Compatibilidade com dados existentes
- Integridade das informações já cadastradas
- Ajuste de rotas e endpoints

---

## 2. 🐞 Correção de Fluxo Inicial (Onboarding)

### 2.1 Problema identificado
A tela de cartões apresenta múltiplas opções mesmo quando **não há nenhum cartão cadastrado**, gerando confusão no fluxo inicial.

### 2.2 Comportamento esperado
Quando **não existir nenhum cartão cadastrado**:
- Exibir **apenas uma única opção**:
  - 👉 “Importar fatura via PDF”

---

## 3. 🚀 Implementação de Fluxo Assistido (Wizard)

### 3.1 Objetivo
Transformar a tela inicial de cartões em um **assistente guiado (wizard)** no primeiro acesso.

---

### 3.2 Requisitos do fluxo

#### Etapa 1 – Entrada
- Exibir somente:
  - Opção de **importação de fatura PDF**
- Ocultar:
  - Listagem de cartões
  - Outras ações

---

#### Etapa 2 – Treinamento da fatura
Após upload do PDF:
- Sistema deve:
  - Processar e interpretar os dados da fatura
  - Identificar padrões (treinamento)

---

#### Etapa 3 – Confirmação do usuário
Após processamento:
- Exibir mensagem:
  - 👉 “Deseja importar esta fatura?”

- Apresentar:
  - Resumo da fatura (recomendado)
  - Botões:
    - Confirmar
    - Cancelar

---

#### Etapa 4 – Importação automática
Ao confirmar, o sistema deve:

1. Criar automaticamente o **cartão**
2. Criar a **fatura**
3. Importar todas as **transações detalhadas**
4. Associar corretamente:
   - Datas
   - Valores
   - Descrições

---

## 4. ⚙️ Regras de Negócio

- O fluxo de onboarding deve ocorrer **somente no primeiro acesso** ou quando:
  - Não houver cartões cadastrados

- Após o primeiro cartão criado:
  - A tela deve passar a exibir:
    - Lista de cartões
    - Ações adicionais (ex: nova importação, edição, etc.)

---

## 5. 🎯 Melhorias de Experiência do Usuário (UX)

- Simplificar o primeiro contato com o sistema
- Reduzir fricção no cadastro inicial
- Guiar o usuário com fluxo claro e objetivo
- Evitar telas vazias com múltiplas opções irrelevantes

---

## 6. ⚠️ Pontos de Atenção Técnica

Garantir:
- Idempotência da importação (evitar duplicidade)
- Tratamento de erros no parsing do PDF
- Feedback claro em caso de falha

Implementar:
- Logs para:
  - Treinamento da fatura
  - Importação

Considerar:
- Possibilidade futura de reprocessamento da fatura