# 🗄️ Настройка базы данных PostgreSQL

## 📋 Проблема
Ошибка: `could not translate host name "db" to address: Name or service not known`

## 🔧 Решения

### **Вариант 1: Изменить .env файл (РЕКОМЕНДУЕТСЯ)**

1. Откройте файл `.env` в корне проекта
2. Измените строку:
   ```env
   # Было:
   DB_HOST=db
   
   # Должно быть:
   DB_HOST=localhost
   ```

### **Вариант 2: Создать базу данных и пользователя**

Если база данных `centris` не существует, выполните:

```bash
# 1. Подключитесь к PostgreSQL как суперпользователь
sudo -u postgres psql

# 2. Выполните команды в PostgreSQL:
CREATE USER centris WITH PASSWORD '111';
CREATE DATABASE centris OWNER centris;
GRANT ALL PRIVILEGES ON DATABASE centris TO centris;
\q

# 3. Проверьте подключение:
psql -h localhost -p 5432 -U centris -d centris -c "SELECT version();"
```

### **Вариант 3: Использовать существующую базу данных**

Если у вас есть другая база данных, измените настройки в `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=ваш_пользователь
DB_PASSWORD=ваш_пароль
DB_NAME=ваша_база_данных
```

## ✅ Проверка

После настройки запустите:

```bash
python3 -c "from db import db; print('✅ Подключение к базе данных успешно!')"
```

## 🚀 Запуск бота

После успешной настройки базы данных:

```bash
python3 app.py
```

## 📝 Примечания

- Убедитесь, что PostgreSQL запущен: `pg_isready -h localhost -p 5432`
- Проверьте права доступа к базе данных
- При первом запуске бот автоматически создаст необходимые таблицы
