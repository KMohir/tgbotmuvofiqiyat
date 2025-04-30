@echo off
echo Установка PostgreSQL...

:: Установка PostgreSQL (требует прав администратора)
winget install -e --id PostgreSQL.PostgreSQL

:: Создание базы данных и пользователя
psql -U postgres -c "ALTER USER postgres WITH PASSWORD '7777';"
psql -U postgres -c "CREATE DATABASE project_db;"

:: Установка Python и необходимых пакетов
pip install psycopg2-binary python-telegram-bot

echo Установка завершена! PostgreSQL настроен.
pause 