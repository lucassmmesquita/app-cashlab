#!/bin/bash
# ─────────────────────────────────────────────────────────
# CashLab — Start Dev (Backend + Frontend)
#
# Uso:
#   ./start-dev.sh          # sobe ambos
#   ./start-dev.sh back     # só backend
#   ./start-dev.sh front    # só frontend
#   ./start-dev.sh stop     # mata ambos
# ─────────────────────────────────────────────────────────

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
API_DIR="$ROOT_DIR/cashlab-api"
APP_DIR="$ROOT_DIR/cashlab-app"

BACK_PORT=8000
FRONT_PORT=8081

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log()  { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; }
info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

kill_port() {
  local port=$1
  local pids=$(lsof -ti:$port 2>/dev/null)
  if [ -n "$pids" ]; then
    echo "$pids" | xargs kill -9 2>/dev/null
    warn "Processo na porta $port encerrado"
  fi
}

start_backend() {
  info "Iniciando Backend (porta $BACK_PORT)..."
  kill_port $BACK_PORT
  sleep 1

  cd "$API_DIR"

  # Ativar venv se existir
  if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
  fi

  python3 -m uvicorn app.main:app --host 0.0.0.0 --port $BACK_PORT --reload &
  BACK_PID=$!
  echo $BACK_PID > "$ROOT_DIR/.back.pid"
  log "Backend rodando (PID $BACK_PID) → http://localhost:$BACK_PORT"
  log "Docs API → http://localhost:$BACK_PORT/docs"
}

start_frontend() {
  info "Iniciando Frontend (porta $FRONT_PORT)..."
  kill_port $FRONT_PORT
  sleep 1

  cd "$APP_DIR"
  npx expo start --web --port $FRONT_PORT &
  FRONT_PID=$!
  echo $FRONT_PID > "$ROOT_DIR/.front.pid"
  log "Frontend rodando (PID $FRONT_PID) → http://localhost:$FRONT_PORT"
}

stop_all() {
  info "Parando serviços..."
  kill_port $BACK_PORT
  kill_port $FRONT_PORT
  rm -f "$ROOT_DIR/.back.pid" "$ROOT_DIR/.front.pid"
  log "Todos os serviços parados"
}

show_banner() {
  echo ""
  echo -e "${CYAN}╔═══════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║         💰 CashLab Dev Server         ║${NC}"
  echo -e "${CYAN}╚═══════════════════════════════════════╝${NC}"
  echo ""
}

# ── Main ───────────────────────────────────────────────────

show_banner

case "${1:-all}" in
  back|backend|api)
    start_backend
    wait
    ;;
  front|frontend|app)
    start_frontend
    wait
    ;;
  stop|kill)
    stop_all
    ;;
  all|"")
    start_backend
    start_frontend
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  Backend:  http://localhost:$BACK_PORT${NC}"
    echo -e "${GREEN}  Frontend: http://localhost:$FRONT_PORT${NC}"
    echo -e "${GREEN}  API Docs: http://localhost:$BACK_PORT/docs${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    info "Pressione Ctrl+C para parar tudo"
    wait
    ;;
  *)
    echo "Uso: ./start-dev.sh [all|back|front|stop]"
    exit 1
    ;;
esac
