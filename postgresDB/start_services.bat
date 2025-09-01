@echo off
echo Starting Avocado database services...
echo.

cd /d "%~dp0\.."
echo Current directory: %CD%

echo Starting PostgreSQL, Redis and Adminer...
docker compose -f "postgresDB\docker-compose.db.yml" --env-file .env up -d

if %ERRORLEVEL% equ 0 (
    echo.
    echo ✅ Services started successfully!
    echo.
    echo 📊 Available services:
    echo   PostgreSQL: localhost:5432
    echo   Redis:      localhost:6379
    echo   Adminer:    http://localhost:8080
    echo.
    echo 🔗 Database connection:
    echo   Host: localhost
    echo   Port: 5432
    echo   Database: avocado_db
    echo   User: avocado_user
    echo   Password: avocado_pass
    echo.
    echo 💡 To stop services, run: stop_services.bat
) else (
    echo.
    echo ❌ Failed to start services. Check Docker Desktop and port availability.
)

echo.
pause
