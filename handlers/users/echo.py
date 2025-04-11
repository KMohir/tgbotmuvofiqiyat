from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiogram.dispatcher.filters.builtin import Command, Text

from db import db
from loader import dp
from keyboards.default.reply import get_lang_for_button, change_lang
from states.state import answer, language
from translation import _

# Обработчик для смены языка
@dp.message_handler(Text(equals=["/change_language", "Tilni o'zgartirish", "Смена языка"]))
async def change_language(message: types.Message):
    if not db.user_exists(message.from_user.id):
        await message.answer("Пожалуйста, зарегистрируйтесь с помощью команды /start.")
        return

    lang = db.get_lang(message.from_user.id)
    await message.answer(_('Tilni tanlang', lang), reply_markup=change_lang())
    await language.lang.set()

@dp.message_handler(state=language.lang)
async def process_language_change(message: types.Message, state: FSMContext):
    if message.text == "O'zbek tili":
        db.change_lang(message.from_user.id, 'uz')
        await message.answer("Til o'zgartirildi", reply_markup=get_lang_for_button(message))
        await state.finish()
    elif message.text == "Русский язык":
        db.change_lang(message.from_user.id, 'ru')
        await message.answer("Язык был обновлен", reply_markup=get_lang_for_button(message))
        await state.finish()
    else:
        lang = db.get_lang(message.from_user.id)
        await message.answer(_("Iltimos, quyidagi tugmalardan birini tanlang", lang), reply_markup=change_lang())
        # Не завершаем состояние, чтобы пользователь мог выбрать язык

# Эхо хендлер для текстовых сообщений без указанного состояния
@dp.message_handler(state=None)
async def bot_echo(message: types.Message):
    if not db.user_exists(message.from_user.id):
        await message.answer("Пожалуйста, зарегистрируйтесь с помощью команды /start.")
        return

    lang = db.get_lang(message.from_user.id)
    await message.answer(_('Iltimos operator javobini kuting!', lang))

# Эхо хендлер для всех сообщений с указанным состоянием
@dp.message_handler(state="*", content_types=types.ContentTypes.ANY)
async def bot_echo_all(message: types.Message, state: FSMContext):
    if not db.user_exists(message.from_user.id):
        await message.answer("Пожалуйста, зарегистрируйтесь с помощью команды /start.")
        return

    lang = db.get_lang(message.from_user.id)
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(_('Iltimos operator javobini kuting!', lang))
    else:
        await message.answer(_('Pastdagi tugmani bosing', lang))