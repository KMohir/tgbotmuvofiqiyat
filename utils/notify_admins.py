import logging

from aiogram import Dispatcher
from utils.safe_admin_notify import safe_send_to_admins


async def on_startup_notify(dp: Dispatcher):
    """Уведомляет администраторов о запуске бота"""
    success_count = await safe_send_to_admins(dp.bot, "Bot Ishga  Tushirildi")
    
    if success_count > 0:
        logging.info(f"Уведомление о запуске отправлено {success_count} администраторам")
    else:
        logging.warning("Не удалось отправить уведомление о запуске ни одному администратору")
