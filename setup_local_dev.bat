@echo off
echo Setting up local development environment for Avocado...
echo.

:: Start databases
echo Starting PostgreSQL and Redis...
docker compose -f docker/docker-compose.db.yml up -d

:: Wait a bit for containers to start
echo Waiting for databases to start...
timeout /t 10 /nobreak >nul

:: Check container status
echo Checking container status...
docker compose -f docker/docker-compose.db.yml ps

:: Test connections
echo.
echo Testing database connections...
python test_connections.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Local development environment is ready!
    echo ========================================
    echo.
    echo PostgreSQL: localhost:5432
    echo Redis: localhost:7379
    echo.
    echo Configuration files:
    echo   Database settings: .env
    echo   Docker settings: docker/docker-compose.db.yml
    echo.
    echo To run the application:
    echo   poetry run python run.py
    echo.
    echo To run migrations:
    echo   alembic upgrade head
    echo.
    echo To stop databases:
    echo   docker\manage_db.bat down
    echo.
) else (
    echo.
    echo ========================================
    echo Setup failed! Please check the errors above.
    echo ========================================
)

pause