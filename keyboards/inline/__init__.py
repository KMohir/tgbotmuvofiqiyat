# Заглушка для inline keyboards
# Все функции перенесены в соответствующие handler файлы

def support_keyboard():
    """Заглушка для клавиатуры поддержки"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Поддержка", callback_data="support"))
    return keyboard

def support_callback():
    """Заглушка для callback поддержки"""
    return "support"

def cancel_support_callback():
    """Заглушка для отмены поддержки"""
    return "cancel_support"
