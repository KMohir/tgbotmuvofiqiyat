import sqlite3
import logging

# Настройка логирования
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def migrate_database():
    """Миграция базы данных для добавления поля is_banned"""
    try:
        conn = sqlite3.connect('centris.db')
        cursor = conn.cursor()
        
        # Проверяем, существует ли поле is_banned
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_banned' not in columns:
            logger.info("Добавляем поле is_banned в таблицу users...")
            cursor.execute('ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT 0')
            conn.commit()
            logger.info("Поле is_banned успешно добавлено")
        else:
            logger.info("Поле is_banned уже существует")
        
        # Создание таблицы админов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            is_superadmin INTEGER DEFAULT 0
        )
        ''')

        # Добавление главного админа
        cursor.execute('''
        INSERT OR IGNORE INTO admins (user_id, is_superadmin) VALUES (?, ?)
        ''', (5657091547, 1))

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