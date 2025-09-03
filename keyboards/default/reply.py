# Файл с функциями для reply клавиатур
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_lang_for_button(user_id, button_text):
    """Функция для выбора языка кнопки"""
    return button_text

def main_menu_keyboard():
    """Главное меню клавиатура"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton("Centris towers"))
    keyboard.add(KeyboardButton("Golden lake"))
    keyboard.add(KeyboardButton("Centris Towers bilan bog'lanish"))
    keyboard.add(KeyboardButton("Bino bilan tanishish"))
    return keyboard

def key():
    """Функция для получения языка"""
    return "uz"
