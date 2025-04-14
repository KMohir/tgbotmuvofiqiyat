from aiogram import executor
from loader import dp
import middlewares, filters, handlers
from utils.misc.set_bot_commands import set_default_commands
from utils.notify_admins import on_startup_notify
from handlers.users.video_scheduler import scheduler  # Импортируем scheduler
from db import db  # Импортируем db для закрытия соединения
import asyncio

from data import config

async def on_startup(dispatcher):
    # Используем существующий объект bot из dp
    bot = dispatcher.bot

    # Удаляем вебхук перед запуском polling
    print("Удаляем webhook...")
    for attempt in range(3):  # Пробуем удалить вебхук до 3 раз
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            print("Webhook успешно удалён.")
            break  # Если успешно, выходим из цикла
        except Exception as e:
            print(f"Попытка {attempt + 1}: Ошибка при удалении webhook: {e}")
            if attempt == 2:  # Если последняя попытка не удалась
                raise Exception("Не удалось удалить webhook после 3 попыток")
            await asyncio.sleep(1)  # Ждём 1 секунду перед следующей попыткой

    # Дополнительно проверяем, что вебхук удалён
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url:
        raise Exception(f"Webhook всё ещё активен: {webhook_info.url}. Пожалуйста, удалите его вручную через API.")

    # Устанавливаем команды бота
    print("Устанавливаем команды бота...")
    try:
        await set_default_commands(dispatcher)
        print("Команды бота установлены.")
    except Exception as e:
        print(f"Ошибка при установке команд: {e}")

    # Уведомляем администраторов
    print("Уведомляем администраторов...")
    try:
        await on_startup_notify(dispatcher)
        print("Администраторы уведомлены.")
    except Exception as e:
        print(f"Ошибка при уведомлении администраторов: {e}")

    # База данных уже создана при инициализации db в db.py
    print("База данных уже инициализирована в db.py.")

    # Запускаем планировщик после старта цикла событий
    print("Запускаем планировщик...")
    try:
        scheduler.start()
        print("Планировщик успешно запущен.")
    except Exception as e:
        print(f"Ошибка при запуске планировщика: {e}")

async def on_shutdown(dispatcher):
    print("Остановка бота...")
    try:
        # Останавливаем планировщик
        scheduler.shutdown()
        print("Планировщик остановлен.")
    except Exception as e:
        print(f"Ошибка при остановке планировщика: {e}")

    try:
        # Закрываем соединение с базой данных
        db.close()
        print("Соединение с базой данных закрыто.")
    except Exception as e:
        print(f"Ошибка при закрытии базы данных: {e}")

    # Закрываем сессию бота
    try:
        await dispatcher.bot.close()
        print("Сессия бота закрыта.")
    except Exception as e:
        print(f"Ошибка при закрытии сессии бота: {e}")

if __name__ == '__main__':
    try:
        executor.start_polling(
            dp,
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown
        )
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")