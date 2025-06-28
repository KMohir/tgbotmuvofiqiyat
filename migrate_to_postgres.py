import sqlite3
import psycopg2
import os
import json
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

def migrate_sqlite_to_postgres():
    """Миграция данных из SQLite в PostgreSQL"""
    try:
        logger.info("Подключаемся к SQLite...")
        # Подключение к SQLite
        sqlite_conn = sqlite3.connect('centris.db')
        sqlite_cursor = sqlite_conn.cursor()
        
        logger.info("Подключаемся к PostgreSQL...")
        # Подключение к PostgreSQL
        pg_conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'mydatabase'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASS', '7777')
        )
        pg_cursor = pg_conn.cursor()
        
        logger.info("Начинаем миграцию данных...")
        
        # Миграция таблицы users
        logger.info("Мигрируем таблицу users...")
        sqlite_cursor.execute("SELECT * FROM users")
        users_data = sqlite_cursor.fetchall()
        logger.info(f"Найдено {len(users_data)} пользователей в SQLite")
        
        for user in users_data:
            try:
                pg_cursor.execute('''
                    INSERT INTO users (user_id, name, phone, datetime, video_index, preferred_time, last_sent, is_subscribed, viewed_videos, is_group, is_banned)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO NOTHING
                ''', user)
            except Exception as e:
                logger.error(f"Ошибка при миграции пользователя {user[0]}: {e}")
        
        # Миграция таблицы support
        logger.info("Мигрируем таблицу support...")
        sqlite_cursor.execute("SELECT user_id, message, datetime FROM support")
        support_data = sqlite_cursor.fetchall()
        logger.info(f"Найдено {len(support_data)} записей support в SQLite")
        
        for support in support_data:
            try:
                pg_cursor.execute('''
                    INSERT INTO support (user_id, message, datetime)
                    VALUES (%s, %s, %s)
                ''', support)
            except Exception as e:
                logger.error(f"Ошибка при миграции записи support: {e}")
        
        # Миграция таблицы settings
        logger.info("Мигрируем таблицу settings...")
        sqlite_cursor.execute("SELECT key, value FROM settings")
        settings_data = sqlite_cursor.fetchall()
        logger.info(f"Найдено {len(settings_data)} настроек в SQLite")
        
        for setting in settings_data:
            try:
                pg_cursor.execute('''
                    INSERT INTO settings (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                ''', setting)
            except Exception as e:
                logger.error(f"Ошибка при миграции настройки {setting[0]}: {e}")
        
        # Миграция настроек групп из settings в group_video_settings
        logger.info("Мигрируем настройки групп...")
        sqlite_cursor.execute("SELECT key, value FROM settings WHERE key LIKE 'group_%_season'")
        group_settings = sqlite_cursor.fetchall()
        logger.info(f"Найдено {len(group_settings)} настроек групп в SQLite")
        
        for setting in group_settings:
            try:
                # Извлекаем chat_id из ключа (group_123_season -> 123)
                parts = setting[0].split('_')
                if len(parts) >= 3:
                    chat_id = int(parts[1])
                    season = setting[1]
                    
                    # Получаем video_index
                    video_key = f"group_{chat_id}_video_index"
                    sqlite_cursor.execute("SELECT value FROM settings WHERE key = ?", (video_key,))
                    video_result = sqlite_cursor.fetchone()
                    video_index = int(video_result[0]) if video_result else 0
                    
                    pg_cursor.execute('''
                        INSERT INTO group_video_settings (chat_id, season, video_index)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (chat_id) DO UPDATE SET season = EXCLUDED.season, video_index = EXCLUDED.video_index
                    ''', (chat_id, season, video_index))
            except Exception as e:
                logger.error(f"Ошибка при миграции настроек группы: {e}")
        
        # Подтверждаем изменения
        pg_conn.commit()
        
        logger.info(f"Миграция завершена успешно!")
        logger.info(f"Перенесено пользователей: {len(users_data)}")
        logger.info(f"Перенесено записей support: {len(support_data)}")
        logger.info(f"Перенесено настроек: {len(settings_data)}")
        logger.info(f"Перенесено настроек групп: {len(group_settings)}")
        
    except Exception as e:
        logger.error(f"Ошибка при миграции: {e}")
        import traceback
        logger.error(f"Полная ошибка: {traceback.format_exc()}")
        if 'pg_conn' in locals():
            pg_conn.rollback()
    finally:
        if 'sqlite_cursor' in locals():
            sqlite_cursor.close()
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'pg_cursor' in locals():
            pg_cursor.close()
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == "__main__":
    migrate_sqlite_to_postgres() 