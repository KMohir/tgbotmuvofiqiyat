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
logger.setLevel(logging.ERROR)
logger.addHandler(log_handler)

# Загрузка переменных окружения
load_dotenv()

class Database:
    def __init__(self):
        try:
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

    def _add_column_if_not_exists(self, cursor, table_name, column_name, column_type):
        cursor.execute("""
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
        """, (table_name, column_name))
        if cursor.fetchone() is None:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            logger.info(f"Добавлен столбец '{column_name}' в таблицу '{table_name}'.")

    def create_tables(self):
        try:
            cursor = self.conn.cursor()
            
            # --- Таблица users ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY
                )
            ''')
            self._add_column_if_not_exists(cursor, 'users', 'name', 'TEXT')
            self._add_column_if_not_exists(cursor, 'users', 'phone', 'TEXT')
            self._add_column_if_not_exists(cursor, 'users', 'datetime', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            self._add_column_if_not_exists(cursor, 'users', 'video_index', 'INTEGER DEFAULT 0')
            self._add_column_if_not_exists(cursor, 'users', 'preferred_time', "TEXT DEFAULT '07:00'")
            self._add_column_if_not_exists(cursor, 'users', 'last_sent', 'TIMESTAMP')
            self._add_column_if_not_exists(cursor, 'users', 'is_subscribed', 'BOOLEAN DEFAULT TRUE')
            self._add_column_if_not_exists(cursor, 'users', 'viewed_videos', "TEXT DEFAULT '[]'")
            self._add_column_if_not_exists(cursor, 'users', 'is_group', 'BOOLEAN DEFAULT FALSE')
            self._add_column_if_not_exists(cursor, 'users', 'is_banned', 'BOOLEAN DEFAULT FALSE')
            self._add_column_if_not_exists(cursor, 'users', 'group_id', 'TEXT')

            # --- Таблица support ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS support (
                    id SERIAL PRIMARY KEY
                )
            ''')
            self._add_column_if_not_exists(cursor, 'support', 'user_id', 'BIGINT')
            self._add_column_if_not_exists(cursor, 'support', 'message', 'TEXT')
            self._add_column_if_not_exists(cursor, 'support', 'datetime', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')

            # --- Таблица settings ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY
                )
            ''')
            self._add_column_if_not_exists(cursor, 'settings', 'value', 'TEXT')

            # --- Таблица group_video_settings ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_video_settings (
                    chat_id TEXT PRIMARY KEY
                )
            ''')
            self._add_column_if_not_exists(cursor, 'group_video_settings', 'centris_enabled', 'BOOLEAN DEFAULT FALSE')
            self._add_column_if_not_exists(cursor, 'group_video_settings', 'centris_season', 'TEXT')
            self._add_column_if_not_exists(cursor, 'group_video_settings', 'centris_start_video', 'INTEGER DEFAULT 0')
            self._add_column_if_not_exists(cursor, 'group_video_settings', 'golden_enabled', 'BOOLEAN DEFAULT FALSE')
            self._add_column_if_not_exists(cursor, 'group_video_settings', 'golden_start_video', 'INTEGER DEFAULT 0')

            # --- Таблица seasons ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS seasons (
                    id SERIAL PRIMARY KEY,
                    project TEXT NOT NULL,
                    name TEXT NOT NULL
                )
            ''')

            # --- Таблица videos ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id SERIAL PRIMARY KEY,
                    season_id INTEGER REFERENCES seasons(id) ON DELETE CASCADE,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    position INTEGER NOT NULL
                )
            ''')
            
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при создании/обновлении таблиц: {e}")
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

    def add_user(self, user_id, name, phone, preferred_time="07:00", is_group=False, group_id=None):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO users (user_id, name, phone, preferred_time, is_group, group_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            ''', (user_id, name, phone, preferred_time, is_group, group_id))
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
            cursor.execute("SELECT user_id, name, phone, datetime, video_index, preferred_time, last_sent, is_subscribed, viewed_videos, is_group, is_banned FROM users")
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
                "INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = excluded.value",
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

    def set_group_video_settings(self, chat_id: int, centris_enabled: bool, centris_season: str, centris_start_video: int, golden_enabled: bool, golden_start_video: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO group_video_settings (chat_id, centris_enabled, centris_season, centris_start_video, golden_enabled, golden_start_video)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (chat_id) DO UPDATE SET
                    centris_enabled = excluded.centris_enabled,
                    centris_season = excluded.centris_season,
                    centris_start_video = excluded.centris_start_video,
                    golden_enabled = excluded.golden_enabled,
                    golden_start_video = excluded.golden_start_video
                """,
                (chat_id, centris_enabled, centris_season, centris_start_video, golden_enabled, golden_start_video)
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при установке настроек видео для группы {chat_id}: {e}")
            self.conn.rollback()

    def get_group_video_settings(self, chat_id: int) -> tuple:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT centris_enabled, centris_season, centris_start_video, golden_enabled, golden_start_video FROM group_video_settings WHERE chat_id = %s", (chat_id,))
            result = cursor.fetchone()
            cursor.close()
            return (result[0], result[1], result[2], result[3], result[4]) if result else (None, None, 0, None, 0)
        except Exception as e:
            logger.error(f"Ошибка при получении настроек видео для группы {chat_id}: {e}")
            return (None, None, 0, None, 0)

    def get_all_groups_with_settings(self) -> list:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT chat_id, centris_enabled, centris_season, centris_start_video, golden_enabled, golden_start_video
                FROM group_video_settings
            ''')
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении настроек групп: {e}")
            return []

    def ban_group(self, group_id: int):
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

    def get_group_viewed_videos(self, chat_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT viewed_videos FROM group_video_settings WHERE chat_id = %s", (chat_id,))
            result = cursor.fetchone()
            cursor.close()
            if result and result[0]:
                return json.loads(result[0])
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении просмотренных видео группы {chat_id}: {e}")
            return []

    def mark_group_video_as_viewed(self, chat_id, video_index):
        try:
            viewed_videos = self.get_group_viewed_videos(chat_id)
            if video_index not in viewed_videos:
                viewed_videos.append(video_index)
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE group_video_settings SET viewed_videos = %s WHERE chat_id = %s",
                    (json.dumps(viewed_videos), chat_id)
                )
                self.conn.commit()
                cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при отметке видео как просмотренного группой {chat_id}: {e}")
            self.conn.rollback()

    def get_next_unwatched_group_video_index(self, chat_id, all_videos_count):
        try:
            viewed_videos = self.get_group_viewed_videos(chat_id)
            for i in range(all_videos_count):
                if i not in viewed_videos:
                    return i
            return 0
        except Exception as e:
            logger.error(f"Ошибка при получении следующего непросмотренного видео для группы {chat_id}: {e}")
            return 0

    def set_group_video_index_and_viewed(self, chat_id, project, season, video_index, viewed_videos):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE group_video_settings SET viewed_videos = %s WHERE chat_id = %s",
                (json.dumps(viewed_videos), chat_id)
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при установке индекса и просмотренных видео для группы {chat_id}: {e}")
            self.conn.rollback()

    def get_users_by_group(self, group_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE group_id = %s", (group_id,))
            result = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении пользователей группы {group_id}: {e}")
            return []

    def add_season_with_videos(self, project, season_name, links, titles):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO seasons (project, name) VALUES (%s, %s) RETURNING id", (project, season_name))
            season_id = cursor.fetchone()[0]
            for pos, (url, title) in enumerate(zip(links, titles)):
                cursor.execute("INSERT INTO videos (season_id, url, title, position) VALUES (%s, %s, %s, %s)", (season_id, url, title, pos))
            self.conn.commit()
            cursor.close()
            logger.info(f"Сезон '{season_name}' успешно добавлен в проект '{project}' с {len(links)} видео")
        except Exception as e:
            logger.error(f"Ошибка при добавлении сезона '{season_name}' в проект '{project}': {e}")
            self.conn.rollback()

    def get_seasons_by_project(self, project):
        try:
            cursor = self.conn.cursor()
            if project == "centr":
                # Для Centris Towers: специальная сортировка, чтобы "Яқинлар I Ташриф Centris Towers" был последним
                cursor.execute("""
                    SELECT id, name FROM seasons 
                    WHERE project = %s 
                    ORDER BY 
                        CASE 
                            WHEN name = 'Яқинлар I Ташриф Centris Towers' THEN 1 
                            ELSE 0 
                        END,
                        id
                """, (project,))
            else:
                # Для других проектов обычная сортировка по ID
                cursor.execute("SELECT id, name FROM seasons WHERE project = %s ORDER BY id", (project,))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении сезонов проекта '{project}': {e}")
            return []

    def get_videos_by_season(self, season_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT url, title, position FROM videos WHERE season_id = %s ORDER BY position", (season_id,))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении видео сезона {season_id}: {e}")
            return []

    def get_season_by_id(self, season_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, project, name FROM seasons WHERE id = %s", (season_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении сезона {season_id}: {e}")
            return None

    def update_season(self, season_id, season_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE seasons SET name = %s WHERE id = %s", (season_name, season_id))
            self.conn.commit()
            cursor.close()
            logger.info(f"Сезон {season_id} обновлен: {season_name}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении сезона {season_id}: {e}")
            self.conn.rollback()
            return False

    def update_video(self, video_id, url, title, position):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE videos SET url = %s, title = %s, position = %s WHERE id = %s", (url, title, position, video_id))
            self.conn.commit()
            cursor.close()
            logger.info(f"Видео {video_id} обновлено")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении видео {video_id}: {e}")
            self.conn.rollback()
            return False

    def get_video_by_id(self, video_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, season_id, url, title, position FROM videos WHERE id = %s", (video_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении видео {video_id}: {e}")
            return None

    def delete_video(self, video_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM videos WHERE id = %s", (video_id,))
            self.conn.commit()
            cursor.close()
            logger.info(f"Видео {video_id} удалено")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении видео {video_id}: {e}")
            self.conn.rollback()
            return False

    def delete_season(self, season_id):
        try:
            cursor = self.conn.cursor()
            # Сначала удаляем все видео сезона (каскадное удаление)
            cursor.execute("DELETE FROM videos WHERE season_id = %s", (season_id,))
            # Затем удаляем сам сезон
            cursor.execute("DELETE FROM seasons WHERE id = %s", (season_id,))
            self.conn.commit()
            cursor.close()
            logger.info(f"Сезон {season_id} и все его видео удалены")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении сезона {season_id}: {e}")
            self.conn.rollback()
            return False

    def get_videos_with_ids_by_season(self, season_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, url, title, position FROM videos WHERE season_id = %s ORDER BY position", (season_id,))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении видео с ID сезона {season_id}: {e}")
            return []

    def get_season_by_name(self, season_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, project, name FROM seasons WHERE name = %s", (season_name,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении сезона по названию '{season_name}': {e}")
            return None

    def get_videos_by_season_name(self, season_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT v.url, v.title, v.position 
                FROM videos v 
                JOIN seasons s ON v.season_id = s.id 
                WHERE s.name = %s 
                ORDER BY v.position
            """, (season_name,))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении видео сезона '{season_name}': {e}")
            return []

    def get_all_videos_by_project(self, project):
        """Получить все видео всех сезонов проекта"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT v.url, v.title, v.position, s.name as season_name
                FROM videos v 
                JOIN seasons s ON v.season_id = s.id 
                WHERE s.project = %s 
                ORDER BY s.id, v.position
            """, (project,))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении всех видео проекта '{project}': {e}")
            return []

    def get_videos_by_season_id(self, season_id):
        """Получить видео по ID сезона"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT url, title, position 
                FROM videos 
                WHERE season_id = %s 
                ORDER BY position
            """, (season_id,))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении видео сезона {season_id}: {e}")
            return []

    def get_seasons_with_videos_by_project(self, project):
        """Получить сезоны с количеством видео, с правильной сортировкой"""
        try:
            cursor = self.conn.cursor()
            if project == "centr":
                # Для Centris Towers: специальная сортировка
                cursor.execute("""
                    SELECT s.id, s.name, COUNT(v.id) as video_count
                    FROM seasons s
                    LEFT JOIN videos v ON s.id = v.season_id
                    WHERE s.project = %s
                    GROUP BY s.id, s.name
                    ORDER BY 
                        CASE 
                            WHEN s.name = 'Яқинлар I Ташриф Centris Towers' THEN 1 
                            ELSE 0 
                        END,
                        s.id
                """, (project,))
            else:
                # Для других проектов обычная сортировка
                cursor.execute("""
                    SELECT s.id, s.name, COUNT(v.id) as video_count
                    FROM seasons s
                    LEFT JOIN videos v ON s.id = v.season_id
                    WHERE s.project = %s
                    GROUP BY s.id, s.name
                    ORDER BY s.id
                """, (project,))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении сезонов с видео проекта '{project}': {e}")
            return []

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()

# Создание экземпляра базы данных
db = Database()
