from datetime import datetime, timedelta

try:

    from aiogram import types
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.filters import Command, Text
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
    from tgbotmuvofiqiyat.loader import dp, bot
    from tgbotmuvofiqiyat.db import db
    from tgbotmuvofiqiyat.states import TimeSelection
    def get_lang_for_button(message):
        button = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Yangiliklarni soat nechida olishni hohlaysiz?")
                ],
                [
                    KeyboardButton(text="FAQ ?")
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
    # Создаём клавиатуру с предопределёнными временами
    def get_time_keyboard():
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        times = ["09:00", "12:00", "15:00", "18:00", "21:00"]
        for time in times:
            markup.add(KeyboardButton(time))
        markup.add(KeyboardButton("Orqaga qaytish"))
        return markup

    @dp.message_handler(Command("time"))
    @dp.message_handler(Text(equals="Yangiliklarni soat nechida olishni hohlaysiz?"))
    async def cmd_time(message: types.Message, state: FSMContext):
        if not db.user_exists(message.from_user.id):
            await message.answer("Iltimos, /start buyrug'i bilan ro'yxatdan o'ting.")
            return


        await message.answer(
            "Iltimos, videolar qaysi soatda yuborilishini tanlang:",
            reply_markup=get_time_keyboard()
        )
        await TimeSelection.time.set()
        current_state = await state.get_state()



    @dp.message_handler(lambda message: not message.text.startswith('/'), state=TimeSelection.time)
    async def process_time(message: types.Message, state: FSMContext):

        time_input = message.text


        if time_input == "Orqaga qaytish":
            await message.answer("Vaqt tanlash bekor qilindi.", reply_markup=ReplyKeyboardRemove())
            await state.finish()

            return

        try:
            hours, minutes = map(int, time_input.split(":"))
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                await message.answer(
                    "Noto'g'ri format! Iltimos, quyidagi tugmalardan birini tanlang:",
                    reply_markup=get_time_keyboard()
                )

                return
        except ValueError:
            await message.answer(
                "Noto'g'ri format! Iltimos, quyidagi tugmalardan birini tanlang:",
                reply_markup=get_time_keyboard()
            )

            return

        try:
            db.set_preferred_time(message.from_user.id, time_input)
            await message.answer(
                f"Videolar har kuni soat {time_input} da yuboriladi.",
                reply_markup=get_lang_for_button(message)
            )
        except Exception as e:
            await message.answer("Vaqtni saqlashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
            print(e)

            return

        await state.finish()
except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('time', formatted_date_time, f"error {exx}")