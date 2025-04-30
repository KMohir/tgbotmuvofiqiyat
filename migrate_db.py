import sqlite3

conn = sqlite3.connect("databaseprotestim.db")
cursor = conn.cursor()

# Добавляем столбец is_subscribed
try:
    cursor.execute("ALTER TABLE users ADD COLUMN is_subscribed INTEGER DEFAULT 1")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Столбец is_subscribed уже существует, пропускаем.")
    else:
        raise e

# Устанавливаем is_subscribed = 1 для всех существующих пользователей
cursor.execute("UPDATE users SET is_subscribed = 1 WHERE is_subscribed IS NULL")
conn.commit()
conn.close()

print("Столбец is_subscribed добавлен в таблицу users и установлен в 1 для всех пользователей.")