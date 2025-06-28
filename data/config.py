from environs import Env
import logging
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# Теперь используем вместо библиотеки python-dotenv библиотеку environs
env = Env()
env.read_env()

try:
    BOT_TOKEN = env.str("BOT_TOKEN")  # Забираем значение типа str
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")
except Exception as e:
    logger.critical(f"Ошибка при загрузке BOT_TOKEN: {e}")
    raise

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
