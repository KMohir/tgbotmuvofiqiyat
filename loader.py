from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
from tgbotmuvofiqiyat.data import config
from tgbotmuvofiqiyat.db import db

# Логирование настраивается в app.py
logger = logging.getLogger(__name__)

try:
    # Инициализация бота
    bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    logger.info("Бот успешно инициализирован")
except Exception as e:
    logger.critical(f"Ошибка при инициализации бота: {e}")
    raise
