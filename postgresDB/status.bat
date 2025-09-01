@echo off
echo Checking Avocado database services status...
echo.

cd /d "%~dp0\.."
echo Current directory: %CD%

echo 🔍 Docker containers status:
docker compose -f "postgresDB\docker-compose.db.yml" --env-file .env ps

echo.
echo 🌐 Port usage:
echo Checking PostgreSQL port 5432...
netstat -an | findstr :5432
echo Checking Redis port 6379...
netstat -an | findstr :6379
echo Checking Adminer port 8080...
netstat -an | findstr :8080

echo.
echo 💾 Docker volumes:
docker volume ls | findstr postgresdb

echo.
pause
