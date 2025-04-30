from aiogram import executor
from loader import dp
import middlewares, filters, handlers
from utils.misc.set_bot_commands import set_default_commands
from utils.notify_admins import on_startup_notify
from handlers.users.video_scheduler import scheduler, init_scheduler
from db import db
import asyncio
import logging
import sqlite3

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger(__name__)

def init_database():
    """Инициализация базы данных и создание всех необходимых таблиц"""
    try:
        conn = sqlite3.connect("databaseprotestim.db")
        cursor = conn.cursor()

        # Создаем таблицу users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                phone TEXT,
                datetime TEXT,
                video_index INTEGER DEFAULT 0,
                preferred_time TEXT DEFAULT "09:00",
                last_sent TEXT DEFAULT NULL,
                is_subscribed INTEGER DEFAULT 1,
                viewed_videos TEXT DEFAULT '[]'
            )
        ''')

        # Создаем таблицу videos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                video_index INTEGER PRIMARY KEY,
                file_id TEXT NOT NULL,
                caption TEXT
            )
        ''')

        # Создаем таблицу support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS support (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                datetime TEXT
            )
        ''')

        # Создаем таблицу settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Проверяем наличие столбца viewed_videos в таблице users
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'viewed_videos' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN viewed_videos TEXT DEFAULT '[]'")
            logger.info("Добавлен столбец viewed_videos в таблицу users")

        conn.commit()
        logger.info("База данных успешно инициализирована")
        print("База данных успешно инициализирована")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        print(f"Ошибка при инициализации базы данных: {e}")
    finally:
        conn.close()

async def on_startup(dispatcher):
    # Инициализируем базу данных
    try:
        init_database()
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")

    # Устанавливаем команды бота
    try:
        await set_default_commands(dispatcher)
        logger.info("Команды бота успешно установлены")
    except Exception as e:
        logger.error(f"Ошибка при установке команд: {e}")

    # Уведомляем администраторов
    try:
        await on_startup_notify(dispatcher)
        logger.info("Администраторы успешно уведомлены")
    except Exception as e:
        logger.error(f"Ошибка при уведомлении администраторов: {e}")

    # Инициализируем планировщик
    try:
        logger.info("Начало инициализации планировщика")
        await init_scheduler()
        logger.info("Планировщик успешно инициализирован")
        
        # Проверяем, запущен ли планировщик
        if scheduler.running:
            logger.info("Планировщик запущен")
            # Получаем список всех задач
            jobs = scheduler.get_jobs()
            logger.info(f"Количество активных задач: {len(jobs)}")
            for job in jobs:
                logger.info(f"Задача: {job.id}, следующее выполнение: {job.next_run_time}")
        else:
            logger.error("Планировщик не запущен!")
            
    except Exception as e:
        logger.error(f"Ошибка при инициализации планировщика: {e}")

async def on_shutdown(dispatcher):
    try:
        scheduler.shutdown()
        logger.info("Планировщик успешно остановлен")
    except Exception as e:
        logger.error(f"Ошибка при остановке планировщика: {e}")

    try:
        if db:
            db.close()
            logger.info("Соединение с базой данных успешно закрыто")
    except Exception as e:
        logger.error(f"Ошибка при закрытии базы данных: {e}")

    try:
        await dispatcher.bot.close()
        logger.info("Сессия бота успешно закрыта")
    except Exception as e:
        logger.error(f"Ошибка при закрытии сессии бота: {e}")

if __name__ == '__main__':
    try:
        logger.info("Запуск бота...")
        executor.start_polling(
            dp,
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown
        )
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        raise