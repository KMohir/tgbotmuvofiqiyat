from datetime import datetime, timedelta

try:

    from aiogram import types
    from aiogram.dispatcher import FSMContext
    from tgbotmuvofiqiyat.loader import dp, bot
    from tgbotmuvofiqiyat.states import RegistrationStates
    from tgbotmuvofiqiyat.db import db

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

except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('language selection ',  f"{time }formatted_date_time",f"error {exx}" )