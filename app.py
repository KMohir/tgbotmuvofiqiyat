from aiogram import executor
from loader import dp, bot
import middlewares
import filters
import handlers
from utils.misc.set_bot_commands import set_default_commands
from utils.notify_admins import on_startup_notify
from handlers.users.video_scheduler import scheduler, init_scheduler
from db import db
from utils.safe_admin_notify import safe_send_error_notification
import logging
import traceback

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
import handlers.users.group_video_commands


async def global_error_handler(update, context):
    """
    Глобальный обработчик ошибок для всех хендлеров
    """
    try:
        # Логируем ошибку
        error_msg = f"Глобальная ошибка: {context.error}"
        logger.error(error_msg, exc_info=True)
        
        # Получаем детали ошибки
        error_details = traceback.format_exc()
        
        # Отправляем уведомление об ошибке
        try:
            await safe_send_error_notification(
                bot=bot,
                error_message=error_msg,
                error_details=error_details[:1000]  # Ограничиваем размер деталей
            )
        except Exception as notify_error:
            logger.error(f"Не удалось отправить уведомление об ошибке: {notify_error}")
        
        # Пытаемся отправить ответ пользователю
        try:
            if update and hasattr(update, 'message') and update.message:
                await update.message.answer(
                    "❌ Произошла ошибка при обработке вашего запроса. "
                    "Попробуйте позже или обратитесь к администратору."
                )
            elif update and hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.answer(
                    "❌ Произошла ошибка. Попробуйте позже.",
                    show_alert=True
                )
        except Exception as reply_error:
            logger.error(f"Не удалось отправить ответ пользователю: {reply_error}")
            
    except Exception as handler_error:
        logger.critical(f"Критическая ошибка в глобальном обработчике ошибок: {handler_error}")


# Регистрируем глобальный обработчик ошибок
dp.errors_handler()(global_error_handler)

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
        logger.info("Планировщик видео успешно начался")
    except Exception as e:
        logger.error(f"Ошибка при инициализации планировщика видео: {e}")


async def on_shutdown(dispatcher):
    try:
        if scheduler and hasattr(scheduler, 'shutdown'):
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
        await dispatcher.bot.session.close()
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