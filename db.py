# import sqlite3  # Для SQLite (оставьте закомментированным)
import psycopg2  # Для PostgreSQL
from datetime import datetime
import json
import logging
import os
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Настройка ротации логов
log_handler = RotatingFileHandler('bot.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Загрузка переменных окружения
load_dotenv()

class Database:
    def __init__(self):
        try:
            # Подключение к PostgreSQL
            self.conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'mydatabase'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASS', '7777')
            )
            self.create_tables()
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            raise

    def create_tables(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    name TEXT,
                    phone TEXT,
                    datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    video_index INTEGER DEFAULT 0,
                    preferred_time TEXT DEFAULT '07:00',
                    last_sent TIMESTAMP,
                    is_subscribed BOOLEAN DEFAULT TRUE,
                    viewed_videos TEXT DEFAULT '[]',
                    is_group BOOLEAN DEFAULT FALSE,
                    is_banned BOOLEAN DEFAULT FALSE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS support (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    message TEXT,
                    datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_video_settings (
                    chat_id BIGINT PRIMARY KEY,
                    season TEXT,
                    video_index INTEGER DEFAULT 0
                )
            ''')
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")
            self.conn.rollback()

    def user_exists(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            exists = cursor.fetchone() is not None
            cursor.close()
            return exists
        except Exception as e:
            logger.error(f"Ошибка при проверке существования пользователя {user_id}: {e}")
            return False

    def add_user(self, user_id, name, phone, preferred_time="07:00", is_group=False):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO users (user_id, name, phone, preferred_time, is_group)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            ''', (user_id, name, phone, preferred_time, is_group))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя {user_id}: {e}")
            self.conn.rollback()

    def update(self, user_id, name, phone, preferred_time="07:00", is_group=False):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE users SET name = %s, phone = %s, preferred_time = %s, is_group = %s
                WHERE user_id = %s
            ''', (name, phone, preferred_time, is_group, user_id))
            self.conn.commit()
            cursor.close()
            logger.info(f"Данные пользователя {user_id} успешно обновлены")
        except Exception as e:
            logger.error(f"Ошибка при обновлении пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_name(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else "Не указано"
        except Exception as e:
            logger.error(f"Ошибка при получении имени пользователя {user_id}: {e}")
            return "Не указано"

    def get_phone(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT phone FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else "Не указано"
        except Exception as e:
            logger.error(f"Ошибка при получении телефона пользователя {user_id}: {e}")
            return "Не указано"

    def get_registration_time(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT datetime FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Ошибка при получении времени регистрации пользователя {user_id}: {e}")
            return None

    def get_all_users(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE is_subscribed = TRUE")
            result = [row[0] for row in cursor.fetchall()]
            logger.info(f"get_all_users: найдено пользователей: {len(result)}")
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении списка пользователей: {e}")
            return []

    def get_all_users_data(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id, name, phone, datetime, video_index, preferred_time, is_group FROM users")
            result = cursor.fetchall()
            logger.info(f"get_all_users_data: найдено пользователей: {len(result)}")
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении данных пользователей: {e}")
            return []

    def get_all_subscribers_with_type(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id, is_group FROM users WHERE is_subscribed = TRUE")
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении подписчиков: {e}")
            return []

    def get_video_index(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT video_index FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return int(result[0]) if result else 0
        except Exception as e:
            logger.error(f"Ошибка при получении индекса видео пользователя {user_id}: {e}")
            return 0

    def update_video_index(self, user_id, index):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE users SET video_index = %s WHERE user_id = %s", (index, user_id))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при обновлении индекса видео пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_viewed_videos(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT viewed_videos FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            if result and result[0]:
                return json.loads(result[0])
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении просмотренных видео пользователя {user_id}: {e}")
            return []

    def mark_video_as_viewed(self, user_id, video_index):
        try:
            viewed_videos = self.get_viewed_videos(user_id)
            if video_index not in viewed_videos:
                viewed_videos.append(video_index)
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE users SET viewed_videos = %s WHERE user_id = %s",
                    (json.dumps(viewed_videos), user_id)
                )
                self.conn.commit()
                cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при отметке видео как просмотренного пользователем {user_id}: {e}")
            self.conn.rollback()

    def get_preferred_time(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT preferred_time FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else "07:00"
        except Exception as e:
            logger.error(f"Ошибка при получении предпочтительного времени пользователя {user_id}: {e}")
            return "07:00"

    def set_preferred_time(self, user_id, time):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE users SET preferred_time = %s WHERE user_id = %s", (time, user_id))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при установке предпочтительного времени пользователя {user_id}: {e}")
            self.conn.rollback()

    def update_last_sent(self, user_id, last_sent):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE users SET last_sent = %s WHERE user_id = %s",
                (last_sent, user_id)
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при обновлении времени последней отправки пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_last_sent(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT last_sent FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Ошибка при получении времени последней отправки пользователя {user_id}: {e}")
            return None

    def set_subscription_status(self, user_id, status):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE users SET is_subscribed = %s WHERE user_id = %s", (status, user_id))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при установке статуса подписки пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_subscription_status(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT is_subscribed FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return bool(result[0]) if result else True
        except Exception as e:
            logger.error(f"Ошибка при получении статуса подписки пользователя {user_id}: {e}")
            return True

    def unsubscribe_user(self, user_id):
        self.set_subscription_status(user_id, False)

    def add_questions(self, user_id, message_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO support (user_id, message) VALUES (%s, %s)",
                (user_id, str(message_id))
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при добавлении вопроса пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_id(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM support ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else 1
        except Exception as e:
            logger.error(f"Ошибка при получении ID вопроса: {e}")
            return 1

    def get_question(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT message FROM support WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return int(result[0]) if result else None
        except Exception as e:
            logger.error(f"Ошибка при получении вопроса пользователя {user_id}: {e}")
            return None

    def set_start_video_index(self, video_index: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                ("start_video_index", str(video_index))
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при установке начального индекса видео: {e}")
            self.conn.rollback()

    def get_start_video_index(self) -> int:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = %s", ("start_video_index",))
            result = cursor.fetchone()
            cursor.close()
            return int(result[0]) if result else 0
        except Exception as e:
            logger.error(f"Ошибка при получении начального индекса видео: {e}")
            return 0

    def set_group_video_settings(self, chat_id: int, season: str, video_index: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO group_video_settings (chat_id, season, video_index) VALUES (%s, %s, %s) ON CONFLICT (chat_id) DO UPDATE SET season = EXCLUDED.season, video_index = EXCLUDED.video_index",
                (chat_id, season, video_index)
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при установке настроек видео для группы {chat_id}: {e}")
            self.conn.rollback()

    def get_group_video_settings(self, chat_id: int) -> tuple:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT season, video_index FROM group_video_settings WHERE chat_id = %s", (chat_id,))
            result = cursor.fetchone()
            cursor.close()
            return (result[0], result[1]) if result else (None, 0)
        except Exception as e:
            logger.error(f"Ошибка при получении настроек видео для группы {chat_id}: {e}")
            return (None, 0)

    def get_all_groups_with_settings(self) -> list:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT chat_id, season, video_index 
                FROM group_video_settings
            ''')
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении настроек групп: {e}")
            return []

    def ban_group(self, group_id: int):
        """Запретить группу"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE users SET is_banned = TRUE, is_subscribed = FALSE 
                WHERE user_id = %s AND is_group = TRUE
            ''', (group_id,))
            self.conn.commit()
            cursor.close()
            logger.info(f"Группа {group_id} заблокирована")
        except Exception as e:
            logger.error(f"Ошибка при блокировке группы {group_id}: {e}")
            self.conn.rollback()

    def unban_group(self, group_id: int):
        """Разрешить группу"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE users SET is_banned = FALSE, is_subscribed = TRUE 
                WHERE user_id = %s AND is_group = TRUE
            ''', (group_id,))
            self.conn.commit()
            cursor.close()
            logger.info(f"Группа {group_id} разблокирована")
        except Exception as e:
            logger.error(f"Ошибка при разблокировке группы {group_id}: {e}")
            self.conn.rollback()

    def is_group_banned(self, group_id: int) -> bool:
        """Проверить, заблокирована ли группа"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT is_banned FROM users 
                WHERE user_id = %s AND is_group = TRUE
            ''', (group_id,))
            result = cursor.fetchone()
            cursor.close()
            return bool(result[0]) if result else False
        except Exception as e:
            logger.error(f"Ошибка при проверке блокировки группы {group_id}: {e}")
            return False

    def get_banned_groups(self) -> list:
        """Получить список заблокированных групп"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT user_id, name FROM users 
                WHERE is_banned = TRUE AND is_group = TRUE
            ''')
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении заблокированных групп: {e}")
            return []

    def close(self):
        try:
            self.conn.close()
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединения с базой данных: {e}")

# Для SQLite (по умолчанию)
# db = Database()

# Для PostgreSQL (оставьте закомментированным)
db = Database()
