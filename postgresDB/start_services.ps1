# Запуск служб бази даних Avocado
Write-Host "Starting Avocado database services..." -ForegroundColor Green
Write-Host ""

# Переходимо в кореневу папку проекту
Set-Location (Split-Path $PSScriptRoot -Parent)
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow

Write-Host "Starting PostgreSQL, Redis and Adminer..." -ForegroundColor Cyan
docker compose -f "postgresDB\docker-compose.db.yml" --env-file .env up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Services started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Available services:" -ForegroundColor Blue
    Write-Host "  PostgreSQL: localhost:5432" -ForegroundColor White
    Write-Host "  Redis:      localhost:6379" -ForegroundColor White
    Write-Host "  Adminer:    http://localhost:8080" -ForegroundColor White
    Write-Host ""
    Write-Host "🔗 Database connection:" -ForegroundColor Blue
    Write-Host "  Host: localhost" -ForegroundColor White
    Write-Host "  Port: 5432" -ForegroundColor White
    Write-Host "  Database: avocado_db" -ForegroundColor White
    Write-Host "  User: avocado_user" -ForegroundColor White
    Write-Host "  Password: avocado_pass" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 To stop services, run: .\stop_services.ps1" -ForegroundColor Yellow
}
else {
    Write-Host ""
    Write-Host "❌ Failed to start services. Check Docker Desktop and port availability." -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to continue"
