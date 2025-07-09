import psycopg2
import logging
import os
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

load_dotenv()

PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_DB = os.getenv('PG_DB', 'project_db')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', '7777')


def column_exists(cursor, table, column):
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name=%s AND column_name=%s
    """, (table, column))
    return cursor.fetchone() is not None

def migrate_database():
    """
    Миграция базы данных для добавления поля is_banned и таблицы admins (PostgreSQL)
    """
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Проверяем, существует ли поле is_banned
        if not column_exists(cursor, 'users', 'is_banned'):
            logger.info("Добавляем поле is_banned в таблицу users...")
            cursor.execute('ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0')
            logger.info("Поле is_banned успешно добавлено")
        else:
            logger.info("Поле is_banned уже существует")

        # Создание таблицы админов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id BIGINT PRIMARY KEY
        )
        ''')

        # Добавление главного админа
        SUPERADMIN_ID = 5657091547
        cursor.execute('''
        INSERT INTO admins (user_id) VALUES (%s)
        ON CONFLICT (user_id) DO NOTHING
        ''', (SUPERADMIN_ID,))

        cursor.close()
        conn.close()
        logger.info("Миграция завершена успешно")

    except Exception as e:
        logger.error(f"Ошибка при миграции: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    migrate_database()