# =============================================================================
# start-dev.ps1 - One-Click Development Environment Launcher
# =============================================================================
# Author: Danilo Viteri Moreno
# Usage: .\start-dev.ps1
#        .\start-dev.ps1 -SkipInstall      # Skip dependency installation
#        .\start-dev.ps1 -BackendOnly       # Launch backend only
#        .\start-dev.ps1 -FrontendOnly      # Launch frontend only
# =============================================================================

param(
    [switch]$SkipInstall,
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

# ─── Helpers ─────────────────────────────────────────────────────────────────

function Write-Banner {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║   Autonomous Technical Auditor Agent         ║" -ForegroundColor Cyan
    Write-Host "  ║   Full-Stack Development Environment         ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Icon, [string]$Text, [string]$Color = "White")
    Write-Host "  [$Icon] " -ForegroundColor $Color -NoNewline
    Write-Host $Text
}

function Write-Ok   { param([string]$Text) Write-Step "OK" $Text "Green" }
function Write-Warn { param([string]$Text) Write-Step "!!" $Text "Yellow" }
function Write-Err  { param([string]$Text) Write-Step "XX" $Text "Red" }
function Write-Info { param([string]$Text) Write-Step ".." $Text "Cyan" }

# ─── Pre-flight Checks ──────────────────────────────────────────────────────

function Test-Prerequisites {
    Write-Host "  Checking prerequisites..." -ForegroundColor DarkGray
    $ok = $true

    # Python
    $venvPython = Join-Path $ROOT ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $pyVersion = & $venvPython --version 2>&1
        Write-Ok "Python venv: $pyVersion"
    } else {
        # Try system python
        $sysPython = Get-Command python -ErrorAction SilentlyContinue
        if ($sysPython) {
            Write-Warn "No .venv found -- creating virtual environment..."
            & python -m venv (Join-Path $ROOT ".venv")
            if ($LASTEXITCODE -ne 0) { Write-Err "Failed to create venv"; $ok = $false }
            else { Write-Ok "Virtual environment created" }
        } else {
            Write-Err "Python not found. Install Python 3.12+ from https://python.org"
            $ok = $false
        }
    }

    # Node.js
    $node = Get-Command node -ErrorAction SilentlyContinue
    if ($node) {
        $nodeVersion = & node --version 2>&1
        Write-Ok "Node.js: $nodeVersion"
    } else {
        Write-Err "Node.js not found. Install from https://nodejs.org"
        $ok = $false
    }

    # npm
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($npm) {
        $npmVersion = & npm --version 2>&1
        Write-Ok "npm: v$npmVersion"
    } else {
        Write-Err "npm not found"
        $ok = $false
    }

    # .env file
    $envFile = Join-Path $ROOT ".env"
    $envExample = Join-Path $ROOT ".env.example"
    if (Test-Path $envFile) {
        Write-Ok ".env file found"
        # Validate API keys
        $envContent = Get-Content $envFile -Raw
        $hasGoogle = $envContent -match "GOOGLE_API_KEY=\w{10,}"
        $hasGroq   = $envContent -match "GROQ_API_KEY=\w{10,}"
        if ($hasGoogle -or $hasGroq) {
            Write-Ok "API key(s) configured"
        } else {
            Write-Warn "No API keys detected in .env -- agent will not work without at least one key"
        }
    } elseif (Test-Path $envExample) {
        Write-Warn ".env not found -- copying from .env.example"
        Copy-Item $envExample $envFile
        Write-Warn "IMPORTANT: Edit .env and add your API keys before using the agent"
    } else {
        Write-Err ".env.example not found -- cannot auto-create .env"
        $ok = $false
    }

    return $ok
}

# ─── Dependency Installation ────────────────────────────────────────────────

function Install-Dependencies {
    $venvPip = Join-Path $ROOT ".venv\Scripts\pip.exe"

    Write-Host ""
    Write-Host "  Installing dependencies..." -ForegroundColor DarkGray

    # Python backend
    Write-Info "Installing Python packages (pip install -e .[dev])..."
    Push-Location $ROOT
    & $venvPip install -e ".[dev]" --quiet 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Python dependency installation failed"
        & $venvPip install -e ".[dev]" 2>&1
        Pop-Location
        return $false
    }
    Write-Ok "Python packages installed"
    Pop-Location

    # Root npm (concurrently)
    if (-not (Test-Path (Join-Path $ROOT "node_modules"))) {
        Write-Info "Installing root npm packages..."
        Push-Location $ROOT
        & npm install --silent 2>&1 | Out-Null
        Pop-Location
    }
    Write-Ok "Root npm packages ready"

    # Frontend npm
    $frontendDir = Join-Path $ROOT "frontend"
    if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
        Write-Info "Installing frontend npm packages..."
        Push-Location $frontendDir
        & npm install --silent 2>&1 | Out-Null
        Pop-Location
    }
    Write-Ok "Frontend npm packages ready"

    return $true
}

# ─── Data Directory ─────────────────────────────────────────────────────────

function Ensure-DataDir {
    $dataDir = Join-Path $ROOT "data"
    if (-not (Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
        Write-Ok "Created data/ directory for SQLite memory"
    }
}

# ─── Server Launch ──────────────────────────────────────────────────────────

function Start-Servers {
    Write-Host ""
    Write-Host "  +-------------------------------------------------+" -ForegroundColor DarkGray
    Write-Host "  |" -ForegroundColor DarkGray -NoNewline
    Write-Host "  API  Backend  " -ForegroundColor Cyan -NoNewline
    Write-Host "->  " -ForegroundColor DarkGray -NoNewline
    Write-Host "http://localhost:8000" -ForegroundColor Yellow -NoNewline
    Write-Host "       |" -ForegroundColor DarkGray
    Write-Host "  |" -ForegroundColor DarkGray -NoNewline
    Write-Host "  WEB  Frontend " -ForegroundColor Magenta -NoNewline
    Write-Host "->  " -ForegroundColor DarkGray -NoNewline
    Write-Host "http://localhost:3000" -ForegroundColor Yellow -NoNewline
    Write-Host "       |" -ForegroundColor DarkGray
    Write-Host "  |" -ForegroundColor DarkGray -NoNewline
    Write-Host "  DOC  Swagger  " -ForegroundColor Green -NoNewline
    Write-Host "->  " -ForegroundColor DarkGray -NoNewline
    Write-Host "http://localhost:8000/docs" -ForegroundColor Yellow -NoNewline
    Write-Host "  |" -ForegroundColor DarkGray
    Write-Host "  +-------------------------------------------------+" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Press Ctrl+C to stop all servers" -ForegroundColor DarkGray
    Write-Host ""

    # Activate venv for the backend command
    $env:VIRTUAL_ENV = Join-Path $ROOT ".venv"
    $env:PATH = "$(Join-Path $ROOT '.venv\Scripts');$env:PATH"

    Push-Location $ROOT

    if ($BackendOnly) {
        Write-Info "Starting backend only..."
        & npm run backend
    } elseif ($FrontendOnly) {
        Write-Info "Starting frontend only..."
        & npm run frontend
    } else {
        & npm run dev
    }

    Pop-Location
}

# ─── Main ────────────────────────────────────────────────────────────────────

Write-Banner

# Pre-flight
if (-not (Test-Prerequisites)) {
    Write-Host ""
    Write-Err "Prerequisites check failed. Fix the issues above and try again."
    exit 1
}

# Dependencies
if (-not $SkipInstall) {
    if (-not (Install-Dependencies)) {
        Write-Host ""
        Write-Err "Dependency installation failed."
        exit 1
    }
} else {
    Write-Warn "Skipping dependency installation (-SkipInstall)"
}

# Data directory
Ensure-DataDir

# Quality gate (quick check)
Write-Host ""
Write-Host "  Running quality checks..." -ForegroundColor DarkGray
$venvPython = Join-Path $ROOT ".venv\Scripts\python.exe"
& $venvPython -m ruff check src/ tests/ --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Ok "Lint check passed"
} else {
    Write-Warn "Lint issues detected (run: ruff check src/ tests/ --fix)"
}

# Launch
Start-Servers
