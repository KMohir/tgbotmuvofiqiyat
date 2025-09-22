import psycopg2
import psycopg2.extras
import json
import logging
# from logging.handlers import RotatingFileHandler
# log_handler = RotatingFileHandler('bot.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
log_handler = logging.FileHandler('bot.log', encoding='utf-8')
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger()
logger.setLevel(logging.ERROR)
logger.addHandler(log_handler)
from environs import Env
import os

# Пример .env:
# DB_HOST=localhost
# DB_PORT=5432
# DB_USER=postgres
# DB_PASSWORD=ваш_пароль
# DB_NAME=centris
#
# Для работы требуется environs
# pip install environs

# Настройка ротации логов
# log_handler = RotatingFileHandler('bot.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
# log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# logger = logging.getLogger()
# logger.setLevel(logging.ERROR)
# logger.addHandler(log_handler)

env = Env()
try:
    env.read_env()
except UnicodeDecodeError as e:
    logger.error(f"Ошибка кодировки в файле .env: {e}")
    logger.error("Убедитесь, что файл .env сохранен в кодировке UTF-8")
    raise
except Exception as e:
    logger.warning(f"Не удалось загрузить файл .env: {e}")
    logger.warning("Продолжаем работу с переменными окружения системы")

class Database:
    def __init__(self):
        try:
            # Подключение к PostgreSQL
            print('1111',env.str('DB_HOST'))
            self.conn = psycopg2.connect(
                host=env.str('DB_HOST', 'localhost'),
                dbname=env.str('DB_NAME', 'tgbotmuvofiqiyat'),
                user=env.str('DB_USER', 'postgres'),
                password=env.str('DB_PASSWORD', '1111'),
                port=env.str('DB_PORT', '5432')
            )
            self.conn.autocommit = True
            self.create_tables()
            self.create_security_tables()  # Создать таблицы безопасности
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            raise

    def migrate_seasons_table(self):
        try:
            cursor = self.conn.cursor()
            # Проверяем, есть ли автоинкремент у id
            cursor.execute("""
                SELECT column_default FROM information_schema.columns
                WHERE table_name='seasons' AND column_name='id'
            """
            )
            default = cursor.fetchone()
            default_str = str(default[0]) if default and default[0] else ""
            
            # Проверяем, нужна ли миграция
            needs_migration = not default or not default[0] or 'nextval' not in default_str
            
            if needs_migration:
                logger.error(f"Поле id в seasons не автоинкрементируется. Текущее значение: {default_str}. Запускаю миграцию...")
            else:
                logger.info(f"Таблица seasons уже имеет правильную структуру с автоинкрементом: {default_str}")
                # Пропускаем миграцию, но выполняем обновление project
                cursor.execute("UPDATE seasons SET project = 'centris' WHERE project = 'centr';")
                self.conn.commit()
                cursor.close()
                return
            
            # Если нужна миграция, выполняем её
            cursor.execute("ALTER TABLE seasons RENAME TO seasons_old;")
            cursor.execute("""
                CREATE TABLE seasons (
                    id SERIAL PRIMARY KEY,
                    project TEXT NOT NULL,
                    name TEXT NOT NULL
                )
            """)
            cursor.execute("INSERT INTO seasons (project, name) SELECT project, name FROM seasons_old;")
            # Обновляем все season_id в videos на новые id
            cursor.execute("""
                UPDATE videos v
                SET season_id = s.id
                FROM seasons s
                WHERE s.name = (SELECT name FROM seasons_old so WHERE so.id = v.season_id)
            """)
            # --- Удаляем внешний ключ, если есть ---
            cursor.execute("ALTER TABLE videos DROP CONSTRAINT IF EXISTS videos_season_id_fkey;")
            # --- Удаляем старую таблицу ---
            cursor.execute("DROP TABLE IF EXISTS seasons_old;")
            # --- Восстанавливаем внешний ключ ---
            cursor.execute("ALTER TABLE videos ADD CONSTRAINT videos_season_id_fkey FOREIGN KEY (season_id) REFERENCES seasons(id) ON DELETE CASCADE;")
            self.conn.commit()
            logger.info("Миграция таблицы seasons завершена!")
            
            # --- Миграция project: centr -> centris ---
            cursor.execute("UPDATE seasons SET project = 'centris' WHERE project = 'centr';")
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при миграции таблицы seasons: {e}")
            self.conn.rollback()

    def create_tables(self):
        self.migrate_seasons_table()
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
                    group_id TEXT,
                    access_granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # --- Таблица group_video_settings ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_video_settings (
                    chat_id TEXT PRIMARY KEY,
                    centris_enabled INTEGER DEFAULT 0,
                    centris_season_id INTEGER,           -- ID сезона в базе (не номер!)
                    centris_start_video INTEGER DEFAULT 0,
                    golden_enabled INTEGER DEFAULT 0,
                    golden_season_id INTEGER,            -- ID сезона в базе (не номер!)
                    golden_start_video INTEGER DEFAULT 0,
                    viewed_videos TEXT DEFAULT '[]',
                    centris_viewed_videos TEXT DEFAULT '[]',  -- Отдельно для Centris
                    golden_viewed_videos TEXT DEFAULT '[]',   -- Отдельно для Golden Lake
                    is_subscribed INTEGER DEFAULT 1,
                    send_times TEXT DEFAULT '["07:00", "11:00", "20:00"]'  -- Время отправки в формате JSON
                )
            ''')
            
            # Миграция: добавляем колонки для отдельного отслеживания просмотренных видео
            try:
                cursor.execute("ALTER TABLE group_video_settings ADD COLUMN IF NOT EXISTS centris_viewed_videos TEXT DEFAULT '[]'")
                cursor.execute("ALTER TABLE group_video_settings ADD COLUMN IF NOT EXISTS golden_viewed_videos TEXT DEFAULT '[]'")
                cursor.execute("ALTER TABLE group_video_settings ADD COLUMN IF NOT EXISTS send_times TEXT DEFAULT '[\"07:00\", \"11:00\", \"20:00\"]'")
                logger.info("Миграция: добавлены колонки для отдельного отслеживания просмотренных видео и времени отправки")
            except Exception as e:
                logger.error(f"Ошибка при добавлении колонок для отслеживания видео и времени: {e}")
            
            # Миграция: добавляем колонки для отслеживания доступа
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS access_granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS access_expires_at TIMESTAMP")
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                logger.info("Миграция: добавлены колонки для отслеживания доступа")
            except Exception as e:
                logger.error(f"Ошибка при добавлении колонок для отслеживания доступа: {e}")
            
            # Проверяем и обновляем структуру существующей таблицы
            cursor.execute('''
                DO $$
                BEGIN
                    -- Добавляем недостающие колонки если их нет
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'group_video_settings' AND column_name = 'centris_season_id') THEN
                        ALTER TABLE group_video_settings ADD COLUMN centris_season_id INTEGER;
                    END IF;
                    
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'group_video_settings' AND column_name = 'golden_season_id') THEN
                        ALTER TABLE group_video_settings ADD COLUMN golden_season_id INTEGER;
                    END IF;
                    
                    -- Добавляем поле для названия группы если его нет
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'group_video_settings' AND column_name = 'group_name') THEN
                        ALTER TABLE group_video_settings ADD COLUMN group_name TEXT DEFAULT 'Noma''lum guruh';
                    END IF;
                    
                    -- Удаляем старые колонки если они есть
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'group_video_settings' AND column_name = 'centris_season') THEN
                        ALTER TABLE group_video_settings DROP COLUMN centris_season;
                    END IF;
                    
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'group_video_settings' AND column_name = 'centris_start_season_id') THEN
                        ALTER TABLE group_video_settings DROP COLUMN centris_start_season_id;
                    END IF;
                    
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'group_video_settings' AND column_name = 'golden_start_season_id') THEN
                        ALTER TABLE group_video_settings DROP COLUMN golden_start_season_id;
                    END IF;
                END $$;
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
            
            # Попытка синхронизировать названия групп
            try:
                self.sync_group_names_from_users()
            except Exception as e:
                logger.error(f"Ошибка при синхронизации названий групп: {e}")
                
        except Exception as e:
            logger.error(f"Ошибка при создании/обновлении таблиц: {e}")
            self.conn.rollback()

    # --- Методы для users ---
    def add_user(self, user_id, name, phone, preferred_time="07:00", is_group=False, group_id=None):
        try:
            from datetime import datetime, timedelta
            cursor = self.conn.cursor()
            
            # Для групп не устанавливаем время доступа
            if is_group:
                cursor.execute('''
                    INSERT INTO users (user_id, name, phone, preferred_time, is_group, group_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO NOTHING
                ''', (user_id, name, phone, preferred_time, int(is_group), group_id, datetime.now()))
            else:
                # Для обычных пользователей предоставляем доступ на 24 часа
                now = datetime.now()
                expires_at = now + timedelta(hours=24)
                cursor.execute('''
                    INSERT INTO users (user_id, name, phone, preferred_time, is_group, group_id, 
                                     access_granted_at, access_expires_at, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO NOTHING
                ''', (user_id, name, phone, preferred_time, int(is_group), group_id, 
                      now, expires_at, now))
            
            self.conn.commit()
            cursor.close()
            logger.info(f"Пользователь {user_id} успешно добавлен/обновлен")
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя {user_id}: {e}")
            self.conn.rollback()
            return False

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
            ''', (name, phone, preferred_time, int(is_group), user_id))
            self.conn.commit()
            cursor.close()
            logger.info(f"Данные пользователя {user_id} успешно обновлены")
        except Exception as e:
            logger.error(f"Ошибка при обновлении пользователя {user_id}: {e}")
            self.conn.rollback()

    def update_last_sent(self, user_id, last_sent_datetime):
        """Обновить время последней отправки видео пользователю"""
        try:
            cursor = self.conn.cursor()
            # Конвертируем datetime в строку для сохранения в text поле
            last_sent_str = last_sent_datetime.strftime("%Y-%m-%d %H:%M:%S") if last_sent_datetime else None
            cursor.execute('''
                UPDATE users SET last_sent = %s WHERE user_id = %s
            ''', (last_sent_str, user_id))
            self.conn.commit()
            cursor.close()
            logger.info(f"Время последней отправки обновлено для пользователя {user_id}: {last_sent_str}")
        except Exception as e:
            logger.error(f"Ошибка при обновлении last_sent для пользователя {user_id}: {e}")
            self.conn.rollback()

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()

    # --- Методы для group_video_settings ---
    def set_group_video_settings(self, chat_id: int, centris_enabled: bool, centris_season_id: int, centris_start_video: int, golden_enabled: bool, golden_season_id: int, golden_start_video: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO group_video_settings (chat_id, centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (chat_id) DO UPDATE SET 
                    centris_enabled=EXCLUDED.centris_enabled, 
                    centris_season_id=EXCLUDED.centris_season_id, 
                    centris_start_video=EXCLUDED.centris_start_video, 
                    golden_enabled=EXCLUDED.golden_enabled, 
                    golden_season_id=EXCLUDED.golden_season_id,
                    golden_start_video=EXCLUDED.golden_start_video
            ''', (str(chat_id), centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при установке настроек видео для группы {chat_id}: {e}")
            self.conn.rollback()

    def update_group_name(self, chat_id: int, group_name: str):
        """
        Обновляет название группы в базе данных
        """
        try:
            cursor = self.conn.cursor()
            
            # Обновляем название в group_video_settings
            cursor.execute('''
                UPDATE group_video_settings 
                SET group_name = %s 
                WHERE chat_id = %s
            ''', (group_name, str(chat_id)))
            
            # Если группа не существует, создаем запись с названием
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO group_video_settings (chat_id, group_name)
                    VALUES (%s, %s)
                ''', (str(chat_id), group_name))
            
            # Также обновляем название в таблице users
            cursor.execute('''
                UPDATE users 
                SET name = %s 
                WHERE user_id = %s AND is_group = 1
            ''', (group_name, int(chat_id)))
            
            # Если группы нет в users, создаем запись
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO users (user_id, name, phone, is_group, is_subscribed)
                    VALUES (%s, %s, 'group', 1, 1)
                    ON CONFLICT (user_id) DO UPDATE SET name = EXCLUDED.name
                ''', (int(chat_id), group_name))
            
            self.conn.commit()
            cursor.close()
            logger.info(f"Название группы {chat_id} обновлено на '{group_name}' в обеих таблицах")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении названия группы {chat_id}: {e}")
            self.conn.rollback()
            return False

    def sync_group_names_from_users(self):
        """
        Синхронизирует названия групп из таблицы users в group_video_settings
        """
        try:
            cursor = self.conn.cursor()
            
            # Получаем все группы с названиями из users
            cursor.execute('''
                SELECT user_id, name 
                FROM users 
                WHERE is_group = 1 AND name IS NOT NULL AND name != ''
            ''')
            groups_with_names = cursor.fetchall()
            
            if not groups_with_names:
                logger.info("Нет групп с названиями для синхронизации")
                cursor.close()
                return
            
            updated_count = 0
            for group_id, group_name in groups_with_names:
                # Проверяем, есть ли группа в group_video_settings
                cursor.execute('''
                    SELECT 1 FROM group_video_settings WHERE chat_id = %s
                ''', (str(group_id),))
                
                if cursor.fetchone():
                    # Обновляем название
                    cursor.execute('''
                        UPDATE group_video_settings 
                        SET group_name = %s 
                        WHERE chat_id = %s
                    ''', (group_name, str(group_id)))
                else:
                    # Создаем запись
                    cursor.execute('''
                        INSERT INTO group_video_settings (chat_id, group_name)
                        VALUES (%s, %s)
                    ''', (str(group_id), group_name))
                
                updated_count += 1
            
            self.conn.commit()
            cursor.close()
            logger.info(f"Синхронизировано названий групп: {updated_count}")
            
        except Exception as e:
            logger.error(f"Ошибка при синхронизации названий групп: {e}")
            self.conn.rollback()

    def get_group_video_settings(self, chat_id: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT centris_enabled, centris_season_id, centris_start_video, golden_enabled, golden_season_id, golden_start_video, send_times
                FROM group_video_settings WHERE chat_id = %s
            ''', (str(chat_id),))
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
            cursor.execute("SELECT viewed_videos FROM group_video_settings WHERE chat_id = %s", (str(chat_id),))
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
                    (json.dumps(viewed_videos), str(chat_id))
                )
                self.conn.commit()
                cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при отметке видео как просмотренного группой {chat_id}: {e}")
            self.conn.rollback()

    def get_group_viewed_videos_by_project(self, chat_id, project):
        """Получить просмотренные видео группы для конкретного проекта"""
        try:
            cursor = self.conn.cursor()
            # Используем отдельные колонки для каждого проекта
            if project == "centris":
                cursor.execute("SELECT centris_viewed_videos FROM group_video_settings WHERE chat_id = %s", (str(chat_id),))
            elif project == "golden_lake" or project == "golden":
                cursor.execute("SELECT golden_viewed_videos FROM group_video_settings WHERE chat_id = %s", (str(chat_id),))
            else:
                return []
            
            result = cursor.fetchone()
            cursor.close()
            if result and result[0]:
                return json.loads(result[0])
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении просмотренных видео группой {chat_id} для проекта {project}: {e}")
            return []

    def mark_group_video_as_viewed_by_project(self, chat_id, video_position, project):
        """Отметить видео как просмотренное для конкретного проекта"""
        try:
            # Специальное значение -1 означает сброс всех просмотренных видео
            if video_position == -1:
                cursor = self.conn.cursor()
                if project == "centris":
                    cursor.execute(
                        "UPDATE group_video_settings SET centris_viewed_videos = %s WHERE chat_id = %s",
                        (json.dumps([]), str(chat_id))
                    )
                elif project == "golden_lake" or project == "golden":
                    cursor.execute(
                        "UPDATE group_video_settings SET golden_viewed_videos = %s WHERE chat_id = %s",
                        (json.dumps([]), str(chat_id))
                    )
                self.conn.commit()
                cursor.close()
                logger.info(f"Сброшены все просмотренные видео для группы {chat_id}, проект {project}")
                return
            
            viewed_videos = self.get_group_viewed_videos_by_project(chat_id, project)
            if video_position not in viewed_videos:
                viewed_videos.append(video_position)
                cursor = self.conn.cursor()
                
                if project == "centris":
                    cursor.execute(
                        "UPDATE group_video_settings SET centris_viewed_videos = %s WHERE chat_id = %s",
                        (json.dumps(viewed_videos), str(chat_id))
                    )
                elif project == "golden_lake" or project == "golden":
                    cursor.execute(
                        "UPDATE group_video_settings SET golden_viewed_videos = %s WHERE chat_id = %s",
                        (json.dumps(viewed_videos), str(chat_id))
                    )
                
                self.conn.commit()
                cursor.close()
                logger.info(f"Видео {video_position} отмечено как просмотренное для группы {chat_id}, проект {project}")
        except Exception as e:
            logger.error(f"Ошибка при отметке видео как просмотренного группой {chat_id} для проекта {project}: {e}")
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
                (json.dumps(viewed_videos), str(chat_id))
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
                (json.dumps([]), str(chat_id))
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
                    UPDATE group_video_settings SET centris_season_id = %s, centris_start_video = %s WHERE chat_id = %s
                ''', (season_id, video_index, str(chat_id)))
            elif project == 'golden':
                cursor.execute('''
                    UPDATE group_video_settings SET golden_season_id = %s, golden_start_video = %s WHERE chat_id = %s
                ''', (season_id, video_index, str(chat_id)))
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
                    SELECT centris_season_id, centris_start_video FROM group_video_settings WHERE chat_id = %s
                ''', (str(chat_id),))
            elif project == 'golden':
                cursor.execute('''
                    SELECT golden_season_id, golden_start_video FROM group_video_settings WHERE chat_id = %s
                ''', (str(chat_id),))
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
                (1 if status else 0, str(chat_id))
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
                (str(chat_id),)
            )
            result = cursor.fetchone()
            cursor.close()
            return bool(result[0]) if result else False
        except Exception as e:
            logger.error(f"Ошибка при получении статуса подписки для группы {chat_id}: {e}")
            return False

    # --- Методы для seasons и videos ---
    def add_season_with_videos(self, project, season_name, links, titles):
        logger.info(f"add_season_with_videos: project={project}, season_name={season_name}, links_count={len(links)}, titles_count={len(titles)}")
        if not links or not titles or len(links) != len(titles):
            logger.error(f"Попытка добавить сезон '{season_name}' без видео или с некорректными списками! links={len(links)}, titles={len(titles)}")
            return None
        
        try:
            cursor = self.conn.cursor()
            # id автоинкрементируется, не указываем его явно
            cursor.execute("INSERT INTO seasons (project, name) VALUES (%s, %s) RETURNING id", (project, season_name))
            season_id = cursor.fetchone()[0] # Получаем ID из последней вставки
            logger.info(f"add_season_with_videos: добавлен сезон id={season_id}, project={project}, name={season_name}")
            
            for pos, (url, title) in enumerate(zip(links, titles)):
                cursor.execute("INSERT INTO videos (season_id, url, title, position) VALUES (%s, %s, %s, %s)", (season_id, url, title, pos))
            
            self.conn.commit()
            cursor.close()
            
            logger.info(f"Сезон '{season_name}' успешно добавлен в проект '{project}' с {len(links)} видео")
            
            # Возвращаем информацию о добавленном сезоне
            return {
                'season_id': season_id,
                'project': project,
                'season_name': season_name,
                'video_count': len(links)
            }
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении сезона '{season_name}' в проект '{project}': {e}")
            self.conn.rollback()
            return None

    def get_seasons_by_project(self, project):
        logger.info(f"get_seasons_by_project: project={project}")
        try:
            cursor = self.conn.cursor()
            if project == "centris":
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
            logger.info(f"get_seasons_by_project: найдено сезонов={len(result)} для project={project}")
            cursor.close()
            return [tuple(row) for row in result]
        except Exception as e:
            logger.error(f"Ошибка при получении сезонов проекта '{project}': {e}")
            return []

    def get_seasons_with_videos_by_project(self, project):
        try:
            cursor = self.conn.cursor()
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

    def get_all_seasons(self, project):
        """
        Получить все сезоны для проекта, отсортированные по ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, project, name FROM seasons WHERE project = %s ORDER BY id", (project,))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении сезонов для проекта '{project}': {e}")
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

    def get_season_name(self, season_id):
        """Получить название сезона по ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM seasons WHERE id = %s", (season_id,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else "Неизвестный сезон"
        except Exception as e:
            logger.error(f"Ошибка при получении названия сезона {season_id}: {e}")
            return "Ошибка получения названия"

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

    def get_video_by_id(self, video_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, season_id, url, title, position FROM videos WHERE id = %s",
                (video_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            return tuple(result) if result else None
        except Exception as e:
            logger.error(f"Ошибка при получении видео по id {video_id}: {e}")
            return None

    # --- Методы для работы с администраторами ---
    def add_admin(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO admins (user_id) VALUES (%s)", (user_id,))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении администратора {user_id}: {e}")
            self.conn.rollback()
            return False

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
        SUPERADMIN_IDS = [5657091547, 7983512278, 5310261745, 8053364577]  # Список супер-администраторов
        # Если это группа и она разрешена — считаем супер-админом
        try:
            if str(user_id).startswith('-'):
                if not self.is_group_banned(user_id):
                    return True
        except Exception:
            pass
        return int(user_id) in SUPERADMIN_IDS

    def get_all_admins(self):
        try:
            # Получаем всех обычных админов из базы
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id FROM admins")
            result = cursor.fetchall()
            cursor.close()
            admins = [(row[0], False) for row in result]
            # Добавляем супер-админов (они всегда есть, даже если не в базе)
            SUPERADMIN_IDS = [5657091547, 7983512278, 5310261745, 8053364577]  # Список супер-администраторов
            for superadmin_id in SUPERADMIN_IDS:
                if not any(admin_id == superadmin_id for admin_id, _ in admins):
                    admins.insert(0, (superadmin_id, True))
                else:
                    # Если супер-админ есть в базе, помечаем его как супер
                    admins = [(admin_id, True) if admin_id == superadmin_id else (admin_id, is_super) for admin_id, is_super in admins]
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

    def get_all_groups_with_settings(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT gvs.chat_id, gvs.centris_enabled, gvs.centris_season_id, gvs.centris_start_video, 
                       gvs.golden_enabled, gvs.golden_season_id, gvs.golden_start_video, gvs.viewed_videos, gvs.is_subscribed, 
                       COALESCE(gvs.group_name, u.name, 'Noma''lum guruh') as group_name, gvs.send_times, u.created_at
                FROM group_video_settings gvs
                LEFT JOIN users u ON gvs.chat_id::bigint = u.user_id AND u.is_group = 1
                ORDER BY u.created_at DESC, gvs.chat_id
            ''')
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении настроек всех групп: {e}")
            return []
    
    def get_all_whitelisted_groups(self):
        """Получить все разрешенные группы с именами, отсортированные по дате добавления (новые первыми)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT u.user_id, u.name, u.created_at
                FROM users u
                WHERE u.is_group = 1 AND u.is_banned = 0
                ORDER BY u.created_at DESC, u.name
            ''')
            all_groups = cursor.fetchall()
            cursor.close()
            
            # Фильтруем только разрешенные группы (в whitelist)
            whitelisted_groups = []
            for group_data in all_groups:
                if len(group_data) >= 3:
                    group_id, name, created_at = group_data
                else:
                    # Обратная совместимость
                    group_id, name = group_data
                    created_at = None
                    
                if self.is_group_whitelisted(group_id):
                    if created_at:
                        whitelisted_groups.append((group_id, name, created_at))
                    else:
                        whitelisted_groups.append((group_id, name))
            
            return whitelisted_groups
        except Exception as e:
            logger.error(f"Ошибка при получении разрешенных групп: {e}")
            return []

    def unban_all_groups(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE users SET is_banned = 0, is_subscribed = 1 
                WHERE is_group = 1
            ''')
            self.conn.commit()
            cursor.close()
            logger.info(f"Все группы разблокированы")
        except Exception as e:
            logger.error(f"Ошибка при разблокировке всех групп: {e}")
            self.conn.rollback()

    # === МЕТОДЫ БЕЗОПАСНОСТИ ===

    def add_user_registration(self, user_id: int, name: str, phone: str) -> bool:
        """Добавить пользователя в процесс регистрации"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO user_security (user_id, name, phone, status, reg_date)
                VALUES (%s, %s, %s, 'pending', CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) 
                DO UPDATE SET name = EXCLUDED.name, phone = EXCLUDED.phone, status = 'pending'
            """, (user_id, name, phone))
            self.conn.commit()
            logger.info(f"Foydalanuvchi {user_id} ro'yxatdan o'tish jarayoniga qo'shildi")
            return True
        except Exception as e:
            logger.error(f"Foydalanuvchi {user_id} ni qo'shishda xatolik: {e}")
            return False

    def get_user_security_status(self, user_id: int) -> str:
        """Получить статус безопасности пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT status FROM user_security WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Foydalanuvchi {user_id} statusini olishda xatolik: {e}")
            return None

    def get_user_security_data(self, user_id: int) -> dict:
        """Получить данные пользователя из системы безопасности"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT user_id, name, phone, status, reg_date, approved_by, approved_date
                FROM user_security WHERE user_id = %s
            """, (user_id,))
            result = cursor.fetchone()
            if result:
                return {
                    'user_id': result[0],
                    'name': result[1],
                    'phone': result[2],
                    'status': result[3],
                    'reg_date': result[4],
                    'approved_by': result[5],
                    'approved_date': result[6]
                }
            return None
        except Exception as e:
            logger.error(f"Foydalanuvchi {user_id} ma'lumotlarini olishda xatolik: {e}")
            return None

    def approve_user(self, user_id: int, admin_id: int) -> bool:
        """Одобрить пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE user_security 
                SET status = 'approved', approved_by = %s, approved_date = CURRENT_TIMESTAMP
                WHERE user_id = %s AND status = 'pending'
            """, (admin_id, user_id))
            self.conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Foydalanuvchi {user_id} admin {admin_id} tomonidan tasdiqlandi")
                return True
            return False
        except Exception as e:
            logger.error(f"Foydalanuvchi {user_id} ni tasdiqlashda xatolik: {e}")
            return False

    def deny_user(self, user_id: int, admin_id: int) -> bool:
        """Отклонить пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE user_security 
                SET status = 'denied', approved_by = %s, approved_date = CURRENT_TIMESTAMP
                WHERE user_id = %s AND status = 'pending'
            """, (admin_id, user_id))
            self.conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Foydalanuvchi {user_id} admin {admin_id} tomonidan rad etildi")
                return True
            return False
        except Exception as e:
            logger.error(f"Foydalanuvchi {user_id} ni rad etishda xatolik: {e}")
            return False

    def get_pending_users(self) -> list:
        """Получить список пользователей ожидающих одобрения"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT user_id, name, phone, reg_date 
                FROM user_security 
                WHERE status = 'pending' 
                ORDER BY reg_date ASC
            """)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Kutayotgan foydalanuvchilarni olishda xatolik: {e}")
            return []

    def get_all_security_users(self) -> list:
        """Получить всех пользователей системы безопасности"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT user_id, name, phone, status, reg_date, approved_by, approved_date
                FROM user_security 
                ORDER BY reg_date DESC
            """)
            results = cursor.fetchall()
            return [
                {
                    'user_id': row[0], 'name': row[1], 'phone': row[2],
                    'status': row[3], 'reg_date': row[4], 'approved_by': row[5], 'approved_date': row[6]
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Barcha xavfsizlik foydalanuvchilarini olishda xatolik: {e}")
            return []

    def is_user_approved(self, user_id: int) -> bool:
        """Проверить одобрен ли пользователь"""
        try:
            status = self.get_user_security_status(user_id)
            return status == 'approved'
        except Exception as e:
            logger.error(f"Foydalanuvchi {user_id} tasdiqlashini tekshirishda xatolik: {e}")
            return False

    # === МЕТОДЫ WHITELIST ГРУПП ===

    def add_group_to_whitelist(self, chat_id: int, title: str, admin_id: int) -> bool:
        """Добавить группу в whitelist"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO group_whitelist (chat_id, title, status, added_date, added_by)
                VALUES (%s, %s, 'active', CURRENT_TIMESTAMP, %s)
                ON CONFLICT (chat_id) 
                DO UPDATE SET title = EXCLUDED.title, status = 'active', 
                              added_date = CURRENT_TIMESTAMP, added_by = EXCLUDED.added_by
            """, (chat_id, title, admin_id))
            self.conn.commit()
            logger.info(f"Guruh {chat_id} whitelist ga qo'shildi")
            return True
        except Exception as e:
            logger.error(f"Guruh {chat_id} ni whitelist ga qo'shishda xatolik: {e}")
            return False

    def remove_group_from_whitelist(self, chat_id: int) -> bool:
        """Удалить группу из whitelist"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM group_whitelist WHERE chat_id = %s", (chat_id,))
            self.conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Guruh {chat_id} whitelist dan o'chirildi")
                return True
            return False
        except Exception as e:
            logger.error(f"Guruh {chat_id} ni whitelist dan o'chirishda xatolik: {e}")
            return False

    def remove_group_completely(self, chat_id: int) -> bool:
        """Полностью удалить группу из всех таблиц базы данных"""
        try:
            cursor = self.conn.cursor()
            
            # Удаляем из всех связанных таблиц
            # В group_video_settings chat_id имеет тип TEXT, поэтому приводим к строке
            cursor.execute("DELETE FROM group_video_settings WHERE chat_id = %s", (str(chat_id),))
            cursor.execute("DELETE FROM group_whitelist WHERE chat_id = %s", (str(chat_id),))
            cursor.execute("DELETE FROM users WHERE user_id = %s AND is_group = 1", (chat_id,))
            
            self.conn.commit()
            logger.info(f"Guruh {chat_id} barcha jadvallardan to'liq o'chirildi")
            return True
        except Exception as e:
            logger.error(f"Guruh {chat_id} ni to'liq o'chirishda xatolik: {e}")
            self.conn.rollback()
            return False

    def get_all_groups(self):
        """Получить список всех групп из базы данных, отсортированных по дате добавления (новые первыми)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT DISTINCT u.user_id, u.name, u.created_at
                FROM users u
                WHERE u.is_group = 1 
                ORDER BY u.created_at DESC, u.name
            """)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка при получении списка групп: {e}")
            return []

    def get_group_by_id(self, chat_id: int):
        """Получить информацию о группе по ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT user_id, name 
                FROM users 
                WHERE user_id = %s AND is_group = 1
            """, (chat_id,))
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Ошибка при получении информации о группе {chat_id}: {e}")
            return None

    def is_group_whitelisted(self, chat_id: int) -> bool:
        """Проверить находится ли группа в whitelist"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT status FROM group_whitelist 
                WHERE chat_id = %s AND status = 'active'
            """, (chat_id,))
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Guruh {chat_id} uchun whitelist ni tekshirishda xatolik: {e}")
            return False

    def get_whitelisted_groups(self) -> list:
        """Получить список групп в whitelist"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT chat_id, title, added_date, added_by
                FROM group_whitelist 
                WHERE status = 'active'
                ORDER BY added_date DESC
            """)
            results = cursor.fetchall()
            return [
                {
                    'chat_id': row[0], 'title': row[1], 
                    'added_date': row[2], 'added_by': row[3]
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Whitelist guruhlarini olishda xatolik: {e}")
            return []

    def get_group_whitelist_data(self, chat_id: int) -> dict:
        """Получить данные группы из whitelist"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT chat_id, title, status, added_date, added_by
                FROM group_whitelist WHERE chat_id = %s
            """, (chat_id,))
            result = cursor.fetchone()
            if result:
                return {
                    'chat_id': result[0], 'title': result[1], 'status': result[2],
                    'added_date': result[3], 'added_by': result[4]
                }
            return None
        except Exception as e:
            logger.error(f"Guruh {chat_id} ma'lumotlarini olishda xatolik: {e}")
            return None

    # === МИГРАЦИЯ ДАННЫХ ===
    
    def migrate_existing_groups_to_whitelist(self) -> int:
        """Мигрировать существующие группы в whitelist"""
        try:
            cursor = self.conn.cursor()
            
            # Получить все группы с настройками видео
            cursor.execute("""
                SELECT DISTINCT chat_id FROM group_video_settings 
                WHERE subscribed = true
            """)
            groups = cursor.fetchall()
            
            migrated_count = 0
            for (chat_id,) in groups:
                # Добавить в whitelist если еще нет
                cursor.execute("""
                    INSERT INTO group_whitelist (chat_id, title, status, added_date, added_by)
                    VALUES (%s, 'Migrated Group', 'active', CURRENT_TIMESTAMP, 0)
                    ON CONFLICT (chat_id) DO NOTHING
                """, (chat_id,))
                if cursor.rowcount > 0:
                    migrated_count += 1
            
            self.conn.commit()
            logger.info(f"{migrated_count} ta guruh whitelist ga ko'chirildi")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Guruhlarni whitelist ga ko'chirishda xatolik: {e}")
            return 0

    def migrate_existing_users_to_approved(self) -> int:
        """Мигрировать существующих пользователей как одобренных"""
        try:
            cursor = self.conn.cursor()
            
            # Получить всех существующих пользователей
            cursor.execute("SELECT DISTINCT user_id FROM users")
            users = cursor.fetchall()
            
            migrated_count = 0
            for (user_id,) in users:
                # Добавить как одобренного если еще нет
                cursor.execute("""
                    INSERT INTO user_security (user_id, name, phone, status, reg_date, approved_by)
                    VALUES (%s, 'Migrated User', 'Unknown', 'approved', CURRENT_TIMESTAMP, 0)
                    ON CONFLICT (user_id) DO NOTHING
                """, (user_id,))
                if cursor.rowcount > 0:
                    migrated_count += 1
            
            self.conn.commit()
            logger.info(f"{migrated_count} ta foydalanuvchi tasdiqlangan holatga ko'chirildi")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Foydalanuvchilarni ko'chirishda xatolik: {e}")
            return 0

    # === СОЗДАНИЕ ТАБЛИЦ БЕЗОПАСНОСТИ ===
    
    def create_security_tables(self):
        """Создать таблицы безопасности если их нет"""
        try:
            cursor = self.conn.cursor()
            
            # Таблица пользователей безопасности
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_security (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE,
                    name TEXT,
                    phone TEXT,
                    status TEXT DEFAULT 'pending',
                    reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_by BIGINT,
                    approved_date TIMESTAMP
                );
            """)
            
            # Таблица whitelist групп
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_whitelist (
                    id SERIAL PRIMARY KEY,
                    chat_id BIGINT UNIQUE,
                    title TEXT,
                    status TEXT DEFAULT 'active',
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    added_by BIGINT
                );
            """)
            
            self.conn.commit()
            logger.info("Xavfsizlik jadvallari yaratildi")
            
        except Exception as e:
            logger.error(f"Xavfsizlik jadvallarini yaratishda xatolik: {e}")

    def add_group_to_whitelist_auto(self, chat_id: int, title: str, admin_id: int) -> bool:
        """Автоматически добавить группу в whitelist при добавлении бота"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO group_whitelist (chat_id, title, status, added_date, added_by)
                VALUES (%s, %s, 'active', CURRENT_TIMESTAMP, %s)
                ON CONFLICT (chat_id) 
                DO UPDATE SET title = EXCLUDED.title, status = 'active', 
                              added_date = CURRENT_TIMESTAMP, added_by = EXCLUDED.added_by
            """, (chat_id, title, admin_id))
            self.conn.commit()
            cursor.close()
            logger.info(f"Группа {chat_id} автоматически добавлена в whitelist")
            return True
        except Exception as e:
            logger.error(f"Ошибка при автоматическом добавлении группы {chat_id} в whitelist: {e}")
            return False

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ВРЕМЕНЕМ ОТПРАВКИ ===
    
    def set_group_send_times(self, chat_id: int, send_times: list) -> bool:
        """Установить время отправки для группы"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO group_video_settings (chat_id, send_times)
                VALUES (%s, %s)
                ON CONFLICT (chat_id) DO UPDATE SET send_times = EXCLUDED.send_times
            """, (str(chat_id), json.dumps(send_times)))
            self.conn.commit()
            cursor.close()
            logger.info(f"Время отправки для группы {chat_id} установлено: {send_times}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при установке времени отправки для группы {chat_id}: {e}")
            self.conn.rollback()
            return False

    def get_group_send_times(self, chat_id: int) -> list:
        """Получить время отправки для группы"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT send_times FROM group_video_settings WHERE chat_id = %s", (str(chat_id),))
            result = cursor.fetchone()
            cursor.close()
            if result and result[0]:
                return json.loads(result[0])
            return ["07:00", "11:00", "20:00"]  # Время по умолчанию
        except Exception as e:
            logger.error(f"Ошибка при получении времени отправки для группы {chat_id}: {e}")
            return ["08:00", "20:00"]

    def set_send_times_for_all_groups(self, send_times: list) -> bool:
        """Массово установить время отправки для всех групп"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE group_video_settings
                SET send_times = %s
                """,
                (json.dumps(send_times),)
            )
            self.conn.commit()
            cursor.close()
            logger.info(f"Глобально обновлены send_times для всех групп: {send_times}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при глобальном обновлении send_times для всех групп: {e}")
            self.conn.rollback()
            return False

    def grant_access(self, user_id: int, hours: int = 24):
        """Предоставить доступ пользователю на указанное количество часов"""
        try:
            from datetime import datetime, timedelta
            cursor = self.conn.cursor()
            
            now = datetime.now()
            expires_at = now + timedelta(hours=hours)
            
            cursor.execute("""
                UPDATE users 
                SET access_granted_at = %s, access_expires_at = %s, is_banned = 0
                WHERE user_id = %s
            """, (now, expires_at, user_id))
            
            self.conn.commit()
            cursor.close()
            logger.info(f"Доступ предоставлен пользователю {user_id} до {expires_at}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при предоставлении доступа пользователю {user_id}: {e}")
            self.conn.rollback()
            return False

    def revoke_access(self, user_id: int):
        """Отозвать доступ у пользователя"""
        try:
            cursor = self.conn.cursor()
            from datetime import datetime
            cursor.execute("""
                UPDATE users 
                SET access_expires_at = %s, is_banned = 1
                WHERE user_id = %s
            """, (datetime.now(), user_id))
            
            self.conn.commit()
            cursor.close()
            logger.info(f"Доступ отозван у пользователя {user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при отзыве доступа у пользователя {user_id}: {e}")
            self.conn.rollback()
            return False

    def is_access_valid(self, user_id: int) -> bool:
        """Проверить, действителен ли доступ пользователя"""
        try:
            from datetime import datetime
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT access_expires_at, is_banned 
                FROM users 
                WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if not result:
                return False
                
            access_expires_at, is_banned = result
            
            # Если пользователь забанен
            if is_banned:
                return False
                
            # Если время доступа не установлено, считаем доступ действительным
            if not access_expires_at:
                return True
                
            # Проверяем, не истек ли доступ
            now = datetime.now()
            return now < access_expires_at
            
        except Exception as e:
            logger.error(f"Ошибка при проверке доступа пользователя {user_id}: {e}")
            return False

    def get_expired_users(self):
        """Получить список пользователей с истекшим доступом"""
        try:
            from datetime import datetime
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT user_id, name, access_expires_at
                FROM users 
                WHERE access_expires_at IS NOT NULL 
                AND access_expires_at < %s 
                AND is_banned = 0
            """, (datetime.now(),))
            
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении пользователей с истекшим доступом: {e}")
            return []

    def auto_revoke_expired_access(self):
        """Автоматически отозвать доступ у пользователей с истекшим временем"""
        try:
            from datetime import datetime
            cursor = self.conn.cursor()
            
            # Получаем пользователей с истекшим доступом
            expired_users = self.get_expired_users()
            
            if not expired_users:
                cursor.close()
                return 0
                
            # Отзываем доступ
            cursor.execute("""
                UPDATE users 
                SET is_banned = 1
                WHERE access_expires_at IS NOT NULL 
                AND access_expires_at < %s 
                AND is_banned = 0
            """, (datetime.now(),))
            
            revoked_count = cursor.rowcount
            self.conn.commit()
            cursor.close()
            
            logger.info(f"Автоматически отозван доступ у {revoked_count} пользователей")
            return revoked_count
            
        except Exception as e:
            logger.error(f"Ошибка при автоматическом отзыве доступа: {e}")
            self.conn.rollback()
            return 0

# create_security_tables метод уже определен в классе Database

# Создание экземпляра базы данных
db = Database()
