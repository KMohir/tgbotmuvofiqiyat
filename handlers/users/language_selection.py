from aiogram import types
from aiogram.dispatcher import FSMContext
from loader import dp, bot
from states.state import RegistrationStates
from db import db

@dp.callback_query_handler(text_contains="lang_", state=RegistrationStates.lang)
async def set_lang(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    if not db.user_exists(call.from_user.id):
        lang = call.data[5:]
        async with state.proxy() as data:
            data['lang'] = lang

        if lang == 'uz':
            await bot.send_message(call.from_user.id, "Ism familiyangizni kiriting")
        elif lang == 'ru':
            await bot.send_message(call.from_user.id, "Введите свое имя и фамилию")
        await RegistrationStates.name.set()