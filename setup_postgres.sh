#!/bin/bash

# Обновление системы
sudo apt update
sudo apt upgrade -y

# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Запуск PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Создание базы данных и пользователя
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '7777';"
sudo -u postgres createdb project_db

# Настройка доступа
echo "host    all             all             127.0.0.1/32            md5" | sudo tee -a /etc/postgresql/*/main/pg_hba.conf
echo "host    all             all             ::1/128                 md5" | sudo tee -a /etc/postgresql/*/main/pg_hba.conf

# Перезапуск PostgreSQL
sudo systemctl restart postgresql

# Установка Python и необходимых пакетов
sudo apt install python3 python3-pip -y
pip3 install psycopg2-binary python-telegram-bot

echo "Установка завершена! PostgreSQL запущен и настроен." 