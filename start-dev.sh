#!/usr/bin/env bash
# =============================================================================
# start-dev.sh - One-Click Development Environment Launcher (Linux/macOS)
# =============================================================================
# Author: Danilo Viteri Moreno
# Usage: ./start-dev.sh
#        ./start-dev.sh --skip-install     # Skip dependency installation
#        ./start-dev.sh --backend-only     # Launch backend only
#        ./start-dev.sh --frontend-only    # Launch frontend only
# =============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SKIP_INSTALL=false
BACKEND_ONLY=false
FRONTEND_ONLY=false

# ─── Parse arguments ────────────────────────────────────────────────────────

for arg in "$@"; do
    case $arg in
        --skip-install)  SKIP_INSTALL=true ;;
        --backend-only)  BACKEND_ONLY=true ;;
        --frontend-only) FRONTEND_ONLY=true ;;
        -h|--help)
            echo "Usage: $0 [--skip-install] [--backend-only] [--frontend-only]"
            exit 0
            ;;
        *) echo "Unknown argument: $arg"; exit 1 ;;
    esac
done

# ─── Colors ─────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
GRAY='\033[1;30m'
MAGENTA='\033[0;35m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn() { echo -e "  ${YELLOW}[!!]${NC} $1"; }
err()  { echo -e "  ${RED}[XX]${NC} $1"; }
info() { echo -e "  ${CYAN}[..]${NC} $1"; }

# ─── Banner ─────────────────────────────────────────────────────────────────

echo ""
echo -e "  ${CYAN}+================================================+${NC}"
echo -e "  ${CYAN}|   Autonomous Technical Auditor Agent            |${NC}"
echo -e "  ${CYAN}|   Full-Stack Development Environment            |${NC}"
echo -e "  ${CYAN}+================================================+${NC}"
echo ""

# ─── Pre-flight Checks ──────────────────────────────────────────────────────

echo -e "  ${GRAY}Checking prerequisites...${NC}"
CHECKS_OK=true

# Python venv
VENV_PYTHON="$ROOT/.venv/bin/python"
if [ -f "$VENV_PYTHON" ]; then
    PY_VERSION=$($VENV_PYTHON --version 2>&1)
    ok "Python venv: $PY_VERSION"
else
    if command -v python3 &>/dev/null; then
        warn "No .venv found -- creating virtual environment..."
        python3 -m venv "$ROOT/.venv"
        ok "Virtual environment created"
    else
        err "Python 3 not found. Install Python 3.12+ from https://python.org"
        CHECKS_OK=false
    fi
fi

# Node.js
if command -v node &>/dev/null; then
    ok "Node.js: $(node --version)"
else
    err "Node.js not found. Install from https://nodejs.org"
    CHECKS_OK=false
fi

# npm
if command -v npm &>/dev/null; then
    ok "npm: v$(npm --version)"
else
    err "npm not found"
    CHECKS_OK=false
fi

# .env
if [ -f "$ROOT/.env" ]; then
    ok ".env file found"
    if grep -qE "GOOGLE_API_KEY=\w{10,}|GROQ_API_KEY=\w{10,}" "$ROOT/.env"; then
        ok "API key(s) configured"
    else
        warn "No API keys detected in .env -- agent will not work without at least one key"
    fi
elif [ -f "$ROOT/.env.example" ]; then
    warn ".env not found -- copying from .env.example"
    cp "$ROOT/.env.example" "$ROOT/.env"
    warn "IMPORTANT: Edit .env and add your API keys before using the agent"
else
    err ".env.example not found -- cannot auto-create .env"
    CHECKS_OK=false
fi

if [ "$CHECKS_OK" = false ]; then
    echo ""
    err "Prerequisites check failed. Fix the issues above and try again."
    exit 1
fi

# ─── Dependencies ───────────────────────────────────────────────────────────

if [ "$SKIP_INSTALL" = false ]; then
    echo ""
    echo -e "  ${GRAY}Installing dependencies...${NC}"

    VENV_PIP="$ROOT/.venv/bin/pip"

    info "Installing Python packages (pip install -e .[dev])..."
    cd "$ROOT"
    $VENV_PIP install -e ".[dev]" --quiet 2>&1 >/dev/null || {
        err "Python dependency installation failed"
        $VENV_PIP install -e ".[dev]"
        exit 1
    }
    ok "Python packages installed"

    if [ ! -d "$ROOT/node_modules" ]; then
        info "Installing root npm packages..."
        cd "$ROOT" && npm install --silent 2>&1 >/dev/null
    fi
    ok "Root npm packages ready"

    if [ ! -d "$ROOT/frontend/node_modules" ]; then
        info "Installing frontend npm packages..."
        cd "$ROOT/frontend" && npm install --silent 2>&1 >/dev/null
    fi
    ok "Frontend npm packages ready"
else
    warn "Skipping dependency installation (--skip-install)"
fi

# ─── Data directory ─────────────────────────────────────────────────────────

mkdir -p "$ROOT/data"

# ─── Quality gate ───────────────────────────────────────────────────────────

echo ""
echo -e "  ${GRAY}Running quality checks...${NC}"
VENV_PYTHON="$ROOT/.venv/bin/python"
cd "$ROOT"
if $VENV_PYTHON -m ruff check src/ tests/ --quiet 2>&1 >/dev/null; then
    ok "Lint check passed"
else
    warn "Lint issues detected (run: ruff check src/ tests/ --fix)"
fi

# ─── Launch ─────────────────────────────────────────────────────────────────

echo ""
echo -e "  ${GRAY}+-------------------------------------------------+${NC}"
echo -e "  ${GRAY}|${NC}  ${CYAN}API${NC}  Backend  ${GRAY}->${NC}  ${YELLOW}http://localhost:8000${NC}       ${GRAY}|${NC}"
echo -e "  ${GRAY}|${NC}  ${MAGENTA}WEB${NC}  Frontend ${GRAY}->${NC}  ${YELLOW}http://localhost:3000${NC}       ${GRAY}|${NC}"
echo -e "  ${GRAY}|${NC}  ${GREEN}DOC${NC}  Swagger  ${GRAY}->${NC}  ${YELLOW}http://localhost:8000/docs${NC}  ${GRAY}|${NC}"
echo -e "  ${GRAY}+-------------------------------------------------+${NC}"
echo ""
echo -e "  ${GRAY}Press Ctrl+C to stop all servers${NC}"
echo ""

# Set venv in PATH so uvicorn uses the right Python
export VIRTUAL_ENV="$ROOT/.venv"
export PATH="$ROOT/.venv/bin:$PATH"

cd "$ROOT"

if [ "$BACKEND_ONLY" = true ]; then
    info "Starting backend only..."
    npm run backend
elif [ "$FRONTEND_ONLY" = true ]; then
    info "Starting frontend only..."
    npm run frontend
else
    npm run dev
fi
