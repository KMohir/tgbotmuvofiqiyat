from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from translation import _


def get_lang_for_button(message):
    button = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Centris towers"),

            ],
            [
                KeyboardButton(text="Olden lake 1.0")
            ],
            [
                KeyboardButton(text="Centris Towers bilan bog'lanish")
            ],
            [
                KeyboardButton(text="Bino bilan tanishish")
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


main_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_keyboard.add(KeyboardButton("Centris towers"), KeyboardButton("Olden lake 1.0"))