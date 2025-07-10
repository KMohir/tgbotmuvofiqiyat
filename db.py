import psycopg2
import psycopg2.extras
import json
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import os

# Пример .env:
# DB_HOST=localhost
# DB_PORT=5432
# DB_USER=postgres
# DB_PASSWORD=ваш_пароль
# DB_NAME=centris
#
# Для работы требуется python-dotenv
# pip install python-dotenv

# Настройка ротации логов
log_handler = RotatingFileHandler('bot.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger()
logger.setLevel(logging.ERROR)
logger.addHandler(log_handler)

load_dotenv()

class Database:
    def __init__(self):
        try:
            # Подключение к PostgreSQL
            self.conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASS'),
                port=os.getenv('DB_PORT', '5432')
            )
            self.conn.autocommit = True
            self.create_tables()
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            raise

    def create_tables(self):
        try:
            cursor = self.conn.cursor()
            # --- Таблица users ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    name TEXT,
                    phone TEXT,
                    datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    video_index INTEGER DEFAULT 0,
                    preferred_time TEXT DEFAULT '07:00',
                    last_sent TEXT,
                    is_subscribed INTEGER DEFAULT 1,
                    viewed_videos TEXT DEFAULT '[]',
                    is_group INTEGER DEFAULT 0,
                    is_banned INTEGER DEFAULT 0,
                    group_id TEXT
                )
            ''')
            # --- Таблица group_video_settings ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_video_settings (
                    chat_id TEXT PRIMARY KEY,
                    centris_enabled INTEGER DEFAULT 0,
                    centris_season TEXT,
                    centris_start_season_id INTEGER,
                    centris_start_video INTEGER DEFAULT 0,
                    golden_enabled INTEGER DEFAULT 0,
                    golden_start_season_id INTEGER,
                    golden_start_video INTEGER DEFAULT 0,
                    viewed_videos TEXT DEFAULT '[]',
                    is_subscribed INTEGER DEFAULT 1
                )
            ''')
            # --- Таблица seasons ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS seasons (
                    id INTEGER PRIMARY KEY,
                    project TEXT NOT NULL,
                    name TEXT NOT NULL
                )
            ''')
            # --- Таблица videos ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id SERIAL PRIMARY KEY,
                    season_id INTEGER,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    FOREIGN KEY(season_id) REFERENCES seasons(id) ON DELETE CASCADE
                )
            ''')
            # --- Таблица admins ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id BIGINT PRIMARY KEY
                )
            ''')
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при создании/обновлении таблиц: {e}")
            self.conn.rollback()

    # --- Методы для users ---
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

    def user_exists(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            exists = cursor.fetchone() is not None
            cursor.close()
            return exists
        except Exception as e:
            logger.error(f"Ошибка при проверке пользователя {user_id}: {e}")
            return False

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

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()

    # --- Методы для group_video_settings ---
    def set_group_video_settings(self, chat_id: int, centris_enabled: bool, centris_season: str, centris_start_video: int, golden_enabled: bool, golden_start_video: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO group_video_settings (chat_id, centris_enabled, centris_season, centris_start_video, golden_enabled, golden_start_video)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (chat_id) DO UPDATE SET centris_enabled=EXCLUDED.centris_enabled, centris_season=EXCLUDED.centris_season, centris_start_video=EXCLUDED.centris_start_video, golden_enabled=EXCLUDED.golden_enabled, golden_start_video=EXCLUDED.golden_start_video
            ''', (chat_id, centris_enabled, centris_season, centris_start_video, golden_enabled, golden_start_video))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при установке настроек видео для группы {chat_id}: {e}")
            self.conn.rollback()

    def get_group_video_settings(self, chat_id: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT centris_enabled, centris_season, centris_start_video, golden_enabled, golden_start_video
                FROM group_video_settings WHERE chat_id = %s
            ''', (chat_id,))
            result = cursor.fetchone()
            cursor.close()
            return tuple(result) if result else None
        except Exception as e:
            logger.error(f"Ошибка при получении настроек видео для группы {chat_id}: {e}")
            return None

    def get_all_users(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE is_subscribed = 1")
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
            cursor.execute("SELECT user_id, is_group FROM users WHERE is_subscribed = 1")
            result = cursor.fetchall()
            cursor.close()
            return [tuple(row) for row in result]
        except Exception as e:
            logger.error(f"Ошибка при получении настроек групп: {e}")
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

    def reset_group_viewed_videos(self, chat_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE group_video_settings SET viewed_videos = %s WHERE chat_id = %s",
                (json.dumps([]), chat_id)
            )
            self.conn.commit()
            cursor.close()
            logger.info(f"Список просмотренных видео для группы {chat_id} сброшен.")
        except Exception as e:
            logger.error(f"Ошибка при сбросе просмотренных видео для группы {chat_id}: {e}")
            self.conn.rollback()

    def set_group_video_start(self, chat_id: int, project: str, season_id: int, video_index: int):
        try:
            cursor = self.conn.cursor()
            if project == 'centris':
                cursor.execute('''
                    UPDATE group_video_settings SET centris_start_season_id = %s, centris_start_video = %s WHERE chat_id = %s
                ''', (season_id, video_index, chat_id))
            elif project == 'golden':
                cursor.execute('''
                    UPDATE group_video_settings SET golden_start_season_id = %s, golden_start_video = %s WHERE chat_id = %s
                ''', (season_id, video_index, chat_id))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при установке стартового сезона/видео для группы {chat_id}, проект {project}: {e}")
            self.conn.rollback()

    def get_group_video_start(self, chat_id: int, project: str):
        try:
            cursor = self.conn.cursor()
            if project == 'centris':
                cursor.execute('''
                    SELECT centris_start_season_id, centris_start_video FROM group_video_settings WHERE chat_id = %s
                ''', (chat_id,))
            elif project == 'golden':
                cursor.execute('''
                    SELECT golden_start_season_id, golden_start_video FROM group_video_settings WHERE chat_id = %s
                ''', (chat_id,))
            result = cursor.fetchone()
            cursor.close()
            return tuple(result) if result else (None, 0)
        except Exception as e:
            logger.error(f"Ошибка при получении стартового сезона/видео для группы {chat_id}, проект {project}: {e}")
            return (None, 0)

    def set_subscription_status(self, chat_id: int, status: bool):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'UPDATE group_video_settings SET is_subscribed = %s WHERE chat_id = %s',
                (1 if status else 0, chat_id)
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при изменении статуса подписки для группы {chat_id}: {e}")
            self.conn.rollback()

    def get_subscription_status(self, chat_id: int) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT is_subscribed FROM group_video_settings WHERE chat_id = %s',
                (chat_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            return bool(result[0]) if result else False
        except Exception as e:
            logger.error(f"Ошибка при получении статуса подписки для группы {chat_id}: {e}")
            return False

    # --- Методы для seasons и videos ---
    def add_season_with_videos(self, project, season_name, links, titles):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO seasons (project, name) VALUES (%s, %s)", (project, season_name))
            season_id = cursor.fetchone()[0] # Получаем ID из последней вставки
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
                cursor.execute("SELECT id, name FROM seasons WHERE project = %s ORDER BY id", (project,))
            result = cursor.fetchall()
            cursor.close()
            return [tuple(row) for row in result]
        except Exception as e:
            logger.error(f"Ошибка при получении сезонов проекта '{project}': {e}")
            return []

    def get_seasons_with_videos_by_project(self, project):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT chat_id, centris_enabled, centris_season, golden_enabled, golden_season
                FROM group_video_settings
            ''')
            result = cursor.fetchall()
            cursor.close()
            return [tuple(row) for row in result]
        except Exception as e:
            logger.error(f"Ошибка при получении сезонов с видео по проекту '{project}': {e}")
            return []

    def get_videos_by_season(self, season_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT url, title, position FROM videos WHERE season_id = %s ORDER BY position", (season_id,))
            result = cursor.fetchall()
            cursor.close()
            return [tuple(row) for row in result]
        except Exception as e:
            logger.error(f"Ошибка при получении видео сезона {season_id}: {e}")
            return []

    def get_season_by_id(self, season_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, project, name FROM seasons WHERE id = %s", (season_id,))
            result = cursor.fetchone()
            cursor.close()
            return tuple(result) if result else None
        except Exception as e:
            logger.error(f"Ошибка при получении сезона {season_id}: {e}")
            return None

    def get_season_by_name(self, season_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, project, name FROM seasons WHERE name = %s", (season_name,))
            result = cursor.fetchone()
            cursor.close()
            return tuple(result) if result else None
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
            return [tuple(row) for row in result]
        except Exception as e:
            logger.error(f"Ошибка при получении видео сезона '{season_name}': {e}")
            return []

    def get_videos_with_ids_by_season(self, season_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, url, title, position FROM videos WHERE season_id = %s ORDER BY position",
                (season_id,)
            )
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении видео с ID сезона {season_id}: {e}")
            return []

    # --- Методы для работы с администраторами ---
    def add_admin(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO admins (user_id) VALUES (%s)", (user_id,))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при добавлении администратора {user_id}: {e}")
            self.conn.rollback()

    def remove_admin(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM admins WHERE user_id = %s", (user_id,))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при удалении администратора {user_id}: {e}")
            self.conn.rollback()

    def list_admins(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id FROM admins")
            result = cursor.fetchall()
            cursor.close()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Ошибка при получении списка админов: {e}")
            return []

    def is_admin(self, user_id):
        try:
            # Супер-админ всегда админ
            if self.is_superadmin(user_id):
                return True
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM admins WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return result is not None
        except Exception as e:
            logger.error(f"Ошибка при проверке is_admin({user_id}): {e}")
            return False

    def is_superadmin(self, user_id):
        SUPERADMIN_ID = 5657091547  # Ваш основной user_id
        return int(user_id) == SUPERADMIN_ID

    def get_all_admins(self):
        try:
            # Получаем всех обычных админов из базы
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id FROM admins")
            result = cursor.fetchall()
            cursor.close()
            admins = [(row[0], False) for row in result]
            # Добавляем супер-админа (он всегда есть, даже если не в базе)
            SUPERADMIN_ID = 5657091547  # ваш id
            if not any(admin_id == SUPERADMIN_ID for admin_id, _ in admins):
                admins.insert(0, (SUPERADMIN_ID, True))
            else:
                # Если супер-админ есть в базе, помечаем его как супер
                admins = [(admin_id, True) if admin_id == SUPERADMIN_ID else (admin_id, is_super) for admin_id, is_super in admins]
            return admins
        except Exception as e:
            logger.error(f"Ошибка при получении списка всех админов: {e}")
            return []

    # --- Получение всех пользователей ---
    def get_all_users(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id, name, phone, datetime, is_group FROM users")
            result = cursor.fetchall()
            cursor.close()
            return [tuple(row) for row in result]
        except Exception as e:
            logger.error(f"Ошибка при получении всех пользователей: {e}")
            return []

    # --- Методы для сезонов и видео ---
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

    def delete_season(self, season_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM videos WHERE season_id = %s", (season_id,))
            cursor.execute("DELETE FROM seasons WHERE id = %s", (season_id,))
            self.conn.commit()
            cursor.close()
            logger.info(f"Сезон {season_id} и все его видео удалены")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении сезона {season_id}: {e}")
            self.conn.rollback()
            return False

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

    # --- Методы для бана/разбана групп ---
    def ban_group(self, group_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE users SET is_banned = 1, is_subscribed = 0 
                WHERE user_id = %s AND is_group = 1
            ''', (group_id,))
            self.conn.commit()
            cursor.close()
            logger.info(f"Группа {group_id} заблокирована")
        except Exception as e:
            logger.error(f"Ошибка при блокировке группы {group_id}: {e}")
            self.conn.rollback()

    def unban_group(self, group_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE users SET is_banned = 0, is_subscribed = 1 
                WHERE user_id = %s AND is_group = 1
            ''', (group_id,))
            self.conn.commit()
            cursor.close()
            logger.info(f"Группа {group_id} разблокирована")
        except Exception as e:
            logger.error(f"Ошибка при разблокировке группы {group_id}: {e}")
            self.conn.rollback()

    def is_group_banned(self, group_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT is_banned FROM users 
                WHERE user_id = %s AND is_group = 1
            ''', (group_id,))
            result = cursor.fetchone()
            cursor.close()
            return bool(result[0]) if result else False
        except Exception as e:
            logger.error(f"Ошибка при проверке блокировки группы {group_id}: {e}")
            return False

    def get_banned_groups(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT user_id, name FROM users 
                WHERE is_banned = 1 AND is_group = 1
            ''')
            result = cursor.fetchall()
            cursor.close()
            return [tuple(row) for row in result]
        except Exception as e:
            logger.error(f"Ошибка при получении заблокированных групп: {e}")
            return []

    def get_all_subscribers_with_type(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id, is_group FROM users WHERE is_subscribed = 1")
            result = cursor.fetchall()
            cursor.close()
            return [tuple(row) for row in result]
        except Exception as e:
            logger.error(f"Ошибка при получении подписчиков: {e}")
            return []

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
            viewed = self.get_viewed_videos(user_id)
            if video_index not in viewed:
                viewed.append(video_index)
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE users SET viewed_videos = %s WHERE user_id = %s",
                    (json.dumps(viewed), user_id)
                )
                self.conn.commit()
                cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при отметке видео как просмотренного пользователем {user_id}: {e}")
            self.conn.rollback()

    # Удалены методы get_group_times и parse_time_str, связанные с индивидуальными временами рассылки

    def is_admin(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM admins WHERE user_id = %s", (user_id,))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Ошибка при проверке админа: {e}")
            return False

    def is_admin(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM admins WHERE user_id = %s", (user_id,))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Ошибка при проверке админа: {e}")
            return False

# Создание экземпляра базы данных
db = Database()
