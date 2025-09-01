@echo off
echo Stopping Avocado database services...
echo.

cd /d "%~dp0\.."
echo Current directory: %CD%

echo Stopping PostgreSQL, Redis and Adminer...
docker compose -f "postgresDB\docker-compose.db.yml" --env-file .env down

if %ERRORLEVEL% equ 0 (
    echo.
    echo ✅ Services stopped successfully!
) else (
    echo.
    echo ❌ Failed to stop services. Check Docker Desktop.
)

echo.
echo To remove all data volumes as well, run:
echo docker compose -f "postgresDB\docker-compose.db.yml" --env-file .env down -v
echo.
pause
echo docker compose -f docker-compose.db.yml down -v
echo.
pause
