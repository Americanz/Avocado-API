@echo off
:: Database management script for Avocado project

if "%1"=="up" (
    echo Starting PostgreSQL and Redis containers...
    docker compose -f docker-compose.db.yml up -d
    goto :end
)

if "%1"=="down" (
    echo Stopping containers...
    docker compose -f docker-compose.db.yml down
    goto :end
)

if "%1"=="restart" (
    echo Restarting containers...
    docker compose -f docker-compose.db.yml restart
    goto :end
)

if "%1"=="status" (
    echo Container status:
    docker compose -f docker-compose.db.yml ps
    goto :end
)

if "%1"=="logs" (
    echo Container logs:
    docker compose -f docker-compose.db.yml logs
    goto :end
)

if "%1"=="clean" (
    echo Stopping and removing containers with data...
    docker compose -f docker-compose.db.yml down -v
    goto :end
)

if "%1"=="psql" (
    echo Connecting to PostgreSQL...
    docker exec -it avocado_postgres psql -U avocado_user -d avocado_db
    goto :end
)

if "%1"=="redis" (
    echo Connecting to Redis...
    docker exec -it avocado_redis redis-cli
    goto :end
)

if "%1"=="test" (
    echo Testing connections...
    cd ..
    python test_connections.py
    goto :end
)

echo Usage: manage_db.bat [command]
echo.
echo Commands:
echo   up       - Start containers
echo   down     - Stop containers  
echo   restart  - Restart containers
echo   status   - Show container status
echo   logs     - Show container logs
echo   clean    - Stop and remove containers with data
echo   psql     - Connect to PostgreSQL
echo   redis    - Connect to Redis CLI
echo   test     - Test database connections

:end