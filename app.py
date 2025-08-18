from aiogram import executor
from loader import dp
import middlewares, filters, handlers
from utils.misc.set_bot_commands import set_default_commands
from utils.notify_admins import on_startup_notify
from handlers.users import admin_image_sender
# Явно импортируем обработчики команд
from handlers.users.admin_image_sender import set_group_video_command
from handlers.users.video_scheduler import scheduler, init_scheduler
from db import db
import asyncio
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.ERROR,  # Вернул обратно ERROR после диагностики
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger(__name__)

db.create_tables()  # Автоматически создать все таблицы, если их нет

print("dp в app.py:", id(dp))

async def on_startup(dispatcher):
    # Установить команды бота
    await set_default_commands(dispatcher)

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