# Заглушка для keyboards модуля
# Все функции перенесены в соответствующие handler файлы

def get_lang_for_button(user_id, button_text):
    """Заглушка для функции выбора языка кнопки"""
    return button_text

def main_menu_keyboard():
    """Заглушка для главного меню"""
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton("Centris towers"))
    keyboard.add(KeyboardButton("Golden lake"))
    keyboard.add(KeyboardButton("Centris Towers bilan bog'lanish"))
    keyboard.add(KeyboardButton("Bino bilan tanishish"))
    return keyboard

def key():
    """Заглушка для функции key"""
    return "uz"
