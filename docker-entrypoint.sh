#!/bin/bash
set -e

# Выполнение инициализации базы данных
echo "Running database initialization..."
python init_db.py

# Запуск основного приложения
echo "Starting main application..."
exec "$@"