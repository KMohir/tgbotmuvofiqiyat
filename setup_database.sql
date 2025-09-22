-- Создание базы данных и пользователя для проекта Centris Towers Bot

-- Создаем пользователя
CREATE USER centris WITH PASSWORD '111';

-- Создаем базу данных
CREATE DATABASE centris OWNER centris;

-- Даем права пользователю
GRANT ALL PRIVILEGES ON DATABASE centris TO centris;

-- Подключаемся к базе данных centris
\c centris;

-- Даем права на схему public
GRANT ALL PRIVILEGES ON SCHEMA public TO centris;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO centris;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO centris;

-- Устанавливаем права по умолчанию для будущих объектов
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO centris;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO centris;
