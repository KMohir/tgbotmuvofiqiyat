# import psycopg2  # Для PostgreSQL (оставлено для возврата)
import sqlite3  # Для SQLite
from datetime import datetime
import json
import logging
import os
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Настройка ротации логов: 5 МБ на файл, хранить 3 последних архива
log_handler = RotatingFileHandler(
    'bot.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Загрузка переменных окружения из .env файла
load_dotenv()

# --- Импортируем оба драйвера ---
try:
    import psycopg2
except ImportError:
    psycopg2 = None

class Database:
    def __init__(self, db_type=None):
        try:
            # Определяем тип базы
            if db_type is None:
                db_type = os.getenv("DB_TYPE", "sqlite").lower()
            self.db_type = db_type

            if db_type == "postgres":
                self.conn = psycopg2.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    port=int(os.getenv("DB_PORT", 5432)),
                    dbname=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASS")
                )
                self.cursor = self.conn.cursor()
            else:
                db_path = os.getenv("SQLITE_PATH", "centris.db")
                self.conn = sqlite3.connect(db_path, check_same_thread=False)
                self.cursor = self.conn.cursor()
            self.create_tables()
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            raise

    def create_tables(self):
        try:
            if self.db_type == "postgres":
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        name TEXT,
                        phone TEXT,
                        datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        video_index INTEGER DEFAULT 0,
                        preferred_time TEXT DEFAULT '07:00',
                        last_sent TIMESTAMP,
                        is_subscribed BOOLEAN DEFAULT TRUE,
                        viewed_videos JSONB DEFAULT '[]'::jsonb,
                        is_group BOOLEAN DEFAULT FALSE
                    )
                ''')
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS support (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT,
                        message TEXT,
                        datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')
            else:
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        name TEXT,
                        phone TEXT,
                        datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        video_index INTEGER DEFAULT 0,
                        preferred_time TEXT DEFAULT '07:00',
                        last_sent TIMESTAMP,
                        is_subscribed BOOLEAN DEFAULT 1,
                        viewed_videos TEXT DEFAULT '[]',
                        is_group BOOLEAN DEFAULT 0
                    )
                ''')
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS support (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        message TEXT,
                        datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")
            self.conn.rollback()

    def user_exists(self, user_id):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            else:
                self.cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Ошибка при проверке существования пользователя {user_id}: {e}")
            return False

    def add_user(self, user_id, name, phone, preferred_time="07:00", is_group=False):
        try:
            if self.db_type == "postgres":
                self.cursor.execute('''
                    INSERT OR IGNORE INTO users (user_id, name, phone, preferred_time, is_group)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (user_id, name, phone, preferred_time, int(is_group)))
                self.cursor.execute('''
                    UPDATE users SET is_subscribed = 1 WHERE user_id = %s
                ''', (user_id,))
            else:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO users (user_id, name, phone, preferred_time, is_group)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, name, phone, preferred_time, int(is_group)))
                self.cursor.execute('''
                    UPDATE users SET is_subscribed = 1 WHERE user_id = ?
                ''', (user_id,))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя {user_id}: {e}")
            self.conn.rollback()

    def update(self, user_id, name, phone, preferred_time="07:00", is_group=False):
        try:
            if self.db_type == "postgres":
                self.cursor.execute('''
                    INSERT OR REPLACE INTO users (user_id, name, phone, preferred_time, is_group)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (user_id, name, phone, preferred_time, int(is_group)))
            else:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO users (user_id, name, phone, preferred_time, is_group)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, name, phone, preferred_time, int(is_group)))
            self.conn.commit()
            logger.info(f"Данные пользователя {user_id} успешно обновлены")
        except Exception as e:
            logger.error(f"Ошибка при обновлении пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_name(self, user_id):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
            else:
                self.cursor.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else "Не указано"
        except Exception as e:
            logger.error(f"Ошибка при получении имени пользователя {user_id}: {e}")
            return "Не указано"

    def get_phone(self, user_id):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT phone FROM users WHERE user_id = %s", (user_id,))
            else:
                self.cursor.execute("SELECT phone FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else "Не указано"
        except Exception as e:
            logger.error(f"Ошибка при получении телефона пользователя {user_id}: {e}")
            return "Не указано"

    def get_registration_time(self, user_id):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT datetime FROM users WHERE user_id = %s", (user_id,))
            else:
                self.cursor.execute("SELECT datetime FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Ошибка при получении времени регистрации пользователя {user_id}: {e}")
            return None

    def get_all_users(self):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT user_id FROM users WHERE is_subscribed = 1")
            else:
                self.cursor.execute("SELECT user_id FROM users WHERE is_subscribed = 1")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка при получении списка пользователей: {e}")
            return []

    def get_all_users_data(self):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT user_id, name, phone, datetime, video_index, preferred_time, is_group FROM users")
            else:
                self.cursor.execute("SELECT user_id, name, phone, datetime, video_index, preferred_time, is_group FROM users")
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка при получении данных пользователей: {e}")
            return []

    def get_all_subscribers_with_type(self):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT user_id, is_group FROM users WHERE is_subscribed = 1")
            else:
                self.cursor.execute("SELECT user_id, is_group FROM users WHERE is_subscribed = 1")
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка при получении подписчиков с типом: {e}")
            return []

    def get_video_index(self, user_id):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT video_index FROM users WHERE user_id = %s", (user_id,))
            else:
                self.cursor.execute("SELECT video_index FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return int(result[0]) if result else 0
        except Exception as e:
            logger.error(f"Ошибка при получении индекса видео пользователя {user_id}: {e}")
            return 0

    def update_video_index(self, user_id, index):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("UPDATE users SET video_index = %s WHERE user_id = %s", (index, user_id))
            else:
                self.cursor.execute("UPDATE users SET video_index = ? WHERE user_id = ?", (index, user_id))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при обновлении индекса видео пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_viewed_videos(self, user_id):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT viewed_videos FROM users WHERE user_id = %s", (user_id,))
            else:
                self.cursor.execute("SELECT viewed_videos FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
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
                if self.db_type == "postgres":
                    self.cursor.execute("UPDATE users SET viewed_videos = %s WHERE user_id = %s", (json.dumps(viewed_videos), user_id))
                else:
                    self.cursor.execute(
                        "UPDATE users SET viewed_videos = ? WHERE user_id = ?",
                        (json.dumps(viewed_videos), user_id)
                    )
                self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при отметке видео как просмотренного пользователем {user_id}: {e}")
            self.conn.rollback()

    def get_preferred_time(self, user_id):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT preferred_time FROM users WHERE user_id = %s", (user_id,))
            else:
                self.cursor.execute("SELECT preferred_time FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else "07:00"
        except Exception as e:
            logger.error(f"Ошибка при получении предпочтительного времени пользователя {user_id}: {e}")
            return "07:00"

    def set_preferred_time(self, user_id, time):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("UPDATE users SET preferred_time = %s WHERE user_id = %s", (time, user_id))
            else:
                self.cursor.execute("UPDATE users SET preferred_time = ? WHERE user_id = ?", (time, user_id))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при установке предпочтительного времени пользователя {user_id}: {e}")
            self.conn.rollback()

    def update_last_sent(self, user_id, last_sent):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("UPDATE users SET last_sent = %s WHERE user_id = %s", (last_sent, user_id))
            else:
                self.cursor.execute(
                    "UPDATE users SET last_sent = ? WHERE user_id = ?",
                    (last_sent, user_id)
                )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при обновлении времени последней отправки пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_last_sent(self, user_id):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT last_sent FROM users WHERE user_id = %s", (user_id,))
            else:
                self.cursor.execute("SELECT last_sent FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Ошибка при получении времени последней отправки пользователя {user_id}: {e}")
            return None

    def set_subscription_status(self, user_id, status):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("UPDATE users SET is_subscribed = %s WHERE user_id = %s", (int(status), user_id))
            else:
                self.cursor.execute("UPDATE users SET is_subscribed = ? WHERE user_id = ?", (int(status), user_id))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при установке статуса подписки пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_subscription_status(self, user_id):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT is_subscribed FROM users WHERE user_id = %s", (user_id,))
            else:
                self.cursor.execute("SELECT is_subscribed FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return bool(result[0]) if result else True
        except Exception as e:
            logger.error(f"Ошибка при получении статуса подписки пользователя {user_id}: {e}")
            return True

    def unsubscribe_user(self, user_id):
        self.set_subscription_status(user_id, False)

    def add_questions(self, user_id, message_id):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("INSERT INTO support (user_id, message) VALUES (%s, %s)", (user_id, str(message_id)))
            else:
                self.cursor.execute(
                    "INSERT INTO support (user_id, message) VALUES (?, ?)",
                    (user_id, str(message_id))
                )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при добавлении вопроса пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_id(self):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT id FROM support ORDER BY id DESC LIMIT 1")
            else:
                self.cursor.execute("SELECT id FROM support ORDER BY id DESC LIMIT 1")
            result = self.cursor.fetchone()
            return result[0] if result else 1
        except Exception as e:
            logger.error(f"Ошибка при получении ID вопроса: {e}")
            return 1

    def get_question(self, user_id):
        try:
            if self.db_type == "postgres":
                self.cursor.execute("SELECT message FROM support WHERE user_id = %s", (user_id,))
            else:
                self.cursor.execute("SELECT message FROM support WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return int(result[0]) if result else None
        except Exception as e:
            logger.error(f"Ошибка при получении вопроса пользователя {user_id}: {e}")
            return None

    def close(self):
        try:
            self.conn.close()
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединения с базой данных: {e}")

# --- Автоматический выбор базы ---
db_type = os.getenv("DB_TYPE", "sqlite").lower()
if db_type == "postgres":
    db = Database(db_type="postgres")
else:
    db = Database(db_type="sqlite")

# Теперь для переключения между SQLite и PostgreSQL достаточно поменять DB_TYPE в .env
# DB_TYPE=sqlite  или  DB_TYPE=postgres
