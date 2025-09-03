import logging
import os
from logging.handlers import RotatingFileHandler

log_filename = f'bot_{os.getpid()}.log'  # уникальный лог-файл для каждого процесса

formatter = logging.Formatter(u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s')

file_handler = RotatingFileHandler(log_filename, maxBytes=1_000_000, backupCount=3, delay=True)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.ERROR)  # или другой уровень по необходимости

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.ERROR)

logger = logging.getLogger()
logger.setLevel(logging.ERROR)
logger.handlers = []  # очищаем старые обработчики
logger.addHandler(file_handler)
logger.addHandler(console_handler)
