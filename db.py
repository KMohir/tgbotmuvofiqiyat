import psycopg2
from datetime import datetime
import json
import logging
import os
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения из .env файла
load_dotenv()

class Database:
    def __init__(self, host, port, dbname, user, password):
        try:
            self.conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password
            )
            self.cursor = self.conn.cursor()
            self.create_tables()
        except psycopg2.Error as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            raise

    def create_tables(self):
        try:
            # Создаем таблицу users
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
                    viewed_videos JSONB DEFAULT '[]'::jsonb
                )
            ''')

            # Создаем таблицу support
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS support (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    message TEXT,
                    datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Создаем таблицу settings
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')

            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Ошибка при создании таблиц: {e}")
            self.conn.rollback()

    def user_exists(self, user_id):
        try:
            self.cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            return self.cursor.fetchone() is not None
        except psycopg2.Error as e:
            logger.error(f"Ошибка при проверке существования пользователя {user_id}: {e}")
            return False

    def add_user(self, user_id, name, phone, preferred_time="07:00"):
        try:
            self.cursor.execute('''
                INSERT INTO users (user_id, name, phone, preferred_time)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            ''', (user_id, name, phone, preferred_time))
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Ошибка при добавлении пользователя {user_id}: {e}")
            self.conn.rollback()

    def update(self, user_id, name, phone, preferred_time="07:00"):
        try:
            self.cursor.execute('''
                INSERT INTO users (user_id, name, phone, preferred_time)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET name = EXCLUDED.name,
                    phone = EXCLUDED.phone,
                    preferred_time = EXCLUDED.preferred_time
            ''', (user_id, name, phone, preferred_time))
            self.conn.commit()
            logger.info(f"Данные пользователя {user_id} успешно обновлены")
        except psycopg2.Error as e:
            logger.error(f"Ошибка при обновлении пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_name(self, user_id):
        try:
            self.cursor.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else "Не указано"
        except psycopg2.Error as e:
            logger.error(f"Ошибка при получении имени пользователя {user_id}: {e}")
            return "Не указано"

    def get_phone(self, user_id):
        try:
            self.cursor.execute("SELECT phone FROM users WHERE user_id = %s", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else "Не указано"
        except psycopg2.Error as e:
            logger.error(f"Ошибка при получении телефона пользователя {user_id}: {e}")
            return "Не указано"

    def get_registration_time(self, user_id):
        try:
            self.cursor.execute("SELECT datetime FROM users WHERE user_id = %s", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except psycopg2.Error as e:
            logger.error(f"Ошибка при получении времени регистрации пользователя {user_id}: {e}")
            return None

    def get_all_users(self):
        try:
            self.cursor.execute("SELECT user_id FROM users WHERE is_subscribed = TRUE")
            return [row[0] for row in self.cursor.fetchall()]
        except psycopg2.Error as e:
            logger.error(f"Ошибка при получении списка пользователей: {e}")
            return []

    def get_all_users_data(self):
        try:
            self.cursor.execute("SELECT user_id, name, phone, datetime, video_index, preferred_time FROM users")
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            logger.error(f"Ошибка при получении данных пользователей: {e}")
            return []

    def get_video_index(self, user_id):
        try:
            self.cursor.execute("SELECT video_index FROM users WHERE user_id = %s", (user_id,))
            result = self.cursor.fetchone()
            return int(result[0]) if result else 0
        except psycopg2.Error as e:
            logger.error(f"Ошибка при получении индекса видео пользователя {user_id}: {e}")
            return 0

    def update_video_index(self, user_id, index):
        try:
            self.cursor.execute("UPDATE users SET video_index = %s WHERE user_id = %s", (index, user_id))
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Ошибка при обновлении индекса видео пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_viewed_videos(self, user_id):
        try:
            self.cursor.execute("SELECT viewed_videos FROM users WHERE user_id = %s", (user_id,))
            result = self.cursor.fetchone()
            if result and result[0]:
                return result[0]
            return []
        except psycopg2.Error as e:
            logger.error(f"Ошибка при получении просмотренных видео пользователя {user_id}: {e}")
            return []

    def mark_video_as_viewed(self, user_id, video_index):
        try:
            viewed_videos = self.get_viewed_videos(user_id)
            if video_index not in viewed_videos:
                viewed_videos.append(video_index)
                self.cursor.execute(
                    "UPDATE users SET viewed_videos = %s WHERE user_id = %s",
                    (json.dumps(viewed_videos), user_id)
                )
                self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Ошибка при отметке видео как просмотренного пользователем {user_id}: {e}")
            self.conn.rollback()

    def get_preferred_time(self, user_id):
        try:
            self.cursor.execute("SELECT preferred_time FROM users WHERE user_id = %s", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else "07:00"
        except psycopg2.Error as e:
            logger.error(f"Ошибка при получении предпочтительного времени пользователя {user_id}: {e}")
            return "07:00"

    def set_preferred_time(self, user_id, time):
        try:
            self.cursor.execute("UPDATE users SET preferred_time = %s WHERE user_id = %s", (time, user_id))
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Ошибка при установке предпочтительного времени пользователя {user_id}: {e}")
            self.conn.rollback()

    def update_last_sent(self, user_id, last_sent):
        try:
            self.cursor.execute(
                "UPDATE users SET last_sent = %s WHERE user_id = %s",
                (last_sent, user_id)
            )
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Ошибка при обновлении времени последней отправки пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_last_sent(self, user_id):
        try:
            self.cursor.execute("SELECT last_sent FROM users WHERE user_id = %s", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except psycopg2.Error as e:
            logger.error(f"Ошибка при получении времени последней отправки пользователя {user_id}: {e}")
            return None

    def set_subscription_status(self, user_id, status):
        try:
            self.cursor.execute("UPDATE users SET is_subscribed = %s WHERE user_id = %s", (status, user_id))
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Ошибка при установке статуса подписки пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_subscription_status(self, user_id):
        try:
            self.cursor.execute("SELECT is_subscribed FROM users WHERE user_id = %s", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else True
        except psycopg2.Error as e:
            logger.error(f"Ошибка при получении статуса подписки пользователя {user_id}: {e}")
            return True

    def unsubscribe_user(self, user_id):
        self.set_subscription_status(user_id, False)

    def add_questions(self, user_id, message_id):
        try:
            self.cursor.execute(
                "INSERT INTO support (user_id, message) VALUES (%s, %s)",
                (user_id, str(message_id))
            )
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Ошибка при добавлении вопроса пользователя {user_id}: {e}")
            self.conn.rollback()

    def get_id(self):
        try:
            self.cursor.execute("SELECT id FROM support ORDER BY id DESC LIMIT 1")
            result = self.cursor.fetchone()
            return result[0] if result else 1
        except psycopg2.Error as e:
            logger.error(f"Ошибка при получении ID вопроса: {e}")
            return 1

    def get_question(self, user_id):
        try:
            self.cursor.execute("SELECT message FROM support WHERE user_id = %s", (user_id,))
            result = self.cursor.fetchone()
            return int(result[0]) if result else None
        except psycopg2.Error as e:
            logger.error(f"Ошибка при получении вопроса пользователя {user_id}: {e}")
            return None

    def close(self):
        try:
            self.conn.close()
        except psycopg2.Error as e:
            logger.error(f"Ошибка при закрытии соединения с базой данных: {e}")

try:
    db = Database(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
except Exception as e:
    logger.critical(f"Критическая ошибка при инициализации базы данных: {e}")
    raise
