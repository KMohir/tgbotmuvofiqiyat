from datetime import datetime, timedelta

try:
    from aiogram import types
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.filters import Command, Text
    from aiogram.types import ReplyKeyboardRemove

    from data.config import support_ids
    from db import db
    from keyboards.default.reply import get_lang_for_button
    from keyboards.inline.support import support_keyboard, support_callback, cancel_support_callback
    from loader import dp, bot
    from states.state import RegistrationStates
    from aiogram import types
    from aiogram.dispatcher.filters import Text
    from loader import dp, bot
    from db import db

    @dp.message_handler(Text(equals=["/takliflar", "Takliflarni yuborish"]))
    async def ask_support(message: types.Message, state: FSMContext):
        user_id = 5657091547  # ID оператора поддержки
        back_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        back_button = types.KeyboardButton("Orqaga")
        back_keyboard.add(back_button)
        await message.answer(
            "Savolingizni yoki murojatingizni 1 ta habar orqali yuboring.",
            reply_markup=back_keyboard
        )
        await state.set_state("wait_for_support_message")
        await state.update_data(second_id=user_id)


    @dp.callback_query_handler(support_callback.filter(messages="one"))
    async def send_to_support(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
        await call.answer()
        user_id = int(callback_data.get("user_id"))

        await call.message.answer(
            "Savolingizni yoki murojatingizni 1 ta habar orqali yuboring.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state("wait_for_support_message")
        await state.update_data(second_id=user_id)


    @dp.message_handler(state="wait_for_support_message", content_types=types.ContentTypes.ANY)
    async def get_support_message(message: types.Message, state: FSMContext):
        data = await state.get_data()
        second_id = data.get("second_id")
        if message.text == "Orqaga":
            await message.answer(
                "Operatsiya bekor qilindi",
                reply_markup=get_lang_for_button(message)
            )
            await state.reset_state()
            return
        await message.answer(
            'Savolingiz / Murojatingiz bizning operatorlarga yuborildi, yaqin orada sizga javob beramiz!',
            reply_markup=ReplyKeyboardRemove()
        )
        name = db.get_name(message.from_user.id)
        phone = db.get_phone(message.from_user.id)
        for support_id in support_ids:
            if str(second_id) == support_id:
                try:
                    keyboard = await support_keyboard(message, messages="one", user_id=message.from_user.id)
                    db.add_questions(message.from_user.id, message.message_id)
                    a = db.get_id()
                    if message.text is None:
                        await message.copy_to(
                            second_id,
                            caption=f"Raqami: {a}\nI.SH.: {name}\nUsername: @{message.from_user.username}\nNomer: <code>{phone}</code>\nHabar: {message.caption or 'Matnsiz'}",
                            reply_markup=keyboard
                        )
                        await message.copy_to(
                            -1002601209038,
                            caption=f"Raqami: {a}\nI.SH.: {name}\nUsername: @{message.from_user.username}\nNomer: <code>{phone}</code>\nHabar: {message.caption or 'Matnsiz'}",
                            reply_markup=keyboard
                        )
                    else:
                        await bot.send_message(
                            second_id,
                            f"Raqami: {a}\nI.SH.: {name}\nUsername: @{message.from_user.username}\nNomer: <code>{phone}</code>\nHabar: {message.text}",
                            reply_markup=keyboard
                        )
                        await bot.send_message(
                            -1002601209038,
                            f"Raqami: {a}\nI.SH.: {name}\nUsername: @{message.from_user.username}\nNomer: <code>{phone}</code>\nHabar: {message.text}"
                        )
                except Exception as e:
                    print(f"Error sending to support: {e}")
                    continue
            else:
                db.add_questions(message.from_user.id, message.message_id)
                reply = db.get_question(second_id)
                keyboard = await support_keyboard(message, messages="one", user_id=message.from_user.id)
                try:
                    if message.text is None:
                        await message.copy_to(
                            second_id,
                            reply_to_message_id=reply,
                            caption=message.caption or "Matnsiz"
                        )
                    else:
                        await bot.send_message(
                            second_id,
                            message.text,
                            reply_to_message_id=reply
                        )
                except Exception as e:
                    print(f"Error replying to support: {e}")
                await bot.send_message(
                    second_id,
                    "Yana savolingiz yoki murojatingiz bo'lsa, /taklif orqali berishingiz mumkin.",
                    reply_markup=get_lang_for_button(message)
                )
        await state.reset_state()


    @dp.callback_query_handler(cancel_support_callback.filter(), state=["in_support", "wait_in_support", None])
    async def exit_support(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
        user_id = int(callback_data.get("user_id"))
        second_state = dp.current_state(user=user_id, chat=user_id)

        if await second_state.get_state() is not None:
            data_second = await second_state.get_data()
            second_id = data_second.get("second_id")
            if int(second_id) == call.from_user.id:
                await second_state.reset_state()
                await bot.send_message(user_id, "Foydalanuvchi texnik yordam seansini yakunladi")

        await call.message.answer("Centris Towers bu sizni bilimingzini sinash uchun qilingan platforma")
        await state.reset_state()


    @dp.message_handler(Text(equals=["/about", "Bino bilan tanishish"]))
    async def bot_help(message: types.Message):
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                text="Centris Towers botiga o'tish",
                url="https://t.me/centris_towers_sells_bot"
            )
        )
        caption = (
            "Centris Towers binolari haqida ko'proq ma'lumot olish uchun quyidagi tugmani bosing:"
        )
        await message.answer(
            caption,
            reply_markup=markup
        )

except Exception as exx:
    from datetime import datetime

    # Получить текущие дату и время
    now = datetime.now()

    # Форматировать дату и время
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print('support call ',  f"{time }formatted_date_time",f"error {exx}" )