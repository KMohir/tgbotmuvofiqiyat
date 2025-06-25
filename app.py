from aiogram import executor
from loader import dp
import middlewares, filters, handlers
from utils.misc.set_bot_commands import set_default_commands
from utils.notify_admins import on_startup_notify
from handlers.users.video_scheduler import scheduler, init_scheduler
from db import db
import asyncio
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger(__name__)

async def on_startup(dispatcher):
    # Уведомляет про запуск
    await on_startup_notify(dispatcher)
    await set_default_commands(dispatcher)

    # Запускаем планировщик (video_scheduler() удалён)

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