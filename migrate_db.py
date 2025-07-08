import psycopg2
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

def migrate_database():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'mydatabase'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASS', '7777')
        )
        cursor = conn.cursor()
        # Добавить поле is_banned, если его нет
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='users' AND column_name='is_banned'
        """)
        if not cursor.fetchone():
            logger.info("Добавляем поле is_banned в таблицу users...")
            cursor.execute('ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT 0')
            conn.commit()
            logger.info("Поле is_banned успешно добавлено")
        else:
            logger.info("Поле is_banned уже существует")
        # Создать таблицу admins, если её нет
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id BIGINT PRIMARY KEY,
                is_superadmin BOOLEAN DEFAULT FALSE
            )
        ''')
        conn.commit()
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