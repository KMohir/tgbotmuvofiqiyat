from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from translation import _


def get_lang_for_button(message):
    button = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Yangiliklarni soat nechida olishni hohlaysiz?")
            ],
            [
                KeyboardButton(text="Video kontentlar")
            ],
            [
                KeyboardButton(text="Centris Towers bilan bog'lanish")
            ],
            [
                KeyboardButton(text="Centris Towers haqida bilish")
            ],
        ],
        resize_keyboard=True
    )
    return button


def key():
    keyboardcontakt = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Kontakni yuborish", request_contact=True)
            ],
        ],
        resize_keyboard=True
    )
    return keyboardcontakt