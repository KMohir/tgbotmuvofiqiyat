# Заглушка для states модуля
# Все состояния перенесены в соответствующие handler файлы

from aiogram.dispatcher.filters.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """Заглушка для состояний регистрации"""
    waiting_for_name = State()
    waiting_for_phone = State()
    name = State()
    phone = State()

class SecurityStates(StatesGroup):
    """Заглушка для состояний безопасности"""
    waiting_for_password = State()
    waiting_name = State()
    waiting_phone = State()
    waiting_password = State()

class TimeSelection(StatesGroup):
    """Заглушка для выбора времени"""
    waiting_for_time = State()
    waiting_time = State()

# Другие заглушки
answer = {}
questions = {}
language = {}
ImageCollection = {}
