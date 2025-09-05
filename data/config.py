from environs import Env
import logging
import os

# Логирование настраивается в app.py
logger = logging.getLogger(__name__)

# Теперь используем вместо библиотеки python-dotenv библиотеку environs
env = Env()
try:
    env.read_env()
except UnicodeDecodeError as e:
    logger.critical(f"Ошибка кодировки в файле .env: {e}")
    logger.critical("Убедитесь, что файл .env сохранен в кодировке UTF-8")
    raise
except Exception as e:
    logger.warning(f"Не удалось загрузить файл .env: {e}")
    logger.warning("Продолжаем работу с переменными окружения системы")

try:
    BOT_TOKEN = env.str("BOT_TOKEN", default="your_bot_token_here")  # Забираем значение типа str
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        logger.warning("BOT_TOKEN не найден в переменных окружения, используем значение по умолчанию")
        BOT_TOKEN = "your_bot_token_here"
except Exception as e:
    logger.critical(f"Ошибка при загрузке BOT_TOKEN: {e}")
    BOT_TOKEN = "your_bot_token_here"

try:
    admins_str = env.str("ADMINS", default="")
    if admins_str:
        # Разделяем по запятой и преобразуем в числа
        ADMINS = [int(admin_id.strip()) for admin_id in admins_str.split(',') if admin_id.strip()]
    else:
        ADMINS = []
    
    if not ADMINS:
        logger.warning("ADMINS не указаны в переменных окружения")
    else:
        logger.info(f"Загружены админы: {ADMINS}")
except Exception as e:
    logger.error(f"Ошибка при загрузке ADMINS: {e}")
    ADMINS = []

try:
    IP = env.str("ip", default="localhost")  # Тоже str, но для айпи адреса хоста
except Exception as e:
    logger.error(f"Ошибка при загрузке IP: {e}")
    IP = "localhost"

support_ids = [
    env.str("operator")
]

SUPER_ADMIN_IDS = [5657091547, 7983512278, 5310261745, 8053364577]  # Список супер-администраторов

# Обратная совместимость - оставляем старую переменную
SUPER_ADMIN_ID = 5657091547

# Пример строки для .env:
# ADMINS=5657091547,7983512278,5310261745
# Если переменная ADMINS уже есть, просто добавьте 5310261745 через запятую

# === НАСТРОЙКИ БЕЗОПАСНОСТИ ===
# Включить систему безопасности
SECURITY_ENABLED = True

# Автоматически покидать неразрешённые группы
AUTO_LEAVE_GROUPS = True

# Требовать регистрацию в приватных чатах
PRIVATE_REGISTRATION_REQUIRED = True
