#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# CashLab — Deploy & Operations CLI
#
# Menu interativo para gerenciar backend, frontend, banco de
# dados e deploy do projeto CashLab.
#
# Uso:  ./deploy.sh
# ═══════════════════════════════════════════════════════════════

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
API_DIR="$ROOT_DIR/cashlab-api"
APP_DIR="$ROOT_DIR/cashlab-app"

RENDER_URL="https://app-cashlab.onrender.com"
RENDER_API="$RENDER_URL/api/v1"

# ── Cores ──────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

log()  { echo -e "${GREEN}  ✅ $1${NC}"; }
warn() { echo -e "${YELLOW}  ⚠️  $1${NC}"; }
err()  { echo -e "${RED}  ❌ $1${NC}"; }
info() { echo -e "${CYAN}  ℹ️  $1${NC}"; }

# ── Helpers ────────────────────────────────────────────────────
separator() {
  echo -e "${DIM}  ─────────────────────────────────────────────${NC}"
}

header() {
  clear
  echo ""
  echo -e "${MAGENTA}${BOLD}  ╔═══════════════════════════════════════════╗${NC}"
  echo -e "${MAGENTA}${BOLD}  ║          💰 CashLab Operations            ║${NC}"
  echo -e "${MAGENTA}${BOLD}  ╚═══════════════════════════════════════════╝${NC}"
  echo ""
}

press_enter() {
  echo ""
  echo -e "${DIM}  Pressione ENTER para voltar ao menu...${NC}"
  read -r
}

# ═══════════════════════════════════════════════════════════════
# 1. BACKEND
# ═══════════════════════════════════════════════════════════════

check_backend_health() {
  echo -e "\n${BOLD}  🏥 Health Check do Backend${NC}"
  separator

  echo -ne "  Render URL: "
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$RENDER_URL/docs" --max-time 10 2>/dev/null)

  if [ "$HTTP_CODE" = "200" ]; then
    log "Backend online (HTTP $HTTP_CODE)"
  elif [ "$HTTP_CODE" = "000" ]; then
    err "Backend offline ou timeout"
  else
    warn "Resposta HTTP $HTTP_CODE"
  fi

  # Test API
  echo -ne "  API /transactions: "
  RESPONSE=$(curl -s "$RENDER_API/transactions?per_page=1" --max-time 10 2>/dev/null)
  if echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'OK — {d[\"meta\"][\"total\"]} transações')" 2>/dev/null; then
    true
  else
    err "Erro ao consultar API"
  fi

  echo -ne "  API /invoices: "
  RESPONSE=$(curl -s "$RENDER_API/invoices" --max-time 10 2>/dev/null)
  if echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'OK — {len(d[\"data\"])} faturas')" 2>/dev/null; then
    true
  else
    err "Erro ao consultar API"
  fi

  echo -ne "  API /banks: "
  RESPONSE=$(curl -s "$RENDER_API/banks" --max-time 10 2>/dev/null)
  if echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'OK — {len(d[\"data\"])} bancos')" 2>/dev/null; then
    true
  else
    err "Erro ao consultar API"
  fi

  press_enter
}

deploy_backend() {
  echo -e "\n${BOLD}  🚀 Deploy Backend (Render)${NC}"
  separator
  info "O Render faz deploy automático ao push na branch main."
  echo ""

  # Show last commit
  echo -e "  ${BOLD}Último commit:${NC}"
  cd "$ROOT_DIR"
  git log -1 --pretty=format:"  %h — %s (%cr)" 2>/dev/null
  echo ""
  echo ""

  # Check if there are uncommitted changes
  if [ -n "$(git status --porcelain)" ]; then
    warn "Existem alterações não commitadas:"
    git status --short | head -10 | sed 's/^/    /'
    echo ""
    echo -ne "  Deseja commitar e fazer push? (s/n): "
    read -r CONFIRM
    if [ "$CONFIRM" = "s" ]; then
      echo -ne "  Mensagem do commit: "
      read -r MSG
      git add -A
      git commit -m "$MSG"
      git push
      log "Push realizado! Render fará deploy em ~5 min."
    fi
  else
    log "Tudo commitado. Último push já foi para o Render."
  fi

  press_enter
}

view_backend_logs() {
  echo -e "\n${BOLD}  📋 Logs do Backend Local${NC}"
  separator

  if pgrep -f "uvicorn app.main:app" > /dev/null 2>&1; then
    log "Backend local rodando"
    info "Últimas linhas de log:"
    echo ""
    # Show last lines from the running process
    ps aux | grep "[u]vicorn app.main" | head -1 | awk '{print "  PID: "$2" | Mem: "$4"% | CPU: "$3"%"}'
  else
    warn "Backend local não está rodando"
    info "Use ./start-dev.sh para iniciar"
  fi

  press_enter
}

# ═══════════════════════════════════════════════════════════════
# 2. FRONTEND
# ═══════════════════════════════════════════════════════════════

run_ios_device() {
  echo -e "\n${BOLD}  📱 Build iOS (Dispositivo Físico)${NC}"
  separator

  cd "$APP_DIR"

  echo -e "  ${BOLD}Profiles disponíveis:${NC}"
  echo "    1) development (dev client)"
  echo "    2) preview (internal distribution)"
  echo "    3) production"
  echo ""
  echo -ne "  Escolha o profile (1/2/3): "
  read -r CHOICE

  case $CHOICE in
    1) PROFILE="development" ;;
    2) PROFILE="preview" ;;
    3) PROFILE="production" ;;
    *) err "Opção inválida"; press_enter; return ;;
  esac

  info "Iniciando EAS build ($PROFILE)..."
  npx eas build --platform ios --profile "$PROFILE"

  press_enter
}

run_expo_dev() {
  echo -e "\n${BOLD}  📱 Expo Dev Server${NC}"
  separator

  cd "$APP_DIR"

  if pgrep -f "expo start" > /dev/null 2>&1; then
    warn "Expo já está rodando"
    echo -ne "  Reiniciar? (s/n): "
    read -r CONFIRM
    if [ "$CONFIRM" = "s" ]; then
      pkill -f "expo start" 2>/dev/null
      sleep 1
    else
      press_enter; return
    fi
  fi

  info "Iniciando Expo dev server na porta 8081..."
  npx expo start --dev-client --port 8081
}

run_ios_local() {
  echo -e "\n${BOLD}  📱 Rodar no iPhone via USB${NC}"
  separator
  cd "$APP_DIR"
  info "Listando dispositivos conectados..."
  echo ""

  xcrun xctrace list devices 2>/dev/null | grep "iPhone" | head -5 | sed 's/^/    /'
  echo ""
  info "Executando build e instalação..."
  npx expo run:ios --device

  press_enter
}

# ═══════════════════════════════════════════════════════════════
# 3. BANCO DE DADOS
# ═══════════════════════════════════════════════════════════════

db_stats() {
  echo -e "\n${BOLD}  📊 Estatísticas do Banco de Dados${NC}"
  separator

  cd "$API_DIR"
  source venv/bin/activate 2>/dev/null

  python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv
load_dotenv()
async def stats():
    engine = create_async_engine(os.getenv('DATABASE_URL'), connect_args={'statement_cache_size': 0})
    async with engine.begin() as conn:
        tables = ['transactions', 'invoices', 'credit_cards', 'banks', 'incomes', 'fixed_expenses', 'members', 'categories']
        for t in tables:
            try:
                r = await conn.execute(text(f'SELECT COUNT(*) FROM {t}'))
                count = r.scalar()
                print(f'  {t:20s} {count:>6} registros')
            except:
                print(f'  {t:20s}  — não encontrada')
        
        # Transações por billing_month
        print()
        print('  Transações por mês:')
        r = await conn.execute(text(\"\"\"
            SELECT COALESCE(billing_month, 'sem_mes') as bm, COUNT(*), COALESCE(SUM(amount),0)
            FROM transactions WHERE deleted_at IS NULL
            GROUP BY bm ORDER BY bm
        \"\"\"))
        for row in r.fetchall():
            print(f'    {row[0]:>10s}: {row[1]:>5} transações  |  R\$ {row[2]:>12,.2f}')
    await engine.dispose()
asyncio.run(stats())
" 2>/dev/null

  press_enter
}

db_migrate() {
  echo -e "\n${BOLD}  🔧 Migração do Banco de Dados${NC}"
  separator

  echo "  Migrações disponíveis:"
  echo "    1) Adicionar billing_month (transactions)"
  echo "    2) Adicionar closing_day/due_day (banks)"
  echo "    3) Remover constraint who (transactions)"
  echo "    4) Executar TODAS as migrações pendentes"
  echo "    5) SQL customizado"
  echo ""
  echo -ne "  Escolha (1-5): "
  read -r CHOICE

  cd "$API_DIR"
  source venv/bin/activate 2>/dev/null

  case $CHOICE in
    1)
      python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os; from dotenv import load_dotenv; load_dotenv()
async def m():
    engine = create_async_engine(os.getenv('DATABASE_URL'), connect_args={'statement_cache_size': 0})
    async with engine.begin() as conn:
        await conn.execute(text('ALTER TABLE transactions ADD COLUMN IF NOT EXISTS billing_month VARCHAR(7)'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS idx_transactions_billing_month ON transactions(billing_month)'))
        print('  ✅ billing_month adicionado')
    await engine.dispose()
asyncio.run(m())
" 2>/dev/null
      ;;
    2)
      python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os; from dotenv import load_dotenv; load_dotenv()
async def m():
    engine = create_async_engine(os.getenv('DATABASE_URL'), connect_args={'statement_cache_size': 0})
    async with engine.begin() as conn:
        await conn.execute(text('ALTER TABLE banks ADD COLUMN IF NOT EXISTS closing_day INTEGER'))
        await conn.execute(text('ALTER TABLE banks ADD COLUMN IF NOT EXISTS due_day INTEGER'))
        await conn.execute(text(\"UPDATE banks SET closing_day=3, due_day=9 WHERE slug='itau' AND closing_day IS NULL\"))
        await conn.execute(text(\"UPDATE banks SET closing_day=17, due_day=22 WHERE slug='bv' AND closing_day IS NULL\"))
        print('  ✅ closing_day/due_day adicionados')
    await engine.dispose()
asyncio.run(m())
" 2>/dev/null
      ;;
    3)
      python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os; from dotenv import load_dotenv; load_dotenv()
async def m():
    engine = create_async_engine(os.getenv('DATABASE_URL'), connect_args={'statement_cache_size': 0})
    async with engine.begin() as conn:
        await conn.execute(text('ALTER TABLE transactions DROP CONSTRAINT IF EXISTS chk_transaction_who'))
        await conn.execute(text('ALTER TABLE transactions ALTER COLUMN who DROP NOT NULL'))
        print('  ✅ Constraint who removida')
    await engine.dispose()
asyncio.run(m())
" 2>/dev/null
      ;;
    4)
      info "Executando todas as migrações..."
      python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os; from dotenv import load_dotenv; load_dotenv()
async def m():
    engine = create_async_engine(os.getenv('DATABASE_URL'), connect_args={'statement_cache_size': 0})
    async with engine.begin() as conn:
        migrations = [
            ('billing_month',    'ALTER TABLE transactions ADD COLUMN IF NOT EXISTS billing_month VARCHAR(7)'),
            ('billing_idx',      'CREATE INDEX IF NOT EXISTS idx_transactions_billing_month ON transactions(billing_month)'),
            ('file_size',        'ALTER TABLE invoices ADD COLUMN IF NOT EXISTS file_size INTEGER'),
            ('closing_day',      'ALTER TABLE banks ADD COLUMN IF NOT EXISTS closing_day INTEGER'),
            ('due_day',          'ALTER TABLE banks ADD COLUMN IF NOT EXISTS due_day INTEGER'),
            ('who_constraint',   'ALTER TABLE transactions DROP CONSTRAINT IF EXISTS chk_transaction_who'),
            ('who_nullable',     'ALTER TABLE transactions ALTER COLUMN who DROP NOT NULL'),
            ('itau_days',        \"UPDATE banks SET closing_day=3, due_day=9 WHERE slug='itau' AND closing_day IS NULL\"),
            ('bv_days',          \"UPDATE banks SET closing_day=17, due_day=22 WHERE slug='bv' AND closing_day IS NULL\"),
        ]
        for name, sql in migrations:
            try:
                await conn.execute(text(sql))
                print(f'  ✅ {name}')
            except Exception as e:
                print(f'  ⚠️  {name}: {e}')
    await engine.dispose()
asyncio.run(m())
" 2>/dev/null
      ;;
    5)
      echo -ne "  SQL> "
      read -r SQL
      python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os; from dotenv import load_dotenv; load_dotenv()
async def m():
    engine = create_async_engine(os.getenv('DATABASE_URL'), connect_args={'statement_cache_size': 0})
    async with engine.begin() as conn:
        r = await conn.execute(text('''$SQL'''))
        try:
            rows = r.fetchall()
            for row in rows[:20]:
                print(f'  {row}')
            if len(rows) > 20:
                print(f'  ... (+{len(rows)-20} mais)')
        except:
            print(f'  ✅ Executado ({r.rowcount} linhas afetadas)')
    await engine.dispose()
asyncio.run(m())
" 2>/dev/null
      ;;
  esac

  press_enter
}

db_clean() {
  echo -e "\n${BOLD}  🧹 Limpar Dados${NC}"
  separator

  echo "  Opções:"
  echo "    1) Limpar transações + faturas + cartões (manter incomes/expenses)"
  echo "    2) Limpar TUDO (reset completo)"
  echo "    3) Cancelar"
  echo ""
  echo -ne "  Escolha (1-3): "
  read -r CHOICE

  if [ "$CHOICE" = "3" ]; then press_enter; return; fi

  echo -ne "  ${RED}Tem certeza? Digite 'CONFIRMAR': ${NC}"
  read -r CONFIRM
  if [ "$CONFIRM" != "CONFIRMAR" ]; then
    warn "Operação cancelada"
    press_enter; return
  fi

  cd "$API_DIR"
  source venv/bin/activate 2>/dev/null

  if [ "$CHOICE" = "1" ]; then
    python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os; from dotenv import load_dotenv; load_dotenv()
async def clean():
    engine = create_async_engine(os.getenv('DATABASE_URL'), connect_args={'statement_cache_size': 0})
    async with engine.begin() as conn:
        await conn.execute(text('DELETE FROM transactions'))
        await conn.execute(text('DELETE FROM invoices'))
        await conn.execute(text('DELETE FROM credit_cards'))
        print('  ✅ Transações, faturas e cartões excluídos')
    await engine.dispose()
asyncio.run(clean())
" 2>/dev/null
  elif [ "$CHOICE" = "2" ]; then
    python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os; from dotenv import load_dotenv; load_dotenv()
async def clean():
    engine = create_async_engine(os.getenv('DATABASE_URL'), connect_args={'statement_cache_size': 0})
    async with engine.begin() as conn:
        for t in ['transactions', 'invoices', 'credit_cards', 'incomes', 'fixed_expenses']:
            await conn.execute(text(f'DELETE FROM {t}'))
            print(f'  🗑️  {t} limpo')
        await conn.execute(text('DELETE FROM banks'))
        print(f'  🗑️  banks limpo')
        print('  ✅ Reset completo!')
    await engine.dispose()
asyncio.run(clean())
" 2>/dev/null
  fi

  press_enter
}

# ═══════════════════════════════════════════════════════════════
# 4. GIT & DEPLOY
# ═══════════════════════════════════════════════════════════════

git_status() {
  echo -e "\n${BOLD}  📦 Git Status${NC}"
  separator

  cd "$ROOT_DIR"
  echo ""
  echo -e "  ${BOLD}Branch:${NC} $(git branch --show-current 2>/dev/null)"
  echo -e "  ${BOLD}Remote:${NC} $(git remote get-url origin 2>/dev/null)"
  echo ""
  echo -e "  ${BOLD}Últimos 5 commits:${NC}"
  git log -5 --pretty=format:"  %C(yellow)%h%C(reset) %s %C(dim)(%cr)%C(reset)" 2>/dev/null
  echo ""
  echo ""

  CHANGES=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  if [ "$CHANGES" -gt 0 ]; then
    warn "$CHANGES arquivo(s) modificado(s):"
    git status --short 2>/dev/null | head -15 | sed 's/^/    /'
  else
    log "Working tree limpo"
  fi

  press_enter
}

quick_push() {
  echo -e "\n${BOLD}  ⚡ Quick Push (commit + push)${NC}"
  separator

  cd "$ROOT_DIR"

  CHANGES=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  if [ "$CHANGES" -eq 0 ]; then
    log "Nada para commitar!"
    press_enter; return
  fi

  echo "  Arquivos modificados:"
  git status --short 2>/dev/null | head -15 | sed 's/^/    /'
  echo ""

  echo -ne "  Mensagem do commit: "
  read -r MSG

  if [ -z "$MSG" ]; then
    err "Mensagem vazia, operação cancelada"
    press_enter; return
  fi

  git add -A
  git commit -m "$MSG"
  git push

  log "Push realizado! Deploy automático em ~5 min."

  press_enter
}

# ═══════════════════════════════════════════════════════════════
# 5. TESTES
# ═══════════════════════════════════════════════════════════════

test_parser() {
  echo -e "\n${BOLD}  🧪 Testar Parser de PDF${NC}"
  separator

  cd "$API_DIR"
  source venv/bin/activate 2>/dev/null

  # List available PDFs
  echo "  PDFs disponíveis em uploads/:"
  ls -la uploads/*.pdf 2>/dev/null | awk '{print "    " $NF " (" $5 " bytes)"}' | sed 's|uploads/||'
  echo ""
  echo -ne "  Nome do arquivo (ou ENTER para o mais recente): "
  read -r PDF_NAME

  if [ -z "$PDF_NAME" ]; then
    PDF_FILE=$(ls -t uploads/*.pdf 2>/dev/null | head -1)
  else
    PDF_FILE="uploads/$PDF_NAME"
  fi

  if [ ! -f "$PDF_FILE" ]; then
    err "Arquivo não encontrado: $PDF_FILE"
    press_enter; return
  fi

  info "Testando parser em: $PDF_FILE"
  echo ""

  python3 -c "
from app.parsers.detector import detect_bank, get_parser
import sys

file_path = '$PDF_FILE'
bank = detect_bank(file_path)
print(f'  Banco detectado: {bank}')

if bank == 'unknown':
    print('  ❌ Banco não reconhecido')
    sys.exit(1)

parser = get_parser(bank)
result = parser.parse(file_path)

print(f'  Mês referência: {result.reference_month}')
print(f'  Vencimento: {result.due_date}')
print(f'  Total fatura: R\$ {result.total_amount:,.2f}')
print(f'  Cartão: ****{result.card_last_digits}')
print(f'  Transações: {len(result.transactions)}')

total = sum(t.amount for t in result.transactions)
print(f'  Soma transações: R\$ {float(total):,.2f}')
diff = float(result.total_amount) - float(total)
print(f'  Diferença: R\$ {diff:,.2f}')

print()
print('  Primeiras 10 transações:')
for t in result.transactions[:10]:
    inst = f' ({t.installment_num}/{t.installment_total})' if t.installment_num else ''
    print(f'    {t.date} | {t.description[:35]:35s} | R\$ {float(t.amount):>10,.2f}{inst}')
" 2>/dev/null

  press_enter
}

# ═══════════════════════════════════════════════════════════════
# MAIN MENU
# ═══════════════════════════════════════════════════════════════

main_menu() {
  while true; do
    header
    echo -e "  ${BOLD}Backend${NC}"
    echo "    1)  🏥  Health check (Render)"
    echo "    2)  🚀  Deploy backend (git push)"
    echo "    3)  📋  Status do processo local"
    echo ""
    echo -e "  ${BOLD}Frontend${NC}"
    echo "    4)  📱  Expo dev server"
    echo "    5)  🔨  EAS Build (iOS)"
    echo "    6)  🔌  Rodar no iPhone (USB)"
    echo ""
    echo -e "  ${BOLD}Banco de Dados${NC}"
    echo "    7)  📊  Estatísticas"
    echo "    8)  🔧  Migrações"
    echo "    9)  🧹  Limpar dados"
    echo ""
    echo -e "  ${BOLD}Git & Testes${NC}"
    echo "    10) 📦  Git status"
    echo "    11) ⚡  Quick push"
    echo "    12) 🧪  Testar parser PDF"
    echo ""
    echo "    0)  🚪  Sair"
    echo ""
    separator
    echo -ne "  Escolha: "
    read -r OPTION

    case $OPTION in
      1)  check_backend_health ;;
      2)  deploy_backend ;;
      3)  view_backend_logs ;;
      4)  run_expo_dev ;;
      5)  run_ios_device ;;
      6)  run_ios_local ;;
      7)  db_stats ;;
      8)  db_migrate ;;
      9)  db_clean ;;
      10) git_status ;;
      11) quick_push ;;
      12) test_parser ;;
      0)  echo -e "\n  ${CYAN}Até mais! 👋${NC}\n"; exit 0 ;;
      *)  warn "Opção inválida" ;;
    esac
  done
}

main_menu
