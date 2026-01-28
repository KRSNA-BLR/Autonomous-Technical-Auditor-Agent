# =============================================================================
# start-dev.ps1 - Script para iniciar el entorno de desarrollo
# =============================================================================
# Autor: Danilo Viteri
# Uso: .\start-dev.ps1
# =============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Autonomous Research Agent" -ForegroundColor White
Write-Host "  Full Stack Development Server" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[API]" -ForegroundColor Cyan -NoNewline
Write-Host " Backend:  " -NoNewline
Write-Host "http://localhost:8000" -ForegroundColor Yellow
Write-Host "[WEB]" -ForegroundColor Magenta -NoNewline
Write-Host " Frontend: " -NoNewline
Write-Host "http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Presiona Ctrl+C para detener ambos servidores" -ForegroundColor DarkGray
Write-Host ""

# Ejecutar ambos servidores con concurrently
npm run dev
