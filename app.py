from aiogram import executor
from tgbotmuvofiqiyat.loader import dp
import tgbotmuvofiqiyat.middlewares as middlewares
import tgbotmuvofiqiyat.filters as filters
import tgbotmuvofiqiyat.handlers as handlers
from tgbotmuvofiqiyat.utils.misc.set_bot_commands import set_default_commands
from tgbotmuvofiqiyat.utils.notify_admins import on_startup_notify
from tgbotmuvofiqiyat.handlers.users.video_scheduler import scheduler, init_scheduler
from tgbotmuvofiqiyat.db import db
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log',
    filemode='a',
    encoding='utf-8'
)

# Настраиваем логгер для проекта
logger = logging.getLogger(__name__)

# Устанавливаем уровень логирования для всех модулей проекта
logging.getLogger('handlers').setLevel(logging.INFO)
logging.getLogger('db').setLevel(logging.INFO)
logging.getLogger('utils').setLevel(logging.INFO)

db.create_tables()  # Автоматически создать все таблицы, если их нет

# Явно импортируем модуль команд групп для их регистрации
import tgbotmuvofiqiyat.handlers.users.group_video_commands

async def on_startup(dispatcher):
    # Установить команды бота
    await set_default_commands(dispatcher)
    
    # Проверяем зарегистрированные команды
    logger.info("🔍 Проверяем зарегистрированные команды...")
    try:
        commands = await dispatcher.bot.get_my_commands()
        logger.info(f"✅ Команды бота: {[cmd.command for cmd in commands]}")
    except Exception as e:
        logger.error(f"❌ Ошибка при получении команд: {e}")

    # Уведомить админов
    await on_startup_notify(dispatcher)

    # Инициализировать middleware
    middlewares.setup(dp)
    
    # Инициализировать планировщик видео
    try:
        await init_scheduler()
        logger.info("Планировщик видео успешно инициализирован")
    except Exception as e:
        logger.error(f"Ошибка при инициализации планировщика видео: {e}")


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