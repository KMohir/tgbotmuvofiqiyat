from aiogram.dispatcher.filters.state import State, StatesGroup

class SecurityStates(StatesGroup):
    """Состояния для системы безопасности"""
    waiting_name = State()
    waiting_phone = State()
