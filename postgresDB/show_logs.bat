@echo off
echo Showing Avocado database services logs...
echo.

cd /d "%~dp0\.."
echo Current directory: %CD%

echo Press Ctrl+C to stop watching logs
echo.
docker compose -f "postgresDB\docker-compose.db.yml" --env-file .env logs -f
