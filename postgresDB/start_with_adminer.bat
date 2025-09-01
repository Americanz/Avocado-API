@echo off
echo Starting PostgreSQL, Redis and Adminer services...
echo.

docker compose -f docker-compose.db.yml up -d

echo.
echo Services started! Access points:
echo - PostgreSQL: localhost:5432
echo - Redis: localhost:7379
echo - Adminer (Database Management): http://localhost:8080
echo.
echo To connect via Adminer:
echo - Server: postgres
echo - Username: avocado_user  
echo - Password: avocado_pass
echo - Database: avocado_db
echo.
echo Press any key to view logs...
pause >nul

docker compose -f docker-compose.db.yml logs --follow