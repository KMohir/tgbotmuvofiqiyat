import logging

# Настройка логирования
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)

# Создаем логгер
logger = logging.getLogger(__name__) 