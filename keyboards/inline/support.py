# Файл с inline клавиатурами для поддержки
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def support_keyboard():
    """Клавиатура поддержки"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Поддержка", callback_data="support"))
    return keyboard

def support_callback():
    """Callback для поддержки"""
    return "support"

def cancel_support_callback():
    """Callback для отмены поддержки"""
    return "cancel_support"
