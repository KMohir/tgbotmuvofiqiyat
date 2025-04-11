from sqlite3 import DatabaseError

from aiogram import executor

from db import create_database  # Оставляем импорт для совместимости, но можем не использовать
from loader import dp
import middlewares, filters, handlers
from utils.misc.set_bot_commands import set_default_commands
from utils.notify_admins import on_startup_notify
from handlers.users.video_scheduler import scheduler  # Импортируем scheduler из video_scheduler.py


async def on_startup(dispatcher):
    print("Бот запускается...")
    await set_default_commands(dispatcher)
    print("Команды бота установлены.")

    await on_startup_notify(dispatcher)
    print("Администраторы уведомлены.")

    # База данных уже создана при инициализации db в db.py
    print("База данных уже инициализирована в db.py.")

    # Запускаем планировщик после старта цикла событий
    print("Запускаем планировщик...")
    try:
        scheduler.start()
        print("Планировщик успешно запущен.")
    except Exception as e:
        print(f"Ошибка при запуске планировщика: {e}")


if __name__ == '__main__':
    try:
        executor.start_polling(dp, on_startup=on_startup)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")