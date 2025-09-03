# 🗄️ Подключение к базе данных centris.sql

## 📝 Обновите .env файл:

Откройте файл `.env` и убедитесь, что он содержит:

```env
# Конфигурация Telegram бота
BOT_TOKEN=8006379698:AAG_D2yWYU9jzY6Xp9RzvGE0A-qgWoFSWlk

# Администраторы (через запятую, без пробелов)
ADMINS=5657091547,8053364577,5310261745

# Настройки сервера
ip=localhost

# Операторы поддержки (через запятую)
operator=5657091547,8053364577,5310261745

# Настройки базы данных PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=centris
DB_USER=postgres
DB_PASS=111
DB_TYPE=postgresql

# Супер-администратор (обратная совместимость)
SUPER_ADMIN_ID=5657091547
```

## 🔧 Если база данных называется по-другому:

### Вариант 1: База называется "centris"
```env
DB_NAME=centris
```

### Вариант 2: База называется "centris.sql" (неправильно)
**Исправьте на:**
```env
DB_NAME=centris
```

### Вариант 3: Файл базы данных centris.sql
Если у вас есть файл `centris.sql`, сначала импортируйте его:

```bash
# Создать базу данных
createdb -U postgres centris

# Импортировать данные из файла
psql -U postgres -d centris -f centris.sql
```

## 🚀 Команды для проверки подключения:

### 1. Проверьте подключение к PostgreSQL:
```bash
psql -U postgres -d centris -c "SELECT version();"
```

### 2. Проверьте таблицы в базе:
```bash
psql -U postgres -d centris -c "\dt"
```

### 3. Проверьте подключение в Python:
```bash
python3 -c "from db import db; print('Подключение успешно!')"
```

## ⚠️ Возможные проблемы:

1. **База данных не существует:**
   ```bash
   createdb -U postgres centris
   ```

2. **Неправильный пароль:**
   - Проверьте `DB_PASS=111` в .env файле

3. **PostgreSQL не запущен:**
   ```bash
   sudo service postgresql start
   ```

## 📋 После настройки:

1. **Перезапустите бота:**
   ```bash
   python3 app.py
   ```

2. **Проверьте команды:**
   ```
   /test_scheduled_video
   ```

База данных подключится автоматически при запуске бота!
